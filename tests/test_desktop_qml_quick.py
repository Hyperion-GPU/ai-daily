from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "tests" / "qml" / "run_quick_tests.py"


def test_qt_quick_test_suite_passes() -> None:
    pytest.importorskip("PySide6")

    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    env.setdefault("AI_DAILY_QML_STYLE", "Basic")
    env.setdefault("QT_FORCE_STDERR_LOGGING", "1")

    result = subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )

    assert result.returncode == 0, (
        "Qt Quick Test suite failed.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )
