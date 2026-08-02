[CmdletBinding()]
param(
    [Parameter()]
    [string]$LicenserHost = $env:EPF_LICENSE_HOST
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Section {
    param([Parameter(Mandatory)][string]$Title)

    Write-Host ""
    Write-Host "=== $Title ===" -ForegroundColor Cyan
}

function Test-WingetPackage {
    param([Parameter(Mandatory)][string]$PackageId)

    $output = & winget list --id $PackageId --exact --source winget `
        --accept-source-agreements --disable-interactivity 2>&1 | Out-String
    return $LASTEXITCODE -eq 0 -and $output -match [regex]::Escape($PackageId)
}

function Install-WingetPackage {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$PackageId
    )

    if (Test-WingetPackage -PackageId $PackageId) {
        return [pscustomobject]@{
            Component = $Name
            Source = $PackageId
            Status = "Already present"
        }
    }

    & winget install --id $PackageId --exact --source winget --silent `
        --accept-package-agreements --accept-source-agreements --disable-interactivity
    if ($LASTEXITCODE -ne 0) {
        return [pscustomobject]@{
            Component = $Name
            Source = $PackageId
            Status = "FAILED"
        }
    }

    return [pscustomobject]@{
        Component = $Name
        Source = $PackageId
        Status = "Installed"
    }
}

function Install-Uv {
    $wasPresent = $null -ne (Get-Command uv -ErrorAction SilentlyContinue)
    $pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
    $python = Get-Command python -ErrorAction SilentlyContinue
    $pip = Get-Command pip -ErrorAction SilentlyContinue

    if ($null -ne $pythonLauncher) {
        & $pythonLauncher.Source -3.11 -m pip install uv
    }
    elseif ($null -ne $python) {
        & $python.Source -m pip install uv
    }
    elseif ($null -ne $pip) {
        & $pip.Source install uv
    }
    else {
        return [pscustomobject]@{
            Component = "uv"
            Source = "pip"
            Status = "FAILED (Python/pip not on PATH)"
        }
    }

    if ($LASTEXITCODE -ne 0) {
        $status = "FAILED"
    }
    elseif ($wasPresent) {
        $status = "Already present"
    }
    else {
        $status = "Installed"
    }

    return [pscustomobject]@{
        Component = "uv"
        Source = "pip"
        Status = $status
    }
}

function Find-AgentService {
    param([Parameter(Mandatory)][string]$Pattern)

    return Get-Service | Where-Object {
        $_.Name -match $Pattern -or $_.DisplayName -match $Pattern
    } | Select-Object -First 1
}

function New-CheckResult {
    param(
        [Parameter(Mandatory)][string]$Check,
        [Parameter(Mandatory)][bool]$Passed,
        [Parameter(Mandatory)][string]$Detail
    )

    $mark = if ($Passed) { [char]0x2713 } else { [char]0x2717 }
    return [pscustomobject]@{
        Status = $mark
        Check = $Check
        Detail = $Detail
        Passed = $Passed
    }
}

Write-Section "Tooling installation"
if ($null -eq (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "winget is required but was not found on PATH."
}

$packages = @(
    @{ Name = "Python 3.11"; Id = "Python.Python.3.11" }
    @{ Name = "Git"; Id = "Git.Git" }
    @{ Name = "Node LTS"; Id = "OpenJS.NodeJS.LTS" }
    @{ Name = "ripgrep"; Id = "BurntSushi.ripgrep.MSVC" }
)

$installResults = foreach ($package in $packages) {
    Install-WingetPackage -Name $package.Name -PackageId $package.Id
}
$installResults = @($installResults) + @(Install-Uv)
$installResults | Format-Table Component, Source, Status -AutoSize

Write-Section "Egress checks"
$urls = @(
    "https://jira.it.keysight.com",
    "https://bitbucket.it.keysight.com",
    $env:DAI_BASE_URL,
    $env:JARVIS_DAI_BASE_URL,
    $env:ANTHROPIC_BASE_URL
)
$urlNames = @(
    "Jira",
    "Bitbucket",
    "Production DAI",
    "JARVIS DAI",
    "Anthropic gateway"
)

$egressResults = for ($index = 0; $index -lt $urls.Count; $index++) {
    $url = $urls[$index]
    if ([string]::IsNullOrWhiteSpace($url)) {
        [pscustomobject]@{ Name = $urlNames[$index]; Url = "<empty>"; Status = "SKIP" }
        continue
    }

    try {
        $uri = [uri]$url
        $port = if ($uri.IsDefaultPort) {
            if ($uri.Scheme -eq "https") { 443 } else { 80 }
        }
        else {
            $uri.Port
        }
        $reachable = Test-NetConnection -ComputerName $uri.DnsSafeHost -Port $port `
            -InformationLevel Quiet -WarningAction SilentlyContinue
        $status = if ($reachable) { "OK" } else { "FAIL" }
    }
    catch {
        $status = "FAIL"
    }

    [pscustomobject]@{ Name = $urlNames[$index]; Url = $url; Status = $status }
}
$egressResults | Format-Table Name, Url, Status -AutoSize

Write-Section "Eggplant component verification (verify only)"
$componentResults = @()
$eggplantPaths = @(
    "C:\Program Files\Eggplant\Eggplant.exe",
    "C:\Program Files\Eggplant\Eggplant Functional\Eggplant.exe"
)
$eggplantPath = $eggplantPaths | Where-Object { Test-Path $_ -PathType Leaf } | Select-Object -First 1
$componentResults += New-CheckResult -Check "Eggplant Functional installed" `
    -Passed ($null -ne $eggplantPath) `
    -Detail $(if ($null -ne $eggplantPath) { $eggplantPath } else { "Executable not found" })

$runscriptPath = "C:\Program Files\Eggplant\runscript.bat"
$componentResults += New-CheckResult -Check "runscript.bat present" `
    -Passed (Test-Path $runscriptPath -PathType Leaf) -Detail $runscriptPath

if ([string]::IsNullOrWhiteSpace($LicenserHost)) {
    $licenseReachable = $false
    $licenseDetail = "Not provided; pass -LicenserHost or set EPF_LICENSE_HOST"
}
else {
    $licenseReachable = Test-NetConnection -ComputerName $LicenserHost `
        -InformationLevel Quiet -WarningAction SilentlyContinue
    $licenseDetail = $LicenserHost
}
$componentResults += New-CheckResult -Check "LicenserHost reachable" `
    -Passed $licenseReachable -Detail $licenseDetail

$designService = Find-AgentService -Pattern "EggplantDAIDesignAgent|Eggplant.*DAI.*Design"
$componentResults += New-CheckResult -Check "Design agent registered" `
    -Passed ($null -ne $designService) `
    -Detail $(if ($null -ne $designService) {
        "$($designService.Name) ($($designService.Status))"
    } else {
        "Windows service not found"
    })

$runService = Find-AgentService -Pattern "EggplantDAIRunAgent|Eggplant.*DAI.*Run"
$componentResults += New-CheckResult -Check "Run agent registered" `
    -Passed ($null -ne $runService) `
    -Detail $(if ($null -ne $runService) {
        "$($runService.Name) ($($runService.Status))"
    } else {
        "Windows service not found"
    })

$suitesPath = "C:\Eggplant_Suites"
$componentResults += New-CheckResult -Check "C:\Eggplant_Suites present" `
    -Passed (Test-Path $suitesPath -PathType Container) -Detail $suitesPath

$sutReachable = Test-NetConnection -ComputerName "Jay_130" -Port 3389 `
    -InformationLevel Quiet -WarningAction SilentlyContinue
$componentResults += New-CheckResult -Check "Jay_130 SUT reachable" `
    -Passed $sutReachable -Detail "Jay_130:3389 (RDP)"

$componentResults | Format-Table Status, Check, Detail -AutoSize
$passedChecks = @($componentResults | Where-Object Passed).Count
$totalChecks = $componentResults.Count
Write-Host "Total: $passedChecks / $totalChecks checks passed"

$installFailures = @($installResults | Where-Object { $_.Status -like "FAILED*" }).Count
$egressFailures = @($egressResults | Where-Object Status -eq "FAIL").Count
$componentFailures = $totalChecks - $passedChecks
if ($installFailures + $egressFailures + $componentFailures -gt 0) {
    exit 1
}
