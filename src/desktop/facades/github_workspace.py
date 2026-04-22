from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from src.services import ApplicationServices

from ..models import GithubProjectListModel, GithubSnapshotListModel
from ..tasks import GithubCommandGateway
from ..workers import AsyncTaskThread


_SORT_LABELS = {
    "stars": "总 Stars",
    "stars_today": "今日增长",
    "stars_weekly": "本周增长",
    "updated": "最近更新",
}

_FETCH_PROGRESS_STAGE_PERCENT = {
    "starting": 5,
    "searching": 15,
    "deduplicating": 68,
    "computing_trends": 80,
    "saving": 92,
    "completed": 100,
    "error": 100,
}


class GithubWorkspaceFacade(QObject):
    currentDateChanged = Signal()
    busyChanged = Signal()
    errorMessageChanged = Signal()
    noticeMessageChanged = Signal()
    staleChanged = Signal()
    categoryFilterChanged = Signal()
    selectedLanguagesChanged = Signal()
    minStarsChanged = Signal()
    sortKeyChanged = Signal()
    searchQueryChanged = Signal()
    trendFilterChanged = Signal()
    hasSelectionChanged = Signal()
    selectedProjectNameChanged = Signal()
    selectedProjectUrlChanged = Signal()
    selectedProjectDescriptionChanged = Signal()
    summaryTextChanged = Signal()
    lastFetchOutcomeChanged = Signal()
    statusToneChanged = Signal()
    fetchProgressValueChanged = Signal()
    availableLanguagesChanged = Signal()

    def __init__(self, services_getter, parent=None) -> None:
        super().__init__(parent)
        self._services_getter = services_getter
        self._gateway = GithubCommandGateway(services_getter)
        self._snapshot_model = GithubSnapshotListModel(self)
        self._project_model = GithubProjectListModel(self)
        self._snapshot_model.selectionChanged.connect(self.currentDateChanged)
        self._project_model.selectionChanged.connect(self._sync_selected_project_properties)
        self._project_model.selectionChanged.connect(self.hasSelectionChanged)
        self._task_thread: AsyncTaskThread | None = None
        self._current_date = ""
        self._busy = False
        self._error_message = ""
        self._notice_message = ""
        self._stale = True
        self._category_filter = ""
        self._selected_languages: list[str] = []
        self._min_stars = 0
        self._sort_key = "stars"
        self._search_query = ""
        self._trend_filter = ""
        self._selected_project_name = ""
        self._selected_project_url = ""
        self._selected_project_description = ""
        self._summary_text = ""
        self._last_fetch_outcome = ""
        self._status_tone = "neutral"
        self._fetch_progress_value = 0
        self._available_languages: list[dict[str, Any]] = []

    def _services(self) -> ApplicationServices:
        return self._services_getter()

    def _filters_payload(self) -> dict[str, Any]:
        return {
            "categoryFilter": self._category_filter,
            "selectedLanguages": list(self._selected_languages),
            "minStars": self._min_stars,
            "sortKey": self._sort_key,
            "searchQuery": self._search_query,
            "trendFilter": self._trend_filter,
        }

    def _base_filters(self) -> dict[str, Any]:
        return {
            "categoryFilter": "",
            "selectedLanguages": [],
            "minStars": 0,
            "sortKey": "stars",
            "searchQuery": "",
            "trendFilter": "",
        }

    def _set_busy(self, value: bool) -> None:
        value = bool(value)
        if value == self._busy:
            return
        self._busy = value
        self.busyChanged.emit()

    def _set_error_message(self, value: str) -> None:
        value = value.strip()
        if value == self._error_message:
            return
        self._error_message = value
        self.errorMessageChanged.emit()
        self._refresh_status_tone()

    def _set_notice_message(self, value: str) -> None:
        value = value.strip()
        if value == self._notice_message:
            return
        self._notice_message = value
        self.noticeMessageChanged.emit()

    def _set_stale(self, value: bool) -> None:
        value = bool(value)
        if value == self._stale:
            return
        self._stale = value
        self.staleChanged.emit()

    def _set_current_date(self, value: str) -> None:
        value = value.strip()
        if value == self._current_date:
            return
        self._current_date = value
        self.currentDateChanged.emit()

    def _set_selected_project_name(self, value: str) -> None:
        if value == self._selected_project_name:
            return
        self._selected_project_name = value
        self.selectedProjectNameChanged.emit()

    def _set_selected_project_url(self, value: str) -> None:
        if value == self._selected_project_url:
            return
        self._selected_project_url = value
        self.selectedProjectUrlChanged.emit()

    def _set_selected_project_description(self, value: str) -> None:
        if value == self._selected_project_description:
            return
        self._selected_project_description = value
        self.selectedProjectDescriptionChanged.emit()

    def _set_summary_text(self, value: str) -> None:
        if value == self._summary_text:
            return
        self._summary_text = value
        self.summaryTextChanged.emit()

    def _set_last_fetch_outcome(self, value: str) -> None:
        if value == self._last_fetch_outcome:
            return
        self._last_fetch_outcome = value
        self.lastFetchOutcomeChanged.emit()
        self._refresh_status_tone()

    def _set_status_tone(self, value: str) -> None:
        if value == self._status_tone:
            return
        self._status_tone = value
        self.statusToneChanged.emit()

    def _set_fetch_progress_value(self, value: int) -> None:
        value = max(0, min(100, int(value)))
        if value == self._fetch_progress_value:
            return
        self._fetch_progress_value = value
        self.fetchProgressValueChanged.emit()

    def _refresh_status_tone(self) -> None:
        if self._error_message:
            self._set_status_tone("error")
            return
        if self._last_fetch_outcome == "degraded":
            self._set_status_tone("warning")
            return
        self._set_status_tone("neutral")

    def _set_available_languages(self, value: list[dict[str, Any]]) -> None:
        normalized = [
            {
                "value": str(item.get("value", "") or ""),
                "label": str(item.get("label", "") or ""),
                "count": int(item.get("count", 0) or 0),
            }
            for item in value
        ]
        if normalized == self._available_languages:
            return
        self._available_languages = normalized
        self.availableLanguagesChanged.emit()

    def _mark_stale(self) -> None:
        if not self._busy:
            self._set_notice_message("")
        self._set_stale(True)

    def _sync_selected_project_properties(self) -> None:
        item = self._project_model.selected_item()
        description = str(item.get("descriptionZh") or item.get("description") or "")
        self._set_selected_project_name(str(item.get("fullName", "") or ""))
        self._set_selected_project_url(str(item.get("htmlUrl", "") or ""))
        self._set_selected_project_description(description)

    def _update_available_languages(self, snapshot: dict[str, Any] | None) -> None:
        stats = (snapshot or {}).get("stats", {})
        by_language = dict(stats.get("byLanguage", {}) or {})
        items = [
            {
                "value": language,
                "label": f"{language} ({count})",
                "count": int(count),
            }
            for language, count in sorted(
                by_language.items(),
                key=lambda item: (-int(item[1]), str(item[0]).casefold()),
            )
            if str(language).strip()
        ]
        self._set_available_languages(items)

    def _update_summary(self, snapshot: dict[str, Any] | None) -> None:
        if not snapshot or not self._current_date:
            self._set_summary_text("")
            return
        total = int(snapshot.get("stats", {}).get("total", len(snapshot.get("projects", []))) or 0)
        parts = [self._current_date, f"{total} 个项目", _SORT_LABELS.get(self._sort_key, self._sort_key)]
        if self._search_query:
            parts.append(f'搜索 “{self._search_query}”')
        self._set_summary_text(" · ".join(parts))

    def _apply_project_snapshot(self, snapshot: dict[str, Any] | None) -> None:
        projects = list((snapshot or {}).get("projects", []))
        self._project_model.replace_items(projects)
        if projects:
            selected_id = self._project_model.selected_id()
            if not selected_id or self._project_model.row_for_id(selected_id) < 0:
                self._project_model.set_selected_id(str(projects[0].get("id", "") or ""))
        else:
            self._project_model.clear()
        self._sync_selected_project_properties()
        self._update_summary(snapshot)

    def _load_project_snapshot(self, date_value: str) -> None:
        raw_snapshot = self._gateway.load_snapshot(date_value, self._base_filters())
        if raw_snapshot is not None:
            self._snapshot_model.update_item_metadata(
                date_value,
                project_count=int(raw_snapshot.get("stats", {}).get("total", 0) or 0),
                generated_at=str(raw_snapshot.get("generatedAt", "") or ""),
            )
            self._update_available_languages(raw_snapshot)
        else:
            self._update_available_languages(None)

        filtered_snapshot = self._gateway.load_snapshot(date_value, self._filters_payload())
        self._apply_project_snapshot(filtered_snapshot)
        self._set_stale(False)

    def get_current_date(self) -> str:
        return self._current_date

    def get_busy(self) -> bool:
        return self._busy

    def get_error_message(self) -> str:
        return self._error_message

    def get_notice_message(self) -> str:
        return self._notice_message

    def get_stale(self) -> bool:
        return self._stale

    def get_category_filter(self) -> str:
        return self._category_filter

    def get_selected_languages(self) -> list[str]:
        return list(self._selected_languages)

    def get_min_stars(self) -> int:
        return self._min_stars

    def get_sort_key(self) -> str:
        return self._sort_key

    def get_search_query(self) -> str:
        return self._search_query

    def get_trend_filter(self) -> str:
        return self._trend_filter

    def get_has_selection(self) -> bool:
        return bool(self._project_model.selected_id())

    def get_selected_project_name(self) -> str:
        return self._selected_project_name

    def get_selected_project_url(self) -> str:
        return self._selected_project_url

    def get_selected_project_description(self) -> str:
        return self._selected_project_description

    def get_summary_text(self) -> str:
        return self._summary_text

    def get_last_fetch_outcome(self) -> str:
        return self._last_fetch_outcome

    def get_status_tone(self) -> str:
        return self._status_tone

    def get_fetch_progress_value(self) -> int:
        return self._fetch_progress_value

    def get_available_languages(self) -> list[dict[str, Any]]:
        return list(self._available_languages)

    def get_snapshot_model(self) -> GithubSnapshotListModel:
        return self._snapshot_model

    def get_project_model(self) -> GithubProjectListModel:
        return self._project_model

    @Slot()
    def markStale(self) -> None:
        self._mark_stale()

    @Slot()
    def reload(self) -> None:
        self._set_error_message("")
        if not self._current_date:
            self.reloadDates()
            if not self._current_date:
                self._project_model.clear()
                self._sync_selected_project_properties()
                self._set_summary_text("")
                self._update_available_languages(None)
                self._set_stale(False)
                return
        self.selectDate(self._current_date)

    @Slot()
    def reloadDates(self) -> None:
        self._set_error_message("")
        payload = self._gateway.list_dates()
        items = list(payload.get("dates", []))
        latest = str(payload.get("latest", "") or "")
        desired_date = self._current_date if self._current_date else latest
        if desired_date and not any(item.get("date") == desired_date for item in items):
            desired_date = latest
        self._snapshot_model.replace_items(items)
        self._snapshot_model.set_selected_date(desired_date)
        self._set_current_date(desired_date)

    @Slot(str)
    def selectDate(self, date_value: str) -> None:
        date_value = date_value.strip()
        if not date_value:
            self._set_current_date("")
            self._snapshot_model.set_selected_date("")
            self._project_model.clear()
            self._sync_selected_project_properties()
            self._set_summary_text("")
            self._update_available_languages(None)
            self._set_stale(False)
            return

        self._set_error_message("")
        self._snapshot_model.set_selected_date(date_value)
        self._set_current_date(date_value)
        self._load_project_snapshot(date_value)

    @Slot(int)
    def selectSnapshotRow(self, row: int) -> None:
        if row < 0 or row >= self._snapshot_model.rowCount():
            return
        item = self._snapshot_model.data(
            self._snapshot_model.index(row, 0),
            next(iter(self._snapshot_model.roleNames())),
        )
        self.selectDate(str(item or ""))

    @Slot(int)
    def selectProjectRow(self, row: int) -> None:
        if row < 0 or row >= self._project_model.rowCount():
            return
        item = self._project_model.data(
            self._project_model.index(row, 0),
            next(iter(self._project_model.roleNames())),
        )
        self._project_model.set_selected_id(str(item or ""))

    @Slot(str)
    def setCategoryFilter(self, value: str) -> None:
        value = value.strip()
        if value == self._category_filter:
            return
        self._category_filter = value
        self.categoryFilterChanged.emit()
        self._mark_stale()

    @Slot("QVariantList")
    def setSelectedLanguages(self, value) -> None:
        normalized = [
            str(item).strip()
            for item in list(value or [])
            if str(item).strip()
        ]
        normalized = normalized[:1]
        if normalized == self._selected_languages:
            return
        self._selected_languages = normalized
        self.selectedLanguagesChanged.emit()
        self._mark_stale()

    @Slot(int)
    def setMinStars(self, value: int) -> None:
        value = max(0, int(value))
        if value == self._min_stars:
            return
        self._min_stars = value
        self.minStarsChanged.emit()
        self._mark_stale()

    @Slot(str)
    def setSortKey(self, value: str) -> None:
        value = value.strip() or "stars"
        if value not in _SORT_LABELS:
            value = "stars"
        if value == self._sort_key:
            return
        self._sort_key = value
        self.sortKeyChanged.emit()
        self._mark_stale()

    @Slot(str)
    def setSearchQuery(self, value: str) -> None:
        value = value.strip()
        if value == self._search_query:
            return
        self._search_query = value
        self.searchQueryChanged.emit()
        self._mark_stale()

    @Slot(str)
    def setTrendFilter(self, value: str) -> None:
        value = value.strip()
        if value not in {"", "hot", "rising", "stable"}:
            value = ""
        if value == self._trend_filter:
            return
        self._trend_filter = value
        self.trendFilterChanged.emit()
        self._mark_stale()

    @Slot()
    def clearFilters(self) -> None:
        self._category_filter = ""
        self.categoryFilterChanged.emit()
        self._selected_languages = []
        self.selectedLanguagesChanged.emit()
        self._min_stars = 0
        self.minStarsChanged.emit()
        self._sort_key = "stars"
        self.sortKeyChanged.emit()
        self._search_query = ""
        self.searchQueryChanged.emit()
        self._trend_filter = ""
        self.trendFilterChanged.emit()
        self._mark_stale()
        if self._current_date:
            self.reload()

    @Slot()
    def runFetch(self) -> None:
        if self._task_thread is not None:
            return
        self._set_busy(True)
        self._set_last_fetch_outcome("")
        self._set_error_message("")
        self._set_notice_message("正在抓取 GitHub 趋势快照...")
        self._set_fetch_progress_value(5)
        self._task_thread = AsyncTaskThread(
            lambda emit: self._gateway.run_fetch(progress_callback=emit),
            self,
        )
        self._task_thread.progress.connect(self._handle_fetch_progress)
        self._task_thread.succeeded.connect(self._handle_fetch_success)
        self._task_thread.failed.connect(self._handle_fetch_failure)
        self._task_thread.finished.connect(self._clear_task)
        self._task_thread.start()

    @Slot()
    def openSelectedRepo(self) -> None:
        if not self._selected_project_url:
            return
        QDesktopServices.openUrl(QUrl(self._selected_project_url))

    def _clear_task(self) -> None:
        self._task_thread = None
        self._set_busy(False)

    def _handle_fetch_progress(self, payload: dict[str, Any]) -> None:
        stage = str(payload.get("stage", "") or "running")
        message = str(payload.get("message", "") or "GitHub 趋势抓取中")
        current = payload.get("current")
        total = payload.get("total")
        if stage == "searching" and isinstance(current, int) and isinstance(total, int) and total > 0:
            percent = 15 + round((current / total) * 45)
        else:
            percent = _FETCH_PROGRESS_STAGE_PERCENT.get(stage, self._fetch_progress_value)
        self._set_fetch_progress_value(percent)
        self._set_notice_message(f"{stage}: {message}")

    def _has_official_snapshots(self) -> bool:
        return bool(self._gateway.list_dates().get("dates", []))

    def _degraded_notice_message(self) -> str:
        if self._has_official_snapshots():
            return "GitHub 抓取受限，已保留当前正式快照；恢复 GITHUB_TOKEN 后重试。"
        return "GitHub 抓取受限，未生成正式快照；请配置 GITHUB_TOKEN 后重试。"

    def _handle_fetch_success(self, result: object) -> None:
        payload = dict(result or {})
        if str(payload.get("outcome", "") or "success") == "degraded":
            self._set_last_fetch_outcome("degraded")
            self._set_error_message("")
            self._set_fetch_progress_value(100)
            self._set_notice_message(self._degraded_notice_message())
            return

        snapshot = payload.get("snapshot")
        self._set_last_fetch_outcome("success")
        self._set_fetch_progress_value(100)
        self._set_notice_message("GitHub 趋势快照已刷新。")
        self.reloadDates()
        latest_date = ""
        for item in self._gateway.list_dates().get("dates", []):
            if item.get("isLatest"):
                latest_date = str(item.get("date", "") or "")
                break
        if latest_date:
            self.selectDate(latest_date)
        elif isinstance(snapshot, dict) and snapshot.get("date"):
            self.selectDate(str(snapshot.get("date", "") or ""))

    def _handle_fetch_failure(self, message: str) -> None:
        self._set_last_fetch_outcome("error")
        self._set_fetch_progress_value(100)
        self._set_error_message(message)
        self._set_notice_message("")

    currentDate = Property(str, get_current_date, notify=currentDateChanged)
    busy = Property(bool, get_busy, notify=busyChanged)
    errorMessage = Property(str, get_error_message, notify=errorMessageChanged)
    noticeMessage = Property(str, get_notice_message, notify=noticeMessageChanged)
    stale = Property(bool, get_stale, notify=staleChanged)
    categoryFilter = Property(str, get_category_filter, setCategoryFilter, notify=categoryFilterChanged)
    selectedLanguages = Property(
        "QVariantList",
        get_selected_languages,
        setSelectedLanguages,
        notify=selectedLanguagesChanged,
    )
    minStars = Property(int, get_min_stars, setMinStars, notify=minStarsChanged)
    sortKey = Property(str, get_sort_key, setSortKey, notify=sortKeyChanged)
    searchQuery = Property(str, get_search_query, setSearchQuery, notify=searchQueryChanged)
    trendFilter = Property(str, get_trend_filter, setTrendFilter, notify=trendFilterChanged)
    hasSelection = Property(bool, get_has_selection, notify=hasSelectionChanged)
    selectedProjectName = Property(str, get_selected_project_name, notify=selectedProjectNameChanged)
    selectedProjectUrl = Property(str, get_selected_project_url, notify=selectedProjectUrlChanged)
    selectedProjectDescription = Property(
        str,
        get_selected_project_description,
        notify=selectedProjectDescriptionChanged,
    )
    summaryText = Property(str, get_summary_text, notify=summaryTextChanged)
    lastFetchOutcome = Property(str, get_last_fetch_outcome, notify=lastFetchOutcomeChanged)
    statusTone = Property(str, get_status_tone, notify=statusToneChanged)
    fetchProgressValue = Property(int, get_fetch_progress_value, notify=fetchProgressValueChanged)
    availableLanguages = Property(
        "QVariantList",
        get_available_languages,
        notify=availableLanguagesChanged,
    )
    snapshotModel = Property(QObject, get_snapshot_model, constant=True)
    projectModel = Property(QObject, get_project_model, constant=True)
