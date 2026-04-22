import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "../components"

Item {
    id: root

    property var tokens
    property QtObject githubFacade

    readonly property var categoryOptions: [
        { text: "全部", value: "" },
        { text: "LLM", value: "llm" },
        { text: "Agent", value: "agent" },
        { text: "CV", value: "cv" },
        { text: "NLP", value: "nlp" },
        { text: "Framework", value: "ml_framework" },
        { text: "MLOps", value: "mlops" },
        { text: "General", value: "general" }
    ]
    readonly property var sortOptions: [
        { text: "按 Stars", value: "stars" },
        { text: "按今日增量", value: "stars_today" },
        { text: "按周增量", value: "stars_weekly" },
        { text: "按最近更新", value: "updated" }
    ]
    readonly property var trendOptions: [
        { text: "全部", value: "" },
        { text: "Hot", value: "hot" },
        { text: "Rising", value: "rising" },
        { text: "Stable", value: "stable" }
    ]
    readonly property var languageOptions: [{ label: "全部", value: "", count: 0 }].concat(
        githubFacade ? githubFacade.availableLanguages : []
    )
    readonly property var selectedProject: githubFacade ? githubFacade.projectModel.selectedItem : ({})
    readonly property bool compactWorkbench: root.width < 1660
    readonly property bool narrowWorkbench: root.width < 1460
    readonly property bool shortWorkbench: root.height < 940
    readonly property int railWidth: root.narrowWorkbench ? 188 : (root.compactWorkbench ? 202 : 220)
    readonly property int detailWidth: root.narrowWorkbench ? 296 : (root.compactWorkbench ? 316 : 338)
    readonly property int detailMinWidth: root.narrowWorkbench ? 276 : (root.compactWorkbench ? 292 : 320)
    readonly property int projectPreferredWidth: root.narrowWorkbench ? 500 : (root.compactWorkbench ? 540 : 580)
    readonly property int projectMinWidth: root.narrowWorkbench ? 340 : (root.compactWorkbench ? 380 : 420)
    readonly property int searchWidth: root.narrowWorkbench ? 184 : (root.compactWorkbench ? 200 : 220)
    readonly property int controlHeight: root.narrowWorkbench ? 34 : 38
    readonly property int actionHeight: root.narrowWorkbench ? 32 : 36
    readonly property int archiveCardHeight: root.shortWorkbench ? (root.narrowWorkbench ? 216 : 236) : 282

    objectName: "githubWorkspace"

    function indexFor(options, value) {
        for (let index = 0; index < options.length; index += 1) {
            if (options[index].value === value) {
                return index
            }
        }
        return 0
    }

    function selectedLanguageValue() {
        if (!githubFacade || githubFacade.selectedLanguages.length === 0) {
            return ""
        }
        return githubFacade.selectedLanguages[0]
    }

    function statusText() {
        if (!githubFacade) {
            return ""
        }
        if (githubFacade.errorMessage.length > 0) {
            return githubFacade.errorMessage
        }
        if (githubFacade.noticeMessage.length > 0) {
            return githubFacade.noticeMessage
        }
        if (githubFacade.stale) {
            return "筛选条件已变更，应用筛选后会刷新仓库列表。"
        }
        return ""
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: root.tokens ? root.tokens.pagePadding : 32
        spacing: root.tokens ? root.tokens.sectionGap : 18

        RowLayout {
            Layout.fillWidth: true
            spacing: 16

            PageHeader {
                Layout.fillWidth: true
                tokens: root.tokens
                eyebrow: "AI DAILY / GITHUB TRENDS"
                title: "GitHub 趋势"
                subtitle: "切换每日快照，在同一张安静的编辑工作台上完成筛选、阅读与仓库细看。"
            }

            RowLayout {
                spacing: 10

                TextField {
                    id: searchField
                    Layout.preferredWidth: root.searchWidth
                    placeholderText: "搜索仓库/摘要..."
                    selectByMouse: true
                    onTextEdited: if (githubFacade) githubFacade.setSearchQuery(text)
                    Binding {
                        target: searchField
                        property: "text"
                        value: githubFacade ? githubFacade.searchQuery : ""
                        when: !searchField.activeFocus
                    }
                    background: Rectangle {
                        radius: root.tokens ? root.tokens.controlRadius : 12
                        color: root.tokens ? root.tokens.surfaceBase : "#FBF8F3"
                        border.width: 1
                        border.color: root.tokens ? root.tokens.borderSubtle : "#E1D7CA"
                    }
                }

                Button {
                    id: fetchButton
                    objectName: "githubFetchButton"
                    text: githubFacade && githubFacade.busy ? "获取中..." : "获取最新快照"
                    enabled: githubFacade ? !githubFacade.busy : false
                    onClicked: if (githubFacade) githubFacade.runFetch()
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
                        radius: root.tokens ? root.tokens.controlRadius : 12
                        color: root.tokens ? root.tokens.accentFill : "#B9916E"
                    }
                }
            }
        }

        StatusBanner {
            id: statusBanner
            objectName: "githubStatusBanner"
            Layout.fillWidth: true
            tokens: root.tokens
            busy: githubFacade ? githubFacade.busy : false
            progressValue: githubFacade ? githubFacade.fetchProgressValue : -1
            progressBarObjectName: "githubProgressBar"
            tone: githubFacade ? githubFacade.statusTone : "neutral"
            text: root.statusText()
        }

        Item {
            objectName: "githubAutomationProbeHost"
            Layout.preferredWidth: 1
            Layout.preferredHeight: 1
            Layout.minimumHeight: 1
            Layout.maximumHeight: 1
            opacity: 0.01
            clip: true

            Label {
                objectName: "githubFetchOutcomeProbe"
                text: githubFacade ? githubFacade.lastFetchOutcome : ""
                font.pixelSize: 1
            }

            Label {
                objectName: "githubStatusToneProbe"
                text: githubFacade ? githubFacade.statusTone : ""
                font.pixelSize: 1
                y: 1
            }
        }

        Rectangle {
            Layout.fillWidth: true
            color: "transparent"
            implicitHeight: summaryColumn.implicitHeight

            ColumnLayout {
                id: summaryColumn
                anchors.fill: parent
                spacing: 10

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 18

                    Label {
                        text: githubFacade && githubFacade.currentDate.length > 0
                            ? githubFacade.currentDate
                            : "尚未选择快照"
                        color: root.tokens ? root.tokens.inkStrong : "#2E261D"
                        font.family: root.tokens ? root.tokens.sansFamily : font.family
                        font.pixelSize: 13
                        font.weight: Font.Medium
                    }

                    Rectangle {
                        Layout.preferredWidth: 1
                        Layout.preferredHeight: 16
                        color: root.tokens ? root.tokens.borderSubtle : "#E1D7CA"
                    }

                    MetricPill {
                        tokens: root.tokens
                        label: "快照"
                        value: githubFacade ? String(githubFacade.snapshotModel.count) : "0"
                    }

                    MetricPill {
                        tokens: root.tokens
                        label: "仓库"
                        value: githubFacade ? String(githubFacade.projectModel.count) : "0"
                    }

                    MetricPill {
                        tokens: root.tokens
                        label: "状态"
                        value: githubFacade && githubFacade.stale ? "待刷新" : "已同步"
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

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: root.narrowWorkbench ? 12 : 16

            ColumnLayout {
                Layout.minimumWidth: root.railWidth
                Layout.preferredWidth: root.railWidth
                Layout.maximumWidth: root.railWidth
                Layout.fillHeight: true
                spacing: 12

                SectionCard {
                    Layout.fillWidth: true
                    Layout.preferredHeight: root.archiveCardHeight
                    tokens: root.tokens
                    heading: "快照归档"
                    supportingText: "按日期切换正式快照。"

                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        ListView {
                            id: snapshotList
                            objectName: "githubSnapshotList"
                            anchors.fill: parent
                            model: githubFacade ? githubFacade.snapshotModel : null
                            spacing: 8
                            clip: true

                            delegate: SnapshotListDelegate {
                                width: ListView.view.width
                                tokens: root.tokens
                                date: model.date
                                label: model.label
                                isSelected: model.isSelected
                                isLatest: model.isLatest
                                projectCount: model.projectCount
                                generatedAt: model.generatedAt || ""
                                onClicked: if (githubFacade) githubFacade.selectSnapshotRow(index)
                            }
                        }

                        Label {
                            anchors.centerIn: parent
                            visible: snapshotList.count === 0
                            text: "暂无 GitHub 快照。"
                            color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                            font.family: root.tokens ? root.tokens.sansFamily : font.family
                        }
                    }
                }

                SectionCard {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    tokens: root.tokens
                    heading: "筛选"
                    supportingText: "把过滤条件收敛到侧栏中，减少对正文空间的占用。"

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 10

                        ScrollView {
                            id: filterScroll
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            contentWidth: availableWidth
                            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                            ColumnLayout {
                                width: filterScroll.availableWidth
                                spacing: 10

                                FilterGroup {
                                    Layout.fillWidth: true
                                    tokens: root.tokens
                                    title: "分类"

                                    ComboBox {
                                        id: categoryCombo
                                        Layout.fillWidth: true
                                        implicitHeight: root.controlHeight
                                        model: root.categoryOptions
                                        textRole: "text"
                                        valueRole: "value"
                                        onActivated: if (githubFacade) githubFacade.setCategoryFilter(currentValue)
                                        Binding {
                                            target: categoryCombo
                                            property: "currentIndex"
                                            value: root.indexFor(root.categoryOptions, githubFacade ? githubFacade.categoryFilter : "")
                                        }
                                    }
                                }

                                FilterGroup {
                                    Layout.fillWidth: true
                                    tokens: root.tokens
                                    title: "语言"

                                    ComboBox {
                                        id: languageCombo
                                        Layout.fillWidth: true
                                        implicitHeight: root.controlHeight
                                        model: root.languageOptions
                                        textRole: "label"
                                        valueRole: "value"
                                        onActivated: {
                                            if (githubFacade) {
                                                githubFacade.setSelectedLanguages(currentValue.length > 0 ? [currentValue] : [])
                                            }
                                        }
                                        Binding {
                                            target: languageCombo
                                            property: "currentIndex"
                                            value: root.indexFor(root.languageOptions, root.selectedLanguageValue())
                                        }
                                    }
                                }

                                FilterGroup {
                                    Layout.fillWidth: true
                                    tokens: root.tokens
                                    title: "趋势"

                                    ComboBox {
                                        id: trendCombo
                                        Layout.fillWidth: true
                                        implicitHeight: root.controlHeight
                                        model: root.trendOptions
                                        textRole: "text"
                                        valueRole: "value"
                                        onActivated: if (githubFacade) githubFacade.setTrendFilter(currentValue)
                                        Binding {
                                            target: trendCombo
                                            property: "currentIndex"
                                            value: root.indexFor(root.trendOptions, githubFacade ? githubFacade.trendFilter : "")
                                        }
                                    }
                                }

                                FilterGroup {
                                    Layout.fillWidth: true
                                    tokens: root.tokens
                                    title: "最小 Stars"

                                    SpinBox {
                                        id: minStarsSpin
                                        Layout.fillWidth: true
                                        implicitHeight: root.controlHeight
                                        from: 0
                                        to: 1000000
                                        editable: true
                                        onValueModified: if (githubFacade) githubFacade.setMinStars(value)
                                        Binding {
                                            target: minStarsSpin
                                            property: "value"
                                            value: githubFacade ? githubFacade.minStars : 0
                                            when: !minStarsSpin.activeFocus
                                        }
                                    }
                                }

                                FilterGroup {
                                    Layout.fillWidth: true
                                    tokens: root.tokens
                                    title: "排序"

                                    ComboBox {
                                        id: sortCombo
                                        Layout.fillWidth: true
                                        implicitHeight: root.controlHeight
                                        model: root.sortOptions
                                        textRole: "text"
                                        valueRole: "value"
                                        onActivated: if (githubFacade) githubFacade.setSortKey(currentValue)
                                        Binding {
                                            target: sortCombo
                                            property: "currentIndex"
                                            value: root.indexFor(root.sortOptions, githubFacade ? githubFacade.sortKey : "stars")
                                        }
                                    }
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            Button {
                                id: applyFiltersButton
                                objectName: "githubApplyFiltersButton"
                                Layout.fillWidth: true
                                Layout.preferredHeight: root.actionHeight
                                text: "应用"
                                font.pixelSize: 12
                                enabled: githubFacade ? !githubFacade.busy : false
                                onClicked: if (githubFacade) githubFacade.reload()
                            }

                            Button {
                                id: clearFiltersButton
                                objectName: "githubClearFiltersButton"
                                Layout.fillWidth: true
                                Layout.preferredHeight: root.actionHeight
                                text: "清空"
                                font.pixelSize: 12
                                enabled: githubFacade ? !githubFacade.busy : false
                                onClicked: if (githubFacade) githubFacade.clearFilters()
                            }
                        }
                    }
                }
            }

            SectionCard {
                Layout.fillWidth: true
                Layout.minimumWidth: root.projectMinWidth
                Layout.preferredWidth: root.projectPreferredWidth
                Layout.fillHeight: true
                tokens: root.tokens
                heading: "项目列表"
                supportingText: "保持筛选后的仓库阅读感与浏览节奏。"

                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    ListView {
                        id: projectList
                        objectName: "githubProjectList"
                        anchors.fill: parent
                        model: githubFacade ? githubFacade.projectModel : null
                        spacing: 10
                        clip: true

                        delegate: ProjectListDelegate {
                            width: ListView.view.width
                            tokens: root.tokens
                            fullName: model.fullName
                            description: model.descriptionZh.length > 0 ? model.descriptionZh : model.description
                            language: model.language
                            category: model.category
                            trend: model.trend
                            stars: model.stars
                            starsToday: model.starsToday
                            starsWeekly: model.starsWeekly
                            updatedAt: model.updatedAt
                            isSelected: model.isSelected
                            onClicked: if (githubFacade) githubFacade.selectProjectRow(index)
                        }
                    }

                    Label {
                        anchors.centerIn: parent
                        visible: projectList.count === 0
                        text: githubFacade && githubFacade.currentDate.length > 0
                            ? "当前筛选下没有项目。"
                            : "先选择一个快照，再开始阅读。"
                        color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                        font.family: root.tokens ? root.tokens.sansFamily : font.family
                    }
                }
            }

            SectionCard {
                Layout.minimumWidth: root.detailMinWidth
                Layout.preferredWidth: root.detailWidth
                Layout.maximumWidth: root.detailWidth + 14
                Layout.fillHeight: true
                tokens: root.tokens
                heading: "详情面板"
                supportingText: "阅读当前模型选中仓库的详细信息。"

                ScrollView {
                    objectName: "githubDetailPanel"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true

                    ColumnLayout {
                        width: parent.width
                        spacing: 14

                        Label {
                            Layout.fillWidth: true
                            text: githubFacade && githubFacade.hasSelection
                                ? githubFacade.selectedProjectName
                                : "请选择仓库"
                            color: root.tokens ? root.tokens.inkStrong : "#2E261D"
                            font.family: root.tokens ? root.tokens.serifFamily : font.family
                            font.pixelSize: 22
                            font.weight: Font.Medium
                            wrapMode: Text.WordWrap
                        }

                        Label {
                            Layout.fillWidth: true
                            text: githubFacade && githubFacade.hasSelection
                                ? githubFacade.selectedProjectDescription
                                : "详情面会跟随当前列表选中项更新。"
                            color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                            font.family: root.tokens ? root.tokens.sansFamily : font.family
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8

                            MetricPill {
                                tokens: root.tokens
                                label: "Stars"
                                value: githubFacade && githubFacade.hasSelection ? String(root.selectedProject.stars || 0) : "-"
                            }

                            MetricPill {
                                tokens: root.tokens
                                label: "Today"
                                value: githubFacade && githubFacade.hasSelection && root.selectedProject.starsToday !== null && root.selectedProject.starsToday !== undefined
                                    ? String(root.selectedProject.starsToday)
                                    : "-"
                            }

                            MetricPill {
                                tokens: root.tokens
                                label: "Week"
                                value: githubFacade && githubFacade.hasSelection && root.selectedProject.starsWeekly !== null && root.selectedProject.starsWeekly !== undefined
                                    ? String(root.selectedProject.starsWeekly)
                                    : "-"
                            }
                        }

                        DetailField { Layout.fillWidth: true; tokens: root.tokens; label: "Language"; value: root.selectedProject.language || "" }
                        DetailField { Layout.fillWidth: true; tokens: root.tokens; label: "Category"; value: root.selectedProject.category || "" }
                        DetailField { Layout.fillWidth: true; tokens: root.tokens; label: "Trend"; value: root.selectedProject.trend || "" }
                        DetailField { Layout.fillWidth: true; tokens: root.tokens; label: "Updated"; value: root.selectedProject.updatedAt || "" }
                        DetailField { Layout.fillWidth: true; tokens: root.tokens; label: "License"; value: root.selectedProject.license || "" }
                        DetailField {
                            Layout.fillWidth: true
                            tokens: root.tokens
                            label: "Forks"
                            value: githubFacade && githubFacade.hasSelection ? String(root.selectedProject.forks || 0) : ""
                        }

                        Flow {
                            Layout.fillWidth: true
                            width: parent.width
                            spacing: 6

                            Repeater {
                                model: root.selectedProject.topics || []

                                TagChip {
                                    required property var modelData

                                    tokens: root.tokens
                                    label: String(modelData)
                                    interactive: false
                                    muted: true
                                }
                            }
                        }
                    }
                }

                Button {
                    id: openRepoButton
                    objectName: "githubOpenRepoButton"
                    text: "打开仓库"
                    enabled: githubFacade ? githubFacade.hasSelection && githubFacade.selectedProjectUrl.length > 0 : false
                    onClicked: if (githubFacade) githubFacade.openSelectedRepo()
                }
            }
        }
    }
}
