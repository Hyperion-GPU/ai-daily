from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from PySide6.QtCore import QThread, Signal


class AsyncTaskThread(QThread):
    progress = Signal(dict)
    succeeded = Signal(object)
    failed = Signal(str)

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
            self.failed.emit(str(exc))
            return
        self.succeeded.emit(result)

