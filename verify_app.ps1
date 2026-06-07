$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

function Get-CompatiblePython {
    $candidates = @()
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $candidates += @{ Command = "py"; Args = @("-3.12") }
        $candidates += @{ Command = "py"; Args = @("-3.11") }
        $candidates += @{ Command = "py"; Args = @("-3.10") }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $candidates += @{ Command = "python"; Args = @() }
    }

    foreach ($candidate in $candidates) {
        $output = & $candidate["Command"] @($candidate["Args"]) -c "import sys, sysconfig; print(f'{sys.version_info.major}.{sys.version_info.minor};{sysconfig.get_config_var('Py_GIL_DISABLED') or 0}')" 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $output) {
            continue
        }

        $parts = $output.Trim().Split(";")
        $version = [version]$parts[0]
        $freeThreaded = $parts[1] -ne "0"
        if ($version.Major -eq 3 -and $version.Minor -ge 10 -and $version.Minor -le 12 -and -not $freeThreaded) {
            return $candidate
        }
    }

    throw "未找到兼容的普通 Python 3.10-3.12。请运行 .\install_python_312.ps1 安装 Python 3.12，关闭并重开 PowerShell 后再运行 .\verify_app.ps1。不要使用 Python 3.13t/free-threaded。"
}

function Test-CompatibleVenv {
    if (-not (Test-Path ".venv\Scripts\python.exe")) {
        return $false
    }
    & ".venv\Scripts\python.exe" -c "import sys, sysconfig; raise SystemExit(0 if (sys.version_info.major == 3 and 10 <= sys.version_info.minor <= 12 and not sysconfig.get_config_var('Py_GIL_DISABLED')) else 1)"
    return $LASTEXITCODE -eq 0
}

if (-not (Test-CompatibleVenv)) {
    if (Test-Path ".venv") {
        $BackupName = ".venv.unsupported-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Move-Item -Path ".venv" -Destination $BackupName
        Write-Host "旧虚拟环境不兼容，已改名为 $BackupName"
    }
    $PythonLauncher = Get-CompatiblePython
    & $PythonLauncher["Command"] @($PythonLauncher["Args"]) -m venv .venv
}

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt
& $Python -m pytest tests -v
