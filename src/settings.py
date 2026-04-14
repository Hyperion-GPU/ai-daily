from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import logging
import os
import shutil
from pathlib import Path
from typing import Mapping

import yaml
from dotenv import load_dotenv

from .runtime import APP_NAME, apply_runtime_metadata, ensure_runtime_dirs, get_runtime_paths, strip_runtime_metadata

try:  # pragma: no cover - exercised indirectly when the dependency exists
    import keyring
except Exception:  # pragma: no cover
    keyring = None


GITHUB_SECRET_USERNAME = "github-token"
logger = logging.getLogger("aidaily")


def _resolve_config_path(config_path: str | Path = "config.yaml", mode: str | None = None) -> Path:
    candidate = Path(config_path)
    if candidate.is_absolute():
        return candidate

    paths = get_runtime_paths(mode=mode)
    if mode == "desktop" or paths.mode == "desktop":
        return paths.user_data_dir / candidate.name
    return paths.repo_root / candidate


def ensure_default_desktop_config(mode: str | None = "desktop") -> Path:
    paths = get_runtime_paths(mode=mode)
    ensure_runtime_dirs(paths)
    if not paths.config_path.exists():
        shutil.copyfile(paths.bundle_root / "config.yaml", paths.config_path)
    return paths.config_path


def load_runtime_env(config: Mapping[str, object] | None = None, mode: str | None = None) -> None:
    paths = get_runtime_paths(config=config, mode=mode)
    if paths.env_path.exists():
        load_dotenv(paths.env_path, override=False)

    repo_env = paths.repo_root / ".env"
    if repo_env != paths.env_path and repo_env.exists():
        load_dotenv(repo_env, override=False)


def load_config(config_path: str | Path = "config.yaml", mode: str | None = None) -> dict:
    resolved_path = _resolve_config_path(config_path=config_path, mode=mode)
    runtime_paths = get_runtime_paths(mode=mode)
    if (
        runtime_paths.mode == "desktop"
        and resolved_path == runtime_paths.config_path
        and not resolved_path.exists()
    ):
        ensure_default_desktop_config(mode="desktop")

    if not resolved_path.exists():
        raise FileNotFoundError(f"Config file not found: {resolved_path}")

    payload = deepcopy(_load_config_payload(str(resolved_path), resolved_path.stat().st_mtime_ns))
    payload = apply_runtime_metadata(payload, mode=mode)
    payload["_runtime"]["config_path"] = str(resolved_path)
    return payload


def save_config(config: Mapping[str, object], config_path: str | Path | None = None, mode: str | None = "desktop") -> Path:
    target_path = _resolve_config_path(config_path or "config.yaml", mode=mode)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    payload = strip_runtime_metadata(config)
    with open(target_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(payload, file, allow_unicode=True, sort_keys=False)
    return target_path


def _secret_username(prefix: str, suffix: str) -> str:
    return f"{prefix}:{suffix}"


def _get_keyring_secret(username: str) -> str | None:
    if keyring is None:
        return None
    try:
        return keyring.get_password(APP_NAME, username)
    except Exception:  # pragma: no cover
        logger.debug("Failed to read keyring secret for %s.", username, exc_info=True)
        return None


def _set_keyring_secret(username: str, value: str | None) -> None:
    if keyring is None:
        return
    try:
        if value:
            keyring.set_password(APP_NAME, username, value)
        else:
            try:
                keyring.delete_password(APP_NAME, username)
            except Exception:
                logger.debug("Failed to delete keyring secret for %s.", username, exc_info=True)
                pass
    except Exception:  # pragma: no cover
        logger.debug("Failed to update keyring secret for %s.", username, exc_info=True)
        return


def get_llm_api_key(config: Mapping[str, object]) -> str | None:
    load_runtime_env(config=config)
    llm_cfg = config.get("llm", {}) if isinstance(config.get("llm"), Mapping) else {}
    provider = str(llm_cfg.get("provider", "siliconflow"))
    provider_cfg = llm_cfg.get(provider, {}) if isinstance(llm_cfg.get(provider), Mapping) else {}
    env_name = str(provider_cfg.get("api_key_env", "SILICONFLOW_API_KEY"))
    return os.getenv(env_name) or _get_keyring_secret(_secret_username("llm", provider))


def set_llm_api_key(config: Mapping[str, object], value: str | None) -> None:
    llm_cfg = config.get("llm", {}) if isinstance(config.get("llm"), Mapping) else {}
    provider = str(llm_cfg.get("provider", "siliconflow"))
    _set_keyring_secret(_secret_username("llm", provider), value.strip() if isinstance(value, str) else None)


def get_github_token(config: Mapping[str, object]) -> str | None:
    load_runtime_env(config=config)
    github_cfg = (
        config.get("github_trending", {})
        if isinstance(config.get("github_trending"), Mapping)
        else {}
    )
    env_name = str(github_cfg.get("token_env", "GITHUB_TOKEN"))
    return os.getenv(env_name) or _get_keyring_secret(GITHUB_SECRET_USERNAME)


def set_github_token(value: str | None) -> None:
    _set_keyring_secret(GITHUB_SECRET_USERNAME, value.strip() if isinstance(value, str) else None)


def validate_configuration(config: Mapping[str, object]) -> list[str]:
    errors: list[str] = []
    llm_cfg = config.get("llm", {}) if isinstance(config.get("llm"), Mapping) else {}
    provider = str(llm_cfg.get("provider", "siliconflow"))
    provider_cfg = llm_cfg.get(provider, {}) if isinstance(llm_cfg.get(provider), Mapping) else {}

    if not provider_cfg.get("base_url"):
        errors.append("LLM base_url 未配置。")
    if not provider_cfg.get("model"):
        errors.append("LLM model 未配置。")
    if not get_llm_api_key(config):
        errors.append("缺少 LLM API Key。")

    github_cfg = (
        config.get("github_trending", {})
        if isinstance(config.get("github_trending"), Mapping)
        else {}
    )
    if github_cfg.get("enabled") and not get_github_token(config):
        errors.append("GitHub Trending 已启用，但缺少 GitHub Token。")
    return errors


def secrets_backend_name() -> str:
    return "keyring" if keyring is not None else "environment"


@lru_cache(maxsize=4)
def _load_config_payload(path_str: str, mtime_ns: int) -> dict:
    with open(path_str, "r", encoding="utf-8") as file:
        payload = yaml.safe_load(file) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Config file must contain a mapping: {path_str}")
    return payload
