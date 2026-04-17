from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from src.runtime import get_runtime_paths, sync_web_data_to_desktop
from src.settings import (
    get_github_token,
    get_llm_api_key,
    load_config,
    save_config,
    set_github_token,
    set_llm_api_key,
    validate_configuration,
)


class DesktopConfigurationService:
    def load(self, *, mode: str = "desktop") -> dict:
        return load_config(mode=mode)

    def save(self, config: Mapping[str, object], *, mode: str = "desktop") -> Path:
        return save_config(config, mode=mode)

    def get_llm_api_key(self, config: Mapping[str, object]) -> str | None:
        return get_llm_api_key(config)

    def set_llm_api_key(self, config: Mapping[str, object], value: str | None) -> None:
        set_llm_api_key(config, value)

    def get_github_token(self, config: Mapping[str, object]) -> str | None:
        return get_github_token(config)

    def set_github_token(self, value: str | None) -> None:
        set_github_token(value)

    def validate(self, config: Mapping[str, object]) -> list[str]:
        return validate_configuration(config)

    def sync_archives(self, config: Mapping[str, object]) -> dict[str, int]:
        return sync_web_data_to_desktop(config=config)

    def user_data_dir(self) -> Path:
        paths = get_runtime_paths(mode="desktop")
        paths.user_data_dir.mkdir(parents=True, exist_ok=True)
        return paths.user_data_dir
