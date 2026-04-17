from __future__ import annotations

import copy
from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.contracts import DesktopSettingsSnapshot, ValidationIssue, ValidationResult
from src.services import ApplicationServices


_KNOWN_PROVIDERS = ("siliconflow", "newapi")


class SettingsCommandGateway:
    def __init__(self, services_getter: Callable[[], ApplicationServices]) -> None:
        self._services_getter = services_getter

    def _services(self) -> ApplicationServices:
        return self._services_getter()

    @staticmethod
    def _normalize_provider(value: str) -> str:
        value = value.strip() or "siliconflow"
        return value if value in _KNOWN_PROVIDERS else "siliconflow"

    @staticmethod
    def _coerce_provider_settings(raw: Any) -> dict[str, dict[str, str]]:
        settings = {
            provider: {"base_url": "", "model": ""}
            for provider in _KNOWN_PROVIDERS
        }
        if not isinstance(raw, dict):
            return settings
        for provider in _KNOWN_PROVIDERS:
            payload = raw.get(provider, {})
            if not isinstance(payload, dict):
                continue
            settings[provider] = {
                "base_url": str(payload.get("base_url", "") or "").strip(),
                "model": str(payload.get("model", "") or "").strip(),
            }
        return settings

    def _coerce_snapshot(self, snapshot: DesktopSettingsSnapshot | dict[str, Any]) -> DesktopSettingsSnapshot:
        if isinstance(snapshot, DesktopSettingsSnapshot):
            return snapshot

        if any(
            key in snapshot
            for key in (
                "provider",
                "base_url",
                "model",
                "temperature",
                "max_tokens",
                "github_enabled",
                "github_token",
                "provider_settings",
            )
        ):
            base = self.load_snapshot_model()
            provider = self._normalize_provider(str(snapshot.get("provider", base.llm.provider) or base.llm.provider))
            siliconflow_cfg = base.llm.siliconflow.model_copy(deep=True).model_dump()
            newapi_cfg = base.llm.newapi.model_copy(deep=True).model_dump()
            provider_settings = self._coerce_provider_settings(snapshot.get("provider_settings"))
            for provider_name, config in (("siliconflow", siliconflow_cfg), ("newapi", newapi_cfg)):
                overrides = provider_settings.get(provider_name, {})
                if overrides.get("base_url"):
                    config["base_url"] = overrides["base_url"]
                if overrides.get("model"):
                    config["model"] = overrides["model"]
            selected_cfg = siliconflow_cfg if provider == "siliconflow" else newapi_cfg
            selected_cfg["base_url"] = str(snapshot.get("base_url", selected_cfg["base_url"]))
            selected_cfg["model"] = str(snapshot.get("model", selected_cfg["model"]))
            selected_cfg["temperature"] = int(snapshot.get("temperature", int(selected_cfg["temperature"] * 100))) / 100
            selected_cfg["max_tokens"] = int(snapshot.get("max_tokens", selected_cfg["max_tokens"]))
            return DesktopSettingsSnapshot.model_validate(
                {
                    "timezone": str(snapshot.get("timezone", base.timezone)),
                    "llm": {
                        "provider": provider,
                        "siliconflow": siliconflow_cfg,
                        "newapi": newapi_cfg,
                    },
                    "pipeline": {
                        "time_window_hours": int(snapshot.get("time_window_hours", base.pipeline.time_window_hours)),
                        "max_articles_per_day": int(snapshot.get("max_articles_per_day", base.pipeline.max_articles_per_day)),
                        "max_articles_to_stage2": int(snapshot.get("max_articles_to_stage2", base.pipeline.max_articles_to_stage2)),
                        "stage1_batch_size": int(snapshot.get("stage1_batch_size", base.pipeline.stage1_batch_size)),
                    },
                    "github_trending": {
                        "enabled": bool(snapshot.get("github_enabled", base.github_trending.enabled)),
                        "min_stars": int(snapshot.get("github_min_stars", base.github_trending.min_stars)),
                        "max_projects_per_day": int(
                            snapshot.get("github_max_projects", base.github_trending.max_projects_per_day)
                        ),
                    },
                    "llm_api_key": str(snapshot.get("llm_api_key", base.llm_api_key)),
                    "github_token": str(snapshot.get("github_token", base.github_token)),
                }
            )

        return DesktopSettingsSnapshot.model_validate(snapshot)

    def load_snapshot_model(self) -> DesktopSettingsSnapshot:
        services = self._services()
        config = copy.deepcopy(services.current_config())
        config_service = services.configuration_service
        llm_cfg = config.get("llm", {})
        pipeline_cfg = config.get("pipeline", {})
        github_cfg = config.get("github_trending", {})
        return DesktopSettingsSnapshot(
            timezone=str(config.get("timezone", "Asia/Shanghai")),
            llm={
                "provider": str(llm_cfg.get("provider", "siliconflow")),
                "siliconflow": {
                    "base_url": str(llm_cfg.get("siliconflow", {}).get("base_url", "")),
                    "model": str(llm_cfg.get("siliconflow", {}).get("model", "")),
                    "temperature": float(llm_cfg.get("siliconflow", {}).get("temperature", 0.3) or 0.3),
                    "max_tokens": int(llm_cfg.get("siliconflow", {}).get("max_tokens", 1500) or 1500),
                },
                "newapi": {
                    "base_url": str(llm_cfg.get("newapi", {}).get("base_url", "")),
                    "model": str(llm_cfg.get("newapi", {}).get("model", "")),
                    "temperature": float(llm_cfg.get("newapi", {}).get("temperature", 0.3) or 0.3),
                    "max_tokens": int(llm_cfg.get("newapi", {}).get("max_tokens", 1500) or 1500),
                },
            },
            pipeline={
                "time_window_hours": int(pipeline_cfg.get("time_window_hours", 48)),
                "max_articles_per_day": int(pipeline_cfg.get("max_articles_per_day", 30)),
                "max_articles_to_stage2": int(pipeline_cfg.get("max_articles_to_stage2", 50)),
                "stage1_batch_size": int(pipeline_cfg.get("stage1_batch_size", 50)),
            },
            github_trending={
                "enabled": bool(github_cfg.get("enabled", False)),
                "min_stars": int(github_cfg.get("min_stars", 500)),
                "max_projects_per_day": int(github_cfg.get("max_projects_per_day", 50)),
            },
            llm_api_key=config_service.get_llm_api_key(config) or "",
            github_token=config_service.get_github_token(config) or "",
        )

    def load_snapshot(self) -> dict[str, Any]:
        snapshot = self.load_snapshot_model()
        provider_cfg = getattr(snapshot.llm, snapshot.llm.provider)
        return {
            "provider": snapshot.llm.provider,
            "provider_settings": {
                "siliconflow": {
                    "base_url": snapshot.llm.siliconflow.base_url,
                    "model": snapshot.llm.siliconflow.model,
                },
                "newapi": {
                    "base_url": snapshot.llm.newapi.base_url,
                    "model": snapshot.llm.newapi.model,
                },
            },
            "timezone": snapshot.timezone,
            "base_url": provider_cfg.base_url,
            "model": provider_cfg.model,
            "temperature": int(provider_cfg.temperature * 100),
            "max_tokens": provider_cfg.max_tokens,
            "llm_api_key": snapshot.llm_api_key,
            "github_enabled": snapshot.github_trending.enabled,
            "github_token": snapshot.github_token,
            "github_min_stars": snapshot.github_trending.min_stars,
            "github_max_projects": snapshot.github_trending.max_projects_per_day,
            "time_window_hours": snapshot.pipeline.time_window_hours,
            "max_articles_per_day": snapshot.pipeline.max_articles_per_day,
            "max_articles_to_stage2": snapshot.pipeline.max_articles_to_stage2,
            "stage1_batch_size": snapshot.pipeline.stage1_batch_size,
        }

    def validate_snapshot_model(self, snapshot: DesktopSettingsSnapshot | dict[str, Any]) -> ValidationResult:
        candidate = self.build_snapshot_model(snapshot)
        provider_cfg = getattr(candidate.llm, candidate.llm.provider)
        issues: list[ValidationIssue] = []
        if not provider_cfg.base_url.strip():
            issues.append(ValidationIssue(field="base_url", message="LLM base_url 未配置。"))
        if not provider_cfg.model.strip():
            issues.append(ValidationIssue(field="model", message="LLM model 未配置。"))
        if not candidate.llm_api_key.strip():
            issues.append(ValidationIssue(field="llm_api_key", message="缺少 LLM API Key。"))
        if candidate.github_trending.enabled and not candidate.github_token.strip():
            issues.append(ValidationIssue(field="github_token", message="GitHub Trending 已启用，但缺少 GitHub Token。"))
        return ValidationResult(valid=not issues, issues=issues)

    def validate_snapshot(self, snapshot: dict[str, Any]) -> list[str]:
        return [issue.message for issue in self.validate_snapshot_model(snapshot).issues]

    def build_snapshot_model(self, snapshot: DesktopSettingsSnapshot | dict[str, Any]) -> DesktopSettingsSnapshot:
        raw = self._coerce_snapshot(snapshot)

        siliconflow_cfg = raw.llm.siliconflow.model_copy(deep=True)
        newapi_cfg = raw.llm.newapi.model_copy(deep=True)
        selected_cfg = getattr(raw.llm, raw.llm.provider)
        normalized_cfg = selected_cfg.model_copy(
            update={
                "base_url": selected_cfg.base_url.strip(),
                "model": selected_cfg.model.strip(),
                "temperature": max(0.0, min(1.0, float(selected_cfg.temperature))),
                "max_tokens": max(1, int(selected_cfg.max_tokens)),
            },
            deep=True,
        )
        if raw.llm.provider == "siliconflow":
            siliconflow_cfg = normalized_cfg
        else:
            newapi_cfg = normalized_cfg

        return DesktopSettingsSnapshot(
            timezone=raw.timezone.strip() or "Asia/Shanghai",
            llm={
                "provider": raw.llm.provider,
                "siliconflow": siliconflow_cfg.model_dump(),
                "newapi": newapi_cfg.model_dump(),
            },
            pipeline={
                "time_window_hours": max(1, int(raw.pipeline.time_window_hours)),
                "max_articles_per_day": max(1, int(raw.pipeline.max_articles_per_day)),
                "max_articles_to_stage2": max(1, int(raw.pipeline.max_articles_to_stage2)),
                "stage1_batch_size": max(1, int(raw.pipeline.stage1_batch_size)),
            },
            github_trending={
                "enabled": bool(raw.github_trending.enabled),
                "min_stars": max(0, int(raw.github_trending.min_stars)),
                "max_projects_per_day": max(1, int(raw.github_trending.max_projects_per_day)),
            },
            llm_api_key=raw.llm_api_key.strip(),
            github_token=raw.github_token.strip(),
        )

    def build_config(self, snapshot: DesktopSettingsSnapshot | dict[str, Any]) -> dict[str, Any]:
        config = copy.deepcopy(self._services().current_config())
        candidate = self.build_snapshot_model(snapshot)
        config["timezone"] = candidate.timezone

        llm_cfg = config.setdefault("llm", {})
        llm_cfg["provider"] = candidate.llm.provider
        llm_cfg["siliconflow"] = candidate.llm.siliconflow.model_dump()
        llm_cfg["newapi"] = candidate.llm.newapi.model_dump()

        pipeline_cfg = config.setdefault("pipeline", {})
        pipeline_cfg["time_window_hours"] = candidate.pipeline.time_window_hours
        pipeline_cfg["max_articles_per_day"] = candidate.pipeline.max_articles_per_day
        pipeline_cfg["max_articles_to_stage2"] = candidate.pipeline.max_articles_to_stage2
        pipeline_cfg["stage1_batch_size"] = candidate.pipeline.stage1_batch_size

        github_cfg = config.setdefault("github_trending", {})
        github_cfg["enabled"] = candidate.github_trending.enabled
        github_cfg["min_stars"] = candidate.github_trending.min_stars
        github_cfg["max_projects_per_day"] = candidate.github_trending.max_projects_per_day
        return config

    def save_snapshot(self, snapshot: DesktopSettingsSnapshot | dict[str, Any]) -> dict[str, Any]:
        services = self._services()
        config_service = services.configuration_service
        candidate = self.build_snapshot_model(snapshot)
        config = self.build_config(candidate)
        config_service.save(config, mode="desktop")
        config_service.set_llm_api_key(config, candidate.llm_api_key)
        config_service.set_github_token(candidate.github_token)
        persisted = config_service.load(mode="desktop")
        services.replace_config(persisted)
        return persisted

    def user_data_dir(self) -> Path:
        return self._services().configuration_service.user_data_dir()
