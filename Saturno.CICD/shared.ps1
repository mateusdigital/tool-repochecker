function Get-SaturnoCicdMember {
    param(
        $InputObject,
        [Parameter(Mandatory = $true)][string]$Name,
        [switch]$Optional
    )

    if ($null -ne $InputObject -and $InputObject.PSObject.Properties.Name -contains $Name) {
        return $InputObject.$Name
    }

    if ($Optional) {
        return $null
    }

    throw "Missing required Saturno.CICD configuration key '$Name'."
}

function Get-SaturnoCicdPackageJson {
    param([string]$ProjectRoot = (Get-Location).ProviderPath)

    $ResolvedProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).ProviderPath
    $PackageJsonPath = Join-Path $ResolvedProjectRoot "package.json"
    if (-not (Test-Path -LiteralPath $PackageJsonPath -PathType Leaf)) {
        throw "package.json not found at $PackageJsonPath"
    }

    return Get-Content -LiteralPath $PackageJsonPath -Raw | ConvertFrom-Json
}

function Get-SaturnoCicdConfig {
    param(
        [string]$ProjectRoot = (Get-Location).ProviderPath,
        [switch]$Optional
    )

    $PackageJson = Get-SaturnoCicdPackageJson -ProjectRoot $ProjectRoot
    $SaturnoConfig = Get-SaturnoCicdMember -InputObject $PackageJson -Name "saturno" -Optional
    $CicdConfig = Get-SaturnoCicdMember -InputObject $SaturnoConfig -Name "cicd" -Optional
    if ($null -ne $CicdConfig) {
        return $CicdConfig
    }

    if ($Optional) {
        return $null
    }

    throw "package.json is missing the saturno.cicd configuration block."
}

function Test-SaturnoCicdPackageJsonScript {
    param(
        [Parameter(Mandatory = $true)]$PackageJson,
        [Parameter(Mandatory = $true)][string]$Name
    )

    if ($null -eq $PackageJson -or $null -eq $PackageJson.scripts) {
        return $false
    }

    return $PackageJson.scripts.PSObject.Properties.Name -contains $Name
}

function Resolve-SaturnoCicdPath {
    param(
        [string]$ProjectRoot = (Get-Location).ProviderPath,
        [string]$ConfiguredPath,
        [Parameter(Mandatory = $true)][string]$DefaultRelativePath
    )

    $ResolvedProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).ProviderPath
    $EffectivePath = if ([string]::IsNullOrWhiteSpace($ConfiguredPath)) { $DefaultRelativePath } else { $ConfiguredPath }

    if ([IO.Path]::IsPathRooted($EffectivePath)) {
        return $EffectivePath
    }

    return Join-Path $ResolvedProjectRoot $EffectivePath
}

function Invoke-SaturnoCicdNpmScript {
    param(
        [string]$ProjectRoot = (Get-Location).ProviderPath,
        [Parameter(Mandatory = $true)][string]$ScriptName,
        [string[]]$Arguments = @()
    )

    $ResolvedProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).ProviderPath
    $NpmArguments = @("run", $ScriptName)
    if ($Arguments.Count -gt 0) {
        $NpmArguments += "--"
        $NpmArguments += $Arguments
    }

    Push-Location $ResolvedProjectRoot
    try {
        & npm @NpmArguments
        if ($LASTEXITCODE -ne 0) {
            throw "npm $($NpmArguments -join ' ') failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}

function Get-SaturnoCicdReleaseAssetPaths {
    param(
        [string]$ProjectRoot = (Get-Location).ProviderPath,
        [string]$PackageOutputDir,
        [string]$ReleaseArchivePath
    )

    if (-not [string]::IsNullOrWhiteSpace($ReleaseArchivePath) -and (Test-Path -LiteralPath $ReleaseArchivePath -PathType Leaf)) {
        return @($ReleaseArchivePath)
    }

    return @()
}

function Write-SaturnoCicdGitHubOutput {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [AllowNull()]$Value
    )

    if ([string]::IsNullOrWhiteSpace($env:GITHUB_OUTPUT)) {
        return
    }

    $RenderedValue = if ($Value -is [System.Collections.IEnumerable] -and -not ($Value -is [string])) {
        @($Value | ForEach-Object { [string]$_ }) -join [Environment]::NewLine
    }
    else {
        [string]$Value
    }

    "$Name=$RenderedValue" | Out-File -FilePath $env:GITHUB_OUTPUT -Encoding utf8 -Append
}
