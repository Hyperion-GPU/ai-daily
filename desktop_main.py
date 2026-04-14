from __future__ import annotations

import ctypes
import importlib
import os
import sys
from collections.abc import Callable


def _set_windows_app_id() -> None:
    if os.name != "nt":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AIDaily.Desktop")
    except Exception:
        return


def _resolve_launcher() -> Callable[[], int]:
    candidates = [
        ("src.desktop.app", "launch_desktop_app"),
        ("src.desktop.app", "main"),
        ("src.desktop.main_window", "launch_desktop_app"),
        ("src.desktop.main_window", "main"),
    ]
    attempted: list[str] = []

    for module_name, attribute in candidates:
        attempted.append(f"{module_name}:{attribute}")
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue

        launcher = getattr(module, attribute, None)
        if callable(launcher):
            return launcher

    raise RuntimeError(f"Desktop entrypoint not found. Tried: {', '.join(attempted)}")


def main() -> int:
    os.environ.setdefault("AI_DAILY_DESKTOP_MODE", "1")
    _set_windows_app_id()
    launcher = _resolve_launcher()
    return int(launcher())


if __name__ == "__main__":
    raise SystemExit(main())

