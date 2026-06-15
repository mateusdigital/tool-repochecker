$ScriptFullPath = $MyInvocation.MyCommand.Path
$ScriptDir = Split-Path $ScriptFullPath -Parent
$RepoCheckerExe = Join-Path $ScriptDir "repochecker.py"

if (-not $script:REPOCHECKER_PYTHON_EXE) {
    $script:REPOCHECKER_PYTHON_EXE = "python"
    $script:REPOCHECKER_PYTHON_ARGS = @()

    if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
        if (Get-Command "python3" -ErrorAction SilentlyContinue) {
            $script:REPOCHECKER_PYTHON_EXE = "python3"
        }
        elseif (Get-Command "py" -ErrorAction SilentlyContinue) {
            $script:REPOCHECKER_PYTHON_EXE = "py"
            $script:REPOCHECKER_PYTHON_ARGS = @("-3")
        }
    }
}

& $script:REPOCHECKER_PYTHON_EXE @($script:REPOCHECKER_PYTHON_ARGS) $RepoCheckerExe $args
