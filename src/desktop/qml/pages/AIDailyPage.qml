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

    function statusText() {
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
            return "筛选条件已改变，刷新后会同步最新的阅读结果。"
        }
        return ""
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: root.tokens ? root.tokens.pagePadding : 30
        spacing: root.tokens ? root.tokens.sectionGap : 16

        RowLayout {
            Layout.fillWidth: true
            spacing: 16

            PageHeader {
                Layout.fillWidth: true
                tokens: root.tokens
                eyebrow: "AI DAILY / DIGEST"
                title: "AI 日报"
                subtitle: "筛选、浏览每天的 AI 线索，把信息整合在一个安静且可控的阅读桌面上。"
            }

            TextField {
                id: searchField
                Layout.preferredWidth: 210
                placeholderText: "搜索文章/项目…"
                selectByMouse: true
                onTextEdited: if (digestFacade) digestFacade.setSearchQuery(text)
                Binding {
                    target: searchField
                    property: "text"
                    value: digestFacade ? digestFacade.searchQuery : ""
                    when: !searchField.activeFocus
                }
                background: Rectangle {
                    radius: root.tokens ? root.tokens.controlRadius : 10
                    color: root.tokens ? root.tokens.surfaceBase : "#FBF8F3"
                    border.width: 1
                    border.color: root.tokens ? root.tokens.borderSubtle : "#E1D7CA"
                }
            }

            Button {
                id: reloadButton
                objectName: "aiDailyReloadButton"
                text: "刷新"
                enabled: digestFacade ? !digestFacade.busy : false
                onClicked: if (digestFacade) digestFacade.reload()
                contentItem: Label {
                    text: reloadButton.text
                    color: root.tokens ? root.tokens.inkStrong : "#2E261D"
                    font.family: root.tokens ? root.tokens.sansFamily : font.family
                    font.pixelSize: 12
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: root.tokens ? root.tokens.controlRadius : 10
                    color: root.tokens ? root.tokens.surfaceBase : "#FBF8F3"
                    border.width: 1
                    border.color: root.tokens ? root.tokens.borderSubtle : "#E1D7CA"
                }
            }

            Button {
                id: fetchButton
                objectName: "aiDailyFetchButton"
                text: digestFacade && digestFacade.busy ? "抓取中…" : "更新今日日报"
                enabled: digestFacade ? !digestFacade.busy : false
                onClicked: if (digestFacade) digestFacade.runFetch()
                contentItem: Label {
                    text: fetchButton.text
                    color: "white"
                    font.family: root.tokens ? root.tokens.sansFamily : font.family
                    font.pixelSize: 12
                    font.weight: Font.Medium
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: root.tokens ? root.tokens.controlRadius : 10
                    color: root.tokens ? root.tokens.accentFill : "#B9916E"
                }
            }
        }

        StatusBanner {
            id: statusBanner
            objectName: "aiDailyStatusBanner"
            Layout.fillWidth: true
            tokens: root.tokens
            busy: digestFacade ? digestFacade.busy : false
            progressValue: digestFacade ? digestFacade.pipelineProgressValue : -1
            progressBarObjectName: "aiDailyProgressBar"
            tone: digestFacade && digestFacade.errorMessage.length > 0 ? "error" : "neutral"
            text: root.statusText()
        }

        Rectangle {
            Layout.fillWidth: true
            color: "transparent"
            implicitHeight: summaryRow.implicitHeight + 18

            ColumnLayout {
                anchors.fill: parent
                spacing: 10

                RowLayout {
                    id: summaryRow
                    Layout.fillWidth: true
                    spacing: 18

                    Label {
                        text: digestFacade && digestFacade.currentDate.length > 0
                            ? digestFacade.currentDate
                            : "尚未选择归档"
                        color: root.tokens ? root.tokens.inkStrong : "#2E261D"
                        font.family: root.tokens ? root.tokens.sansFamily : font.family
                        font.pixelSize: 13
                        font.weight: Font.Medium
                    }

                    Rectangle {
                        Layout.preferredWidth: 1
                        Layout.preferredHeight: 15
                        color: root.tokens ? root.tokens.borderSubtle : "#E1D7CA"
                    }

                    MetricPill {
                        tokens: root.tokens
                        label: "收录文章"
                        value: digestFacade ? String(digestFacade.archiveCount) : "0"
                    }

                    MetricPill {
                        tokens: root.tokens
                        label: "今日新增"
                        value: digestFacade ? String(digestFacade.currentDateArticleCount) : "0"
                    }

                    MetricPill {
                        tokens: root.tokens
                        label: "当前筛选"
                        value: digestFacade ? String(digestFacade.filteredArticleCount) : "0"
                    }

                    Item { Layout.fillWidth: true }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: Qt.rgba(225 / 255, 215 / 255, 202 / 255, 0.7)
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            color: "transparent"
            implicitHeight: filterColumn.implicitHeight + 10

            ColumnLayout {
                id: filterColumn
                anchors.fill: parent
                spacing: 10

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Flow {
                        Layout.fillWidth: true
                        width: parent.width
                        spacing: 6

                        Repeater {
                            model: root.categoryOptions

                            TagChip {
                                required property var modelData

                                tokens: root.tokens
                                label: modelData.text
                                selected: digestFacade ? digestFacade.categoryFilter === modelData.value : modelData.value === ""
                                onClicked: if (digestFacade) digestFacade.setCategoryFilter(modelData.value)
                            }
                        }
                    }

                    Button {
                        id: clearFiltersButton
                        text: "清空筛选"
                        enabled: digestFacade ? !digestFacade.busy : false
                        onClicked: if (digestFacade) digestFacade.clearFilters()
                        contentItem: Label {
                            text: clearFiltersButton.text
                            color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                            font.family: root.tokens ? root.tokens.sansFamily : font.family
                            font.pixelSize: 11
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle {
                            radius: root.tokens ? root.tokens.controlRadius : 10
                            color: root.tokens ? root.tokens.surfaceBase : "#FBF8F3"
                            border.width: 1
                            border.color: root.tokens ? root.tokens.borderSubtle : "#E1D7CA"
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 14

                    Flow {
                        id: tagFlow
                        Layout.fillWidth: true
                        width: parent.width
                        spacing: 6

                        Repeater {
                            model: digestFacade ? digestFacade.availableTags : []

                            TagChip {
                                required property var modelData

                                readonly property string tagValue: String(modelData.value || modelData)

                                tokens: root.tokens
                                label: String(modelData.label || modelData.value || modelData)
                                selected: root.hasSelectedTag(tagValue)
                                muted: !root.hasSelectedTag(tagValue)
                                onClicked: if (digestFacade) digestFacade.toggleTagSelection(tagValue)
                            }
                        }
                    }

                    Label {
                        text: "重要度 ≥"
                        color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                        font.family: root.tokens ? root.tokens.sansFamily : font.family
                        font.pixelSize: 11
                    }

                    Slider {
                        id: importanceSlider
                        Layout.preferredWidth: 90
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
                        text: digestFacade ? String(digestFacade.minImportance) : "1"
                        color: root.tokens ? root.tokens.inkStrong : "#2E261D"
                        font.family: root.tokens ? root.tokens.sansFamily : font.family
                        font.pixelSize: 12
                    }

                    ComboBox {
                        id: sortCombo
                        Layout.preferredWidth: 116
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

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: Qt.rgba(225 / 255, 215 / 255, 202 / 255, 0.7)
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 16

            SectionCard {
                Layout.preferredWidth: 188
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

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: root.tokens ? root.tokens.panelRadius : 16
                color: root.tokens ? root.tokens.surfaceBase : "#FBF8F3"
                border.width: 1
                border.color: root.tokens ? root.tokens.borderSubtle : "#E1D7CA"

                RowLayout {
                    anchors.fill: parent
                    spacing: 0

                    Item {
                        Layout.preferredWidth: 430
                        Layout.fillHeight: true

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 0
                            spacing: 0

                            Label {
                                Layout.fillWidth: true
                                leftPadding: 24
                                rightPadding: 24
                                topPadding: 18
                                bottomPadding: 12
                                text: "阅读清单 · " + (digestFacade ? String(digestFacade.articleModel.count) : "0") + " 篇"
                                color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                                font.family: root.tokens ? root.tokens.sansFamily : font.family
                                font.pixelSize: 11
                                font.letterSpacing: 0.3
                            }

                            ListView {
                                id: articleList
                                objectName: "aiDailyArticleList"
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                Layout.leftMargin: 14
                                Layout.rightMargin: 14
                                Layout.bottomMargin: 14
                                model: digestFacade ? digestFacade.articleModel : null
                                spacing: 0
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

                    Rectangle {
                        Layout.preferredWidth: 1
                        Layout.fillHeight: true
                        color: Qt.rgba(225 / 255, 215 / 255, 202 / 255, 0.7)
                    }

                    ScrollView {
                        id: aiDetailScroll
                        objectName: "aiDailyDetailPanel"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        contentWidth: availableWidth
                        contentHeight: detailColumn.y + detailColumn.implicitHeight + 30
                        clip: true

                        ColumnLayout {
                            id: detailColumn
                            objectName: "aiDailyDetailColumn"
                            width: Math.max(Math.min(aiDetailScroll.availableWidth - 64, 680), 280)
                            x: Math.max((aiDetailScroll.availableWidth - width) / 2, 32)
                            y: 30
                            spacing: 16

                            Label {
                                Layout.fillWidth: true
                                text: digestFacade && digestFacade.hasSelection
                                    ? [String(root.selectedArticle.sourceName || ""),
                                       String(root.selectedArticle.publishedLabel || "")]
                                          .filter(Boolean)
                                          .join(" / ")
                                    : "尚未选择文章"
                                color: Qt.rgba(110 / 255, 101 / 255, 92 / 255, 0.7)
                                font.family: root.tokens ? root.tokens.sansFamily : font.family
                                font.pixelSize: 11
                                font.capitalization: Font.AllUppercase
                                font.letterSpacing: 0.3
                            }

                            Label {
                                Layout.fillWidth: true
                                text: digestFacade && digestFacade.hasSelection
                                    ? String(root.selectedArticle.title || "未命名文章")
                                    : "请选择一篇文章"
                                color: root.tokens ? root.tokens.inkStrong : "#2E261D"
                                font.family: root.tokens ? root.tokens.serifFamily : font.family
                                font.pixelSize: 22
                                font.weight: Font.Medium
                                wrapMode: Text.WordWrap
                            }

                            DetailField {
                                Layout.fillWidth: true
                                tokens: root.tokens
                                label: "Source"
                                value: digestFacade && digestFacade.hasSelection ? String(root.selectedArticle.sourceName || "") : ""
                            }

                            DetailField {
                                Layout.fillWidth: true
                                tokens: root.tokens
                                label: "Link"
                                value: digestFacade && digestFacade.hasSelection ? String(root.selectedArticle.url || "") : ""
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 12

                                DetailField {
                                    Layout.fillWidth: true
                                    tokens: root.tokens
                                    label: "Topics"
                                    value: digestFacade && digestFacade.hasSelection
                                        ? String(root.selectedArticle.sourceCategoryLabel || "未分类")
                                        : ""
                                }

                                ColumnLayout {
                                    spacing: 4

                                    Label {
                                        text: "Importance"
                                        color: root.tokens ? root.tokens.inkSoft : "#998C7C"
                                        font.family: root.tokens ? root.tokens.sansFamily : font.family
                                        font.pixelSize: 10
                                        font.letterSpacing: 0.4
                                    }

                                    RowLayout {
                                        spacing: 6

                                        Repeater {
                                            model: 5

                                            Rectangle {
                                                required property int index

                                                Layout.preferredWidth: 5
                                                Layout.preferredHeight: 5
                                                radius: 3
                                                color: index < (digestFacade && digestFacade.hasSelection ? Number(root.selectedArticle.importance || 0) : 0)
                                                    ? (root.tokens ? root.tokens.accentFill : "#B9916E")
                                                    : (root.tokens ? root.tokens.borderSubtle : "#E1D7CA")
                                            }
                                        }

                                        Label {
                                            text: digestFacade && digestFacade.hasSelection
                                                ? String(root.selectedArticle.importance || 0) + "/5"
                                                : "-"
                                            color: root.tokens ? root.tokens.inkStrong : "#2E261D"
                                            font.family: root.tokens ? root.tokens.sansFamily : font.family
                                            font.pixelSize: 12
                                        }
                                    }
                                }
                            }

                            Flow {
                                Layout.fillWidth: true
                                width: parent.width
                                spacing: 6

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
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 1
                                color: root.tokens ? root.tokens.borderSubtle : "#E1D7CA"
                            }

                            Label {
                                Layout.fillWidth: true
                                text: digestFacade && digestFacade.hasSelection
                                    ? String(root.selectedArticle.summaryZh || "暂无中文摘要。")
                                    : "抓取并选择文章后，这里会显示摘要正文。"
                                color: root.tokens ? root.tokens.inkStrong : "#2E261D"
                                font.family: root.tokens ? root.tokens.sansFamily : font.family
                                font.pixelSize: 14
                                lineHeight: 1.85
                                wrapMode: Text.WordWrap
                            }

                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 1
                                color: root.tokens ? root.tokens.borderSubtle : "#E1D7CA"
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 10

                                Button {
                                    id: openArticleButton
                                    objectName: "aiDailyOpenArticleButton"
                                    text: "阅读全文"
                                    enabled: digestFacade
                                        ? digestFacade.hasSelection && String(root.selectedArticle.url || "").length > 0
                                        : false
                                    onClicked: if (digestFacade) digestFacade.openSelectedArticle()
                                    contentItem: Label {
                                        text: openArticleButton.text
                                        color: root.tokens ? root.tokens.inkStrong : "#2E261D"
                                        font.family: root.tokens ? root.tokens.sansFamily : font.family
                                        font.pixelSize: 12
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                    background: Rectangle {
                                        radius: root.tokens ? root.tokens.controlRadius : 10
                                        color: root.tokens ? root.tokens.surfaceBase : "#FBF8F3"
                                        border.width: 1
                                        border.color: root.tokens ? root.tokens.borderSubtle : "#E1D7CA"
                                    }
                                }

                                Item {
                                    Layout.fillWidth: true
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
