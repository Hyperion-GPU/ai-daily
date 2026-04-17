from __future__ import annotations

from PySide6.QtCore import QObject, Property, Signal, Slot


class ShellFacade(QObject):
    currentWorkspaceChanged = Signal()
    currentIndexChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._workspaces: list[dict[str, str]] = [
            {
                "key": "ai-daily",
                "title": "AI Daily",
                "subtitle": "日报工作台",
                "description": "按日期归档、筛选与阅读 AI 日报，并在同一张 quiet editorial workbench 上完成抓取与详情联动。",
                "iconSource": "qrc:/qt/qml/AIDaily/Desktop/assets/branding/icon-digest.svg",
            },
            {
                "key": "github-trends",
                "title": "GitHub Trends",
                "subtitle": "趋势工作台",
                "description": "按日期切换快照、应用筛选并在阅读式布局中浏览趋势项目与仓库详情。",
                "iconSource": "qrc:/qt/qml/AIDaily/Desktop/assets/branding/icon-trending.svg",
            },
            {
                "key": "settings",
                "title": "Settings",
                "subtitle": "配置工作台",
                "description": "集中维护 provider、密钥、运行参数与桌面数据目录等配置项。",
                "iconSource": "qrc:/qt/qml/AIDaily/Desktop/assets/branding/icon-settings.svg",
            },
        ]
        self._current_workspace = "settings"

    @Property("QVariantList", constant=True)
    def workspaces(self) -> list[dict[str, str]]:
        return self._workspaces

    @Property(str, notify=currentWorkspaceChanged)
    def currentWorkspace(self) -> str:
        return self._current_workspace

    @Property(int, notify=currentIndexChanged)
    def currentIndex(self) -> int:
        return self._index_for(self._current_workspace)

    @Slot(str)
    def setCurrentWorkspace(self, workspace: str) -> None:
        self.selectWorkspace(workspace)

    @Slot(str)
    def selectWorkspace(self, key: str) -> None:
        key = key.strip()
        if not key or key == self._current_workspace or self._index_for(key) < 0:
            return
        self._current_workspace = key
        self.currentWorkspaceChanged.emit()
        self.currentIndexChanged.emit()

    @Slot(int)
    def selectIndex(self, index: int) -> None:
        if index < 0 or index >= len(self._workspaces):
            return
        self.selectWorkspace(self._workspaces[index]["key"])

    @Slot(str, result="QVariantMap")
    def workspace(self, key: str) -> dict[str, str]:
        for item in self._workspaces:
            if item["key"] == key:
                return item
        return {}

    def _index_for(self, key: str) -> int:
        for index, item in enumerate(self._workspaces):
            if item["key"] == key:
                return index
        return -1
