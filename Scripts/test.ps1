param(
    [string]$ProjectRoot = (Split-Path $PSScriptRoot -Parent)
)

$ErrorActionPreference = "Stop"
$PythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "python3" }

Push-Location $ProjectRoot
try {
    & $PythonCmd -m pip install coverage
    if ($LASTEXITCODE -ne 0) { throw "pip install coverage failed." }

    & $PythonCmd -m coverage run -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw "Tests failed." }

    & $PythonCmd -m coverage report --fail-under=35
    if ($LASTEXITCODE -ne 0) { throw "Coverage below 35%." }
}
finally {
    Pop-Location
}
