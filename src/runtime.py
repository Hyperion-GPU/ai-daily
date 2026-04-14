from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

APP_NAME = "AI Daily"
DESKTOP_MODE_ENV = "AI_DAILY_DESKTOP_MODE"


@dataclass(frozen=True)
class RuntimePaths:
    mode: str
    repo_root: Path
    bundle_root: Path
    user_data_dir: Path
    writable_root: Path
    config_path: Path
    env_path: Path
    output_dir: Path
    state_file: Path
    prompts_dir: Path
    frontend_dist: Path
    brand_dir: Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _bundle_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", _repo_root()))


def _user_data_dir() -> Path:
    local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata:
        return Path(local_appdata) / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME


def is_desktop_runtime(config: Mapping[str, object] | None = None, mode: str | None = None) -> bool:
    if mode == "desktop":
        return True
    if mode == "web":
        return False

    runtime_cfg = {}
    if isinstance(config, Mapping):
        runtime_cfg = config.get("_runtime", {}) if isinstance(config.get("_runtime"), Mapping) else {}

    config_mode = runtime_cfg.get("mode")
    if config_mode == "desktop":
        return True
    if config_mode == "web":
        return False

    return os.getenv(DESKTOP_MODE_ENV) == "1" or bool(getattr(sys, "frozen", False))


def _raw_output_dir(config: Mapping[str, object] | None = None) -> str:
    outputs_cfg = {}
    if isinstance(config, Mapping):
        raw_outputs = config.get("outputs")
        if isinstance(raw_outputs, Mapping):
            outputs_cfg = raw_outputs

    return str(outputs_cfg.get("output_dir", "output"))


def _resolve_output_dir(raw_output_dir: str, writable_root: Path) -> Path:
    output_dir = Path(raw_output_dir)
    if not output_dir.is_absolute():
        output_dir = writable_root / output_dir
    return output_dir


def get_runtime_paths(config: Mapping[str, object] | None = None, mode: str | None = None) -> RuntimePaths:
    repo_root = _repo_root()
    bundle_root = _bundle_root()
    user_data_dir = _user_data_dir()
    desktop_mode = is_desktop_runtime(config=config, mode=mode)
    resolved_mode = "desktop" if desktop_mode else "web"
    writable_root = user_data_dir if desktop_mode else repo_root

    output_dir = _resolve_output_dir(_raw_output_dir(config), writable_root)

    state_file = writable_root / "data" / "state.json"
    config_path = user_data_dir / "config.yaml" if desktop_mode else repo_root / "config.yaml"
    env_path = user_data_dir / ".env" if desktop_mode else repo_root / ".env"

    return RuntimePaths(
        mode=resolved_mode,
        repo_root=repo_root,
        bundle_root=bundle_root,
        user_data_dir=user_data_dir,
        writable_root=writable_root,
        config_path=config_path,
        env_path=env_path,
        output_dir=output_dir,
        state_file=state_file,
        prompts_dir=bundle_root / "prompts",
        frontend_dist=bundle_root / "frontend" / "dist",
        brand_dir=bundle_root / "assets" / "branding",
    )


def ensure_runtime_dirs(paths: RuntimePaths) -> None:
    paths.user_data_dir.mkdir(parents=True, exist_ok=True)
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    paths.state_file.parent.mkdir(parents=True, exist_ok=True)


def _unique_existing_paths(candidates: list[Path]) -> list[Path]:
    unique: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate
        if resolved in seen or not candidate.exists():
            continue
        seen.add(resolved)
        unique.append(candidate)
    return unique


def _should_copy_file(source: Path, target: Path) -> bool:
    if not target.exists():
        return True

    source_stat = source.stat()
    target_stat = target.stat()
    if source_stat.st_mtime_ns > target_stat.st_mtime_ns:
        return True
    if source_stat.st_mtime_ns == target_stat.st_mtime_ns and source_stat.st_size != target_stat.st_size:
        return True
    return False


def sync_web_data_to_desktop(config: Mapping[str, object] | None = None) -> dict[str, int]:
    paths = get_runtime_paths(config=config, mode="desktop")
    ensure_runtime_dirs(paths)

    copied_files = 0
    skipped_files = 0

    raw_output_dir = Path(_raw_output_dir(config))
    if raw_output_dir.is_absolute():
        output_candidates = [raw_output_dir]
    else:
        output_candidates = [
            paths.repo_root / raw_output_dir,
            paths.bundle_root / raw_output_dir,
        ]

    output_sources = _unique_existing_paths(output_candidates)
    for source_root in output_sources:
        try:
            if source_root.resolve() == paths.output_dir.resolve():
                continue
        except OSError:
            pass

        for source in source_root.rglob("*"):
            if not source.is_file():
                continue

            relative_path = source.relative_to(source_root)
            if relative_path.name.endswith(".partial.json"):
                skipped_files += 1
                continue

            target = paths.output_dir / relative_path
            if _should_copy_file(source, target):
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                copied_files += 1
            else:
                skipped_files += 1

    state_sources = _unique_existing_paths(
        [
            paths.repo_root / "data" / "state.json",
            paths.bundle_root / "data" / "state.json",
        ]
    )
    state_copied = 0
    for source in state_sources:
        try:
            if source.resolve() == paths.state_file.resolve():
                continue
        except OSError:
            pass
        if _should_copy_file(source, paths.state_file):
            paths.state_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, paths.state_file)
            state_copied += 1
        else:
            skipped_files += 1

    return {
        "copied_files": copied_files,
        "skipped_files": skipped_files,
        "state_copied": state_copied,
    }


def apply_runtime_metadata(config: dict, mode: str | None = None) -> dict:
    paths = get_runtime_paths(config=config, mode=mode)
    enriched = dict(config)
    enriched["_runtime"] = {
        "mode": paths.mode,
        "config_path": str(paths.config_path),
        "env_path": str(paths.env_path),
        "output_dir": str(paths.output_dir),
        "state_file": str(paths.state_file),
        "prompts_dir": str(paths.prompts_dir),
        "frontend_dist": str(paths.frontend_dist),
        "brand_dir": str(paths.brand_dir),
        "user_data_dir": str(paths.user_data_dir),
    }
    return enriched


def strip_runtime_metadata(config: Mapping[str, object]) -> dict:
    return {key: value for key, value in config.items() if key != "_runtime"}
