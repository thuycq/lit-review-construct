import re
from pathlib import Path

import litreview_construct


ROOT = Path(__file__).resolve().parents[1]


def test_beta_version_is_synchronized() -> None:
    version = litreview_construct.__version__
    assert version == "0.1.0b3"

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    windows_installer = (ROOT / "install.ps1").read_text(encoding="utf-8")
    mac_installer = (ROOT / "install.sh").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    project_version = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
    windows_version = re.search(r'^\$ExpectedVersion = "([^"]+)"$', windows_installer, re.MULTILINE)
    mac_version = re.search(r'^EXPECTED_VERSION="([^"]+)"$', mac_installer, re.MULTILINE)
    assert project_version is not None
    assert windows_version is not None
    assert mac_version is not None
    assert project_version.group(1) == version
    assert windows_version.group(1) == version
    assert mac_version.group(1) == version
    assert f"**Current beta:** `{version}`" in readme
    assert (ROOT / "install.command").exists()
