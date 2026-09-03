$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExpectedVersion = "0.1.0b2"
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

# uv-installed tools normally share the uv bin directory. Make that directory
# available immediately so repair/reinstall can verify lrc without requiring a
# terminal restart first.
Ensure-SessionPath -Directory $UvBin

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

$OpenCodeCommands = Join-Path $HOME ".config\opencode\commands"
New-Item -ItemType Directory -Force -Path $OpenCodeCommands | Out-Null
$CanonicalOpenCodeCommands = Join-Path $RepoRoot "commands\opencode"
if (Test-Path $CanonicalOpenCodeCommands) {
    Get-ChildItem -Path $CanonicalOpenCodeCommands -Filter "*.md" -File | ForEach-Object {
        Copy-Item -Force $_.FullName (Join-Path $OpenCodeCommands $_.Name)
    }
}

$ClaudeCommands = Join-Path $HOME ".claude\commands"
New-Item -ItemType Directory -Force -Path $ClaudeCommands | Out-Null
$ClaudeLr = Join-Path $RepoRoot "commands\claude\lr.md"
if (Test-Path $ClaudeLr) {
    Copy-Item -Force $ClaudeLr (Join-Path $ClaudeCommands "lr.md")
}

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

$InstallRoot = Join-Path $env:LOCALAPPDATA "LiteratureReviewConstruct"
New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null

$ResolvedLrc = Get-Command lrc -ErrorAction SilentlyContinue
$ResolvedPath = $null
$InstalledVersion = $null
if ($ResolvedLrc) {
    $ResolvedPath = [string]$ResolvedLrc.Source
} else {
    $candidateLrc = Join-Path $UvBin "lrc.exe"
    if (Test-Path $candidateLrc) {
        $ResolvedPath = $candidateLrc
    }
}
if ($ResolvedPath) {
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
    uv = $Uv
    runtime_bin = $UvBin
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
if ($ResolvedPath) {
    Write-Host "Resolved lrc: $ResolvedPath"
    Write-Host "Installed runtime: $InstalledVersion"
    if ($InstalledVersion -ne $ExpectedVersion) {
        Write-Warning "The installed lrc runtime did not report the expected version. Re-run install.bat to repair it."
    }
} else {
    Write-Warning "lrc could not be verified after installation. Re-run install.bat to repair the runtime."
}
Write-Host ""
Write-Host "Existing research folders and .litreview state are preserved during repair/reinstall."
Write-Host "Open a dedicated research folder in your preferred AI host and say:"
Write-Host "  Start or continue the Literature Review Construct project in this folder."
Write-Host "OpenCode, Claude Code, and Gemini CLI also have an /lr shortcut."
