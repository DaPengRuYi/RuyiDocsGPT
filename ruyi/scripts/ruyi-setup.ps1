# ============================================================
# RuyiDocsGPT 一键环境搭建 (Windows PowerShell)
#   powershell -ExecutionPolicy Bypass -File .\ruyi\scripts\ruyi-setup.ps1
# 做的事: 建 venv -> 装依赖 -> 检查 Redis/Postgres -> 提示配 .env
# 不装任何全局工具; 不写死任何密钥。
# ============================================================
$ErrorActionPreference = "Stop"

# 切到仓库根目录(脚本在 ruyi/scripts/ 下, 上两级即根)
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $RepoRoot
Write-Host "== 仓库根目录: $RepoRoot ==" -ForegroundColor Cyan

# 1) Python 检查
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { Write-Host "[X] 未找到 python, 请先装 Python 3.11" -ForegroundColor Red; exit 1 }
$pyver = (& python --version) 2>&1
Write-Host "[1/5] Python: $pyver"

# 2) 建 venv
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  Write-Host "[2/5] 创建虚拟环境 .venv ..."
  & python -m venv .venv
} else {
  Write-Host "[2/5] .venv 已存在, 跳过"
}
$venvPy = ".\.venv\Scripts\python.exe"

# 3) 装依赖(重: torch/docling/faiss 等, 首次较久)
Write-Host "[3/5] 升级 pip 并安装依赖(首次较久, 请耐心)..."
& $venvPy -m pip install --upgrade pip -q
& $venvPy -m pip install -r application\requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Host "[X] 依赖安装失败" -ForegroundColor Red; exit 1 }
Write-Host "    依赖安装完成"

# 4) 检查 Redis / Postgres
Write-Host "[4/5] 检查外部依赖..."
$redisUp = (Get-NetTCPConnection -State Listen -LocalPort 6379 -ErrorAction SilentlyContinue) -ne $null
if ($redisUp) { Write-Host "    [ok] Redis 在 6379 监听" -ForegroundColor Green }
else { Write-Host "    [!] 未检测到 Redis(6379). 请先启动 Redis" -ForegroundColor Yellow }

$pgUp = (Get-NetTCPConnection -State Listen -LocalPort 5432 -ErrorAction SilentlyContinue) -ne $null
if ($pgUp) { Write-Host "    [ok] Postgres 在 5432 监听" -ForegroundColor Green }
else { Write-Host "    [!] 未检测到 Postgres(5432). 请先启动 Postgres" -ForegroundColor Yellow }

Write-Host ""
Write-Host "    数据库说明: 本项目用隔离库 docsgpt(role/db 均为 docsgpt)。"
Write-Host "    若尚未创建, 用你的 PG 超级用户执行(密码自填, 勿写进脚本):"
Write-Host "      CREATE ROLE docsgpt LOGIN PASSWORD 'docsgpt' CREATEDB;" -ForegroundColor DarkGray
Write-Host "      CREATE DATABASE docsgpt OWNER docsgpt;" -ForegroundColor DarkGray
Write-Host "    (启动时 AUTO_MIGRATE 会自动建表, 无需手动跑迁移)"

# 5) .env 提示
Write-Host "[5/5] 配置文件..."
if (-not (Test-Path ".\.env")) {
  Write-Host "    未发现 .env。请复制模板并填入你的硅基流动 key:" -ForegroundColor Yellow
  Write-Host "      Copy-Item .\ruyi\.env.example .\.env" -ForegroundColor DarkGray
  Write-Host "      然后编辑 .env, 把 API_KEY 换成 sk-xxxx" -ForegroundColor DarkGray
} else {
  Write-Host "    [ok] .env 已存在" -ForegroundColor Green
}

Write-Host ""
Write-Host "== 环境搭建完成。下一步: .\ruyi\scripts\ruyi-start.ps1 ==" -ForegroundColor Cyan
