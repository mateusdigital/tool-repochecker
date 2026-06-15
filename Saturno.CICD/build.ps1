param(
    [string]$ProjectRoot = (Get-Location).ProviderPath,
    [string]$Preset = "Default",
    [ValidateSet("development", "production")][string]$Environment = "development",
    [ValidateSet("debug", "release")][string]$ExportMode = "release",
    [int]$BuildNumber,
    [string]$ReleaseName,
    [string]$BuildOutputDir,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$ForwardedArgs
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "shared.ps1")

$ResolvedProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).ProviderPath
$PackageJson = Get-SaturnoCicdPackageJson -ProjectRoot $ResolvedProjectRoot
$CicdConfig = Get-SaturnoCicdConfig -ProjectRoot $ResolvedProjectRoot -Optional
$BuildConfig = Get-SaturnoCicdMember -InputObject $CicdConfig -Name "build" -Optional

if ([string]::IsNullOrWhiteSpace($ReleaseName)) {
    $EffectiveBuildNumber = if ($BuildNumber -gt 0) { $BuildNumber } else { [int]$PackageJson.build }
    $ReleaseName = "$($PackageJson.name)-$($PackageJson.version)-build.$EffectiveBuildNumber"
}

if ([string]::IsNullOrWhiteSpace($BuildOutputDir)) {
    $BuildOutputDir = Join-Path (Join-Path $ResolvedProjectRoot "__BUILD") $ReleaseName
}

$ConfiguredStageRoot = [string](Get-SaturnoCicdMember -InputObject $BuildConfig -Name "stagingRoot" -Optional)
$BuildStageDir = Resolve-SaturnoCicdPath -ProjectRoot $ResolvedProjectRoot -ConfiguredPath $ConfiguredStageRoot -DefaultRelativePath (Join-Path "__BUILD" "_staging")
$ExpectedFiles = @(Get-SaturnoCicdMember -InputObject $BuildConfig -Name "expectedFiles" -Optional) | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) }

Write-Host "==> Building: $ReleaseName"
Write-Host "==> Preset: $Preset"
Write-Host "==> Environment: $Environment"
Write-Host "==> Export mode: $ExportMode"
Write-Host "==> Stage directory: $BuildStageDir"
Write-Host "==> Release directory: $BuildOutputDir"

Invoke-SaturnoCicdNpmScript -ProjectRoot $ResolvedProjectRoot -ScriptName "build" -Arguments $ForwardedArgs

if (-not (Test-Path -LiteralPath $BuildStageDir -PathType Container)) {
    throw "Build stage directory not found: $BuildStageDir"
}

$MissingFiles = @($ExpectedFiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $BuildStageDir $_) -PathType Leaf) })
if ($MissingFiles.Count -gt 0) {
    throw "Build staging output is missing expected artifacts: $($MissingFiles -join ', ')"
}

Remove-Item -LiteralPath $BuildOutputDir -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $BuildOutputDir | Out-Null
Get-ChildItem -LiteralPath $BuildStageDir -Force | ForEach-Object {
    if ([string]::Equals($_.FullName, $BuildOutputDir, [System.StringComparison]::OrdinalIgnoreCase)) {
        return
    }
    Copy-Item -LiteralPath $_.FullName -Destination $BuildOutputDir -Recurse -Force
}

Write-Host "==> Done"
