from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Property, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from ..models import DigestArchiveListModel, DigestArticleListModel
from ..tasks import DigestCommandGateway
from ..workers import AsyncTaskThread, normalize_failure_payload
from .digest_workspace_support import DigestFilterState, DigestSnapshotLoader


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
_FILTER_RELOAD_DEBOUNCE_MS = 120


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
        self._task_threads: dict[int, AsyncTaskThread] = {}
        self._task_request_id = 0
        self._snapshot_request_id = 0
        self._pending_filter_request_id = 0
        self._filters = DigestFilterState()
        self._snapshot_loader = DigestSnapshotLoader(self._gateway)
        self._filter_reload_timer = QTimer(self)
        self._filter_reload_timer.setSingleShot(True)
        self._filter_reload_timer.setInterval(_FILTER_RELOAD_DEBOUNCE_MS)
        self._filter_reload_timer.timeout.connect(self._apply_pending_filter_reload)
        self._current_date = ""
        self._busy = False
        self._error_message = ""
        self._notice_message = ""
        self._stale = True
        self._available_tags: list[dict[str, Any]] = []
        self._archive_count = 0
        self._current_date_article_count = 0
        self._filtered_article_count = 0
        self._summary_text = ""
        self._pipeline_progress_text = ""
        self._pipeline_progress_value = 0
        self._last_fetch_outcome = ""

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

    @staticmethod
    def _normalize_available_tags(tags: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
        return normalized

    def _replace_available_tags(self, tags: list[dict[str, Any]]) -> bool:
        normalized = self._normalize_available_tags(tags)
        if normalized == self._available_tags:
            return False
        self._available_tags = normalized
        return True

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

    def _sync_available_tags_and_selection(self, tags: list[dict[str, Any]]) -> None:
        available_tags_changed = self._replace_available_tags(tags)
        selected_tags_changed = self._filters.sync_selected_tags_to_available(self._available_tags)
        if selected_tags_changed:
            self.selectedTagsChanged.emit()
        if available_tags_changed:
            self.availableTagsChanged.emit()

    def _clear_article_state(self) -> None:
        self._article_model.clear()
        self._set_current_date_article_count(0)
        self._set_filtered_article_count(0)
        self._sync_available_tags_and_selection([])
        self._set_summary_text("")
        self.hasSelectionChanged.emit()
        self.selectedArticleChanged.emit()
        self.selectedArticleIdChanged.emit()

    def _update_summary_text(self) -> None:
        self._set_summary_text(
            self._filters.summary_text(
                current_date=self._current_date,
                filtered_count=self._filtered_article_count,
                sort_labels=_SORT_LABELS,
            )
        )

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

    def _invalidate_base_snapshot_cache(self) -> None:
        self._snapshot_loader.invalidate_cache()

    def _next_snapshot_request_id(self) -> int:
        self._snapshot_request_id += 1
        return self._snapshot_request_id

    def _is_latest_snapshot_request(self, request_id: int) -> bool:
        return request_id == self._snapshot_request_id

    def _cancel_pending_filter_reload(self) -> None:
        if self._filter_reload_timer.isActive():
            self._filter_reload_timer.stop()
        self._pending_filter_request_id = 0

    def _schedule_current_date_reload(self) -> None:
        if not self._current_date:
            return
        self._pending_filter_request_id = self._next_snapshot_request_id()
        self._filter_reload_timer.start()

    def _apply_pending_filter_reload(self) -> None:
        request_id = self._pending_filter_request_id
        self._pending_filter_request_id = 0
        if not request_id or not self._is_latest_snapshot_request(request_id) or not self._current_date:
            return
        self._load_snapshot_for_date(self._current_date, request_id=request_id)

    def _load_snapshot_for_date(self, date_value: str, *, request_id: int) -> None:
        if not self._is_latest_snapshot_request(request_id) or date_value != self._current_date:
            return
        base_snapshot_load = self._snapshot_loader.load(date_value, DigestFilterState())
        if not self._is_latest_snapshot_request(request_id) or date_value != self._current_date:
            return
        self._set_current_date_article_count(base_snapshot_load.current_article_count)
        self._sync_available_tags_and_selection(base_snapshot_load.available_tags)
        if not self._is_latest_snapshot_request(request_id) or date_value != self._current_date:
            return
        snapshot_load = (
            base_snapshot_load
            if self._filters.is_base()
            else self._snapshot_loader.load(date_value, self._filters)
        )
        if not self._is_latest_snapshot_request(request_id) or date_value != self._current_date:
            return
        self._apply_article_snapshot(snapshot_load.filtered_snapshot)
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
        return self._filters.category_filter

    def get_selected_tags(self) -> list[str]:
        return list(self._filters.selected_tags)

    def get_min_importance(self) -> int:
        return self._filters.min_importance

    def get_sort_key(self) -> str:
        return self._filters.sort_key

    def get_search_query(self) -> str:
        return self._filters.search_query

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
        self._cancel_pending_filter_reload()
        self._invalidate_base_snapshot_cache()
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
        available_dates = {str(item.get("date", "") or "") for item in items}
        self._snapshot_loader.prune_cache(available_dates)
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
        self._cancel_pending_filter_reload()
        self._reload_dates()

    @Slot(str)
    def selectDate(self, date_value: str) -> None:
        date_value = date_value.strip()
        self._cancel_pending_filter_reload()
        request_id = self._next_snapshot_request_id()
        if not date_value:
            self._archive_model.set_selected_date("")
            self._set_current_date("")
            self._clear_article_state()
            self._set_stale(False)
            return
        self._set_error_message("")
        self._archive_model.set_selected_date(date_value)
        self._set_current_date(date_value)
        self._load_snapshot_for_date(date_value, request_id=request_id)

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
        self._schedule_current_date_reload()

    @Slot(str)
    def setCategoryFilter(self, value: str) -> None:
        value = value.strip()
        if value == self._filters.category_filter:
            return
        self._filters.category_filter = value
        self.categoryFilterChanged.emit()
        self._reload_current_date_if_ready()

    @Slot(str)
    def toggleTagSelection(self, value: str) -> None:
        value = value.strip()
        if not value:
            return
        if value in self._filters.selected_tags:
            self._filters.selected_tags = [tag for tag in self._filters.selected_tags if tag != value]
        else:
            self._filters.selected_tags = [*self._filters.selected_tags, value]
        self.selectedTagsChanged.emit()
        self._reload_current_date_if_ready()

    @Slot()
    def clearSelectedTags(self) -> None:
        if not self._filters.selected_tags:
            return
        self._filters.selected_tags = []
        self.selectedTagsChanged.emit()
        self._reload_current_date_if_ready()

    @Slot(int)
    def setMinImportance(self, value: int) -> None:
        value = max(1, min(5, int(value)))
        if value == self._filters.min_importance:
            return
        self._filters.min_importance = value
        self.minImportanceChanged.emit()
        self._reload_current_date_if_ready()

    @Slot(str)
    def setSortKey(self, value: str) -> None:
        value = value.strip() or "importance"
        if value not in _SORT_LABELS:
            value = "importance"
        if value == self._filters.sort_key:
            return
        self._filters.sort_key = value
        self.sortKeyChanged.emit()
        self._reload_current_date_if_ready()

    @Slot(str)
    def setSearchQuery(self, value: str) -> None:
        value = value.strip()
        if value == self._filters.search_query:
            return
        self._filters.search_query = value
        self.searchQueryChanged.emit()
        self._reload_current_date_if_ready()

    @Slot()
    def clearFilters(self) -> None:
        changed = False
        if self._filters.category_filter:
            self._filters.category_filter = ""
            self.categoryFilterChanged.emit()
            changed = True
        if self._filters.selected_tags:
            self._filters.selected_tags = []
            self.selectedTagsChanged.emit()
            changed = True
        if self._filters.min_importance != 1:
            self._filters.min_importance = 1
            self.minImportanceChanged.emit()
            changed = True
        if self._filters.sort_key != "importance":
            self._filters.sort_key = "importance"
            self.sortKeyChanged.emit()
            changed = True
        if self._filters.search_query:
            self._filters.search_query = ""
            self.searchQueryChanged.emit()
            changed = True
        if changed:
            self._reload_current_date_if_ready()

    @Slot()
    def runFetch(self) -> None:
        request_id = self._next_task_request_id()
        self._set_busy(True)
        self._set_error_message("")
        self._set_notice_message("正在抓取 RSS 与摘要...")
        self._set_pipeline_progress_text("starting: 正在抓取 RSS 与摘要...")
        self._set_pipeline_progress_value(5)
        task_thread = AsyncTaskThread(
            lambda emit: self._gateway.run_fetch(progress_callback=emit),
            self,
        )
        self._task_threads[request_id] = task_thread
        self._task_thread = task_thread
        task_thread.progress.connect(
            lambda payload, request_id=request_id: self._handle_progress(request_id, payload)
        )
        task_thread.succeeded.connect(
            lambda result, request_id=request_id: self._handle_success(request_id, result)
        )
        task_thread.failed.connect(
            lambda failure, request_id=request_id: self._handle_failure(request_id, failure)
        )
        task_thread.finished.connect(
            lambda request_id=request_id, task_thread=task_thread: self._clear_task(request_id, task_thread)
        )
        task_thread.start()

    @Slot()
    def openSelectedArticle(self) -> None:
        url = str(self.get_selected_article().get("url", "") or "")
        if not url:
            return
        QDesktopServices.openUrl(QUrl(url))

    def _next_task_request_id(self) -> int:
        self._task_request_id += 1
        return self._task_request_id

    def _is_latest_task(self, request_id: int) -> bool:
        return request_id == self._task_request_id

    def _clear_task(self, request_id: int, task_thread: AsyncTaskThread) -> None:
        self._task_threads.pop(request_id, None)
        if self._task_thread is task_thread:
            self._task_thread = None
        task_thread.deleteLater()
        if self._is_latest_task(request_id):
            self._set_busy(False)

    def _handle_progress(self, request_id: int, payload: dict[str, Any]) -> None:
        if not self._is_latest_task(request_id):
            return
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

    def _handle_success(self, request_id: int, result: object) -> None:
        if not self._is_latest_task(request_id):
            return
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
            self._invalidate_base_snapshot_cache()
            latest_date = self._reload_dates(select_latest=True)
            if latest_date:
                self.selectDate(latest_date)

    def _handle_failure(self, request_id: int, failure: object) -> None:
        if not self._is_latest_task(request_id):
            return
        payload = normalize_failure_payload(failure)
        message = str(payload.get("message", "") or "任务失败")
        stage = str(payload.get("stage", "") or "task")
        self._set_last_fetch_outcome("error")
        self._set_error_message(message)
        self._set_notice_message("")
        self._set_pipeline_progress_text(f"{stage}: {message}" if stage == "error" else f"error: {message}")
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
