import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_windows_launchers_use_the_windows_virtual_environment():
    install = (ROOT / "install.bat").read_text(encoding="utf-8")
    run = (ROOT / "run.bat").read_text(encoding="utf-8")

    assert r".venv\Scripts\python.exe" in install
    assert r".venv\Scripts\python.exe" in run
    assert 'call "%~dp0install.bat"' in run
    assert "-m qrcd.cli" in run


def test_windows_batch_goto_targets_exist():
    for name in ("install.bat", "run.bat"):
        content = (ROOT / name).read_text(encoding="utf-8")
        labels = set(re.findall(r"(?m)^:([A-Za-z0-9_]+)\s*$", content))
        targets = set(re.findall(r"(?im)\bgoto\s+:?([A-Za-z0-9_]+)", content))

        assert targets <= labels


def test_cross_platform_command_uses_lrcgetter_brand():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'name = "lrcgetter"' in pyproject
    assert 'lrcgetter = "qrcd.cli:main"' in pyproject
