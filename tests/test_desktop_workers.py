from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from src.desktop.workers import AsyncTaskThread, normalize_failure_payload


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    return app


def test_async_task_thread_emits_success_and_progress(qapp: QApplication) -> None:
    async def runner(progress_callback):
        progress_callback({"stage": "running", "message": "working"})
        return {"result": "ok"}

    progress_events: list[dict] = []
    success_events: list[object] = []
    failure_events: list[object] = []
    thread = AsyncTaskThread(runner)
    thread.progress.connect(progress_events.append)
    thread.succeeded.connect(success_events.append)
    thread.failed.connect(failure_events.append)

    thread.run()

    assert progress_events == [{"stage": "running", "message": "working"}]
    assert success_events == [{"result": "ok"}]
    assert failure_events == []


def test_async_task_thread_emits_structured_failure(qapp: QApplication) -> None:
    async def runner(progress_callback):
        _ = progress_callback
        raise TimeoutError("network timeout")

    failure_events: list[object] = []
    thread = AsyncTaskThread(runner)
    thread.failed.connect(failure_events.append)

    thread.run()

    assert failure_events == [
        {
            "code": "timeout_error",
            "stage": "task",
            "message": "network timeout",
            "retryable": True,
            "details": {"exceptionType": "TimeoutError"},
        }
    ]


def test_normalize_failure_payload_keeps_legacy_string_compatible() -> None:
    assert normalize_failure_payload("plain failure") == {
        "code": "task_failed",
        "stage": "task",
        "message": "plain failure",
        "retryable": False,
    }
