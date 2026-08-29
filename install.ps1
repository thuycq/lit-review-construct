$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExpectedVersion = "0.1.0b2"
Write-Host "Lit Review Construct installer"
Write-Host "Repository: $RepoRoot"
Write-Host "Runtime target: $ExpectedVersion"

function Resolve-Uv {
    $cmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $defaultUv = Join-Path $HOME ".local\bin\uv.exe"
    if (Test-Path $defaultUv) { return $defaultUv }

    Write-Host "uv not found. Installing uv..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

    $cmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    if (Test-Path $defaultUv) { return $defaultUv }

    throw "uv installation completed but uv.exe could not be located."
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
    if ($existing -notmatch "LIT-REVIEW-CONSTRUCT:BEGIN") {
        Add-Content -Encoding UTF8 -Path $Target -Value ""
        Get-Content -Raw -Path $Template | Add-Content -Encoding UTF8 -Path $Target
    }
}

$Uv = Resolve-Uv
Write-Host "Using uv: $Uv"

& $Uv python install 3.12
if ($LASTEXITCODE -ne 0) { throw "Python 3.12 installation failed." }

# --reinstall is intentional: beta builds are installed from a local checkout.
& $Uv tool install --force --reinstall --python 3.12 $RepoRoot
if ($LASTEXITCODE -ne 0) { throw "Lit Review Construct runtime installation failed." }

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
Sync-Skills -Source (Join-Path $RepoRoot "skills") -Targets $SkillRoots

# OpenCode shortcuts.
$OpenCodeCommands = Join-Path $HOME ".config\opencode\commands"
New-Item -ItemType Directory -Force -Path $OpenCodeCommands | Out-Null
$CanonicalOpenCodeCommands = Join-Path $RepoRoot "commands\opencode"
if (Test-Path $CanonicalOpenCodeCommands) {
    Get-ChildItem -Path $CanonicalOpenCodeCommands -Filter "*.md" -File | ForEach-Object {
        Copy-Item -Force $_.FullName (Join-Path $OpenCodeCommands $_.Name)
    }
}

# Claude Code shortcut. Skills are installed above.
$ClaudeCommands = Join-Path $HOME ".claude\commands"
New-Item -ItemType Directory -Force -Path $ClaudeCommands | Out-Null
$ClaudeLr = Join-Path $RepoRoot "commands\claude\lr.md"
if (Test-Path $ClaudeLr) {
    Copy-Item -Force $ClaudeLr (Join-Path $ClaudeCommands "lr.md")
}

# Gemini CLI shortcuts and gated global context.
$GeminiRoot = Join-Path $HOME ".gemini"
$GeminiCommands = Join-Path $GeminiRoot "commands"
New-Item -ItemType Directory -Force -Path $GeminiCommands | Out-Null
foreach ($name in @("lr.toml", "lr-status.toml")) {
    $source = Join-Path $RepoRoot "commands\gemini\$name"
    if (Test-Path $source) {
        Copy-Item -Force $source (Join-Path $GeminiCommands $name)
    }
}
Add-GeminiContext -Template (Join-Path $RepoRoot "commands\gemini\global-context.md") -Target (Join-Path $GeminiRoot "GEMINI.md")

$InstallRoot = Join-Path $env:LOCALAPPDATA "LitReviewConstruct"
New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null

$ResolvedLrc = Get-Command lrc -ErrorAction SilentlyContinue
$ResolvedPath = $null
$InstalledVersion = $null
if ($ResolvedLrc) {
    $ResolvedPath = $ResolvedLrc.Source
    try {
        $InstalledVersion = (& $ResolvedPath version).Trim()
    } catch {
        $InstalledVersion = $null
    }
}

$Manifest = @{
    installed_at = (Get-Date).ToUniversalTime().ToString("o")
    source_repository = $RepoRoot
    expected_version = $ExpectedVersion
    installed_version = $InstalledVersion
    resolved_lrc = $ResolvedPath
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
    opencode_commands = $OpenCodeCommands
    claude_commands = $ClaudeCommands
    gemini_commands = $GeminiCommands
}
$Manifest | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 (Join-Path $InstallRoot "install-manifest.json")

Write-Host ""
Write-Host "Installed Lit Review Construct beta core and multi-host adapters."
Write-Host "Supported host adapters:"
Write-Host "  - Codex"
Write-Host "  - OpenCode"
Write-Host "  - Claude Code"
Write-Host "  - Cursor"
Write-Host "  - Windsurf"
Write-Host "  - GitHub Copilot"
Write-Host "  - Cline"
Write-Host "  - Gemini CLI"
if ($ResolvedPath) {
    Write-Host "Resolved lrc: $ResolvedPath"
    Write-Host "Installed runtime: $InstalledVersion"
    if ($InstalledVersion -ne $ExpectedVersion) {
        Write-Warning "The current shell resolves an unexpected lrc version. Close and reopen the terminal before testing."
    }
} else {
    Write-Warning "lrc is not visible in this shell yet. Close and reopen the terminal before testing."
}
Write-Host ""
Write-Host "Open a dedicated research folder in your preferred AI host and say:"
Write-Host "  Start a new Lit Review Construct project in this folder."
Write-Host "OpenCode, Claude Code, and Gemini CLI also have an /lr shortcut."
