$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "未找到 .venv。请先运行 .\run_app.ps1 创建普通 Python 3.10-3.12 虚拟环境。"
}

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements-geometry.txt

Write-Host ""
Write-Host "几何内核已安装。请重启 Streamlit："
Write-Host "cd D:\work\codex\03-cost"
Write-Host ".\run_app.ps1"

