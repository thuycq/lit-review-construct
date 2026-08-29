import re
from pathlib import Path

import litreview_construct


ROOT = Path(__file__).resolve().parents[1]


def test_beta_version_is_synchronized() -> None:
    version = litreview_construct.__version__
    assert version == "0.1.0b1"

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    installer = (ROOT / "install.ps1").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    project_version = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
    expected_version = re.search(r'^\$ExpectedVersion = "([^"]+)"$', installer, re.MULTILINE)
    assert project_version is not None
    assert expected_version is not None
    assert project_version.group(1) == version
    assert expected_version.group(1) == version
    assert f"**`{version}`**" in readme
