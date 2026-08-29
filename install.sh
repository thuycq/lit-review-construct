#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_VERSION="0.1.0b2"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This installer is intended for macOS."
  echo "On Windows, use install.bat."
  exit 1
fi

echo "Lit Review Construct installer"
echo "Repository: $REPO_ROOT"
echo "Runtime target: $EXPECTED_VERSION"

resolve_uv() {
  if command -v uv >/dev/null 2>&1; then
    command -v uv
    return
  fi
  if [[ -x "$HOME/.local/bin/uv" ]]; then
    echo "$HOME/.local/bin/uv"
    return
  fi
  echo "uv not found. Installing uv..." >&2
  curl -LsSf https://astral.sh/uv/install.sh | sh
  if command -v uv >/dev/null 2>&1; then
    command -v uv
  elif [[ -x "$HOME/.local/bin/uv" ]]; then
    echo "$HOME/.local/bin/uv"
  else
    echo "uv installation completed but uv could not be located." >&2
    exit 1
  fi
}

UV="$(resolve_uv)"
echo "Using uv: $UV"

"$UV" python install 3.12
"$UV" tool install --force --reinstall --python 3.12 "$REPO_ROOT"

CANONICAL_SKILLS="$REPO_ROOT/skills"

# Host-specific and portable global skill roots.
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

# OpenCode shortcuts.
OPENCODE_COMMANDS="$HOME/.config/opencode/commands"
mkdir -p "$OPENCODE_COMMANDS"
if [[ -d "$REPO_ROOT/commands/opencode" ]]; then
  cp -f "$REPO_ROOT/commands/opencode"/*.md "$OPENCODE_COMMANDS/" 2>/dev/null || true
fi

# Claude Code shortcut. Claude Code continues to use the shared skills above.
CLAUDE_COMMANDS="$HOME/.claude/commands"
mkdir -p "$CLAUDE_COMMANDS"
if [[ -f "$REPO_ROOT/commands/claude/lr.md" ]]; then
  cp -f "$REPO_ROOT/commands/claude/lr.md" "$CLAUDE_COMMANDS/lr.md"
fi

# Gemini CLI shortcuts + gated global context.
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
  if ! grep -q "LIT-REVIEW-CONSTRUCT:BEGIN" "$GEMINI_CONTEXT"; then
    printf '\n' >> "$GEMINI_CONTEXT"
    cat "$REPO_ROOT/commands/gemini/global-context.md" >> "$GEMINI_CONTEXT"
  fi
fi

INSTALL_ROOT="$HOME/Library/Application Support/LitReviewConstruct"
mkdir -p "$INSTALL_ROOT"

LRC_PATH="$(command -v lrc || true)"
INSTALLED_VERSION=""
if [[ -n "$LRC_PATH" ]]; then
  INSTALLED_VERSION="$("$LRC_PATH" version 2>/dev/null || true)"
fi

cat > "$INSTALL_ROOT/install-manifest.json" <<EOF
{
  "installed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "source_repository": "$REPO_ROOT",
  "expected_version": "$EXPECTED_VERSION",
  "installed_version": "$INSTALLED_VERSION",
  "resolved_lrc": "$LRC_PATH",
  "python": "3.12",
  "hosts": ["codex", "opencode", "claude-code", "cursor", "windsurf", "github-copilot", "cline", "gemini-cli"]
}
EOF

echo ""
echo "Installed Lit Review Construct core and host adapters for macOS."
echo "Supported host adapters:"
echo "  - Codex"
echo "  - OpenCode"
echo "  - Claude Code"
echo "  - Cursor"
echo "  - Windsurf"
echo "  - GitHub Copilot"
echo "  - Cline"
echo "  - Gemini CLI"
if [[ -n "$LRC_PATH" ]]; then
  echo "Resolved lrc: $LRC_PATH"
  echo "Installed runtime: $INSTALLED_VERSION"
fi
echo ""
echo "Open a dedicated research folder in your preferred AI host and say:"
echo "  Start a new Lit Review Construct project in this folder."
echo "OpenCode, Claude Code, and Gemini CLI also have an /lr shortcut."
