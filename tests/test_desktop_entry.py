from __future__ import annotations

"""Desktop entry contract: qml-only runtime, explicit widgets now fail as removed."""

import types

import pytest

import desktop_main


def test_resolve_ui_mode_defaults_to_qml(monkeypatch) -> None:
    monkeypatch.delenv("AI_DAILY_DESKTOP_UI", raising=False)
    assert desktop_main._resolve_ui_mode() == "qml"


def test_resolve_ui_mode_preserves_explicit_widgets_removed_request(monkeypatch) -> None:
    monkeypatch.setenv("AI_DAILY_DESKTOP_UI", "widgets")
    assert desktop_main._resolve_ui_mode() == "widgets"


def test_resolve_ui_mode_accepts_qml(monkeypatch) -> None:
    monkeypatch.setenv("AI_DAILY_DESKTOP_UI", "qml")
    assert desktop_main._resolve_ui_mode() == "qml"


def test_resolve_ui_mode_invalid_value_falls_back_to_qml(monkeypatch) -> None:
    monkeypatch.setenv("AI_DAILY_DESKTOP_UI", "not-a-real-mode")
    assert desktop_main._resolve_ui_mode() == "qml"


def test_resolve_launcher_prefers_qml_by_default(monkeypatch) -> None:
    monkeypatch.delenv("AI_DAILY_DESKTOP_UI", raising=False)

    def fake_import_module(name: str):
        if name == "src.desktop.qml_app":
            return types.SimpleNamespace(launch_qml_desktop_app=lambda: 0)
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(desktop_main.importlib, "import_module", fake_import_module)

    launcher = desktop_main._resolve_launcher()

    assert launcher() == 0


def test_resolve_launcher_raises_when_removed_widgets_mode_is_requested(monkeypatch) -> None:
    monkeypatch.setenv("AI_DAILY_DESKTOP_UI", "widgets")
    attempted: list[str] = []

    def fake_import_module(name: str):
        attempted.append(name)
        raise AssertionError(f"should not import {name} for removed widgets mode")

    monkeypatch.setattr(desktop_main.importlib, "import_module", fake_import_module)

    with pytest.raises(desktop_main.RemovedDesktopUiModeError, match="no longer supported"):
        desktop_main._resolve_launcher()

    assert attempted == []


def test_main_raises_when_removed_widgets_mode_is_requested(monkeypatch) -> None:
    monkeypatch.setenv("AI_DAILY_DESKTOP_UI", "widgets")
    monkeypatch.setattr(desktop_main, "_set_windows_app_id", lambda: None)

    with pytest.raises(desktop_main.RemovedDesktopUiModeError, match="no longer supported"):
        desktop_main.main()


def test_resolve_launcher_raises_when_qml_requested_but_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("AI_DAILY_DESKTOP_UI", "qml")

    def fake_import_module(name: str):
        raise ModuleNotFoundError(name)

    monkeypatch.setattr(desktop_main.importlib, "import_module", fake_import_module)

    with pytest.raises(RuntimeError) as excinfo:
        desktop_main._resolve_launcher()

    message = str(excinfo.value)
    assert (
        "Desktop entrypoint not found. Tried: "
        "src.desktop.qml_app:launch_qml_desktop_app, src.desktop.qml_app:main."
    ) in message
    assert "Last import error: No module named 'src.desktop.qml_app'" in message
