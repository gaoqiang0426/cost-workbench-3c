$ErrorActionPreference = "Stop"

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "未找到 winget。请从 https://www.python.org/downloads/windows/ 手动安装 Python 3.12，并勾选 Add python.exe to PATH。"
}

winget install --id Python.Python.3.12 --source winget --scope user --accept-package-agreements --accept-source-agreements

Write-Host ""
Write-Host "Python 3.12 安装命令已执行。请关闭并重新打开 PowerShell，然后运行："
Write-Host "cd D:\work\codex\03-cost"
Write-Host ".\run_app.ps1"

