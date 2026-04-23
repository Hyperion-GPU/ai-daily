from __future__ import annotations

import copy
import tempfile
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from src.desktop.facades import SettingsFacade
from src.desktop.tasks import SettingsCommandGateway


class FakeConfigurationService:
    def __init__(self) -> None:
        self._persisted_config: dict = {}
        self.llm_api_key = ""
        self.github_token = ""
        self.saved_config: dict | None = None

    def load(self, *, mode: str = "desktop") -> dict:
        _ = mode
        return copy.deepcopy(self._persisted_config)

    def save(self, config: dict, *, mode: str = "desktop"):
        _ = mode
        self.saved_config = copy.deepcopy(config)
        self._persisted_config = copy.deepcopy(config)
        return None

    def get_llm_api_key(self, config: dict) -> str | None:
        _ = config
        return self.llm_api_key

    def set_llm_api_key(self, config: dict, value: str | None) -> None:
        _ = config
        self.llm_api_key = (value or "").strip()

    def get_github_token(self, config: dict) -> str | None:
        _ = config
        return self.github_token

    def set_github_token(self, value: str | None) -> None:
        self.github_token = (value or "").strip()

    def user_data_dir(self):
        path = Path(tempfile.gettempdir()) / "ai-daily-settings-facade"
        path.mkdir(parents=True, exist_ok=True)
        return path


class FakeServices:
    def __init__(self) -> None:
        self._config = {
            "timezone": "Asia/Shanghai",
            "llm": {
                "provider": "siliconflow",
                "siliconflow": {
                    "base_url": "https://api.siliconflow.cn/v1",
                    "model": "deepseek-ai/DeepSeek-V3.2",
                    "temperature": 0.3,
                    "max_tokens": 1500,
                },
                "newapi": {
                    "base_url": "https://example.com/newapi",
                    "model": "deepseek-chat",
                    "temperature": 0.3,
                    "max_tokens": 1500,
                },
            },
            "pipeline": {
                "time_window_hours": 48,
                "max_articles_per_day": 30,
                "max_articles_to_stage2": 50,
                "stage1_batch_size": 50,
            },
            "github_trending": {
                "enabled": False,
                "min_stars": 500,
                "max_projects_per_day": 50,
            },
        }
        self.configuration_service = FakeConfigurationService()
        self.configuration_service._persisted_config = copy.deepcopy(self._config)

    def current_config(self) -> dict:
        return copy.deepcopy(self._config)

    def replace_config(self, config: dict) -> None:
        self._config = copy.deepcopy(config)


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    return app


@pytest.fixture
def fake_services() -> FakeServices:
    return FakeServices()


def test_settings_gateway_loads_snapshot_from_services(fake_services: FakeServices) -> None:
    fake_services.configuration_service.llm_api_key = "sk-test"
    fake_services.configuration_service.github_token = "gh-test"

    gateway = SettingsCommandGateway(lambda: fake_services)
    snapshot = gateway.load_snapshot()

    assert snapshot["provider"] == "siliconflow"
    assert snapshot["provider_settings"] == {
        "siliconflow": {
            "base_url": "https://api.siliconflow.cn/v1",
            "model": "deepseek-ai/DeepSeek-V3.2",
        },
        "newapi": {
            "base_url": "https://example.com/newapi",
            "model": "deepseek-chat",
        },
    }
    assert snapshot["llm_api_key"] == "sk-test"
    assert snapshot["github_token"] == "gh-test"
    assert snapshot["time_window_hours"] == 48


def test_settings_gateway_validates_unsaved_snapshot(fake_services: FakeServices) -> None:
    gateway = SettingsCommandGateway(lambda: fake_services)
    errors = gateway.validate_snapshot(
        {
            "base_url": "",
            "model": "",
            "llm_api_key": "",
            "github_enabled": True,
            "github_token": "",
        }
    )

    assert errors == [
        "LLM base_url 未配置。",
        "LLM model 未配置。",
        "缺少 LLM API Key。",
        "GitHub Trending 已启用，但缺少 GitHub Token。",
    ]


def test_settings_facade_tracks_stale_and_saves(fake_services: FakeServices, qapp: QApplication) -> None:
    facade = SettingsFacade(lambda: fake_services)
    facade.reload()
    qapp.processEvents()

    assert facade.stale is False
    facade.setModel("new-model")
    qapp.processEvents()
    assert facade.stale is True

    facade.setLlmApiKey("sk-live")
    facade.save()
    qapp.processEvents()

    assert facade.stale is False
    assert facade.noticeMessage == "设置已保存。"
    assert fake_services.configuration_service.saved_config is not None
    assert fake_services.configuration_service.saved_config["llm"]["siliconflow"]["model"] == "new-model"
    assert fake_services.configuration_service.llm_api_key == "sk-live"


def test_settings_facade_switches_provider_to_target_defaults(
    fake_services: FakeServices,
    qapp: QApplication,
) -> None:
    facade = SettingsFacade(lambda: fake_services)
    facade.reload()
    qapp.processEvents()

    assert facade.provider == "siliconflow"
    assert facade.baseUrl == "https://api.siliconflow.cn/v1"
    assert facade.model == "deepseek-ai/DeepSeek-V3.2"

    facade.setProvider("newapi")
    qapp.processEvents()

    assert facade.provider == "newapi"
    assert facade.baseUrl == "https://example.com/newapi"
    assert facade.model == "deepseek-chat"


def test_settings_facade_exposes_available_provider_registry(
    fake_services: FakeServices,
    qapp: QApplication,
) -> None:
    facade = SettingsFacade(lambda: fake_services)
    qapp.processEvents()

    assert facade.availableProviders == [
        {
            "value": "siliconflow",
            "label": "siliconflow",
            "fields": [
                {"key": "base_url", "label": "Base URL"},
                {"key": "model", "label": "Model"},
            ],
        },
        {
            "value": "newapi",
            "label": "newapi",
            "fields": [
                {"key": "base_url", "label": "Base URL"},
                {"key": "model", "label": "Model"},
            ],
        },
    ]


def test_settings_facade_normalizes_unknown_provider_to_default(
    fake_services: FakeServices,
    qapp: QApplication,
) -> None:
    facade = SettingsFacade(lambda: fake_services)
    facade.reload()
    facade.setProvider("newapi")
    qapp.processEvents()

    facade.setProvider("unknown-provider")
    qapp.processEvents()

    assert facade.provider == "siliconflow"
    assert facade.baseUrl == "https://api.siliconflow.cn/v1"
    assert facade.model == "deepseek-ai/DeepSeek-V3.2"


def test_settings_facade_applies_legacy_snapshot_fields_for_selected_provider(
    fake_services: FakeServices,
    qapp: QApplication,
) -> None:
    facade = SettingsFacade(lambda: fake_services)

    facade._apply_snapshot(
        {
            "provider": "missing-provider",
            "provider_settings": {
                "newapi": {
                    "base_url": " https://newapi.from-settings/v1 ",
                    "model": " newapi-model ",
                },
                "ignored": {
                    "base_url": "https://ignored.example/v1",
                    "model": "ignored-model",
                },
            },
            "base_url": " https://legacy.siliconflow/v1 ",
            "model": " legacy-model ",
            "timezone": "Asia/Shanghai",
            "temperature": 30,
            "max_tokens": 1500,
        }
    )
    qapp.processEvents()

    assert facade.provider == "siliconflow"
    assert facade.baseUrl == "https://legacy.siliconflow/v1"
    assert facade.model == "legacy-model"

    facade.setProvider("newapi")
    qapp.processEvents()

    assert facade.baseUrl == "https://newapi.from-settings/v1"
    assert facade.model == "newapi-model"
    assert "ignored" not in facade._snapshot()["provider_settings"]


def test_settings_facade_preserves_manual_override_per_provider(
    fake_services: FakeServices,
    qapp: QApplication,
) -> None:
    facade = SettingsFacade(lambda: fake_services)
    facade.reload()
    qapp.processEvents()

    facade.setProvider("newapi")
    facade.setBaseUrl("https://custom.newapi/v1")
    facade.setModel("custom-chat")
    qapp.processEvents()

    facade.setProvider("siliconflow")
    qapp.processEvents()
    assert facade.baseUrl == "https://api.siliconflow.cn/v1"
    assert facade.model == "deepseek-ai/DeepSeek-V3.2"

    facade.setProvider("newapi")
    qapp.processEvents()
    assert facade.baseUrl == "https://custom.newapi/v1"
    assert facade.model == "custom-chat"


def test_settings_facade_provider_specific_field_access_updates_active_provider_only(
    fake_services: FakeServices,
    qapp: QApplication,
) -> None:
    facade = SettingsFacade(lambda: fake_services)
    facade.reload()
    qapp.processEvents()

    facade.setProvider("newapi")
    facade.setBaseUrl("https://custom.newapi/v1")
    facade.setModel("custom-chat")
    qapp.processEvents()

    snapshot = facade._snapshot()
    assert snapshot["provider"] == "newapi"
    assert snapshot["base_url"] == "https://custom.newapi/v1"
    assert snapshot["model"] == "custom-chat"
    assert snapshot["provider_settings"]["newapi"] == {
        "base_url": "https://custom.newapi/v1",
        "model": "custom-chat",
    }
    assert snapshot["provider_settings"]["siliconflow"] == {
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "deepseek-ai/DeepSeek-V3.2",
    }


def test_settings_facade_save_preserves_non_current_provider_override(
    fake_services: FakeServices,
    qapp: QApplication,
) -> None:
    facade = SettingsFacade(lambda: fake_services)
    facade.reload()
    qapp.processEvents()

    facade.setProvider("newapi")
    facade.setBaseUrl("https://custom.newapi/v1")
    facade.setModel("custom-chat")
    facade.setProvider("siliconflow")
    facade.setLlmApiKey("sk-live")
    facade.save()
    qapp.processEvents()

    persisted = fake_services.configuration_service.saved_config
    assert persisted is not None
    assert persisted["llm"]["provider"] == "siliconflow"
    assert persisted["llm"]["newapi"]["base_url"] == "https://custom.newapi/v1"
    assert persisted["llm"]["newapi"]["model"] == "custom-chat"


def test_settings_facade_validation_surfaces_errors(fake_services: FakeServices, qapp: QApplication) -> None:
    facade = SettingsFacade(lambda: fake_services)
    facade.reload()
    facade.setBaseUrl("")
    facade.setLlmApiKey("")
    facade.validate()
    qapp.processEvents()

    assert "LLM base_url 未配置。" in facade.validationSummary
    assert "缺少 LLM API Key。" in facade.validationSummary
