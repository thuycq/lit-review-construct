#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_VERSION="0.1.0b3"
INSTALL_ROOT="$HOME/Library/Application Support/LiteratureReviewConstruct"
RUNTIME_ROOT="$INSTALL_ROOT/runtime"
LAUNCHER_DIR="$HOME/.local/bin"
LAUNCHER="$LAUNCHER_DIR/lrc"
LOG_ROOT="$HOME/Library/Logs/LiteratureReviewConstruct"
LOG_FILE="$LOG_ROOT/install.log"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This installer is intended for macOS."
  echo "On Windows, use install.bat."
  exit 1
fi

mkdir -p "$INSTALL_ROOT" "$LAUNCHER_DIR" "$LOG_ROOT"
touch "$LOG_FILE"
exec > >(tee -a "$LOG_FILE") 2>&1

on_error() {
  local code=$?
  echo ""
  echo "Installation did not complete."
  echo "Diagnostic log: $LOG_FILE"
  echo "You can retry from Terminal with:"
  echo "  bash \"$REPO_ROOT/install.sh\""
  exit "$code"
}
trap on_error ERR

echo ""
echo "Literature Review Construct — macOS installer"
echo "Repository: $REPO_ROOT"
echo "Runtime target: $EXPECTED_VERSION"
echo "macOS: $(sw_vers -productVersion 2>/dev/null || echo unknown)"
echo "Architecture: $(uname -m)"
echo "Shell: ${SHELL:-unknown}"
echo "Log: $LOG_FILE"
echo ""

resolve_uv() {
  if command -v uv >/dev/null 2>&1; then
    command -v uv
    return
  fi
  if [[ -x "$HOME/.local/bin/uv" ]]; then
    echo "$HOME/.local/bin/uv"
    return
  fi
  echo "Preparing the local Python runtime manager..." >&2
  curl -LsSf https://astral.sh/uv/install.sh | sh
  if command -v uv >/dev/null 2>&1; then
    command -v uv
  elif [[ -x "$HOME/.local/bin/uv" ]]; then
    echo "$HOME/.local/bin/uv"
  else
    echo "uv installation completed but uv could not be located." >&2
    return 1
  fi
}

UV="$(resolve_uv)"
echo "Runtime manager: $UV"

# LRC owns a private Python runtime. The lecturer does not need Homebrew, PowerShell,
# VS Code, or a manually managed Python installation.
"$UV" python install 3.12
rm -rf "$RUNTIME_ROOT"
"$UV" venv --python 3.12 "$RUNTIME_ROOT"
"$UV" pip install --python "$RUNTIME_ROOT/bin/python" --reinstall "$REPO_ROOT"

cat > "$LAUNCHER" <<EOF_LAUNCHER
#!/bin/sh
exec "$RUNTIME_ROOT/bin/lrc" "\$@"
EOF_LAUNCHER
chmod +x "$LAUNCHER"
export PATH="$LAUNCHER_DIR:$PATH"

ZPROFILE="$HOME/.zprofile"
if ! grep -q "LRC-PATH:BEGIN" "$ZPROFILE" 2>/dev/null; then
  cat >> "$ZPROFILE" <<'EOF_PATH'

# LRC-PATH:BEGIN
export PATH="$HOME/.local/bin:$PATH"
# LRC-PATH:END
EOF_PATH
fi

CANONICAL_SKILLS="$REPO_ROOT/skills"
SKILL_ROOTS=(
  "$HOME/.codex/skills"
  "$HOME/.config/opencode/skills"
  "$HOME/.claude/skills"
  "$HOME/.agents/skills"
  "$HOME/.cursor/skills"
  "$HOME/.codeium/windsurf/skills"
  "$HOME/.copilot/skills"
  "$HOME/.cline/skills"
)

for root in "${SKILL_ROOTS[@]}"; do
  mkdir -p "$root"
done

if [[ -d "$CANONICAL_SKILLS" ]]; then
  for skill_dir in "$CANONICAL_SKILLS"/*; do
    [[ -d "$skill_dir" ]] || continue
    skill_name="$(basename "$skill_dir")"
    for root in "${SKILL_ROOTS[@]}"; do
      rm -rf "$root/$skill_name"
      cp -R "$skill_dir" "$root/$skill_name"
    done
  done
fi

OPENCODE_COMMANDS="$HOME/.config/opencode/commands"
mkdir -p "$OPENCODE_COMMANDS"
if [[ -d "$REPO_ROOT/commands/opencode" ]]; then
  cp -f "$REPO_ROOT/commands/opencode"/*.md "$OPENCODE_COMMANDS/" 2>/dev/null || true
fi

CLAUDE_COMMANDS="$HOME/.claude/commands"
mkdir -p "$CLAUDE_COMMANDS"
if [[ -f "$REPO_ROOT/commands/claude/lr.md" ]]; then
  cp -f "$REPO_ROOT/commands/claude/lr.md" "$CLAUDE_COMMANDS/lr.md"
fi

GEMINI_COMMANDS="$HOME/.gemini/commands"
GEMINI_CONTEXT="$HOME/.gemini/GEMINI.md"
mkdir -p "$GEMINI_COMMANDS"
if [[ -f "$REPO_ROOT/commands/gemini/lr.toml" ]]; then
  cp -f "$REPO_ROOT/commands/gemini/lr.toml" "$GEMINI_COMMANDS/lr.toml"
fi
if [[ -f "$REPO_ROOT/commands/gemini/lr-status.toml" ]]; then
  cp -f "$REPO_ROOT/commands/gemini/lr-status.toml" "$GEMINI_COMMANDS/lr-status.toml"
fi
if [[ -f "$REPO_ROOT/commands/gemini/global-context.md" ]]; then
  mkdir -p "$(dirname "$GEMINI_CONTEXT")"
  touch "$GEMINI_CONTEXT"
  if ! grep -q "LITERATURE-REVIEW-CONSTRUCT:BEGIN" "$GEMINI_CONTEXT"; then
    printf '\n' >> "$GEMINI_CONTEXT"
    cat "$REPO_ROOT/commands/gemini/global-context.md" >> "$GEMINI_CONTEXT"
  fi
fi

INSTALLED_VERSION="$("$LAUNCHER" version)"
if [[ "$INSTALLED_VERSION" != "$EXPECTED_VERSION" ]]; then
  echo "Installed version mismatch: expected $EXPECTED_VERSION, got $INSTALLED_VERSION" >&2
  exit 1
fi

cat > "$INSTALL_ROOT/install-manifest.json" <<EOF_MANIFEST
{
  "installed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "source_repository": "$REPO_ROOT",
  "expected_version": "$EXPECTED_VERSION",
  "installed_version": "$INSTALLED_VERSION",
  "platform": "macOS",
  "architecture": "$(uname -m)",
  "runtime_python": "$RUNTIME_ROOT/bin/python",
  "launcher": "$LAUNCHER",
  "log": "$LOG_FILE",
  "hosts": ["codex", "opencode", "claude-code", "cursor", "windsurf", "github-copilot", "cline", "gemini-cli"]
}
EOF_MANIFEST

trap - ERR

echo ""
echo "✓ Literature Review Construct installed successfully."
echo "Installed runtime: $INSTALLED_VERSION"
echo "Private Python runtime: $RUNTIME_ROOT"
echo "LRC launcher: $LAUNCHER"
echo "Diagnostic log: $LOG_FILE"
echo ""
echo "No Homebrew, PowerShell, VS Code, or manual Python setup is required."
echo "Close and reopen Codex/OpenCode if it was already running."
echo "Then open a dedicated research folder and say:"
echo "  Start a new Literature Review Construct project in this folder."
echo ""
echo "If a macOS AI app cannot find 'lrc' after restart, LRC is also available at:"
echo "  $LAUNCHER"
