"""Issue #20: STATUS.md digest presence and regeneration."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

EXP_DIR = Path(__file__).resolve().parents[1]
STATUS = EXP_DIR / "STATUS.md"
GEN = EXP_DIR / "tools" / "gen_digest.py"


def test_status_lists_all_acs():
    assert STATUS.exists(), f"missing {STATUS}"
    text = STATUS.read_text(encoding="utf-8")
    for n in range(1, 8):
        assert f"AC-{n}" in text, f"AC-{n} not listed in STATUS.md"


def test_status_regeneration_script_runs(tmp_path):
    if shutil.which("git") is None:
        pytest.skip("git not available")
    assert GEN.exists(), f"missing {GEN}"
    # Regenerate into a copy so the working tree is not modified by the test.
    work = tmp_path / "STATUS.md"
    work.write_text(STATUS.read_text(encoding="utf-8"), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(GEN), "--status", str(work)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    text = work.read_text(encoding="utf-8")
    assert "<!-- AUTO:BEGIN -->" in text and "<!-- AUTO:END -->" in text
    assert "AC-1" in text, "hand-maintained AC section must be preserved"
