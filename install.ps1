$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent
$HomeDir = if ($HOME -eq "") { "$env:USERPROFILE" } else { $HOME }
$ProgramName = "repochecker"
$RootPath = Join-Path $HomeDir ".saturnosoftware/$ProgramName"
$BinPath = Join-Path $RootPath "bin"
$ConfigPath = Join-Path $RootPath "config"
$DataPath = Join-Path $RootPath "data"

if (Test-Path -LiteralPath (Join-Path $ScriptDir "App") -PathType Container) {
    $SourcePath = Join-Path $ScriptDir "App"
}
elseif (Test-Path -LiteralPath (Join-Path $ScriptDir "repochecker") -PathType Container) {
    $SourcePath = Join-Path $ScriptDir "repochecker"
}
else {
    throw "[repochecker] Missing packaged App/ or source repochecker/ directory."
}

$PackageJson = Join-Path $ScriptDir "package.json"
if (-not (Test-Path -LiteralPath $PackageJson -PathType Leaf)) {
    throw "[repochecker] Missing package.json metadata file."
}

Write-Output "Installing ..."

foreach ($Dir in @($RootPath, $BinPath, $ConfigPath, $DataPath)) {
    if (-not (Test-Path -LiteralPath $Dir)) {
        Write-Output "  Creating: $Dir"
        $null = New-Item -Path $Dir -ItemType Directory -Force
    }
}

$PayloadMap = @(
    @{ SourceNames = @("repochecker.py", "main.py"); DestinationName = "repochecker.py" },
    @{ SourceNames = @("repochecker.ps1"); DestinationName = "repochecker.ps1" },
    @{ SourceNames = @("repochecker.sh"); DestinationName = "repochecker.sh" }
)

foreach ($Entry in $PayloadMap) {
    $Source = $null
    foreach ($SourceName in $Entry.SourceNames) {
        $Candidate = Join-Path $SourcePath $SourceName
        if (Test-Path -LiteralPath $Candidate -PathType Leaf) {
            $Source = $Candidate
            break
        }
    }
    if ([string]::IsNullOrWhiteSpace($Source) -or -not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        throw "[repochecker] Missing install payload: $($Entry.SourceNames -join ', ')"
    }
    Copy-Item -LiteralPath $Source -Destination (Join-Path $BinPath $Entry.DestinationName) -Force
}
Copy-Item -LiteralPath $PackageJson -Destination (Join-Path $RootPath "package.json") -Force

$InstalledEntrypoint = Join-Path $BinPath "repochecker.py"
$InstalledWrapper = Join-Path $BinPath "repochecker.ps1"
if (-not (Test-Path -LiteralPath $InstalledEntrypoint -PathType Leaf)) {
    throw "[repochecker] Installed Python entrypoint is missing: $InstalledEntrypoint"
}
if (-not (Test-Path -LiteralPath $InstalledWrapper -PathType Leaf)) {
    throw "[repochecker] Installed PowerShell wrapper is missing: $InstalledWrapper"
}

$VersionResult = & python $InstalledEntrypoint --version
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($VersionResult)) {
    throw "[repochecker] Post-install version smoke test failed."
}

Write-Output ""
Write-Output "$ProgramName was installed at:"
Write-Output "  $RootPath"
Write-Output "Binary directory:"
Write-Output "  $BinPath"
Write-Output "Data directory:"
Write-Output "  $DataPath"
Write-Output ""
Write-Output "You might need to add it to the PATH."
Write-Output "  Or source it directly: . `"$BinPath/repochecker.ps1`""
Write-Output ""
Write-Output "Done... ;D"
