from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, QResource, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication

from src.runtime import sync_web_data_to_desktop
from src.services import ApplicationServices
from src.settings import load_config

from .facades import DigestWorkspaceFacade, GithubWorkspaceFacade, SettingsFacade, ShellFacade

DEFAULT_QUICK_STYLE = "Basic"
SUPPORTED_QUICK_STYLES = {"Basic", "Fusion"}
QML_IMPORT_ROOT = "qrc:/qt/qml"
QML_MAIN_URL = QUrl(f"{QML_IMPORT_ROOT}/AIDaily/Desktop/Main.qml")
RESOURCE_BUNDLE_PATH = Path(__file__).resolve().with_name("resources.rcc")
_RESOURCE_BUNDLE_REGISTERED = False


def register_qml_resources() -> Path:
    global _RESOURCE_BUNDLE_REGISTERED

    if _RESOURCE_BUNDLE_REGISTERED:
        return RESOURCE_BUNDLE_PATH
    if not RESOURCE_BUNDLE_PATH.is_file():
        raise RuntimeError(f"Desktop resource bundle not found: {RESOURCE_BUNDLE_PATH}")
    if not QResource.registerResource(str(RESOURCE_BUNDLE_PATH)):
        raise RuntimeError(f"Failed to register desktop resource bundle: {RESOURCE_BUNDLE_PATH}")
    _RESOURCE_BUNDLE_REGISTERED = True
    return RESOURCE_BUNDLE_PATH


register_qml_resources()


@dataclass(slots=True)
class QmlRuntime:
    app: QApplication
    engine: QQmlApplicationEngine
    shell: ShellFacade
    settings: SettingsFacade
    digest: DigestWorkspaceFacade
    github: GithubWorkspaceFacade
    services: ApplicationServices

    @property
    def root_object(self) -> QObject | None:
        objects = self.engine.rootObjects()
        return objects[0] if objects else None

    def close(self) -> None:
        root = self.root_object
        if root is not None:
            root.setProperty("visible", False)
            root.deleteLater()
        self.engine.deleteLater()
        self.app.processEvents()


def _resolve_quick_style() -> str:
    requested = (
        os.environ.get("AI_DAILY_QML_STYLE")
        or os.environ.get("QT_QUICK_CONTROLS_STYLE")
        or DEFAULT_QUICK_STYLE
    )
    return requested if requested in SUPPORTED_QUICK_STYLES else DEFAULT_QUICK_STYLE


def configure_quick_controls() -> str:
    style = _resolve_quick_style()
    os.environ.setdefault("QT_QUICK_CONTROLS_CONF", ":/qtquickcontrols2.conf")
    os.environ["QT_QUICK_CONTROLS_STYLE"] = style
    QQuickStyle.setStyle(style)
    QQuickStyle.setFallbackStyle("Fusion")
    return style


def create_desktop_services() -> ApplicationServices:
    config = load_config(mode="desktop")
    sync_web_data_to_desktop(config=config)
    return ApplicationServices(
        config=config,
        load_config_fn=lambda: load_config(mode="desktop"),
    )


def _app_icon() -> QIcon:
    for candidate in (
        ":/qt/qml/AIDaily/Desktop/assets/branding/ai-daily-icon.png",
        ":/qt/qml/AIDaily/Desktop/assets/branding/icon-settings.svg",
    ):
        icon = QIcon(candidate)
        if not icon.isNull():
            return icon
    return QIcon()


def create_qml_runtime(
    argv: list[str] | None = None,
    *,
    show: bool = False,
    shell: ShellFacade | None = None,
    settings: SettingsFacade | None = None,
    digest: DigestWorkspaceFacade | None = None,
    github: GithubWorkspaceFacade | None = None,
    services: ApplicationServices | None = None,
) -> QmlRuntime:
    configure_quick_controls()
    app = QApplication.instance()
    if app is None:
        app = QApplication(list(argv or sys.argv))

    icon = _app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    runtime_services = services or create_desktop_services()
    shell_facade = shell or ShellFacade()
    settings_facade = settings or SettingsFacade(lambda: runtime_services)
    digest_facade = digest or DigestWorkspaceFacade(lambda: runtime_services)
    github_facade = github or GithubWorkspaceFacade(lambda: runtime_services)

    settings_facade.saved.connect(digest_facade.markStale)
    settings_facade.saved.connect(github_facade.markStale)

    def _reload_digest_if_needed() -> None:
        if shell_facade.currentWorkspace == "ai-daily" and (digest_facade.stale or not digest_facade.currentDate):
            digest_facade.reload()

    def _reload_github_if_needed() -> None:
        if shell_facade.currentWorkspace == "github-trends" and (github_facade.stale or not github_facade.currentDate):
            github_facade.reload()

    shell_facade.currentWorkspaceChanged.connect(_reload_digest_if_needed)
    shell_facade.currentWorkspaceChanged.connect(_reload_github_if_needed)

    engine = QQmlApplicationEngine()
    engine.addImportPath(QML_IMPORT_ROOT)
    engine.rootContext().setContextProperty("appShellFacade", shell_facade)
    engine.rootContext().setContextProperty("desktopSettingsFacade", settings_facade)
    engine.rootContext().setContextProperty("desktopDigestFacade", digest_facade)
    engine.rootContext().setContextProperty("desktopGithubFacade", github_facade)
    engine.load(QML_MAIN_URL)

    if not engine.rootObjects():
        raise RuntimeError(f"Failed to load QML root from {QML_MAIN_URL.toString()}")

    root = engine.rootObjects()[0]
    root.setProperty("visible", show)
    return QmlRuntime(
        app=app,
        engine=engine,
        shell=shell_facade,
        settings=settings_facade,
        digest=digest_facade,
        github=github_facade,
        services=runtime_services,
    )


def launch_qml_desktop_app(argv: list[str] | None = None) -> int:
    runtime = create_qml_runtime(argv=argv, show=True)
    return int(runtime.app.exec())


def main(argv: list[str] | None = None) -> int:
    return launch_qml_desktop_app(argv=argv)


__all__ = [
    "DEFAULT_QUICK_STYLE",
    "QML_IMPORT_ROOT",
    "QML_MAIN_URL",
    "QmlRuntime",
    "RESOURCE_BUNDLE_PATH",
    "ShellFacade",
    "SettingsFacade",
    "configure_quick_controls",
    "create_desktop_services",
    "create_qml_runtime",
    "launch_qml_desktop_app",
    "main",
    "register_qml_resources",
]
