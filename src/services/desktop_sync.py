from __future__ import annotations

from collections.abc import Mapping

from src.runtime import sync_web_data_to_desktop


class DesktopArchiveSyncService:
    def sync(self, config: Mapping[str, object]) -> dict[str, int]:
        return sync_web_data_to_desktop(config=config)
