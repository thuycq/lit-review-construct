from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_host_adapter_files_exist() -> None:
    expected = [
        "commands/opencode/lr.md",
        "commands/claude/lr.md",
        "commands/gemini/lr.toml",
        "commands/gemini/lr-status.toml",
        "commands/gemini/global-context.md",
        "install.sh",
    ]
    for relative in expected:
        assert (ROOT / relative).is_file(), relative


def test_installers_cover_supported_host_skill_roots() -> None:
    windows = (ROOT / "install.ps1").read_text(encoding="utf-8")
    mac = (ROOT / "install.sh").read_text(encoding="utf-8")

    windows_markers = [
        ".codex\\skills",
        ".config\\opencode\\skills",
        ".claude\\skills",
        ".agents\\skills",
        ".cursor\\skills",
        ".codeium\\windsurf\\skills",
        ".copilot\\skills",
        ".cline\\skills",
    ]
    mac_markers = [
        ".codex/skills",
        ".config/opencode/skills",
        ".claude/skills",
        ".agents/skills",
        ".cursor/skills",
        ".codeium/windsurf/skills",
        ".copilot/skills",
        ".cline/skills",
    ]
    for marker in windows_markers:
        assert marker in windows
    for marker in mac_markers:
        assert marker in mac


def test_gemini_global_context_is_gated() -> None:
    text = (ROOT / "commands" / "gemini" / "global-context.md").read_text(encoding="utf-8")
    assert ".litreview/project.yaml" in text
    assert "explicitly asks" in text
    assert "Outside an active Lit Review Construct workspace" in text
