# ============================================================
# RuyiDocsGPT 一键停止 (Windows PowerShell)
#   powershell -ExecutionPolicy Bypass -File .\ruyi\scripts\ruyi-stop.ps1
# 停止本仓库启动的后端(uvicorn) 与 worker(celery)。
# 只按 "命令行含 application.asgi / application.app.celery" 匹配, 不误伤其它 python。
# ============================================================
$ErrorActionPreference = "SilentlyContinue"

$procs = Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -match 'uvicorn application\.asgi' -or
  $_.CommandLine -match 'celery -A application\.app\.celery'
}

if (-not $procs) {
  Write-Host "没有发现运行中的 RuyiDocsGPT 服务。" -ForegroundColor Yellow
  exit 0
}

foreach ($p in $procs) {
  $short = $p.CommandLine
  if ($short.Length -gt 60) { $short = $short.Substring(0,60) + "..." }
  Write-Host ("停止 PID {0}: {1}" -f $p.ProcessId, $short)
  Stop-Process -Id $p.ProcessId -Force
}

Start-Sleep -Seconds 2
if (Get-NetTCPConnection -State Listen -LocalPort 7091 -ErrorAction SilentlyContinue) {
  Write-Host "[!] 7091 仍被占用, 可能有残留, 请手动检查。" -ForegroundColor Yellow
} else {
  Write-Host "已停止, 7091 已释放。" -ForegroundColor Green
}
