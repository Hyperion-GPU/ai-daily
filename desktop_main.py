from __future__ import annotations

import ctypes
import importlib
import os
from collections.abc import Callable


class RemovedDesktopUiModeError(RuntimeError):
    """Raised when a removed desktop UI mode is requested explicitly."""


_WIDGETS_REMOVED_MESSAGE = (
    "AI_DAILY_DESKTOP_UI=widgets has been removed and is no longer supported. "
    "QML is the only supported desktop UI."
)


def _set_windows_app_id() -> None:
    if os.name != "nt":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AIDaily.Desktop")
    except Exception:
        return


def _resolve_ui_mode() -> str:
    requested = os.environ.get("AI_DAILY_DESKTOP_UI", "qml").strip().lower()
    return requested if requested in {"widgets", "qml"} else "qml"


def _raise_if_removed_ui_mode(ui_mode: str) -> None:
    if ui_mode != "widgets":
        return
    raise RemovedDesktopUiModeError(_WIDGETS_REMOVED_MESSAGE)


def _resolve_launcher(ui_mode: str | None = None) -> Callable[[], int]:
    ui_mode = ui_mode or _resolve_ui_mode()
    _raise_if_removed_ui_mode(ui_mode)
    qml_candidates = [
        ("src.desktop.qml_app", "launch_qml_desktop_app"),
        ("src.desktop.qml_app", "main"),
    ]
    candidates = qml_candidates
    attempted: list[str] = []
    last_import_error: ModuleNotFoundError | None = None

    for module_name, attribute in candidates:
        attempted.append(f"{module_name}:{attribute}")
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            last_import_error = exc
            continue

        launcher = getattr(module, attribute, None)
        if callable(launcher):
            return launcher

    message = f"Desktop entrypoint not found. Tried: {', '.join(attempted)}"
    if last_import_error is not None:
        missing_name = getattr(last_import_error, "name", None)
        if not missing_name and getattr(last_import_error, "args", ()):
            missing_name = str(last_import_error.args[0])
        last_error_text = (
            f"No module named '{missing_name}'"
            if missing_name
            else str(last_import_error)
        )
        message += f". Last import error: {last_error_text}"
        raise RuntimeError(message) from last_import_error
    raise RuntimeError(message)


def main() -> int:
    os.environ.setdefault("AI_DAILY_DESKTOP_MODE", "1")
    _set_windows_app_id()
    ui_mode = _resolve_ui_mode()
    _raise_if_removed_ui_mode(ui_mode)
    launcher = _resolve_launcher(ui_mode)
    return int(launcher())


if __name__ == "__main__":
    raise SystemExit(main())
