from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

from src.services import ApplicationServices

from ..tasks import SettingsCommandGateway


_KNOWN_PROVIDERS = ("siliconflow", "newapi")


class SettingsFacade(QObject):
    providerChanged = Signal()
    timezoneChanged = Signal()
    baseUrlChanged = Signal()
    modelChanged = Signal()
    temperatureChanged = Signal()
    maxTokensChanged = Signal()
    llmApiKeyChanged = Signal()
    llmApiKeyVisibleChanged = Signal()
    githubEnabledChanged = Signal()
    githubTokenChanged = Signal()
    githubTokenVisibleChanged = Signal()
    githubMinStarsChanged = Signal()
    githubMaxProjectsChanged = Signal()
    timeWindowHoursChanged = Signal()
    maxArticlesPerDayChanged = Signal()
    maxArticlesToStage2Changed = Signal()
    stage1BatchSizeChanged = Signal()
    staleChanged = Signal()
    busyChanged = Signal()
    errorMessageChanged = Signal()
    noticeMessageChanged = Signal()
    validationSummaryChanged = Signal()
    saved = Signal()

    def __init__(self, services_getter, parent=None) -> None:
        super().__init__(parent)
        self._services_getter = services_getter
        self._gateway = SettingsCommandGateway(services_getter)
        self._suspend_stale = False
        self._provider = "siliconflow"
        self._provider_settings = {
            provider: {"base_url": "", "model": ""}
            for provider in _KNOWN_PROVIDERS
        }
        self._timezone = "Asia/Shanghai"
        self._base_url = ""
        self._model = ""
        self._temperature = 30
        self._max_tokens = 1500
        self._llm_api_key = ""
        self._llm_api_key_visible = False
        self._github_enabled = False
        self._github_token = ""
        self._github_token_visible = False
        self._github_min_stars = 500
        self._github_max_projects = 50
        self._time_window_hours = 48
        self._max_articles_per_day = 30
        self._max_articles_to_stage2 = 50
        self._stage1_batch_size = 50
        self._stale = False
        self._busy = False
        self._error_message = ""
        self._notice_message = ""
        self._validation_summary = ""

    def _services(self) -> ApplicationServices:
        return self._services_getter()

    def _mark_stale(self) -> None:
        if self._suspend_stale or self._stale:
            return
        self._stale = True
        self.staleChanged.emit()

    def _set_error_message(self, value: str) -> None:
        value = value.strip()
        if value == self._error_message:
            return
        self._error_message = value
        self.errorMessageChanged.emit()

    def _set_notice_message(self, value: str) -> None:
        value = value.strip()
        if value == self._notice_message:
            return
        self._notice_message = value
        self.noticeMessageChanged.emit()

    def _set_validation_summary(self, value: str) -> None:
        value = value.strip()
        if value == self._validation_summary:
            return
        self._validation_summary = value
        self.validationSummaryChanged.emit()

    def _set_busy(self, value: bool) -> None:
        if value == self._busy:
            return
        self._busy = value
        self.busyChanged.emit()

    def _normalize_provider(self, value: str) -> str:
        value = value.strip() or "siliconflow"
        return value if value in _KNOWN_PROVIDERS else "siliconflow"

    def _coerce_provider_settings(self, raw: Any) -> dict[str, dict[str, str]]:
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

    def _apply_snapshot(self, snapshot: dict[str, Any]) -> None:
        provider = self._normalize_provider(str(snapshot.get("provider", "siliconflow") or "siliconflow"))
        provider_settings = self._coerce_provider_settings(snapshot.get("provider_settings"))
        if not provider_settings[provider]["base_url"]:
            provider_settings[provider]["base_url"] = str(snapshot.get("base_url", "") or "").strip()
        if not provider_settings[provider]["model"]:
            provider_settings[provider]["model"] = str(snapshot.get("model", "") or "").strip()

        self._suspend_stale = True
        try:
            if provider_settings != self._provider_settings:
                self._provider_settings = provider_settings
            if provider != self._provider:
                self._provider = provider
                self.providerChanged.emit()

            base_url = self._provider_settings[self._provider]["base_url"]
            if base_url != self._base_url:
                self._base_url = base_url
                self.baseUrlChanged.emit()

            model = self._provider_settings[self._provider]["model"]
            if model != self._model:
                self._model = model
                self.modelChanged.emit()

            self.setTimezone(str(snapshot.get("timezone", "Asia/Shanghai")))
            self.setTemperature(int(snapshot.get("temperature", 30)))
            self.setMaxTokens(int(snapshot.get("max_tokens", 1500)))
            self.setLlmApiKey(str(snapshot.get("llm_api_key", "")))
            self.setGithubEnabled(bool(snapshot.get("github_enabled", False)))
            self.setGithubToken(str(snapshot.get("github_token", "")))
            self.setGithubMinStars(int(snapshot.get("github_min_stars", 500)))
            self.setGithubMaxProjects(int(snapshot.get("github_max_projects", 50)))
            self.setTimeWindowHours(int(snapshot.get("time_window_hours", 48)))
            self.setMaxArticlesPerDay(int(snapshot.get("max_articles_per_day", 30)))
            self.setMaxArticlesToStage2(int(snapshot.get("max_articles_to_stage2", 50)))
            self.setStage1BatchSize(int(snapshot.get("stage1_batch_size", 50)))
        finally:
            self._suspend_stale = False
        if self._stale:
            self._stale = False
            self.staleChanged.emit()

    def _snapshot(self) -> dict[str, Any]:
        return {
            "provider": self._provider,
            "provider_settings": {
                provider: dict(settings)
                for provider, settings in self._provider_settings.items()
            },
            "timezone": self._timezone,
            "base_url": self._base_url,
            "model": self._model,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "llm_api_key": self._llm_api_key,
            "github_enabled": self._github_enabled,
            "github_token": self._github_token,
            "github_min_stars": self._github_min_stars,
            "github_max_projects": self._github_max_projects,
            "time_window_hours": self._time_window_hours,
            "max_articles_per_day": self._max_articles_per_day,
            "max_articles_to_stage2": self._max_articles_to_stage2,
            "stage1_batch_size": self._stage1_batch_size,
        }

    @Slot()
    def reload(self) -> None:
        self._set_error_message("")
        self._set_notice_message("")
        self._set_validation_summary("")
        self._apply_snapshot(self._gateway.load_snapshot())

    @Slot()
    def validate(self) -> None:
        self._set_error_message("")
        errors = self._gateway.validate_snapshot(self._snapshot())
        if errors:
            self._set_validation_summary("\n".join(errors))
            self._set_notice_message("")
            return
        self._set_validation_summary("")
        self._set_notice_message("基础配置检查通过。")

    @Slot()
    def save(self) -> None:
        self._set_error_message("")
        self._set_notice_message("")
        errors = self._gateway.validate_snapshot(self._snapshot())
        if errors:
            self._set_validation_summary("\n".join(errors))
            return

        self._set_validation_summary("")
        self._set_busy(True)
        try:
            self._gateway.save_snapshot(self._snapshot())
        except Exception as exc:
            self._set_error_message(str(exc))
            return
        finally:
            self._set_busy(False)

        if self._stale:
            self._stale = False
            self.staleChanged.emit()
        self._set_notice_message("设置已保存。")
        self.saved.emit()

    @Slot()
    def openDataDir(self) -> None:
        data_dir = self._gateway.user_data_dir()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_dir)))

    @Slot()
    def toggleLlmApiKeyVisible(self) -> None:
        self._llm_api_key_visible = not self._llm_api_key_visible
        self.llmApiKeyVisibleChanged.emit()

    @Slot()
    def toggleGithubTokenVisible(self) -> None:
        self._github_token_visible = not self._github_token_visible
        self.githubTokenVisibleChanged.emit()

    def get_provider(self) -> str:
        return self._provider

    @Slot(str)
    def setProvider(self, value: str) -> None:
        value = self._normalize_provider(value)
        if value == self._provider:
            return

        self._provider = value
        next_settings = self._provider_settings.get(
            value,
            {"base_url": "", "model": ""},
        )
        previous_base_url = self._base_url
        previous_model = self._model
        self._base_url = next_settings["base_url"]
        self._model = next_settings["model"]
        self.providerChanged.emit()
        if self._base_url != previous_base_url:
            self.baseUrlChanged.emit()
        if self._model != previous_model:
            self.modelChanged.emit()
        self._mark_stale()

    def get_timezone(self) -> str:
        return self._timezone

    @Slot(str)
    def setTimezone(self, value: str) -> None:
        value = value.strip() or "Asia/Shanghai"
        if value == self._timezone:
            return
        self._timezone = value
        self.timezoneChanged.emit()
        self._mark_stale()

    def get_base_url(self) -> str:
        return self._base_url

    @Slot(str)
    def setBaseUrl(self, value: str) -> None:
        value = value.strip()
        if value == self._base_url:
            return
        self._base_url = value
        self._provider_settings[self._provider]["base_url"] = value
        self.baseUrlChanged.emit()
        self._mark_stale()

    def get_model(self) -> str:
        return self._model

    @Slot(str)
    def setModel(self, value: str) -> None:
        value = value.strip()
        if value == self._model:
            return
        self._model = value
        self._provider_settings[self._provider]["model"] = value
        self.modelChanged.emit()
        self._mark_stale()

    def get_temperature(self) -> int:
        return self._temperature

    @Slot(int)
    def setTemperature(self, value: int) -> None:
        value = max(0, min(100, int(value)))
        if value == self._temperature:
            return
        self._temperature = value
        self.temperatureChanged.emit()
        self._mark_stale()

    def get_max_tokens(self) -> int:
        return self._max_tokens

    @Slot(int)
    def setMaxTokens(self, value: int) -> None:
        value = max(1, int(value))
        if value == self._max_tokens:
            return
        self._max_tokens = value
        self.maxTokensChanged.emit()
        self._mark_stale()

    def get_llm_api_key(self) -> str:
        return self._llm_api_key

    @Slot(str)
    def setLlmApiKey(self, value: str) -> None:
        value = value.strip()
        if value == self._llm_api_key:
            return
        self._llm_api_key = value
        self.llmApiKeyChanged.emit()
        self._mark_stale()

    def get_llm_api_key_visible(self) -> bool:
        return self._llm_api_key_visible

    def get_github_enabled(self) -> bool:
        return self._github_enabled

    @Slot(bool)
    def setGithubEnabled(self, value: bool) -> None:
        value = bool(value)
        if value == self._github_enabled:
            return
        self._github_enabled = value
        self.githubEnabledChanged.emit()
        self._mark_stale()

    def get_github_token(self) -> str:
        return self._github_token

    @Slot(str)
    def setGithubToken(self, value: str) -> None:
        value = value.strip()
        if value == self._github_token:
            return
        self._github_token = value
        self.githubTokenChanged.emit()
        self._mark_stale()

    def get_github_token_visible(self) -> bool:
        return self._github_token_visible

    def get_github_min_stars(self) -> int:
        return self._github_min_stars

    @Slot(int)
    def setGithubMinStars(self, value: int) -> None:
        value = max(0, int(value))
        if value == self._github_min_stars:
            return
        self._github_min_stars = value
        self.githubMinStarsChanged.emit()
        self._mark_stale()

    def get_github_max_projects(self) -> int:
        return self._github_max_projects

    @Slot(int)
    def setGithubMaxProjects(self, value: int) -> None:
        value = max(1, int(value))
        if value == self._github_max_projects:
            return
        self._github_max_projects = value
        self.githubMaxProjectsChanged.emit()
        self._mark_stale()

    def get_time_window_hours(self) -> int:
        return self._time_window_hours

    @Slot(int)
    def setTimeWindowHours(self, value: int) -> None:
        value = max(1, int(value))
        if value == self._time_window_hours:
            return
        self._time_window_hours = value
        self.timeWindowHoursChanged.emit()
        self._mark_stale()

    def get_max_articles_per_day(self) -> int:
        return self._max_articles_per_day

    @Slot(int)
    def setMaxArticlesPerDay(self, value: int) -> None:
        value = max(1, int(value))
        if value == self._max_articles_per_day:
            return
        self._max_articles_per_day = value
        self.maxArticlesPerDayChanged.emit()
        self._mark_stale()

    def get_max_articles_to_stage2(self) -> int:
        return self._max_articles_to_stage2

    @Slot(int)
    def setMaxArticlesToStage2(self, value: int) -> None:
        value = max(1, int(value))
        if value == self._max_articles_to_stage2:
            return
        self._max_articles_to_stage2 = value
        self.maxArticlesToStage2Changed.emit()
        self._mark_stale()

    def get_stage1_batch_size(self) -> int:
        return self._stage1_batch_size

    @Slot(int)
    def setStage1BatchSize(self, value: int) -> None:
        value = max(1, int(value))
        if value == self._stage1_batch_size:
            return
        self._stage1_batch_size = value
        self.stage1BatchSizeChanged.emit()
        self._mark_stale()

    def get_stale(self) -> bool:
        return self._stale

    def get_busy(self) -> bool:
        return self._busy

    def get_error_message(self) -> str:
        return self._error_message

    def get_notice_message(self) -> str:
        return self._notice_message

    def get_validation_summary(self) -> str:
        return self._validation_summary

    provider = Property(str, get_provider, setProvider, notify=providerChanged)
    timezone = Property(str, get_timezone, setTimezone, notify=timezoneChanged)
    baseUrl = Property(str, get_base_url, setBaseUrl, notify=baseUrlChanged)
    model = Property(str, get_model, setModel, notify=modelChanged)
    temperature = Property(int, get_temperature, setTemperature, notify=temperatureChanged)
    maxTokens = Property(int, get_max_tokens, setMaxTokens, notify=maxTokensChanged)
    llmApiKey = Property(str, get_llm_api_key, setLlmApiKey, notify=llmApiKeyChanged)
    llmApiKeyVisible = Property(bool, get_llm_api_key_visible, notify=llmApiKeyVisibleChanged)
    githubEnabled = Property(bool, get_github_enabled, setGithubEnabled, notify=githubEnabledChanged)
    githubToken = Property(str, get_github_token, setGithubToken, notify=githubTokenChanged)
    githubTokenVisible = Property(bool, get_github_token_visible, notify=githubTokenVisibleChanged)
    githubMinStars = Property(int, get_github_min_stars, setGithubMinStars, notify=githubMinStarsChanged)
    githubMaxProjects = Property(int, get_github_max_projects, setGithubMaxProjects, notify=githubMaxProjectsChanged)
    timeWindowHours = Property(int, get_time_window_hours, setTimeWindowHours, notify=timeWindowHoursChanged)
    maxArticlesPerDay = Property(int, get_max_articles_per_day, setMaxArticlesPerDay, notify=maxArticlesPerDayChanged)
    maxArticlesToStage2 = Property(int, get_max_articles_to_stage2, setMaxArticlesToStage2, notify=maxArticlesToStage2Changed)
    stage1BatchSize = Property(int, get_stage1_batch_size, setStage1BatchSize, notify=stage1BatchSizeChanged)
    stale = Property(bool, get_stale, notify=staleChanged)
    busy = Property(bool, get_busy, notify=busyChanged)
    errorMessage = Property(str, get_error_message, notify=errorMessageChanged)
    noticeMessage = Property(str, get_notice_message, notify=noticeMessageChanged)
    validationSummary = Property(str, get_validation_summary, notify=validationSummaryChanged)
