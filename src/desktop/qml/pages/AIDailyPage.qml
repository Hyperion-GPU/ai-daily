import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "../components"

Item {
    id: root

    property var tokens
    property var digestFacade

    readonly property var categoryOptions: [
        { text: "全部", value: "" },
        { text: "ArXiv", value: "arxiv" },
        { text: "新闻", value: "news" },
        { text: "官方", value: "official" },
        { text: "社区", value: "community" }
    ]
    readonly property var sortOptions: [
        { text: "按重要度", value: "importance" },
        { text: "按发布时间", value: "published" }
    ]
    readonly property var selectedArticle: digestFacade ? digestFacade.selectedArticle : ({})
    readonly property var articleTags: selectedArticle && selectedArticle.tags ? selectedArticle.tags : []

    objectName: "aiDailyWorkspace"

    function indexFor(options, value) {
        for (let index = 0; index < options.length; index += 1) {
            if (options[index].value === value) {
                return index
            }
        }
        return 0
    }

    function hasSelectedTag(tag) {
        if (!digestFacade || !digestFacade.selectedTags) {
            return false
        }
        return digestFacade.selectedTags.indexOf(tag) >= 0
    }

    function formatStatusText() {
        if (!digestFacade) {
            return ""
        }
        if (digestFacade.errorMessage.length > 0) {
            return digestFacade.errorMessage
        }
        if (digestFacade.busy && digestFacade.pipelineProgressText.length > 0) {
            return digestFacade.pipelineProgressText
        }
        if (digestFacade.noticeMessage.length > 0) {
            return digestFacade.noticeMessage
        }
        if (digestFacade.stale) {
            return "配置已变化，当前工作区将在刷新后同步。"
        }
        return ""
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: root.tokens ? root.tokens.pagePadding : 32
        spacing: root.tokens ? root.tokens.sectionGap : 20

        RowLayout {
            Layout.fillWidth: true
            spacing: 16

            PageHeader {
                Layout.fillWidth: true
                tokens: root.tokens
                eyebrow: "AI Daily / Digest"
                title: "AI Daily"
                subtitle: "把归档、筛选、阅读与抓取放回同一张安静的编辑式工作台。"
            }

            Button {
                id: reloadButton
                objectName: "aiDailyReloadButton"
                text: "刷新"
                enabled: digestFacade ? !digestFacade.busy : false
                onClicked: if (digestFacade) digestFacade.reload()
            }

            Button {
                id: fetchButton
                objectName: "aiDailyFetchButton"
                text: digestFacade && digestFacade.busy ? "抓取中..." : "抓取日报"
                enabled: digestFacade ? !digestFacade.busy : false
                onClicked: if (digestFacade) digestFacade.runFetch()
            }
        }

        StatusBanner {
            id: statusBanner
            objectName: "aiDailyStatusBanner"
            Layout.fillWidth: true
            tokens: root.tokens
            busy: digestFacade ? digestFacade.busy : false
            tone: digestFacade && digestFacade.errorMessage.length > 0 ? "error" : "neutral"
            text: root.formatStatusText()
        }

        Rectangle {
            id: summaryBar
            objectName: "aiDailySummaryBar"
            Layout.fillWidth: true
            radius: root.tokens ? root.tokens.radiusMedium : 20
            color: root.tokens ? root.tokens.surfaceRaised : "#F7F1E8"
            border.width: 1
            border.color: root.tokens ? root.tokens.borderSubtle : "#D8CCB8"
            implicitHeight: summaryColumn.implicitHeight + 28

            ColumnLayout {
                id: summaryColumn
                anchors.fill: parent
                anchors.margins: 16
                spacing: 14

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    MetricPill {
                        tokens: root.tokens
                        label: "归档"
                        value: digestFacade ? String(digestFacade.archiveCount) : "0"
                    }

                    MetricPill {
                        tokens: root.tokens
                        label: "原始"
                        value: digestFacade ? String(digestFacade.currentDateArticleCount) : "0"
                    }

                    MetricPill {
                        tokens: root.tokens
                        label: "当前"
                        value: digestFacade ? String(digestFacade.filteredArticleCount) : "0"
                    }

                    Item { Layout.fillWidth: true }

                    Button {
                        text: "清空筛选"
                        enabled: digestFacade ? !digestFacade.busy : false
                        onClicked: if (digestFacade) digestFacade.clearFilters()
                    }
                }

                Label {
                    Layout.fillWidth: true
                    text: digestFacade && digestFacade.summaryText.length > 0
                        ? digestFacade.summaryText
                        : "选择归档后，这里会同步当前日期与筛选上下文。"
                    color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                    font.family: root.tokens ? root.tokens.sansFamily : font.family
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 14

                    FilterGroup {
                        Layout.preferredWidth: 180
                        tokens: root.tokens
                        title: "分类"

                        ComboBox {
                            id: categoryCombo
                            Layout.fillWidth: true
                            model: root.categoryOptions
                            textRole: "text"
                            valueRole: "value"
                            onActivated: if (digestFacade) digestFacade.setCategoryFilter(currentValue)
                            Binding {
                                target: categoryCombo
                                property: "currentIndex"
                                value: root.indexFor(root.categoryOptions, digestFacade ? digestFacade.categoryFilter : "")
                            }
                        }
                    }

                    FilterGroup {
                        Layout.preferredWidth: 180
                        tokens: root.tokens
                        title: "重要度"

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Slider {
                                id: importanceSlider
                                Layout.fillWidth: true
                                from: 1
                                to: 5
                                stepSize: 1
                                snapMode: Slider.SnapAlways
                                onMoved: if (digestFacade) digestFacade.setMinImportance(Math.round(value))
                                Binding {
                                    target: importanceSlider
                                    property: "value"
                                    value: digestFacade ? digestFacade.minImportance : 1
                                    when: !importanceSlider.pressed
                                }
                            }

                            Label {
                                text: digestFacade ? String(digestFacade.minImportance) + "/5" : "1/5"
                                color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                                font.family: root.tokens ? root.tokens.sansFamily : font.family
                                font.pixelSize: 12
                            }
                        }
                    }

                    FilterGroup {
                        Layout.preferredWidth: 160
                        tokens: root.tokens
                        title: "排序"

                        ComboBox {
                            id: sortCombo
                            Layout.fillWidth: true
                            model: root.sortOptions
                            textRole: "text"
                            valueRole: "value"
                            onActivated: if (digestFacade) digestFacade.setSortKey(currentValue)
                            Binding {
                                target: sortCombo
                                property: "currentIndex"
                                value: root.indexFor(root.sortOptions, digestFacade ? digestFacade.sortKey : "importance")
                            }
                        }
                    }

                    FilterGroup {
                        Layout.fillWidth: true
                        tokens: root.tokens
                        title: "搜索"

                        TextField {
                            id: searchField
                            Layout.fillWidth: true
                            placeholderText: "搜索标题或摘要"
                            onTextEdited: if (digestFacade) digestFacade.setSearchQuery(text)
                            Binding {
                                target: searchField
                                property: "text"
                                value: digestFacade ? digestFacade.searchQuery : ""
                                when: !searchField.activeFocus
                            }
                        }
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8

                    Label {
                        text: "标签"
                        color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                        font.family: root.tokens ? root.tokens.sansFamily : font.family
                        font.pixelSize: 12
                    }

                    Item {
                        id: tagFlowHolder
                        objectName: "aiDailyTagFlow"
                        Layout.fillWidth: true
                        implicitHeight: Math.max(tagFlow.implicitHeight, 34)

                        Flow {
                            id: tagFlow
                            width: parent.width
                            spacing: 8

                            Repeater {
                                model: digestFacade ? digestFacade.availableTags : []

                                TagChip {
                                    required property var modelData

                                    readonly property string tagValue: String(modelData.value || modelData)

                                    tokens: root.tokens
                                    label: String(modelData.label || modelData.value || modelData)
                                    selected: root.hasSelectedTag(tagValue)
                                    onClicked: if (digestFacade) digestFacade.toggleTagSelection(tagValue)
                                }
                            }

                            Label {
                                visible: digestFacade && digestFacade.availableTags.length === 0
                                text: "当前归档暂无可用标签。"
                                color: root.tokens ? root.tokens.inkSoft : "#998C7C"
                                font.family: root.tokens ? root.tokens.sansFamily : font.family
                                font.pixelSize: 12
                            }
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 16

            SectionCard {
                Layout.preferredWidth: 260
                Layout.fillHeight: true
                tokens: root.tokens
                heading: "归档"
                supportingText: "按日期回看已经落盘的日报。"

                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    ListView {
                        id: archiveList
                        objectName: "aiDailyArchiveList"
                        anchors.fill: parent
                        model: digestFacade ? digestFacade.archiveModel : null
                        spacing: 8
                        clip: true

                        delegate: ArchiveListDelegate {
                            width: ListView.view.width
                            tokens: root.tokens
                            date: model.date
                            label: model.label
                            articleCount: model.articleCount
                            isLatest: model.isLatest
                            isSelected: model.isSelected
                            onClicked: if (digestFacade) digestFacade.selectArchiveRow(index)
                        }
                    }

                    Label {
                        anchors.centerIn: parent
                        visible: archiveList.count === 0
                        text: "暂无日报归档。"
                        color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                        font.family: root.tokens ? root.tokens.sansFamily : font.family
                    }
                }
            }

            SectionCard {
                Layout.fillWidth: true
                Layout.fillHeight: true
                tokens: root.tokens
                heading: "文章列表"
                supportingText: "让列表承担筛选与浏览，让右侧承担阅读与判断。"

                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    ListView {
                        id: articleList
                        objectName: "aiDailyArticleList"
                        anchors.fill: parent
                        model: digestFacade ? digestFacade.articleModel : null
                        spacing: 10
                        clip: true

                        delegate: ArticleListDelegate {
                            width: ListView.view.width
                            tokens: root.tokens
                            title: model.title
                            sourceName: model.sourceName
                            sourceCategoryLabel: model.sourceCategoryLabel
                            publishedLabel: model.publishedLabel
                            summaryZh: model.summaryZh
                            importance: model.importance
                            tags: model.tags
                            isSelected: model.isSelected
                            onClicked: if (digestFacade) digestFacade.selectArticleRow(index)
                        }
                    }

                    Label {
                        anchors.centerIn: parent
                        visible: articleList.count === 0
                        text: digestFacade && digestFacade.currentDate.length > 0
                            ? "当前筛选下没有结果。"
                            : "选择一个归档日期后开始阅读。"
                        color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                        font.family: root.tokens ? root.tokens.sansFamily : font.family
                    }
                }
            }

            SectionCard {
                Layout.preferredWidth: 390
                Layout.fillHeight: true
                tokens: root.tokens
                heading: "阅读面"
                supportingText: "先读摘要，再决定是否打开原文继续追踪。"

                ScrollView {
                    objectName: "aiDailyDetailPanel"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true

                    ColumnLayout {
                        width: parent.width
                        spacing: 14

                        Label {
                            Layout.fillWidth: true
                            text: digestFacade && digestFacade.hasSelection
                                ? String(root.selectedArticle.title || "未命名文章")
                                : (digestFacade && digestFacade.currentDate.length > 0
                                    ? "请选择一篇文章"
                                    : "暂无日报归档")
                            color: root.tokens ? root.tokens.inkStrong : "#2E261D"
                            font.family: root.tokens ? root.tokens.serifFamily : font.family
                            font.pixelSize: 24
                            font.weight: Font.DemiBold
                            wrapMode: Text.WordWrap
                        }

                        Label {
                            Layout.fillWidth: true
                            text: digestFacade && digestFacade.hasSelection
                                ? [String(root.selectedArticle.sourceName || ""), String(root.selectedArticle.publishedLabel || "")]
                                    .filter(Boolean)
                                    .join(" · ")
                                : (digestFacade && digestFacade.currentDate.length > 0
                                    ? "右侧阅读面会跟随列表选中项更新。"
                                    : "抓取一次日报后，这里会形成可检索的阅读归档。")
                            color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                            font.family: root.tokens ? root.tokens.sansFamily : font.family
                            font.pixelSize: 13
                            wrapMode: Text.WordWrap
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            MetricPill {
                                tokens: root.tokens
                                label: "分类"
                                value: digestFacade && digestFacade.hasSelection
                                    ? String(root.selectedArticle.sourceCategoryLabel || "未分类")
                                    : "-"
                            }

                            MetricPill {
                                tokens: root.tokens
                                label: "重要度"
                                value: digestFacade && digestFacade.hasSelection
                                    ? String(root.selectedArticle.importance || 0) + "/5"
                                    : "-"
                            }
                        }

                        DetailField {
                            tokens: root.tokens
                            label: "来源"
                            value: digestFacade && digestFacade.hasSelection
                                ? String(root.selectedArticle.sourceName || "")
                                : ""
                        }

                        DetailField {
                            tokens: root.tokens
                            label: "发布时间"
                            value: digestFacade && digestFacade.hasSelection
                                ? String(root.selectedArticle.publishedLabel || "")
                                : ""
                        }

                        DetailField {
                            tokens: root.tokens
                            label: "分类"
                            value: digestFacade && digestFacade.hasSelection
                                ? String(root.selectedArticle.sourceCategoryLabel || "")
                                : ""
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Label {
                                text: "标签"
                                color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                                font.family: root.tokens ? root.tokens.sansFamily : font.family
                                font.pixelSize: 12
                            }

                            Flow {
                                Layout.fillWidth: true
                                width: parent.width
                                spacing: 8

                                Repeater {
                                    model: root.articleTags

                                    TagChip {
                                        required property var modelData

                                        tokens: root.tokens
                                        label: String(modelData)
                                        interactive: false
                                        muted: true
                                    }
                                }

                                Label {
                                    visible: digestFacade ? digestFacade.hasSelection && root.articleTags.length === 0 : true
                                    text: digestFacade && digestFacade.hasSelection ? "暂无标签。" : "未选择文章。"
                                    color: root.tokens ? root.tokens.inkSoft : "#998C7C"
                                    font.family: root.tokens ? root.tokens.sansFamily : font.family
                                    font.pixelSize: 12
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            radius: root.tokens ? root.tokens.controlRadius : 14
                            color: root.tokens ? root.tokens.surfaceBase : "#FBF8F2"
                            border.width: 1
                            border.color: root.tokens ? root.tokens.borderSubtle : "#D8CCB8"
                            implicitHeight: summaryLabel.implicitHeight + 24

                            Label {
                                id: summaryLabel
                                anchors.fill: parent
                                anchors.margins: 12
                                text: digestFacade && digestFacade.hasSelection
                                    ? String(root.selectedArticle.summaryZh || "暂无中文摘要。")
                                    : (digestFacade && digestFacade.currentDate.length > 0
                                        ? "当前没有可展示的摘要内容。"
                                        : "抓取并选择文章后，这里会展示中文摘要。")
                                color: root.tokens ? root.tokens.inkStrong : "#2E261D"
                                font.family: root.tokens ? root.tokens.sansFamily : font.family
                                font.pixelSize: 14
                                wrapMode: Text.WordWrap
                            }
                        }

                        Label {
                            Layout.fillWidth: true
                            text: "先浏览摘要，再决定是否打开原文继续阅读。"
                            color: root.tokens ? root.tokens.inkSoft : "#998C7C"
                            font.family: root.tokens ? root.tokens.sansFamily : font.family
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                Button {
                    id: openArticleButton
                    objectName: "aiDailyOpenArticleButton"
                    Layout.alignment: Qt.AlignLeft
                    text: "打开原文"
                    enabled: digestFacade
                        ? digestFacade.hasSelection && String(root.selectedArticle.url || "").length > 0
                        : false
                    onClicked: if (digestFacade) digestFacade.openSelectedArticle()
                }
            }
        }
    }
}
