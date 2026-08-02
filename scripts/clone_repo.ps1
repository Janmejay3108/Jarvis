[CmdletBinding()]
param(
    [Parameter()]
    [string]$RepoUrl = $env:BITBUCKET_REPO_URL,

    [Parameter()]
    [string]$ClonePath = "C:\agent\repo",

    [Parameter()]
    [string]$Branch = "Testing_Mar10",

    [Parameter()]
    [string]$AgenticUrl = $env:JARVIS_REPO_URL,

    [Parameter()]
    [string]$SuitesPath = "C:\Eggplant_Suites"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Git {
    param([Parameter(Mandatory)][string[]]$Arguments)

    & $script:GitPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "git command failed: git $($Arguments -join ' ')"
    }
}

function Register-JarvisTask {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][Microsoft.Management.Infrastructure.CimInstance[]]$Actions,
        [Parameter(Mandatory)][Microsoft.Management.Infrastructure.CimInstance]$Trigger,
        [Parameter(Mandatory)][string]$Description
    )

    Register-ScheduledTask -TaskName $Name -Action $Actions -Trigger $Trigger `
        -Description $Description -User "SYSTEM" -RunLevel Highest -Force | Out-Null
    return [pscustomobject]@{
        Item = $Name
        Status = "Registered"
    }
}

if ([string]::IsNullOrWhiteSpace($RepoUrl)) {
    throw "RepoUrl is required; pass -RepoUrl or set BITBUCKET_REPO_URL."
}
if ([string]::IsNullOrWhiteSpace($AgenticUrl)) {
    throw "AgenticUrl is required; pass -AgenticUrl or set JARVIS_REPO_URL."
}

$gitCommand = Get-Command git -ErrorAction Stop
$pythonCommand = Get-Command python -ErrorAction Stop
$script:GitPath = $gitCommand.Source
$pythonPath = $pythonCommand.Source
$projectRoot = Split-Path $PSScriptRoot -Parent
$summary = @()

if (Test-Path $ClonePath -PathType Container) {
    if (-not (Test-Path (Join-Path $ClonePath ".git") -PathType Container)) {
        throw "ClonePath exists but is not a git repository: $ClonePath"
    }
    $summary += [pscustomobject]@{ Item = "Production clone"; Status = "Already present" }
}
else {
    $cloneParent = Split-Path $ClonePath -Parent
    New-Item -ItemType Directory -Path $cloneParent -Force | Out-Null
    Invoke-Git -Arguments @("clone", $RepoUrl, $ClonePath)
    $summary += [pscustomobject]@{ Item = "Production clone"; Status = "Cloned" }
}

Invoke-Git -Arguments @("-C", $ClonePath, "checkout", $Branch)
$summary += [pscustomobject]@{ Item = "Production branch"; Status = $Branch }

$remoteNames = & $script:GitPath -C $ClonePath remote
if ($LASTEXITCODE -ne 0) {
    throw "Unable to list remotes in $ClonePath"
}
if ($remoteNames -contains "agentic-eggplant-automation") {
    Invoke-Git -Arguments @(
        "-C",
        $ClonePath,
        "remote",
        "set-url",
        "agentic-eggplant-automation",
        $AgenticUrl
    )
    $remoteStatus = "Updated"
}
else {
    Invoke-Git -Arguments @(
        "-C",
        $ClonePath,
        "remote",
        "add",
        "agentic-eggplant-automation",
        $AgenticUrl
    )
    $remoteStatus = "Added"
}
$summary += [pscustomobject]@{
    Item = "agentic-eggplant-automation remote"
    Status = $remoteStatus
}

$hourlyTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) `
    -RepetitionInterval (New-TimeSpan -Hours 1)
$nightlyTrigger = New-ScheduledTaskTrigger -Daily -At "02:00"
$productionPullAction = New-ScheduledTaskAction -Execute $script:GitPath `
    -Argument "-C `"$ClonePath`" pull --ff-only"
$suitesPullAction = New-ScheduledTaskAction -Execute $script:GitPath `
    -Argument "-C `"$SuitesPath`" pull --ff-only"

$handlerMapBuilder = Join-Path $projectRoot "scripts\build_handler_map.py"
$vocabularyBuilder = Join-Path $projectRoot "scripts\build_vocabulary.py"
$handlerMapOutput = Join-Path $projectRoot "tracks\enovia\handler_map.yaml"
$vocabularyOutput = Join-Path $projectRoot "tracks\enovia\handler_vocabulary.json"
$handlerMapAction = New-ScheduledTaskAction -Execute $pythonPath -Argument (
    "`"$handlerMapBuilder`" `"$ClonePath`" --output `"$handlerMapOutput`""
)
$vocabularyAction = New-ScheduledTaskAction -Execute $pythonPath -Argument (
    "`"$vocabularyBuilder`" `"$ClonePath`" --output `"$vocabularyOutput`""
)

$summary += Register-JarvisTask -Name "JARVIS Production Repo Hourly Pull" `
    -Actions @($productionPullAction) -Trigger $hourlyTrigger `
    -Description "Pull the Enovia production working copy hourly with --ff-only."
$summary += Register-JarvisTask -Name "JARVIS Static Knowledge Nightly Rebuild" `
    -Actions @($handlerMapAction, $vocabularyAction) -Trigger $nightlyTrigger `
    -Description "Rebuild the SenseTalk handler map and vocabulary nightly."
$summary += Register-JarvisTask -Name "JARVIS Validation Suites Hourly Pull" `
    -Actions @($suitesPullAction) -Trigger $hourlyTrigger `
    -Description "Pull the JARVIS validation suites clone hourly with --ff-only."

Write-Host ""
Write-Host "JARVIS clone and scheduled-task setup complete" -ForegroundColor Green
$summary | Format-Table Item, Status -AutoSize
Write-Host "Production clone: $ClonePath"
Write-Host "Validation suites: $SuitesPath"
Write-Host "Static outputs: $handlerMapOutput; $vocabularyOutput"
