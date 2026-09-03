$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExpectedVersion = "0.1.0b3"
$PackageName = "lit-review-construct"
$InstallRoot = Join-Path $env:LOCALAPPDATA "LiteratureReviewConstruct"
New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null

Write-Host "Literature Review Construct installer"
Write-Host "Repository: $RepoRoot"
Write-Host "Runtime target: $ExpectedVersion"

function Resolve-Uv {
    $cmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($cmd) { return [string]$cmd.Source }

    $defaultUv = Join-Path $HOME ".local\bin\uv.exe"
    if (Test-Path $defaultUv) { return [string]$defaultUv }

    Write-Host "uv not found. Installing uv..."
    # Keep installer progress visible without allowing its stdout to become the
    # return value of Resolve-Uv. PowerShell functions otherwise return every
    # object written to the success stream, which can corrupt $Uv.
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex" | Out-Host

    $cmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($cmd) { return [string]$cmd.Source }
    if (Test-Path $defaultUv) { return [string]$defaultUv }

    throw "uv installation completed but uv.exe could not be located."
}

function Ensure-SessionPath {
    param([Parameter(Mandatory = $true)][string]$Directory)
    if (-not (Test-Path $Directory)) { return }
    $parts = @($env:Path -split ';' | Where-Object { $_ })
    if ($parts -notcontains $Directory) {
        $env:Path = "$Directory;$env:Path"
    }
}

function Sync-Skills {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string[]]$Targets
    )

    foreach ($targetRoot in $Targets) {
        New-Item -ItemType Directory -Force -Path $targetRoot | Out-Null
    }

    if (-not (Test-Path $Source)) { return }

    Get-ChildItem -Path $Source -Directory | ForEach-Object {
        $skillName = $_.Name
        foreach ($targetRoot in $Targets) {
            $target = Join-Path $targetRoot $skillName
            if (Test-Path $target) { Remove-Item -Recurse -Force $target }
            Copy-Item -Recurse -Force $_.FullName $target
        }
    }
}

function Add-GeminiContext {
    param(
        [Parameter(Mandatory = $true)][string]$Template,
        [Parameter(Mandatory = $true)][string]$Target
    )
    if (-not (Test-Path $Template)) { return }
    $parent = Split-Path -Parent $Target
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    if (-not (Test-Path $Target)) {
        New-Item -ItemType File -Force -Path $Target | Out-Null
    }
    $existing = Get-Content -Raw -Path $Target -ErrorAction SilentlyContinue
    if ($null -eq $existing) { $existing = "" }
    if ($existing -notmatch "LITERATURE-REVIEW-CONSTRUCT:BEGIN") {
        Add-Content -Encoding UTF8 -Path $Target -Value ""
        Get-Content -Raw -Path $Template | Add-Content -Encoding UTF8 -Path $Target
    }
}

$Uv = Resolve-Uv
if (-not (Test-Path $Uv)) {
    throw "Resolved uv path does not exist: $Uv"
}
$UvBin = Split-Path -Parent $Uv
Ensure-SessionPath -Directory $UvBin
Write-Host "Using uv: $Uv"

& $Uv python install 3.12
if ($LASTEXITCODE -ne 0) { throw "Python 3.12 installation failed." }

& $Uv tool install --force --reinstall --python 3.12 $RepoRoot
if ($LASTEXITCODE -ne 0) { throw "Literature Review Construct runtime installation failed." }

# Ask uv for the actual executable directory used for installed tools. This
# avoids resolving an older lrc launcher elsewhere on PATH.
$RuntimeBin = $null
try {
    $candidateToolBin = (& $Uv tool dir --bin 2>$null | Out-String).Trim()
    if ($candidateToolBin -and (Test-Path $candidateToolBin)) {
        $RuntimeBin = $candidateToolBin
    }
} catch {
    $RuntimeBin = $null
}
if (-not $RuntimeBin) {
    $RuntimeBin = $UvBin
}
Ensure-SessionPath -Directory $RuntimeBin

$ResolvedPath = Join-Path $RuntimeBin "lrc.exe"
if (-not (Test-Path $ResolvedPath)) {
    # Compatibility fallback for installations where uv and tool launchers share
    # the uv executable directory but `uv tool dir --bin` is unavailable.
    $fallbackLrc = Join-Path $UvBin "lrc.exe"
    if (Test-Path $fallbackLrc) {
        $ResolvedPath = $fallbackLrc
        $RuntimeBin = $UvBin
    } else {
        throw "LRC runtime installation completed, but the newly installed lrc.exe could not be located."
    }
}

$InstalledVersion = $null
try {
    $InstalledVersion = (& $ResolvedPath version).Trim()
} catch {
    throw "The newly installed LRC launcher could not start: $ResolvedPath"
}
if ($InstalledVersion -ne $ExpectedVersion) {
    throw "Installed LRC runtime version '$InstalledVersion' does not match expected version '$ExpectedVersion'."
}

# Sanity-check a feature introduced/validated in this beta. If this fails, the
# installer must not report success because Codex would otherwise resolve an
# incomplete or stale runtime later.
& $ResolvedPath fulltext --help *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Installed LRC runtime is incomplete: the 'fulltext' command is unavailable."
}
Write-Host "Verified lrc runtime and fulltext command: $ResolvedPath"

$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$SkillRoots = @(
    (Join-Path $CodexHome "skills"),
    (Join-Path $HOME ".config\opencode\skills"),
    (Join-Path $HOME ".claude\skills"),
    (Join-Path $HOME ".agents\skills"),
    (Join-Path $HOME ".cursor\skills"),
    (Join-Path $HOME ".codeium\windsurf\skills"),
    (Join-Path $HOME ".copilot\skills"),
    (Join-Path $HOME ".cline\skills")
)
$SkillSource = Join-Path $RepoRoot "skills"
$SkillNames = @()
if (Test-Path $SkillSource) {
    $SkillNames = @(Get-ChildItem -Path $SkillSource -Directory | ForEach-Object { $_.Name })
}
Sync-Skills -Source $SkillSource -Targets $SkillRoots

$OpenCodeCommands = Join-Path $HOME ".config\opencode\commands"
New-Item -ItemType Directory -Force -Path $OpenCodeCommands | Out-Null
$CanonicalOpenCodeCommands = Join-Path $RepoRoot "commands\opencode"
$OpenCodeCommandFiles = @()
if (Test-Path $CanonicalOpenCodeCommands) {
    Get-ChildItem -Path $CanonicalOpenCodeCommands -Filter "*.md" -File | ForEach-Object {
        $target = Join-Path $OpenCodeCommands $_.Name
        Copy-Item -Force $_.FullName $target
        $OpenCodeCommandFiles += $target
    }
}

$ClaudeCommands = Join-Path $HOME ".claude\commands"
New-Item -ItemType Directory -Force -Path $ClaudeCommands | Out-Null
$ClaudeLr = Join-Path $RepoRoot "commands\claude\lr.md"
$ClaudeCommandFiles = @()
if (Test-Path $ClaudeLr) {
    $target = Join-Path $ClaudeCommands "lr.md"
    Copy-Item -Force $ClaudeLr $target
    $ClaudeCommandFiles += $target
}

$GeminiRoot = Join-Path $HOME ".gemini"
$GeminiCommands = Join-Path $GeminiRoot "commands"
New-Item -ItemType Directory -Force -Path $GeminiCommands | Out-Null
$GeminiCommandFiles = @()
foreach ($name in @("lr.toml", "lr-status.toml")) {
    $source = Join-Path $RepoRoot "commands\gemini\$name"
    if (Test-Path $source) {
        $target = Join-Path $GeminiCommands $name
        Copy-Item -Force $source $target
        $GeminiCommandFiles += $target
    }
}
$GeminiContextFile = Join-Path $GeminiRoot "GEMINI.md"
Add-GeminiContext -Template (Join-Path $RepoRoot "commands\gemini\global-context.md") -Target $GeminiContextFile

$Manifest = @{
    status = "installed"
    installed_at = (Get-Date).ToUniversalTime().ToString("o")
    source_repository = $RepoRoot
    package_name = $PackageName
    expected_version = $ExpectedVersion
    installed_version = $InstalledVersion
    resolved_lrc = $ResolvedPath
    uv = $Uv
    runtime_bin = $RuntimeBin
    python = "3.12"
    hosts = @(
        "codex",
        "opencode",
        "claude-code",
        "cursor",
        "windsurf",
        "github-copilot",
        "cline",
        "gemini-cli"
    )
    skill_roots = $SkillRoots
    skill_names = $SkillNames
    opencode_commands = $OpenCodeCommands
    opencode_command_files = $OpenCodeCommandFiles
    claude_commands = $ClaudeCommands
    claude_command_files = $ClaudeCommandFiles
    gemini_commands = $GeminiCommands
    gemini_command_files = $GeminiCommandFiles
    gemini_context_file = $GeminiContextFile
    research_workspaces_managed = $false
}
$Manifest | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $InstallRoot "install-manifest.json")

Write-Host ""
Write-Host "Installed Literature Review Construct beta core and multi-host adapters."
Write-Host "Supported host adapters:"
Write-Host "  - Codex"
Write-Host "  - OpenCode"
Write-Host "  - Claude Code"
Write-Host "  - Cursor"
Write-Host "  - Windsurf"
Write-Host "  - GitHub Copilot"
Write-Host "  - Cline"
Write-Host "  - Gemini CLI"
Write-Host "Resolved lrc: $ResolvedPath"
Write-Host "Installed runtime: $InstalledVersion"
Write-Host "Verified command: fulltext"
Write-Host ""
Write-Host "Existing research folders and .litreview state are preserved during repair/reinstall."
Write-Host "Open a dedicated research folder in your preferred AI host and say:"
Write-Host "  Start or continue the Literature Review Construct project in this folder."
Write-Host "OpenCode, Claude Code, and Gemini CLI also have an /lr shortcut."
