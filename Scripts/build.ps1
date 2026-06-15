param(
    [string]$ProjectRoot = (Split-Path $PSScriptRoot -Parent),
    [string]$BuildOutputDir = (Join-Path $ProjectRoot "out/build"),
    [string]$ReleaseName = "repochecker"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).ProviderPath
$AppOutputDir = Join-Path $BuildOutputDir "App"

Write-Host "==> Building: $ReleaseName"

Remove-Item -LiteralPath $BuildOutputDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $AppOutputDir | Out-Null

$PackageJson = Join-Path $ProjectRoot "package.json"
if (-not (Test-Path -LiteralPath $PackageJson -PathType Leaf)) {
    throw "package.json not found at: $PackageJson"
}
Copy-Item -LiteralPath $PackageJson -Destination $BuildOutputDir -Force

$OptionalFiles = @("README.md", "COPYING.txt", "LICENSE", "AUTHORS.txt", "CHANGELOG.txt", "install.sh", "install.ps1")
foreach ($File in $OptionalFiles) {
    $Source = Join-Path $ProjectRoot $File
    if (Test-Path -LiteralPath $Source -PathType Leaf) {
        Copy-Item -LiteralPath $Source -Destination $BuildOutputDir -Force
    }
}

$AppFiles = @{
    "main.py" = "repochecker.py"
    "repochecker.ps1" = "repochecker.ps1"
    "repochecker.sh" = "repochecker.sh"
}

foreach ($Entry in $AppFiles.GetEnumerator()) {
    $Source = Join-Path $ProjectRoot "repochecker/$($Entry.Key)"
    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        throw "Required app file not found: $Source"
    }
    Copy-Item -LiteralPath $Source -Destination (Join-Path $AppOutputDir $Entry.Value) -Force
}

Write-Host "==> Done"
