param(
    [string]$ProjectRoot = (Split-Path $PSScriptRoot -Parent),
    [string]$Preset = "Default",
    [ValidateSet("development", "production")][string]$Environment = "development",
    [ValidateSet("debug", "release")][string]$ExportMode = "release",
    [int]$BuildNumber,
    [string]$ReleaseName,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$ForwardedArgs
)

$ErrorActionPreference = "Stop"

$ResolvedProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).ProviderPath
Push-Location $ResolvedProjectRoot
try {
    & npm test -- @ForwardedArgs
    if ($LASTEXITCODE -ne 0) {
        throw "npm test failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
