from __future__ import annotations

import copy
import os
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from src.runtime import get_runtime_paths, sync_web_data_to_desktop
from src.services import ApplicationServices
from src.settings import (
    get_github_token,
    get_llm_api_key,
    load_config,
    save_config,
    set_github_token,
    set_llm_api_key,
)

from .workers import AsyncTaskThread

CATEGORY_LABELS = {
    "": "全部",
    "arxiv": "Arxiv",
    "official": "官方",
    "news": "新闻",
    "community": "社区",
}
GITHUB_CATEGORY_LABELS = {
    "": "全部",
    "llm": "LLM",
    "agent": "Agent",
    "cv": "CV",
    "nlp": "NLP",
    "ml_framework": "框架",
    "mlops": "MLOps",
    "general": "综合",
}
TREND_LABELS = {
    "": "全部",
    "hot": "Hot",
    "rising": "Rising",
    "stable": "Stable",
}

DESKTOP_THEME = {
    "paper_base": "#f5f4f1",
    "paper_surface": "#f9f8f6",
    "paper_elevated": "#ffffff",
    "paper_strong": "#eae8e4",
    "ink_strong": "#191918",
    "ink": "#3d3d3a",
    "ink_soft": "#6b6b66",
    "ink_faint": "#9a9a94",
    "ink_hint": "#b5b5ae",
    "line": "#ddd9d3",
    "line_strong": "#cfc9c1",
    "line_faint": "#e8e5e0",
    "accent": "#c4956a",
    "accent_hover": "#b5875e",
    "accent_pressed": "#a67a54",
    "accent_soft": "#f1e7dd",
    "accent_text": "#a07550",
    "paper_inset": "#f0efec",
    "nav_selected_bar": "#c4956a",
}

DESKTOP_PANEL_TITLE_STYLE = (
    f"font-size: 20px; font-weight: 600; color: {DESKTOP_THEME['ink_strong']}; letter-spacing: -0.4px;"
)
DESKTOP_BRAND_STYLE = (
    f"font-size: 22px; font-weight: 600; color: {DESKTOP_THEME['ink_strong']}; letter-spacing: -0.5px;"
)
DESKTOP_SUBTITLE_STYLE = f"color: {DESKTOP_THEME['ink_soft']}; font-size: 13px;"
DESKTOP_STAT_VALUE_STYLE = (
    f"font-size: 18px; font-weight: 600; color: {DESKTOP_THEME['ink_strong']}; letter-spacing: -0.2px;"
)
DESKTOP_STAT_LABEL_STYLE = (
    f"color: {DESKTOP_THEME['ink_soft']}; font-size: 11px; letter-spacing: 0.4px; text-transform: uppercase;"
)

DESKTOP_DETAIL_CSS = f"""
    body {{
        font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        font-size: 13px;
        line-height: 1.8;
        color: {DESKTOP_THEME["ink"]};
        margin: 0;
        padding: 4px 0;
    }}
    h2 {{
        font-size: 17px;
        font-weight: 600;
        color: {DESKTOP_THEME["ink_strong"]};
        margin: 0 0 14px 0;
        padding-bottom: 10px;
        border-bottom: 1px solid {DESKTOP_THEME["line_faint"]};
        letter-spacing: -0.3px;
        line-height: 1.35;
    }}
    .meta {{
        margin: 0 0 6px 0;
        padding: 0;
    }}
    .meta p {{
        margin: 3px 0;
        font-size: 12px;
        color: {DESKTOP_THEME["ink_soft"]};
        line-height: 1.6;
    }}
    .meta b {{
        font-weight: 600;
        color: {DESKTOP_THEME["ink_soft"]};
        display: inline-block;
        min-width: 65px;
    }}
    p {{
        margin: 4px 0;
    }}
    b {{
        font-weight: 600;
        color: {DESKTOP_THEME["ink_soft"]};
    }}
    hr {{
        border: none;
        border-top: 1px solid {DESKTOP_THEME["line_faint"]};
        margin: 16px 0;
    }}
    .summary {{
        margin-top: 10px;
        line-height: 1.9;
        color: {DESKTOP_THEME["ink"]};
        font-size: 13px;
    }}
"""


def create_desktop_services() -> ApplicationServices:
    config = load_config(mode="desktop")
    sync_web_data_to_desktop(config=config)
    return ApplicationServices(
        config=config,
        load_config_fn=lambda: load_config(mode="desktop"),
    )


def app_icon() -> QIcon:
    paths = get_runtime_paths(mode="desktop")
    candidates = [
        paths.brand_dir / "ai-daily.ico",
        paths.brand_dir / "ai-daily-mark.svg",
        paths.brand_dir / "favicon.svg",
    ]
    for candidate in candidates:
        if candidate.exists():
            return QIcon(str(candidate))
    return QIcon()


def format_datetime(raw: str | None) -> str:
    if not raw:
        return "—"
    return raw.replace("T", " ").replace("Z", "")


def _make_spin(
    min_val: int,
    max_val: int,
    min_width: int = 90,
    suffix: str = "",
    step: int = 1,
) -> QSpinBox:
    spin = QSpinBox()
    spin.setRange(min_val, max_val)
    spin.setMinimumWidth(min_width)
    if suffix:
        spin.setSuffix(suffix)
    if step != 1:
        spin.setSingleStep(step)
    return spin


def set_global_style(app: QApplication) -> None:
    app.setStyleSheet(
        f"""
        QWidget {{
            background: {DESKTOP_THEME["paper_base"]};
            color: {DESKTOP_THEME["ink"]};
            font-size: 13px;
            font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        }}
        QMainWindow, QSplitter {{
            background: {DESKTOP_THEME["paper_base"]};
        }}
        QListWidget, QTableWidget, QTextBrowser, QLineEdit, QComboBox, QSpinBox {{
            background: {DESKTOP_THEME["paper_elevated"]};
            border: 1px solid {DESKTOP_THEME["line"]};
            border-radius: 6px;
            selection-background-color: {DESKTOP_THEME["accent_soft"]};
            selection-color: {DESKTOP_THEME["ink_strong"]};
        }}
        QLineEdit, QComboBox {{
            padding: 6px 10px;
            min-height: 28px;
        }}
        QComboBox {{
            padding-right: 24px;
        }}
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
            border-color: {DESKTOP_THEME["accent"]};
        }}
        QGroupBox, QFrame#panel {{
            background: {DESKTOP_THEME["paper_elevated"]};
            border: 1px solid {DESKTOP_THEME["line"]};
            border-radius: 8px;
            margin-top: 6px;
        }}
        QGroupBox {{
            padding: 20px 18px 18px;
            font-weight: 500;
            font-size: 13px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 14px;
            padding: 0 6px;
            color: {DESKTOP_THEME["ink_faint"]};
            font-weight: 500;
            font-size: 10px;
            letter-spacing: 0.6px;
            text-transform: uppercase;
        }}
        QPushButton {{
            background: {DESKTOP_THEME["accent"]};
            color: #fffdfb;
            border: 1px solid {DESKTOP_THEME["accent"]};
            border-radius: 6px;
            padding: 7px 20px;
            font-weight: 600;
            font-size: 13px;
            letter-spacing: 0.1px;
        }}
        QPushButton:hover {{
            background: {DESKTOP_THEME["accent_hover"]};
            border-color: {DESKTOP_THEME["accent_hover"]};
        }}
        QPushButton:pressed {{
            background: {DESKTOP_THEME["accent_pressed"]};
            border-color: {DESKTOP_THEME["accent_pressed"]};
        }}
        QPushButton:disabled {{
            background: {DESKTOP_THEME["paper_strong"]};
            color: {DESKTOP_THEME["ink_hint"]};
            border-color: {DESKTOP_THEME["line"]};
        }}
        QPushButton#ghost {{
            background: transparent;
            color: {DESKTOP_THEME["ink_soft"]};
            border: 1px solid {DESKTOP_THEME["line"]};
        }}
        QPushButton#ghost:hover {{
            color: {DESKTOP_THEME["ink_strong"]};
            border-color: {DESKTOP_THEME["line_strong"]};
            background: {DESKTOP_THEME["paper_surface"]};
        }}
        QPushButton#ghost:pressed {{
            background: {DESKTOP_THEME["paper_strong"]};
            border-color: {DESKTOP_THEME["line_strong"]};
        }}
        QListWidget {{
            padding: 4px;
            outline: none;
        }}
        QListWidget::item {{
            padding: 8px 12px;
            margin: 1px 0;
            border-radius: 6px;
            border: none;
            color: {DESKTOP_THEME["ink"]};
        }}
        QListWidget::item:hover {{
            background: {DESKTOP_THEME["paper_surface"]};
        }}
        QListWidget::item:selected {{
            background: {DESKTOP_THEME["accent_soft"]};
            color: {DESKTOP_THEME["ink_strong"]};
        }}
        QListWidget#navList {{
            padding: 4px 0;
            outline: none;
            border: none;
            background: transparent;
        }}
        QListWidget#navList::item {{
            padding: 10px 16px 10px 14px;
            margin: 0;
            border-radius: 0;
            border-left: 3px solid transparent;
            color: {DESKTOP_THEME["ink_soft"]};
            font-size: 13px;
        }}
        QListWidget#navList::item:hover {{
            background: {DESKTOP_THEME["paper_strong"]};
            color: {DESKTOP_THEME["ink"]};
            border-left: 3px solid transparent;
        }}
        QListWidget#navList::item:selected {{
            background: transparent;
            color: {DESKTOP_THEME["ink_strong"]};
            font-weight: 600;
            border-left: 3px solid {DESKTOP_THEME["nav_selected_bar"]};
        }}
        QFrame#navPanel {{
            background: {DESKTOP_THEME["paper_inset"]};
            border: none;
            border-right: 1px solid {DESKTOP_THEME["line"]};
            border-radius: 0;
        }}
        QFrame#statCard {{
            background: {DESKTOP_THEME["paper_surface"]};
            border: 1px solid {DESKTOP_THEME["line_faint"]};
            border-radius: 6px;
            margin-top: 0;
        }}
        QHeaderView::section {{
            background: transparent;
            color: {DESKTOP_THEME["ink_faint"]};
            border: none;
            border-bottom: 1px solid {DESKTOP_THEME["line_faint"]};
            padding: 8px 10px;
            font-weight: 500;
            font-size: 10px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}
        QTableWidget {{
            gridline-color: transparent;
            alternate-background-color: {DESKTOP_THEME["paper_surface"]};
        }}
        QTableWidget::item {{
            padding: 8px 10px;
        }}
        QTableWidget::item:selected {{
            background: {DESKTOP_THEME["accent_soft"]};
            color: {DESKTOP_THEME["ink_strong"]};
        }}
        QTableWidget::item:hover {{
            background: {DESKTOP_THEME["paper_strong"]};
        }}
        QProgressBar {{
            border: 1px solid {DESKTOP_THEME["line"]};
            border-radius: 999px;
            text-align: center;
            background: {DESKTOP_THEME["paper_strong"]};
            min-height: 10px;
            max-height: 10px;
            font-size: 0px;
        }}
        QProgressBar::chunk {{
            border-radius: 999px;
            background: {DESKTOP_THEME["accent"]};
        }}
        QTextBrowser {{
            font-size: 13px;
            line-height: 1.7;
            padding: 18px 20px;
        }}
        QSplitter::handle {{
            background: transparent;
            width: 8px;
        }}
        QSplitter::handle:hover {{
            background: {DESKTOP_THEME["line"]};
            border-radius: 2px;
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 4px 0;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(0, 0, 0, 0.08);
            border-radius: 4px;
            min-height: 32px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: rgba(0, 0, 0, 0.16);
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar:horizontal {{
            background: transparent;
            height: 8px;
            margin: 0 4px;
        }}
        QScrollBar::handle:horizontal {{
            background: rgba(0, 0, 0, 0.08);
            border-radius: 4px;
            min-width: 32px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: rgba(0, 0, 0, 0.16);
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
        QScrollBar::add-page, QScrollBar::sub-page {{
            background: transparent;
        }}
        QSpinBox {{
            padding: 0 24px 0 10px;
            min-height: 28px;
        }}
        QSpinBox::up-button, QSpinBox::down-button {{
            width: 20px;
            border: none;
            background: transparent;
        }}
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background: {DESKTOP_THEME["paper_strong"]};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        QComboBox QAbstractItemView {{
            background: {DESKTOP_THEME["paper_elevated"]};
            border: 1px solid {DESKTOP_THEME["line"]};
            border-radius: 6px;
            padding: 4px;
            selection-background-color: {DESKTOP_THEME["accent_soft"]};
            selection-color: {DESKTOP_THEME["ink_strong"]};
            outline: none;
        }}
        QToolTip {{
            background: {DESKTOP_THEME["paper_elevated"]};
            color: {DESKTOP_THEME["ink"]};
            border: 1px solid {DESKTOP_THEME["line"]};
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
        }}
        QStatusBar {{
            background: {DESKTOP_THEME["paper_surface"]};
            color: {DESKTOP_THEME["ink_faint"]};
            border-top: 1px solid {DESKTOP_THEME["line"]};
            font-size: 12px;
            padding: 4px 12px;
        }}
        QFormLayout {{
            spacing: 8px;
        }}
        QLabel {{
            background: transparent;
        }}
        QCheckBox {{
            background: transparent;
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {DESKTOP_THEME["line_strong"]};
            border-radius: 3px;
            background: {DESKTOP_THEME["paper_elevated"]};
        }}
        QCheckBox::indicator:checked {{
            background: {DESKTOP_THEME["accent"]};
            border-color: {DESKTOP_THEME["accent"]};
        }}
        QMessageBox {{
            background: {DESKTOP_THEME["paper_elevated"]};
        }}
        QMessageBox QLabel {{
            color: {DESKTOP_THEME["ink"]};
            font-size: 13px;
        }}
        """
    )


class StatCard(QFrame):
    def __init__(self, title: str, value: str = "—", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("statCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(DESKTOP_STAT_VALUE_STYLE)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(DESKTOP_STAT_LABEL_STYLE)
        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class DigestPage(QWidget):
    def __init__(self, services_getter: Callable[[], ApplicationServices], parent=None) -> None:
        super().__init__(parent)
        self._services_getter = services_getter
        self._task_thread: AsyncTaskThread | None = None
        self._date_entries: list[dict] = []
        self._current_payload: dict | None = None
        self._visible_articles: list[dict] = []
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        hero = QGroupBox("AI 日报")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setSpacing(12)
        title_row = QHBoxLayout()
        copy_box = QVBoxLayout()
        copy_box.setSpacing(2)
        title = QLabel("每天一份可检索的 AI 编辑日报")
        title.setStyleSheet(DESKTOP_PANEL_TITLE_STYLE)
        subtitle = QLabel("在桌面端直接抓取、筛选、浏览并打开原文。")
        subtitle.setStyleSheet(DESKTOP_SUBTITLE_STYLE)
        copy_box.addWidget(title)
        copy_box.addWidget(subtitle)
        title_row.addLayout(copy_box)
        title_row.addStretch(1)
        self.fetch_button = QPushButton("抓取今日日报")
        self.fetch_button.setFixedHeight(34)
        self.fetch_button.clicked.connect(self.start_fetch)
        title_row.addWidget(self.fetch_button)
        hero_layout.addLayout(title_row)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        self.archive_card = StatCard("归档天数")
        self.article_card = StatCard("当前文章数")
        self.latest_card = StatCard("最新日期")
        for card in (self.archive_card, self.article_card, self.latest_card):
            stats_row.addWidget(card)
        hero_layout.addLayout(stats_row)

        progress_row = QVBoxLayout()
        self.progress_label = QLabel("等待手动抓取")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_row.addWidget(self.progress_label)
        progress_row.addWidget(self.progress_bar)
        hero_layout.addLayout(progress_row)
        root.addWidget(hero)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        left_panel = QGroupBox("日期与筛选")
        left_layout = QVBoxLayout(left_panel)
        self.date_list = QListWidget()
        self.date_list.currentRowChanged.connect(self._on_date_selected)
        left_layout.addWidget(self.date_list, 1)

        filters = QWidget()
        filters_layout = QFormLayout(filters)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索标题或摘要")
        self.search_input.textChanged.connect(self._apply_filters)
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("逗号分隔标签")
        self.tag_input.textChanged.connect(self._apply_filters)
        self.category_combo = QComboBox()
        for value, label in CATEGORY_LABELS.items():
            self.category_combo.addItem(label, value)
        self.category_combo.currentIndexChanged.connect(self._apply_filters)
        self.importance_spin = _make_spin(1, 5, min_width=80)
        self.importance_spin.setValue(1)
        self.importance_spin.valueChanged.connect(self._apply_filters)
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("按重要性", "importance")
        self.sort_combo.addItem("按发布时间", "published")
        self.sort_combo.currentIndexChanged.connect(self._apply_filters)
        filters_layout.addRow("搜索", self.search_input)
        filters_layout.addRow("标签", self.tag_input)
        filters_layout.addRow("分类", self.category_combo)
        filters_layout.addRow("最低重要性", self.importance_spin)
        filters_layout.addRow("排序", self.sort_combo)
        left_layout.addWidget(filters)
        splitter.addWidget(left_panel)

        center_panel = QGroupBox("文章列表")
        center_layout = QVBoxLayout(center_panel)
        self.article_table = QTableWidget(0, 5)
        self.article_table.setAlternatingRowColors(True)
        self.article_table.setHorizontalHeaderLabels(["标题", "来源", "分类", "重要性", "发布时间"])
        self.article_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.article_table.setSelectionMode(QTableWidget.SingleSelection)
        self.article_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.article_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.article_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.article_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.article_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.article_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.article_table.itemSelectionChanged.connect(self._update_article_detail)
        center_layout.addWidget(self.article_table)
        splitter.addWidget(center_panel)

        right_panel = QGroupBox("文章详情")
        right_layout = QVBoxLayout(right_panel)
        self.article_detail = QTextBrowser()
        self.article_detail.setOpenExternalLinks(False)
        self.open_article_button = QPushButton("打开原文")
        self.open_article_button.clicked.connect(self._open_current_article)
        self.open_article_button.setEnabled(False)
        right_layout.addWidget(self.article_detail, 1)
        right_layout.addWidget(self.open_article_button)
        splitter.addWidget(right_panel)

        splitter.setSizes([240, 620, 400])
        root.addWidget(splitter, 1)

    def _services(self) -> ApplicationServices:
        return self._services_getter()

    def reload(self) -> None:
        payload = self._services().get_dates()
        self._date_entries = payload["dates"]
        self.date_list.blockSignals(True)
        self.date_list.clear()
        for entry in self._date_entries:
            self.date_list.addItem(QListWidgetItem(f'{entry["date"]} · {entry["total"]}'))
        self.date_list.blockSignals(False)

        self.archive_card.set_value(str(len(self._date_entries)))
        latest_entry = self._date_entries[0] if self._date_entries else None
        self.latest_card.set_value(latest_entry["date"] if latest_entry else "—")
        total_articles = sum(entry.get("total", 0) for entry in self._date_entries)
        self.article_card.set_value(str(total_articles))

        if self._date_entries:
            self.date_list.setCurrentRow(0)
        else:
            self._current_payload = None
            self._visible_articles = []
            self.article_table.setRowCount(0)
            self.article_detail.setHtml(f"<style>{DESKTOP_DETAIL_CSS}</style><p>暂无日报数据。</p>")

    def _on_date_selected(self, index: int) -> None:
        if index < 0 or index >= len(self._date_entries):
            return
        date = self._date_entries[index]["date"]
        self._current_payload = self._services().get_digest(
            date,
            tags=[],
            category=None,
            min_importance=1,
            sort="importance",
            q=None,
        )
        self._apply_filters()

    def _selected_tags(self) -> list[str]:
        return [item.strip() for item in self.tag_input.text().split(",") if item.strip()]

    def _apply_filters(self) -> None:
        if not self._current_payload:
            return

        q = self.search_input.text().strip() or None
        category = self.category_combo.currentData()
        tags = self._selected_tags()
        payload = self._services().get_digest(
            self._current_payload["date"],
            tags=tags,
            category=category or None,
            min_importance=int(self.importance_spin.value()),
            sort=str(self.sort_combo.currentData()),
            q=q,
        )
        self._current_payload = payload
        articles = payload["articles"] if payload else []
        self._visible_articles = articles
        self.article_table.setRowCount(len(articles))
        for row, article in enumerate(articles):
            self.article_table.setItem(row, 0, QTableWidgetItem(article["title"]))
            self.article_table.setItem(row, 1, QTableWidgetItem(article["source_name"]))
            self.article_table.setItem(row, 2, QTableWidgetItem(article["source_category"]))
            self.article_table.setItem(row, 3, QTableWidgetItem(str(article["importance"])))
            self.article_table.setItem(row, 4, QTableWidgetItem(format_datetime(article["published"])))

        self.article_card.set_value(str(len(articles)))
        if articles:
            self.article_table.selectRow(0)
        else:
            self.open_article_button.setEnabled(False)
            self.article_detail.setHtml(f"<style>{DESKTOP_DETAIL_CSS}</style><p>当前筛选下没有结果。</p>")

    def _current_article(self) -> dict | None:
        row = self.article_table.currentRow()
        if row < 0 or row >= len(self._visible_articles):
            return None
        return self._visible_articles[row]

    def _update_article_detail(self) -> None:
        article = self._current_article()
        if not article:
            self.open_article_button.setEnabled(False)
            self.article_detail.setHtml(f"<style>{DESKTOP_DETAIL_CSS}</style><p>请选择一篇文章查看详情。</p>")
            return

        tags = " / ".join(article.get("tags", [])) or "—"
        html = f"""
        <style>{DESKTOP_DETAIL_CSS}</style>
        <h2>{article['title']}</h2>
        <div class="meta">
        <p><b>来源</b>{article['source_name']}</p>
        <p><b>分类</b>{article['source_category']}</p>
        <p><b>发布时间</b>{format_datetime(article['published'])}</p>
        <p><b>标签</b>{tags}</p>
        <p><b>重要性</b>{article['importance']}/5</p>
        </div>
        <hr />
        <p class="summary">{article['summary_zh']}</p>
        """
        self.article_detail.setHtml(html)
        self.open_article_button.setEnabled(True)

    def _open_current_article(self) -> None:
        article = self._current_article()
        if not article:
            return
        QDesktopServices.openUrl(QUrl(article["url"]))

    def start_fetch(self) -> None:
        if self._task_thread is not None:
            return

        self.fetch_button.setEnabled(False)
        self.progress_label.setText("正在抓取 RSS 与摘要…")
        self.progress_bar.setValue(5)
        self._task_thread = AsyncTaskThread(
            lambda emit: self._services().run_pipeline_async(progress_callback=emit),
            self,
        )
        self._task_thread.progress.connect(self._handle_progress)
        self._task_thread.succeeded.connect(self._handle_success)
        self._task_thread.failed.connect(self._handle_failure)
        self._task_thread.finished.connect(self._clear_task)
        self._task_thread.start()

    def _clear_task(self) -> None:
        self.fetch_button.setEnabled(True)
        self._task_thread = None

    def _handle_progress(self, payload: dict) -> None:
        stage = payload.get("stage") or "running"
        message = payload.get("message") or "处理中"
        current = payload.get("current")
        total = payload.get("total")
        if isinstance(current, int) and isinstance(total, int) and total > 0:
            percent = max(0, min(100, round((current / total) * 100)))
        else:
            stage_percent = {
                "starting": 5,
                "fetching": 20,
                "stage1": 45,
                "stage2": 75,
                "finalizing": 92,
                "completed": 100,
                "error": 100,
            }
            percent = stage_percent.get(str(stage), 0)
        self.progress_label.setText(f"{stage}: {message}")
        self.progress_bar.setValue(percent)

    def _handle_success(self, result: object) -> None:
        outcome = result.get("result") if isinstance(result, dict) else None
        if outcome == "no_new_items":
            QMessageBox.information(self, "AI 日报", "没有新的日报内容，已保留现有归档。")
        else:
            QMessageBox.information(self, "AI 日报", "今日日报已更新。")
        self.progress_label.setText("已完成")
        self.progress_bar.setValue(100)
        self.reload()

    def _handle_failure(self, message: str) -> None:
        self.progress_label.setText(message)
        self.progress_bar.setValue(100)
        QMessageBox.critical(self, "AI 日报", message)


class GithubTrendingPage(QWidget):
    def __init__(self, services_getter: Callable[[], ApplicationServices], parent=None) -> None:
        super().__init__(parent)
        self._services_getter = services_getter
        self._task_thread: AsyncTaskThread | None = None
        self._date_entries: list[str] = []
        self._current_payload: dict | None = None
        self._visible_projects: list[dict] = []
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        hero = QGroupBox("GitHub 趋势")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setSpacing(12)
        title_row = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("追踪 AI 相关仓库的近期上升趋势")
        title.setStyleSheet(DESKTOP_PANEL_TITLE_STYLE)
        subtitle = QLabel("本地点击触发抓取，支持按分类、语言、趋势筛选。")
        subtitle.setStyleSheet(DESKTOP_SUBTITLE_STYLE)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        title_row.addLayout(title_box)
        title_row.addStretch(1)
        self.fetch_button = QPushButton("抓取最新趋势")
        self.fetch_button.setFixedHeight(34)
        self.fetch_button.clicked.connect(self.start_fetch)
        title_row.addWidget(self.fetch_button)
        hero_layout.addLayout(title_row)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        self.snapshot_card = StatCard("快照数量")
        self.project_card = StatCard("当前项目数")
        self.latest_card = StatCard("最新日期")
        for card in (self.snapshot_card, self.project_card, self.latest_card):
            stats_row.addWidget(card)
        hero_layout.addLayout(stats_row)

        self.progress_label = QLabel("等待手动抓取")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        hero_layout.addWidget(self.progress_label)
        hero_layout.addWidget(self.progress_bar)
        root.addWidget(hero)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        left_panel = QGroupBox("日期与筛选")
        left_layout = QVBoxLayout(left_panel)
        self.date_list = QListWidget()
        self.date_list.currentRowChanged.connect(self._on_date_selected)
        left_layout.addWidget(self.date_list, 1)
        filters = QWidget()
        filters_layout = QFormLayout(filters)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索仓库名或描述")
        self.search_input.textChanged.connect(self._apply_filters)
        self.category_combo = QComboBox()
        for value, label in GITHUB_CATEGORY_LABELS.items():
            self.category_combo.addItem(label, value)
        self.category_combo.currentIndexChanged.connect(self._apply_filters)
        self.language_combo = QComboBox()
        self.language_combo.addItem("全部", "")
        self.language_combo.currentIndexChanged.connect(self._apply_filters)
        self.min_stars_spin = _make_spin(0, 1_000_000, min_width=120, step=100)
        self.min_stars_spin.valueChanged.connect(self._apply_filters)
        self.trend_combo = QComboBox()
        for value, label in TREND_LABELS.items():
            self.trend_combo.addItem(label, value)
        self.trend_combo.currentIndexChanged.connect(self._apply_filters)
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("总 Stars", "stars")
        self.sort_combo.addItem("今日增长", "stars_today")
        self.sort_combo.addItem("本周增长", "stars_weekly")
        self.sort_combo.addItem("最近更新", "updated")
        self.sort_combo.currentIndexChanged.connect(self._apply_filters)
        filters_layout.addRow("搜索", self.search_input)
        filters_layout.addRow("分类", self.category_combo)
        filters_layout.addRow("语言", self.language_combo)
        filters_layout.addRow("最低 Stars", self.min_stars_spin)
        filters_layout.addRow("趋势", self.trend_combo)
        filters_layout.addRow("排序", self.sort_combo)
        left_layout.addWidget(filters)
        splitter.addWidget(left_panel)

        center_panel = QGroupBox("仓库列表")
        center_layout = QVBoxLayout(center_panel)
        self.project_table = QTableWidget(0, 5)
        self.project_table.setAlternatingRowColors(True)
        self.project_table.setHorizontalHeaderLabels(["仓库", "语言", "Stars", "趋势", "更新"])
        self.project_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.project_table.setSelectionMode(QTableWidget.SingleSelection)
        self.project_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.project_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.project_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.project_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.project_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.project_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.project_table.itemSelectionChanged.connect(self._update_project_detail)
        center_layout.addWidget(self.project_table)
        splitter.addWidget(center_panel)

        right_panel = QGroupBox("仓库详情")
        right_layout = QVBoxLayout(right_panel)
        self.project_detail = QTextBrowser()
        self.open_repo_button = QPushButton("打开仓库")
        self.open_repo_button.clicked.connect(self._open_current_repo)
        self.open_repo_button.setEnabled(False)
        right_layout.addWidget(self.project_detail, 1)
        right_layout.addWidget(self.open_repo_button)
        splitter.addWidget(right_panel)

        splitter.setSizes([240, 620, 400])
        root.addWidget(splitter, 1)

    def _services(self) -> ApplicationServices:
        return self._services_getter()

    def reload(self) -> None:
        payload = self._services().get_github_dates()
        self._date_entries = payload["dates"]
        self.date_list.blockSignals(True)
        self.date_list.clear()
        for date in self._date_entries:
            self.date_list.addItem(QListWidgetItem(date))
        self.date_list.blockSignals(False)
        self.snapshot_card.set_value(str(len(self._date_entries)))
        self.latest_card.set_value(self._date_entries[0] if self._date_entries else "—")
        if self._date_entries:
            self.date_list.setCurrentRow(0)
        else:
            self.project_table.setRowCount(0)
            self.project_detail.setHtml(f"<style>{DESKTOP_DETAIL_CSS}</style><p>暂无 GitHub 趋势数据。</p>")

    def _on_date_selected(self, index: int) -> None:
        if index < 0 or index >= len(self._date_entries):
            return
        date = self._date_entries[index]
        self._current_payload = self._services().get_github_trending_by_date(
            date,
            category=None,
            language=[],
            min_stars=0,
            sort="stars",
            q=None,
            trend=None,
        )
        self._rebuild_language_options()
        self._apply_filters()

    def _rebuild_language_options(self) -> None:
        current = self.language_combo.currentData()
        self.language_combo.blockSignals(True)
        self.language_combo.clear()
        self.language_combo.addItem("全部", "")
        languages = (self._current_payload or {}).get("stats", {}).get("by_language", {})
        for language, count in sorted(languages.items(), key=lambda item: item[1], reverse=True):
            self.language_combo.addItem(f"{language} ({count})", language)
        index = max(0, self.language_combo.findData(current))
        self.language_combo.setCurrentIndex(index)
        self.language_combo.blockSignals(False)

    def _apply_filters(self) -> None:
        if not self._date_entries or self.date_list.currentRow() < 0:
            return
        date = self._date_entries[self.date_list.currentRow()]
        payload = self._services().get_github_trending_by_date(
            date,
            category=self.category_combo.currentData() or None,
            language=[self.language_combo.currentData()] if self.language_combo.currentData() else [],
            min_stars=int(self.min_stars_spin.value()),
            sort=str(self.sort_combo.currentData()),
            q=self.search_input.text().strip() or None,
            trend=self.trend_combo.currentData() or None,
        )
        self._current_payload = payload
        projects = payload["projects"] if payload else []
        self._visible_projects = projects
        self.project_table.setRowCount(len(projects))
        for row, project in enumerate(projects):
            self.project_table.setItem(row, 0, QTableWidgetItem(project["full_name"]))
            self.project_table.setItem(row, 1, QTableWidgetItem(project.get("language") or "—"))
            self.project_table.setItem(row, 2, QTableWidgetItem(str(project["stars"])))
            self.project_table.setItem(row, 3, QTableWidgetItem(project.get("trend") or "—"))
            self.project_table.setItem(row, 4, QTableWidgetItem(format_datetime(project.get("updated_at"))))
        self.project_card.set_value(str(len(projects)))
        if projects:
            self.project_table.selectRow(0)
        else:
            self.project_detail.setHtml(f"<style>{DESKTOP_DETAIL_CSS}</style><p>当前筛选下没有项目。</p>")
            self.open_repo_button.setEnabled(False)

    def _current_project(self) -> dict | None:
        row = self.project_table.currentRow()
        if row < 0 or row >= len(self._visible_projects):
            return None
        return self._visible_projects[row]

    def _update_project_detail(self) -> None:
        project = self._current_project()
        if not project:
            self.project_detail.setHtml(f"<style>{DESKTOP_DETAIL_CSS}</style><p>请选择一个项目查看详情。</p>")
            self.open_repo_button.setEnabled(False)
            return
        topics = ", ".join(project.get("topics") or []) or "—"
        html = f"""
        <style>{DESKTOP_DETAIL_CSS}</style>
        <h2>{project['full_name']}</h2>
        <div class="meta">
        <p><b>描述</b>{project.get('description_zh') or project.get('description') or '—'}</p>
        <p><b>语言</b>{project.get('language') or '—'}</p>
        <p><b>分类</b>{project.get('category') or '—'}</p>
        <p><b>Stars</b>{project['stars']}</p>
        <p><b>今日增长</b>{project.get('stars_today') if project.get('stars_today') is not None else '—'}</p>
        <p><b>本周增长</b>{project.get('stars_weekly') if project.get('stars_weekly') is not None else '—'}</p>
        <p><b>趋势</b>{project.get('trend') or '—'}</p>
        <p><b>License</b>{project.get('license') or '—'}</p>
        <p><b>Topics</b>{topics}</p>
        </div>
        """
        self.project_detail.setHtml(html)
        self.open_repo_button.setEnabled(True)

    def _open_current_repo(self) -> None:
        project = self._current_project()
        if not project:
            return
        QDesktopServices.openUrl(QUrl(project["html_url"]))

    def start_fetch(self) -> None:
        if self._task_thread is not None:
            return

        self.fetch_button.setEnabled(False)
        self.progress_label.setText("正在抓取 GitHub 趋势…")
        self.progress_bar.setValue(5)
        self._task_thread = AsyncTaskThread(
            lambda emit: self._services().run_github_fetch_async(progress_callback=emit),
            self,
        )
        self._task_thread.progress.connect(self._handle_progress)
        self._task_thread.succeeded.connect(self._handle_success)
        self._task_thread.failed.connect(self._handle_failure)
        self._task_thread.finished.connect(self._clear_task)
        self._task_thread.start()

    def _clear_task(self) -> None:
        self.fetch_button.setEnabled(True)
        self._task_thread = None

    def _handle_progress(self, payload: dict) -> None:
        stage = payload.get("stage") or "running"
        message = payload.get("message") or "处理中"
        current = payload.get("topics_done")
        total = payload.get("topics_total")
        if isinstance(current, int) and isinstance(total, int) and total > 0:
            percent = max(0, min(100, round((current / total) * 100)))
        else:
            stage_percent = {
                "starting": 5,
                "searching": 35,
                "deduplicating": 72,
                "computing_trends": 88,
                "saving": 96,
                "completed": 100,
                "error": 100,
            }
            percent = stage_percent.get(str(stage), 0)
        self.progress_label.setText(f"{stage}: {message}")
        self.progress_bar.setValue(percent)

    def _handle_success(self, result: object) -> None:
        QMessageBox.information(self, "GitHub 趋势", "GitHub 趋势快照已更新。")
        self.progress_label.setText("已完成")
        self.progress_bar.setValue(100)
        self.reload()

    def _handle_failure(self, message: str) -> None:
        self.progress_label.setText(message)
        self.progress_bar.setValue(100)
        QMessageBox.critical(self, "GitHub 趋势", message)


class SettingsPage(QWidget):
    def __init__(
        self,
        services_getter: Callable[[], ApplicationServices],
        on_saved: Callable[[dict], None],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._services_getter = services_getter
        self._on_saved = on_saved
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        intro = QGroupBox("设置")
        intro_layout = QVBoxLayout(intro)
        title = QLabel("桌面版本地配置与密钥")
        title.setStyleSheet(DESKTOP_PANEL_TITLE_STYLE)
        subtitle = QLabel("普通设置写入用户目录；密钥优先存入系统 keyring。")
        subtitle.setStyleSheet(DESKTOP_SUBTITLE_STYLE)
        intro_layout.addWidget(title)
        intro_layout.addWidget(subtitle)
        root.addWidget(intro)

        grid = QGridLayout()
        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 2)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        llm_group = QGroupBox("LLM")
        llm_form = QFormLayout(llm_group)
        self.provider_combo = QComboBox()
        self.provider_combo.addItem("siliconflow", "siliconflow")
        self.provider_combo.addItem("newapi", "newapi")
        self.provider_combo.currentIndexChanged.connect(self._reload_provider_fields)
        self.timezone_input = QLineEdit()
        self.base_url_input = QLineEdit()
        self.model_input = QLineEdit()
        self.temperature_input = _make_spin(0, 100, min_width=130, suffix=" / 100")
        self.max_tokens_input = _make_spin(1, 100000, min_width=110)
        self.llm_api_key_input = QLineEdit()
        self.llm_api_key_input.setEchoMode(QLineEdit.Password)
        llm_form.addRow("Provider", self.provider_combo)
        llm_form.addRow("Timezone", self.timezone_input)
        llm_form.addRow("Base URL", self.base_url_input)
        llm_form.addRow("Model", self.model_input)
        llm_form.addRow("Temperature", self.temperature_input)
        llm_form.addRow("Max Tokens", self.max_tokens_input)
        llm_form.addRow("LLM API Key", self.llm_api_key_input)
        grid.addWidget(llm_group, 0, 0)

        pipeline_group = QGroupBox("Pipeline")
        pipeline_group.setMinimumWidth(280)
        pipeline_form = QFormLayout(pipeline_group)
        self.time_window_input = _make_spin(1, 720, min_width=90)
        self.max_articles_input = _make_spin(1, 500, min_width=90)
        self.max_stage2_input = _make_spin(1, 1000, min_width=90)
        self.stage1_batch_input = _make_spin(1, 1000, min_width=90)
        pipeline_form.addRow("时间窗口（小时）", self.time_window_input)
        pipeline_form.addRow("日报上限", self.max_articles_input)
        pipeline_form.addRow("Stage2 上限", self.max_stage2_input)
        pipeline_form.addRow("Stage1 Batch", self.stage1_batch_input)
        grid.addWidget(pipeline_group, 0, 1)

        github_group = QGroupBox("GitHub Trending")
        github_form = QFormLayout(github_group)
        self.github_enabled_input = QCheckBox("启用 GitHub Trending")
        self.github_token_input = QLineEdit()
        self.github_token_input.setEchoMode(QLineEdit.Password)
        self.github_min_stars_input = _make_spin(0, 1_000_000, min_width=120)
        self.github_max_projects_input = _make_spin(1, 500, min_width=90)
        github_form.addRow("", self.github_enabled_input)
        github_form.addRow("GitHub Token", self.github_token_input)
        github_form.addRow("最小 Stars", self.github_min_stars_input)
        github_form.addRow("每日项目上限", self.github_max_projects_input)
        grid.addWidget(github_group, 1, 0, 1, 2)

        container = QWidget()
        container.setLayout(grid)
        root.addWidget(container)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self.open_dir_button = QPushButton("打开数据目录")
        self.open_dir_button.setObjectName("ghost")
        self.open_dir_button.clicked.connect(self._open_data_dir)
        self.test_button = QPushButton("测试配置")
        self.test_button.setObjectName("ghost")
        self.test_button.clicked.connect(self._test_settings)
        self.save_button = QPushButton("保存设置")
        self.save_button.clicked.connect(self._save_settings)
        button_row.addWidget(self.open_dir_button)
        button_row.addWidget(self.test_button)
        button_row.addWidget(self.save_button)
        root.addLayout(button_row)

    def _services(self) -> ApplicationServices:
        return self._services_getter()

    def reload(self) -> None:
        config = copy.deepcopy(self._services().current_config())
        llm_cfg = config.get("llm", {})
        provider = llm_cfg.get("provider", "siliconflow")
        self.provider_combo.setCurrentIndex(max(0, self.provider_combo.findData(provider)))
        self.timezone_input.setText(str(config.get("timezone", "Asia/Shanghai")))

        provider_cfg = llm_cfg.get(provider, {})
        self.base_url_input.setText(str(provider_cfg.get("base_url", "")))
        self.model_input.setText(str(provider_cfg.get("model", "")))
        self.temperature_input.setValue(int(float(provider_cfg.get("temperature", 0.3)) * 100))
        self.max_tokens_input.setValue(int(provider_cfg.get("max_tokens", 1500)))
        self.llm_api_key_input.setText(get_llm_api_key(config) or "")

        pipeline_cfg = config.get("pipeline", {})
        self.time_window_input.setValue(int(pipeline_cfg.get("time_window_hours", 48)))
        self.max_articles_input.setValue(int(pipeline_cfg.get("max_articles_per_day", 30)))
        self.max_stage2_input.setValue(int(pipeline_cfg.get("max_articles_to_stage2", 50)))
        self.stage1_batch_input.setValue(int(pipeline_cfg.get("stage1_batch_size", 50)))

        github_cfg = config.get("github_trending", {})
        self.github_enabled_input.setChecked(bool(github_cfg.get("enabled", False)))
        self.github_token_input.setText(get_github_token(config) or "")
        self.github_min_stars_input.setValue(int(github_cfg.get("min_stars", 500)))
        self.github_max_projects_input.setValue(int(github_cfg.get("max_projects_per_day", 50)))

    def _reload_provider_fields(self) -> None:
        config = self._services().current_config()
        llm_cfg = config.get("llm", {})
        provider = self.provider_combo.currentData()
        provider_cfg = llm_cfg.get(provider, {})
        self.base_url_input.setText(str(provider_cfg.get("base_url", "")))
        self.model_input.setText(str(provider_cfg.get("model", "")))
        self.temperature_input.setValue(int(float(provider_cfg.get("temperature", 0.3)) * 100))
        self.max_tokens_input.setValue(int(provider_cfg.get("max_tokens", 1500)))

    def _build_config(self) -> dict:
        config = copy.deepcopy(self._services().current_config())
        provider = self.provider_combo.currentData()
        config["timezone"] = self.timezone_input.text().strip() or "Asia/Shanghai"
        llm_cfg = config.setdefault("llm", {})
        llm_cfg["provider"] = provider
        provider_cfg = llm_cfg.setdefault(provider, {})
        provider_cfg["base_url"] = self.base_url_input.text().strip()
        provider_cfg["model"] = self.model_input.text().strip()
        provider_cfg["temperature"] = self.temperature_input.value() / 100
        provider_cfg["max_tokens"] = self.max_tokens_input.value()

        pipeline_cfg = config.setdefault("pipeline", {})
        pipeline_cfg["time_window_hours"] = self.time_window_input.value()
        pipeline_cfg["max_articles_per_day"] = self.max_articles_input.value()
        pipeline_cfg["max_articles_to_stage2"] = self.max_stage2_input.value()
        pipeline_cfg["stage1_batch_size"] = self.stage1_batch_input.value()

        github_cfg = config.setdefault("github_trending", {})
        github_cfg["enabled"] = self.github_enabled_input.isChecked()
        github_cfg["min_stars"] = self.github_min_stars_input.value()
        github_cfg["max_projects_per_day"] = self.github_max_projects_input.value()
        return config

    def _save_settings(self) -> None:
        config = self._build_config()
        save_config(config, mode="desktop")
        set_llm_api_key(config, self.llm_api_key_input.text())
        set_github_token(self.github_token_input.text())
        persisted = load_config(mode="desktop")
        self._on_saved(persisted)
        QMessageBox.information(self, "设置", "设置已保存。")

    def _test_settings(self) -> None:
        config = self._build_config()
        errors = []
        if not self.base_url_input.text().strip():
            errors.append("LLM base_url 未配置。")
        if not self.model_input.text().strip():
            errors.append("LLM model 未配置。")
        if not self.llm_api_key_input.text().strip() and not get_llm_api_key(config):
            errors.append("缺少 LLM API Key。")
        if self.github_enabled_input.isChecked() and not self.github_token_input.text().strip() and not get_github_token(config):
            errors.append("GitHub Trending 已启用，但缺少 GitHub Token。")
        if errors:
            QMessageBox.warning(self, "配置检查", "\n".join(errors))
            return
        QMessageBox.information(self, "配置检查", "基础配置检查通过。")

    def _open_data_dir(self) -> None:
        data_dir = get_runtime_paths(mode="desktop").user_data_dir
        data_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_dir)))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._services = create_desktop_services()
        self.setWindowTitle("AI Daily")
        self.resize(1540, 920)
        icon = app_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)
        self._build_ui()

    def _build_ui(self) -> None:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        nav_panel = QFrame()
        nav_panel.setObjectName("navPanel")
        nav_panel.setFixedWidth(200)
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(0, 20, 0, 14)
        nav_layout.setSpacing(4)
        brand = QLabel("AI Daily")
        brand.setStyleSheet(DESKTOP_BRAND_STYLE)
        brand.setContentsMargins(18, 0, 18, 0)
        subtitle = QLabel("温暖的 AI 编辑部")
        subtitle.setStyleSheet(DESKTOP_SUBTITLE_STYLE)
        subtitle.setContentsMargins(18, 0, 18, 0)
        nav_layout.addWidget(brand)
        nav_layout.addWidget(subtitle)
        nav_layout.addSpacing(14)

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navList")
        for label in ("AI 日报", "GitHub 趋势", "设置"):
            self.nav_list.addItem(QListWidgetItem(label))
        self.nav_list.currentRowChanged.connect(self._switch_page)
        nav_layout.addWidget(self.nav_list, 1)
        layout.addWidget(nav_panel, 0)

        self.pages = QStackedWidget()
        self.digest_page = DigestPage(self.services)
        self.github_page = GithubTrendingPage(self.services)
        self.settings_page = SettingsPage(self.services, self._on_settings_saved)
        self.pages.addWidget(self.digest_page)
        self.pages.addWidget(self.github_page)
        self.pages.addWidget(self.settings_page)
        layout.addWidget(self.pages, 1)

        self.setCentralWidget(container)
        self.statusBar().showMessage("桌面版已就绪，默认保持手动刷新。")
        self.nav_list.setCurrentRow(0)

    def services(self) -> ApplicationServices:
        return self._services

    def _switch_page(self, index: int) -> None:
        self.pages.setCurrentIndex(max(0, index))

    def _on_settings_saved(self, config: dict) -> None:
        self._services.replace_config(config)
        self.settings_page.reload()
        self.digest_page.reload()
        self.github_page.reload()
        self.statusBar().showMessage("设置已更新。", 4000)


def launch_desktop_app() -> int:
    os.environ.setdefault("AI_DAILY_DESKTOP_MODE", "1")
    app = QApplication.instance() or QApplication([])
    set_global_style(app)
    icon = app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)
    window = MainWindow()
    window.show()
    return app.exec()


def main() -> int:
    return launch_desktop_app()
