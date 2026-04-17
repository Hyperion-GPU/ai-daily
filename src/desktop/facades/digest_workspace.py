from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from ..models import DigestArchiveListModel, DigestArticleListModel
from ..tasks import DigestCommandGateway
from ..workers import AsyncTaskThread


_SORT_LABELS = {
    "importance": "按重要度",
    "published": "按发布时间",
}

_PROGRESS_STAGE_PERCENT = {
    "starting": 5,
    "fetching": 20,
    "stage1": 45,
    "stage2": 75,
    "finalizing": 92,
    "completed": 100,
    "error": 100,
}


class DigestWorkspaceFacade(QObject):
    currentDateChanged = Signal()
    selectedArticleIdChanged = Signal()
    busyChanged = Signal()
    errorMessageChanged = Signal()
    noticeMessageChanged = Signal()
    staleChanged = Signal()
    categoryFilterChanged = Signal()
    selectedTagsChanged = Signal()
    minImportanceChanged = Signal()
    sortKeyChanged = Signal()
    searchQueryChanged = Signal()
    availableTagsChanged = Signal()
    archiveCountChanged = Signal()
    currentDateArticleCountChanged = Signal()
    filteredArticleCountChanged = Signal()
    summaryTextChanged = Signal()
    pipelineProgressTextChanged = Signal()
    pipelineProgressValueChanged = Signal()
    lastFetchOutcomeChanged = Signal()
    hasSelectionChanged = Signal()
    selectedArticleChanged = Signal()

    def __init__(self, services_getter, parent=None) -> None:
        super().__init__(parent)
        self._gateway = DigestCommandGateway(services_getter)
        self._archive_model = DigestArchiveListModel(self)
        self._article_model = DigestArticleListModel(self)
        self._article_model.selectionChanged.connect(self.selectedArticleIdChanged)
        self._article_model.selectionChanged.connect(self.hasSelectionChanged)
        self._article_model.selectionChanged.connect(self.selectedArticleChanged)
        self._task_thread: AsyncTaskThread | None = None
        self._current_date = ""
        self._busy = False
        self._error_message = ""
        self._notice_message = ""
        self._stale = True
        self._category_filter = ""
        self._selected_tags: list[str] = []
        self._min_importance = 1
        self._sort_key = "importance"
        self._search_query = ""
        self._available_tags: list[dict[str, Any]] = []
        self._archive_count = 0
        self._current_date_article_count = 0
        self._filtered_article_count = 0
        self._summary_text = ""
        self._pipeline_progress_text = ""
        self._pipeline_progress_value = 0
        self._last_fetch_outcome = ""

    def _filters_payload(self) -> dict[str, Any]:
        return {
            "selectedTags": list(self._selected_tags),
            "categoryFilter": self._category_filter,
            "minImportance": self._min_importance,
            "sortKey": self._sort_key,
            "searchQuery": self._search_query,
        }

    def _base_filters(self) -> dict[str, Any]:
        return {
            "selectedTags": [],
            "categoryFilter": "",
            "minImportance": 1,
            "sortKey": "importance",
            "searchQuery": "",
        }

    def _set_current_date(self, value: str) -> None:
        value = value.strip()
        if value == self._current_date:
            return
        self._current_date = value
        self.currentDateChanged.emit()

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

    def _set_available_tags(self, tags: list[dict[str, Any]]) -> None:
        normalized: list[dict[str, Any]] = []
        for tag in tags:
            value = str(tag.get("value", "") or "").strip()
            if not value:
                continue
            normalized.append(
                {
                    "value": value,
                    "label": str(tag.get("label", value) or value),
                    "count": int(tag.get("count", 0) or 0),
                }
            )
        if normalized == self._available_tags:
            return
        self._available_tags = normalized
        self.availableTagsChanged.emit()

    def _set_archive_count(self, value: int) -> None:
        value = int(value)
        if value == self._archive_count:
            return
        self._archive_count = value
        self.archiveCountChanged.emit()

    def _set_current_date_article_count(self, value: int) -> None:
        value = int(value)
        if value == self._current_date_article_count:
            return
        self._current_date_article_count = value
        self.currentDateArticleCountChanged.emit()

    def _set_filtered_article_count(self, value: int) -> None:
        value = int(value)
        if value == self._filtered_article_count:
            return
        self._filtered_article_count = value
        self.filteredArticleCountChanged.emit()

    def _set_summary_text(self, value: str) -> None:
        if value == self._summary_text:
            return
        self._summary_text = value
        self.summaryTextChanged.emit()

    def _set_pipeline_progress_text(self, value: str) -> None:
        if value == self._pipeline_progress_text:
            return
        self._pipeline_progress_text = value
        self.pipelineProgressTextChanged.emit()

    def _set_pipeline_progress_value(self, value: int) -> None:
        value = max(0, min(100, int(value)))
        if value == self._pipeline_progress_value:
            return
        self._pipeline_progress_value = value
        self.pipelineProgressValueChanged.emit()

    def _set_last_fetch_outcome(self, value: str) -> None:
        if value == self._last_fetch_outcome:
            return
        self._last_fetch_outcome = value
        self.lastFetchOutcomeChanged.emit()

    def _sync_selected_tags_to_available(self) -> None:
        if not self._selected_tags:
            return
        visible = {item["value"] for item in self._available_tags}
        filtered = [tag for tag in self._selected_tags if tag in visible]
        if filtered == self._selected_tags:
            return
        self._selected_tags = filtered
        self.selectedTagsChanged.emit()

    def _clear_article_state(self) -> None:
        self._article_model.clear()
        self._set_current_date_article_count(0)
        self._set_filtered_article_count(0)
        self._set_available_tags([])
        self._set_summary_text("")
        self.hasSelectionChanged.emit()
        self.selectedArticleChanged.emit()
        self.selectedArticleIdChanged.emit()

    def _update_summary_text(self) -> None:
        if not self._current_date:
            self._set_summary_text("")
            return
        parts = [
            self._current_date,
            f"{self._filtered_article_count} 篇文章",
            _SORT_LABELS.get(self._sort_key, self._sort_key),
        ]
        if self._search_query:
            parts.append(f'搜索 “{self._search_query}”')
        if self._category_filter:
            parts.append(f"分类 {self._category_filter}")
        if self._selected_tags:
            parts.append("标签 " + " / ".join(self._selected_tags))
        self._set_summary_text(" · ".join(parts))

    def _apply_article_snapshot(self, snapshot: dict[str, Any] | None) -> None:
        items = list((snapshot or {}).get("articles", []))
        previous_selected_id = self._article_model.selected_id()
        self._article_model.replace_items(items)
        if items:
            if not previous_selected_id or self._article_model.row_for_id(previous_selected_id) < 0:
                self._article_model.set_selected_id(str(items[0].get("id", "") or ""))
        else:
            self._article_model.clear()
        self._set_filtered_article_count(int((snapshot or {}).get("stats", {}).get("total", len(items)) or 0))
        self._update_summary_text()
        self.hasSelectionChanged.emit()
        self.selectedArticleChanged.emit()
        self.selectedArticleIdChanged.emit()

    def _available_tags_from_snapshot(self, snapshot: dict[str, Any] | None) -> list[dict[str, Any]]:
        by_tag = dict((snapshot or {}).get("stats", {}).get("byTag", {}) or {})
        return [
            {
                "value": str(tag),
                "label": f"{tag} ({_count})",
                "count": int(_count),
            }
            for tag, _count in sorted(
                by_tag.items(),
                key=lambda item: (-int(item[1]), str(item[0]).casefold()),
            )
            if str(tag).strip()
        ]

    def _load_snapshot_for_date(self, date_value: str) -> None:
        base_snapshot = self._gateway.load_snapshot(date_value, self._base_filters())
        self._set_current_date_article_count(int((base_snapshot or {}).get("stats", {}).get("total", 0) or 0))
        self._set_available_tags(self._available_tags_from_snapshot(base_snapshot))
        self._sync_selected_tags_to_available()

        filtered_snapshot = self._gateway.load_snapshot(date_value, self._filters_payload())
        self._apply_article_snapshot(filtered_snapshot)
        self._set_stale(False)

    def get_current_date(self) -> str:
        return self._current_date

    def get_selected_article_id(self) -> str:
        return self._article_model.selected_id()

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

    def get_selected_tags(self) -> list[str]:
        return list(self._selected_tags)

    def get_min_importance(self) -> int:
        return self._min_importance

    def get_sort_key(self) -> str:
        return self._sort_key

    def get_search_query(self) -> str:
        return self._search_query

    def get_available_tags(self) -> list[dict[str, Any]]:
        return list(self._available_tags)

    def get_archive_count(self) -> int:
        return self._archive_count

    def get_current_date_article_count(self) -> int:
        return self._current_date_article_count

    def get_filtered_article_count(self) -> int:
        return self._filtered_article_count

    def get_summary_text(self) -> str:
        return self._summary_text

    def get_pipeline_progress_text(self) -> str:
        return self._pipeline_progress_text

    def get_pipeline_progress_value(self) -> int:
        return self._pipeline_progress_value

    def get_last_fetch_outcome(self) -> str:
        return self._last_fetch_outcome

    def get_has_selection(self) -> bool:
        return bool(self._article_model.selected_id())

    def get_selected_article(self) -> dict[str, Any]:
        return self._article_model.selected_item()

    def get_archive_model(self) -> DigestArchiveListModel:
        return self._archive_model

    def get_article_model(self) -> DigestArticleListModel:
        return self._article_model

    @Slot()
    def markStale(self) -> None:
        if not self._busy:
            self._set_notice_message("配置已变化，当前日报工作区等待刷新。")
        self._set_stale(True)

    @Slot()
    def reload(self) -> None:
        self._set_error_message("")
        self._reload_dates()
        if not self._current_date:
            self._clear_article_state()
            self._set_stale(False)
            return
        self.selectDate(self._current_date)

    def _reload_dates(self, *, select_latest: bool = False) -> str:
        payload = self._gateway.list_dates()
        items = list(payload.get("dates", []))
        latest = str(payload.get("latest", "") or "")
        desired_date = latest if select_latest else (self._current_date or latest)
        if desired_date and not any(item.get("date") == desired_date for item in items):
            desired_date = latest
        self._archive_model.replace_items(items)
        self._archive_model.set_selected_date(desired_date)
        self._set_current_date(desired_date)
        self._set_archive_count(len(items))
        return desired_date

    @Slot()
    def reloadDates(self) -> None:
        self._reload_dates()

    @Slot(str)
    def selectDate(self, date_value: str) -> None:
        date_value = date_value.strip()
        if not date_value:
            self._archive_model.set_selected_date("")
            self._set_current_date("")
            self._clear_article_state()
            self._set_stale(False)
            return
        self._set_error_message("")
        self._archive_model.set_selected_date(date_value)
        self._set_current_date(date_value)
        self._load_snapshot_for_date(date_value)

    @Slot(int)
    def selectArchiveRow(self, row: int) -> None:
        if row < 0 or row >= self._archive_model.rowCount():
            return
        item = self._archive_model.data(
            self._archive_model.index(row, 0),
            next(iter(self._archive_model.roleNames())),
        )
        self.selectDate(str(item or ""))

    @Slot(int)
    def selectArticleRow(self, row: int) -> None:
        if row < 0 or row >= self._article_model.rowCount():
            return
        item = self._article_model.data(
            self._article_model.index(row, 0),
            next(iter(self._article_model.roleNames())),
        )
        self._article_model.set_selected_id(str(item or ""))
        self.hasSelectionChanged.emit()
        self.selectedArticleChanged.emit()
        self.selectedArticleIdChanged.emit()

    def _reload_current_date_if_ready(self) -> None:
        if self._current_date:
            self.selectDate(self._current_date)

    @Slot(str)
    def setCategoryFilter(self, value: str) -> None:
        value = value.strip()
        if value == self._category_filter:
            return
        self._category_filter = value
        self.categoryFilterChanged.emit()
        self._reload_current_date_if_ready()

    @Slot(str)
    def toggleTagSelection(self, value: str) -> None:
        value = value.strip()
        if not value:
            return
        if value in self._selected_tags:
            self._selected_tags = [tag for tag in self._selected_tags if tag != value]
        else:
            self._selected_tags = [*self._selected_tags, value]
        self.selectedTagsChanged.emit()
        self._reload_current_date_if_ready()

    @Slot()
    def clearSelectedTags(self) -> None:
        if not self._selected_tags:
            return
        self._selected_tags = []
        self.selectedTagsChanged.emit()
        self._reload_current_date_if_ready()

    @Slot(int)
    def setMinImportance(self, value: int) -> None:
        value = max(1, min(5, int(value)))
        if value == self._min_importance:
            return
        self._min_importance = value
        self.minImportanceChanged.emit()
        self._reload_current_date_if_ready()

    @Slot(str)
    def setSortKey(self, value: str) -> None:
        value = value.strip() or "importance"
        if value not in _SORT_LABELS:
            value = "importance"
        if value == self._sort_key:
            return
        self._sort_key = value
        self.sortKeyChanged.emit()
        self._reload_current_date_if_ready()

    @Slot(str)
    def setSearchQuery(self, value: str) -> None:
        value = value.strip()
        if value == self._search_query:
            return
        self._search_query = value
        self.searchQueryChanged.emit()
        self._reload_current_date_if_ready()

    @Slot()
    def clearFilters(self) -> None:
        changed = False
        if self._category_filter:
            self._category_filter = ""
            self.categoryFilterChanged.emit()
            changed = True
        if self._selected_tags:
            self._selected_tags = []
            self.selectedTagsChanged.emit()
            changed = True
        if self._min_importance != 1:
            self._min_importance = 1
            self.minImportanceChanged.emit()
            changed = True
        if self._sort_key != "importance":
            self._sort_key = "importance"
            self.sortKeyChanged.emit()
            changed = True
        if self._search_query:
            self._search_query = ""
            self.searchQueryChanged.emit()
            changed = True
        if changed:
            self._reload_current_date_if_ready()

    @Slot()
    def runFetch(self) -> None:
        if self._task_thread is not None:
            return
        self._set_busy(True)
        self._set_error_message("")
        self._set_notice_message("正在抓取 RSS 与摘要...")
        self._set_pipeline_progress_text("starting: 正在抓取 RSS 与摘要...")
        self._set_pipeline_progress_value(5)
        self._task_thread = AsyncTaskThread(
            lambda emit: self._gateway.run_fetch(progress_callback=emit),
            self,
        )
        self._task_thread.progress.connect(self._handle_progress)
        self._task_thread.succeeded.connect(self._handle_success)
        self._task_thread.failed.connect(self._handle_failure)
        self._task_thread.finished.connect(self._clear_task)
        self._task_thread.start()

    @Slot()
    def openSelectedArticle(self) -> None:
        url = str(self.get_selected_article().get("url", "") or "")
        if not url:
            return
        QDesktopServices.openUrl(QUrl(url))

    def _clear_task(self) -> None:
        self._task_thread = None
        self._set_busy(False)

    def _handle_progress(self, payload: dict[str, Any]) -> None:
        stage = str(payload.get("stage", "") or "running")
        message = str(payload.get("message", "") or "处理中")
        current = payload.get("current")
        total = payload.get("total")
        if isinstance(current, int) and isinstance(total, int) and total > 0:
            percent = max(0, min(100, round((current / total) * 100)))
        else:
            percent = _PROGRESS_STAGE_PERCENT.get(stage, 0)
        status_text = f"{stage}: {message}"
        self._set_pipeline_progress_text(status_text)
        self._set_pipeline_progress_value(percent)
        self._set_notice_message(status_text)

    def _handle_success(self, result: object) -> None:
        payload = dict(result or {})
        outcome = str(payload.get("outcome", payload.get("result", "")) or "success")
        if outcome == "no_new_items":
            self._set_last_fetch_outcome("no_new_items")
            notice = "没有新的日报内容，已保留现有归档。"
        else:
            self._set_last_fetch_outcome("success")
            notice = "今日日报已更新。"
        self._set_pipeline_progress_text("completed: 已完成")
        self._set_pipeline_progress_value(100)
        self._set_notice_message(notice)
        if outcome == "success":
            latest_date = self._reload_dates(select_latest=True)
            if latest_date:
                self.selectDate(latest_date)

    def _handle_failure(self, message: str) -> None:
        self._set_last_fetch_outcome("error")
        self._set_error_message(message)
        self._set_notice_message("")
        self._set_pipeline_progress_text(f"error: {message}")
        self._set_pipeline_progress_value(100)

    currentDate = Property(str, get_current_date, notify=currentDateChanged)
    selectedArticleId = Property(str, get_selected_article_id, notify=selectedArticleIdChanged)
    busy = Property(bool, get_busy, notify=busyChanged)
    errorMessage = Property(str, get_error_message, notify=errorMessageChanged)
    noticeMessage = Property(str, get_notice_message, notify=noticeMessageChanged)
    stale = Property(bool, get_stale, notify=staleChanged)
    categoryFilter = Property(str, get_category_filter, setCategoryFilter, notify=categoryFilterChanged)
    selectedTags = Property("QVariantList", get_selected_tags, notify=selectedTagsChanged)
    minImportance = Property(int, get_min_importance, setMinImportance, notify=minImportanceChanged)
    sortKey = Property(str, get_sort_key, setSortKey, notify=sortKeyChanged)
    searchQuery = Property(str, get_search_query, setSearchQuery, notify=searchQueryChanged)
    availableTags = Property("QVariantList", get_available_tags, notify=availableTagsChanged)
    archiveCount = Property(int, get_archive_count, notify=archiveCountChanged)
    currentDateArticleCount = Property(int, get_current_date_article_count, notify=currentDateArticleCountChanged)
    filteredArticleCount = Property(int, get_filtered_article_count, notify=filteredArticleCountChanged)
    summaryText = Property(str, get_summary_text, notify=summaryTextChanged)
    pipelineProgressText = Property(str, get_pipeline_progress_text, notify=pipelineProgressTextChanged)
    pipelineProgressValue = Property(int, get_pipeline_progress_value, notify=pipelineProgressValueChanged)
    lastFetchOutcome = Property(str, get_last_fetch_outcome, notify=lastFetchOutcomeChanged)
    hasSelection = Property(bool, get_has_selection, notify=hasSelectionChanged)
    selectedArticle = Property("QVariantMap", get_selected_article, notify=selectedArticleChanged)
    archiveModel = Property(QObject, get_archive_model, constant=True)
    articleModel = Property(QObject, get_article_model, constant=True)
