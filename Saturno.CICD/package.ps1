param(
    [string]$ProjectRoot = (Get-Location).ProviderPath,
    [string]$Preset = "Default",
    [ValidateSet("development", "production")][string]$Environment = "development",
    [ValidateSet("debug", "release")][string]$ExportMode = "release",
    [int]$BuildNumber,
    [string]$ReleaseName,
    [string]$BuildOutputDir,
    [string]$PackageOutputDir,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$ForwardedArgs
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "shared.ps1")

$ResolvedProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).ProviderPath
$PackageJson = Get-SaturnoCicdPackageJson -ProjectRoot $ResolvedProjectRoot
Add-Type -AssemblyName System.IO.Compression.FileSystem

if ([string]::IsNullOrWhiteSpace($ReleaseName)) {
    $EffectiveBuildNumber = if ($BuildNumber -gt 0) { $BuildNumber } else { [int]$PackageJson.build }
    $ReleaseName = "$($PackageJson.name)-$($PackageJson.version)-build.$EffectiveBuildNumber"
}

if ([string]::IsNullOrWhiteSpace($BuildOutputDir)) {
    $BuildOutputDir = Join-Path (Join-Path $ResolvedProjectRoot "__BUILD") $ReleaseName
}
if ([string]::IsNullOrWhiteSpace($PackageOutputDir)) {
    $PackageOutputDir = Join-Path (Join-Path $ResolvedProjectRoot "__DIST") $ReleaseName
}

$DistRoot = Split-Path -Parent $PackageOutputDir
$ArchivePath = Join-Path $DistRoot "$ReleaseName.zip"

if (-not (Test-Path -LiteralPath $BuildOutputDir -PathType Container)) {
    throw "Build output not found at $BuildOutputDir. Run build first."
}

Write-Host "==> Packaging: $ReleaseName"
Write-Host "==> Build input: $BuildOutputDir"
Write-Host "==> Package output: $PackageOutputDir"
Write-Host "==> Archive output: $ArchivePath"

Remove-Item -LiteralPath $PackageOutputDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $ArchivePath -Force -ErrorAction SilentlyContinue

if (Test-SaturnoCicdPackageJsonScript -PackageJson $PackageJson -Name "package") {
    $CustomPackageArguments = @(
        "-ProjectRoot", $ResolvedProjectRoot,
        "-Preset", $Preset,
        "-Environment", $Environment,
        "-ExportMode", $ExportMode,
        "-BuildNumber", "$BuildNumber",
        "-ReleaseName", $ReleaseName,
        "-BuildOutputDir", $BuildOutputDir,
        "-PackageOutputDir", $PackageOutputDir
    ) + $ForwardedArgs
    Invoke-SaturnoCicdNpmScript -ProjectRoot $ResolvedProjectRoot -ScriptName "package" -Arguments $CustomPackageArguments
}
else {
    New-Item -ItemType Directory -Force -Path $PackageOutputDir | Out-Null
    Get-ChildItem -LiteralPath $BuildOutputDir -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $PackageOutputDir -Recurse -Force
    }
}

if (-not (Test-Path -LiteralPath $PackageOutputDir -PathType Container)) {
    throw "Packaged output not found at $PackageOutputDir after packaging."
}

Push-Location $DistRoot
try {
    [System.IO.Compression.ZipFile]::CreateFromDirectory($PackageOutputDir, $ArchivePath, [System.IO.Compression.CompressionLevel]::Optimal, $true)
}
finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $ArchivePath -PathType Leaf)) {
    throw "Packaged archive not found at $ArchivePath after packaging."
}

$AssetPaths = @(Get-SaturnoCicdReleaseAssetPaths -ProjectRoot $ResolvedProjectRoot -PackageOutputDir $PackageOutputDir -ReleaseArchivePath $ArchivePath)
Write-SaturnoCicdGitHubOutput -Name "release_dir" -Value $PackageOutputDir
Write-SaturnoCicdGitHubOutput -Name "release_name" -Value $ReleaseName
Write-SaturnoCicdGitHubOutput -Name "archive_path" -Value $ArchivePath
Write-SaturnoCicdGitHubOutput -Name "asset_paths" -Value $AssetPaths
Write-SaturnoCicdGitHubOutput -Name "asset_paths_json" -Value ($AssetPaths | ConvertTo-Json -Compress)

Write-Host "==> Archive size bytes: $((Get-Item -LiteralPath $ArchivePath).Length)"
Write-Host "==> Done"
