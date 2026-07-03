# ============================================================
# RuyiDocsGPT 一键启动 (Windows PowerShell)
#   powershell -ExecutionPolicy Bypass -File .\ruyi\scripts\ruyi-start.ps1
# 启动: 后端 uvicorn(:7091) + 文档索引 worker(celery, solo 池)
# 关键: 强制 UTF-8(规避中文 Windows 编码坑); worker 用 --pool=solo(Windows 必须)
# ============================================================
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $RepoRoot
$venvPy = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPy)) { Write-Host "[X] 未找到 .venv, 请先跑 ruyi-setup.ps1" -ForegroundColor Red; exit 1 }
if (-not (Test-Path ".\.env")) { Write-Host "[X] 未找到 .env, 请先复制 ruyi\.env.example 并填 key" -ForegroundColor Red; exit 1 }

# 端口占用检查
if (Get-NetTCPConnection -State Listen -LocalPort 7091 -ErrorAction SilentlyContinue) {
  Write-Host "[!] 7091 已被占用, 可能后端已在运行。如需重启请先跑 ruyi-stop.ps1" -ForegroundColor Yellow
  exit 1
}

# 统一 UTF-8 环境(关键)
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$logDir = Join-Path $RepoRoot "ruyi\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

Write-Host "== 启动后端 uvicorn :7091 ==" -ForegroundColor Cyan
Start-Process -FilePath $venvPy `
  -ArgumentList "-X","utf8","-m","uvicorn","application.asgi:asgi_app","--host","127.0.0.1","--port","7091","--log-level","info" `
  -WorkingDirectory $RepoRoot `
  -RedirectStandardOutput (Join-Path $logDir "backend.out.log") `
  -RedirectStandardError  (Join-Path $logDir "backend.err.log") `
  -WindowStyle Hidden

Write-Host "== 启动 worker celery(solo 池) ==" -ForegroundColor Cyan
Start-Process -FilePath $venvPy `
  -ArgumentList "-X","utf8","-m","celery","-A","application.app.celery","worker","--loglevel=INFO","--pool=solo","--concurrency=1" `
  -WorkingDirectory $RepoRoot `
  -RedirectStandardOutput (Join-Path $logDir "worker.out.log") `
  -RedirectStandardError  (Join-Path $logDir "worker.err.log") `
  -WindowStyle Hidden

# 等待后端健康
Write-Host "== 等待后端就绪(最多 ~60s, 首次含迁移可能稍久) =="
$ok = $false
for ($i=0; $i -lt 20; $i++) {
  Start-Sleep -Seconds 3
  try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:7091/api/health" -TimeoutSec 3 -UseBasicParsing
    if ($r.StatusCode -eq 200) { $ok = $true; break }
  } catch { }
}

if ($ok) {
  Write-Host ""
  Write-Host "== 已启动 ==" -ForegroundColor Green
  Write-Host "   后端: http://127.0.0.1:7091/api/health  -> {""status"":""ok""}"
  Write-Host "   日志: ruyi\logs\backend.*.log / worker.*.log"
  Write-Host "   停止: .\ruyi\scripts\ruyi-stop.ps1"
} else {
  Write-Host "[X] 后端未在预期时间内就绪, 请看 ruyi\logs\backend.err.log" -ForegroundColor Red
  exit 1
}
