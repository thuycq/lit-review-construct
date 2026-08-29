$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExpectedVersion = "0.1.0.dev2"
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

$Uv = Resolve-Uv
Write-Host "Using uv: $Uv"

& $Uv python install 3.12
if ($LASTEXITCODE -ne 0) { throw "Python 3.12 installation failed." }

# --reinstall is intentional: the toolkit is installed from a local checkout and
# development builds may change without a release-version change.
& $Uv tool install --force --reinstall --python 3.12 $RepoRoot
if ($LASTEXITCODE -ne 0) { throw "Lit Review Construct runtime installation failed." }

$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$CodexSkills = Join-Path $CodexHome "skills"
$OpenCodeSkills = Join-Path $HOME ".config\opencode\skills"

New-Item -ItemType Directory -Force -Path $CodexSkills | Out-Null
New-Item -ItemType Directory -Force -Path $OpenCodeSkills | Out-Null

$CanonicalSkills = Join-Path $RepoRoot "skills"
if (Test-Path $CanonicalSkills) {
    Get-ChildItem -Path $CanonicalSkills -Directory | ForEach-Object {
        $skillName = $_.Name
        $codexTarget = Join-Path $CodexSkills $skillName
        $openCodeTarget = Join-Path $OpenCodeSkills $skillName

        if (Test-Path $codexTarget) { Remove-Item -Recurse -Force $codexTarget }
        if (Test-Path $openCodeTarget) { Remove-Item -Recurse -Force $openCodeTarget }

        Copy-Item -Recurse -Force $_.FullName $codexTarget
        Copy-Item -Recurse -Force $_.FullName $openCodeTarget
    }
}

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
    codex_skills = $CodexSkills
    opencode_skills = $OpenCodeSkills
}
$Manifest | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $InstallRoot "install-manifest.json")

Write-Host ""
Write-Host "Installed Lit Review Construct core and host skills."
Write-Host "Codex skills: $CodexSkills"
Write-Host "OpenCode skills: $OpenCodeSkills"
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
Write-Host "Open a research folder and run: lrc init"
