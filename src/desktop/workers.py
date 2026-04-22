from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QThread, Signal


@dataclass(frozen=True)
class TaskFailure:
    code: str
    stage: str
    message: str
    retryable: bool
    details: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "stage": self.stage,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.details:
            payload["details"] = dict(self.details)
        return payload


def failure_from_exception(exc: BaseException, *, stage: str = "task") -> TaskFailure:
    code = _exception_code(exc)
    retryable = isinstance(exc, (ConnectionError, TimeoutError, OSError))
    return TaskFailure(
        code=code,
        stage=stage,
        message=str(exc) or exc.__class__.__name__,
        retryable=retryable,
        details={"exceptionType": exc.__class__.__name__},
    )


def normalize_failure_payload(payload: object) -> dict[str, Any]:
    if isinstance(payload, TaskFailure):
        return payload.to_payload()
    if isinstance(payload, BaseException):
        return failure_from_exception(payload).to_payload()
    if isinstance(payload, dict):
        message = str(payload.get("message", "") or "")
        code = str(payload.get("code", "") or "task_failed")
        stage = str(payload.get("stage", "") or "task")
        return {
            "code": code,
            "stage": stage,
            "message": message or code,
            "retryable": bool(payload.get("retryable", False)),
            **({"details": payload["details"]} if payload.get("details") else {}),
        }
    message = str(payload or "")
    return {
        "code": "task_failed",
        "stage": "task",
        "message": message or "任务失败",
        "retryable": False,
    }


def _exception_code(exc: BaseException) -> str:
    name = exc.__class__.__name__
    chars: list[str] = []
    for index, char in enumerate(name):
        if char.isupper() and index > 0:
            chars.append("_")
        chars.append(char.lower())
    return "".join(chars) or "task_failed"


class AsyncTaskThread(QThread):
    progress = Signal(dict)
    succeeded = Signal(object)
    failed = Signal(object)

    def __init__(
        self,
        runner: Callable[[Callable[[dict], None]], Awaitable[Any]],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._runner = runner

    def run(self) -> None:  # pragma: no cover - exercised through the UI
        try:
            result = asyncio.run(self._runner(self.progress.emit))
        except Exception as exc:
            self.failed.emit(failure_from_exception(exc).to_payload())
            return
        self.succeeded.emit(result)
