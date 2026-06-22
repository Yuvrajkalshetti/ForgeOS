"""Guards for the one-command installer scripts (release tooling, not core).

Validates the installer files exist, target the global `forgeos`/`forge` command via
`uv tool install`, and (when bash is present) are syntactically valid. No core change.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_install_sh_exists_and_is_syntactically_valid() -> None:
    sh = ROOT / "install.sh"
    assert sh.is_file()
    text = sh.read_text(encoding="utf-8")
    assert text.startswith("#!")  # shebang present
    assert "uv tool install" in text  # installs the global command
    assert "uv tool update-shell" in text  # puts the global command on PATH
    assert "forgeos" in text  # guides the user to the forgeos command
    bash = shutil.which("bash")
    if bash:  # syntax-check only where bash is available
        result = subprocess.run([bash, "-n", str(sh)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


def test_install_ps1_exists_for_windows() -> None:
    ps1 = ROOT / "install.ps1"
    assert ps1.is_file()
    assert "uv tool install" in ps1.read_text(encoding="utf-8")
