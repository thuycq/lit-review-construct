param(
    [switch]$FullCleanup,
    [switch]$Yes
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallRoot = Join-Path $env:LOCALAPPDATA "LiteratureReviewConstruct"
$ManifestPath = Join-Path $InstallRoot "install-manifest.json"
$DefaultPackageName = "lit-review-construct"

Write-Host "Literature Review Construct uninstaller"
Write-Host ""
Write-Host "Research folders and .litreview project state are NEVER removed by this uninstaller."
Write-Host "uv and shared Python installations are also preserved."
Write-Host ""

if (-not $Yes) {
    if (-not $FullCleanup) {
        Write-Host "[1] Uninstall toolkit"
        Write-Host "    Remove LRC runtime, installed skills, command adapters, and injected context."
        Write-Host "    Keep LRC local settings/cache/manifest for future repair or reinstall."
        Write-Host ""
        Write-Host "[2] Full cleanup"
        Write-Host "    Remove toolkit components plus LRC local settings/cache/manifest."
        Write-Host "    Research projects are still preserved."
        Write-Host ""
        Write-Host "[3] Cancel"
        $choice = Read-Host "Choose 1, 2, or 3"
        switch ($choice) {
            "1" { }
            "2" { $FullCleanup = $true }
            default {
                Write-Host "Uninstall cancelled."
                exit 0
            }
        }
    } else {
        $confirm = Read-Host "Full cleanup will remove LRC local settings/cache. Continue? [y/N]"
        if ($confirm -notmatch '^(?i:y|yes)$') {
            Write-Host "Uninstall cancelled."
            exit 0
        }
    }
}

function Get-ManifestProperty {
    param(
        $Manifest,
        [Parameter(Mandatory = $true)][string]$Name,
        $Default = $null
    )
    if ($null -ne $Manifest -and $Manifest.PSObject.Properties.Name -contains $Name) {
        return $Manifest.$Name
    }
    return $Default
}

function Remove-ItemIfExists {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [switch]$Recurse
    )
    if (-not (Test-Path $Path)) { return }
    if ($Recurse) {
        Remove-Item -Recurse -Force $Path
    } else {
        Remove-Item -Force $Path
    }
    Write-Host "Removed: $Path"
}

function Remove-GeminiContextBlock {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path $Path)) { return }
    $content = Get-Content -Raw -Path $Path -ErrorAction SilentlyContinue
    if ($null -eq $content -or $content -notmatch "LITERATURE-REVIEW-CONSTRUCT:BEGIN") { return }

    $pattern = '(?s)\s*<!-- LITERATURE-REVIEW-CONSTRUCT:BEGIN -->.*?<!-- LITERATURE-REVIEW-CONSTRUCT:END -->\s*'
    $cleaned = [regex]::Replace($content, $pattern, [Environment]::NewLine).Trim()
    if ([string]::IsNullOrWhiteSpace($cleaned)) {
        Remove-Item -Force $Path
        Write-Host "Removed empty Gemini context file: $Path"
    } else {
        Set-Content -Encoding UTF8 -Path $Path -Value ($cleaned + [Environment]::NewLine)
        Write-Host "Removed LRC block from: $Path"
    }
}

$Manifest = $null
if (Test-Path $ManifestPath) {
    try {
        $Manifest = Get-Content -Raw -Path $ManifestPath | ConvertFrom-Json
    } catch {
        Write-Warning "The install manifest could not be read. Falling back to known LRC paths."
        $Manifest = $null
    }
}

$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$FallbackSkillRoots = @(
    (Join-Path $CodexHome "skills"),
    (Join-Path $HOME ".config\opencode\skills"),
    (Join-Path $HOME ".claude\skills"),
    (Join-Path $HOME ".agents\skills"),
    (Join-Path $HOME ".cursor\skills"),
    (Join-Path $HOME ".codeium\windsurf\skills"),
    (Join-Path $HOME ".copilot\skills"),
    (Join-Path $HOME ".cline\skills")
)

$SkillRoots = @(Get-ManifestProperty -Manifest $Manifest -Name "skill_roots" -Default $FallbackSkillRoots)
$SkillNames = @(Get-ManifestProperty -Manifest $Manifest -Name "skill_names" -Default @())
if ($SkillNames.Count -eq 0) {
    $skillSource = Join-Path $RepoRoot "skills"
    if (Test-Path $skillSource) {
        $SkillNames = @(Get-ChildItem -Path $skillSource -Directory | ForEach-Object { $_.Name })
    }
}

Write-Host "Removing LRC host integrations..."
foreach ($root in $SkillRoots) {
    if (-not $root) { continue }
    foreach ($skillName in $SkillNames) {
        if (-not $skillName) { continue }
        Remove-ItemIfExists -Path (Join-Path ([string]$root) ([string]$skillName)) -Recurse
    }
}

$OpenCodeCommandFiles = @(Get-ManifestProperty -Manifest $Manifest -Name "opencode_command_files" -Default @(
    (Join-Path $HOME ".config\opencode\commands\lr.md"),
    (Join-Path $HOME ".config\opencode\commands\lr-status.md")
))
$ClaudeCommandFiles = @(Get-ManifestProperty -Manifest $Manifest -Name "claude_command_files" -Default @(
    (Join-Path $HOME ".claude\commands\lr.md")
))
$GeminiCommandFiles = @(Get-ManifestProperty -Manifest $Manifest -Name "gemini_command_files" -Default @(
    (Join-Path $HOME ".gemini\commands\lr.toml"),
    (Join-Path $HOME ".gemini\commands\lr-status.toml")
))

foreach ($path in @($OpenCodeCommandFiles + $ClaudeCommandFiles + $GeminiCommandFiles)) {
    if ($path) { Remove-ItemIfExists -Path ([string]$path) }
}

$GeminiContextFile = [string](Get-ManifestProperty -Manifest $Manifest -Name "gemini_context_file" -Default (Join-Path $HOME ".gemini\GEMINI.md"))
Remove-GeminiContextBlock -Path $GeminiContextFile

Write-Host "Removing LRC runtime..."
$PackageName = [string](Get-ManifestProperty -Manifest $Manifest -Name "package_name" -Default $DefaultPackageName)
$Uv = [string](Get-ManifestProperty -Manifest $Manifest -Name "uv" -Default "")
if (-not $Uv -or -not (Test-Path $Uv)) {
    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    if ($uvCommand) {
        $Uv = [string]$uvCommand.Source
    } else {
        $defaultUv = Join-Path $HOME ".local\bin\uv.exe"
        if (Test-Path $defaultUv) { $Uv = $defaultUv }
    }
}

if ($Uv -and (Test-Path $Uv)) {
    & $Uv tool uninstall $PackageName | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "uv could not confirm removal of the LRC runtime. Host integrations were still removed."
    }
} else {
    Write-Warning "uv was not found, so the LRC runtime could not be removed automatically."
}

if ($FullCleanup) {
    if (Test-Path $InstallRoot) {
        Remove-Item -Recurse -Force $InstallRoot
        Write-Host "Removed LRC local settings/cache: $InstallRoot"
    }
} else {
    New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
    $UninstallState = @{
        status = "uninstalled"
        uninstalled_at = (Get-Date).ToUniversalTime().ToString("o")
        full_cleanup = $false
        package_name = $PackageName
        source_repository = $RepoRoot
        research_workspaces_removed = $false
        uv_removed = $false
        python_removed = $false
    }
    $UninstallState | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 $ManifestPath
    Write-Host "Kept LRC local settings/cache for future reinstall or repair."
}

Write-Host ""
Write-Host "Literature Review Construct has been uninstalled."
Write-Host "Research folders, PDFs, outputs, and .litreview project state were not touched."
Write-Host "uv and shared Python installations were not removed."
