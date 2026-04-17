import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "../components"

Item {
    id: root

    property var tokens
    property QtObject githubFacade

    readonly property var categoryOptions: [
        { text: "All", value: "" },
        { text: "LLM", value: "llm" },
        { text: "Agent", value: "agent" },
        { text: "CV", value: "cv" },
        { text: "NLP", value: "nlp" },
        { text: "Framework", value: "ml_framework" },
        { text: "MLOps", value: "mlops" },
        { text: "General", value: "general" }
    ]
    readonly property var sortOptions: [
        { text: "Stars", value: "stars" },
        { text: "Stars Today", value: "stars_today" },
        { text: "Stars Weekly", value: "stars_weekly" },
        { text: "Recently Updated", value: "updated" }
    ]
    readonly property var trendOptions: [
        { text: "All", value: "" },
        { text: "Hot", value: "hot" },
        { text: "Rising", value: "rising" },
        { text: "Stable", value: "stable" }
    ]
    readonly property var languageOptions: [{ label: "All", value: "", count: 0 }].concat(
        githubFacade ? githubFacade.availableLanguages : []
    )
    readonly property var selectedProject: githubFacade ? githubFacade.projectModel.selectedItem : ({})

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
                eyebrow: "AI Daily / GitHub"
                title: "GitHub Trends"
                subtitle: "Switch snapshots by day and keep filters, list reading, and detail review in one quiet workbench."
            }

            Button {
                id: fetchButton
                objectName: "githubFetchButton"
                text: githubFacade && githubFacade.busy ? "Fetching..." : "Fetch Latest"
                enabled: githubFacade ? !githubFacade.busy : false
                onClicked: if (githubFacade) githubFacade.runFetch()
            }
        }

        StatusBanner {
            id: statusBanner
            objectName: "githubStatusBanner"
            Layout.fillWidth: true
            tokens: root.tokens
            busy: githubFacade ? githubFacade.busy : false
            tone: githubFacade ? githubFacade.statusTone : "neutral"
            text: {
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
                    return "Filters changed. Apply filters to refresh the result list."
                }
                return ""
            }
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
            id: summaryBar
            objectName: "githubSummaryBar"
            Layout.fillWidth: true
            radius: root.tokens ? root.tokens.radiusMedium : 20
            color: root.tokens ? root.tokens.surfaceRaised : "#F7F1E8"
            border.width: 1
            border.color: root.tokens ? root.tokens.borderSubtle : "#D8CCB8"
            implicitHeight: summaryColumn.implicitHeight + 28

            ColumnLayout {
                id: summaryColumn
                anchors.fill: parent
                anchors.margins: 14
                spacing: 14

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    MetricPill {
                        tokens: root.tokens
                        label: "Snapshots"
                        value: githubFacade ? String(githubFacade.snapshotModel.count) : "0"
                    }

                    MetricPill {
                        tokens: root.tokens
                        label: "Results"
                        value: githubFacade ? String(githubFacade.projectModel.count) : "0"
                    }

                    MetricPill {
                        tokens: root.tokens
                        label: "State"
                        value: githubFacade && githubFacade.stale ? "Stale" : "Synced"
                    }

                    Item { Layout.fillWidth: true }

                    Button {
                        id: applyFiltersButton
                        objectName: "githubApplyFiltersButton"
                        text: "Apply Filters"
                        enabled: githubFacade ? !githubFacade.busy : false
                        onClicked: if (githubFacade) githubFacade.reload()
                    }

                    Button {
                        id: clearFiltersButton
                        objectName: "githubClearFiltersButton"
                        text: "Clear Filters"
                        enabled: githubFacade ? !githubFacade.busy : false
                        onClicked: if (githubFacade) githubFacade.clearFilters()
                    }
                }

                Label {
                    Layout.fillWidth: true
                    text: githubFacade && githubFacade.summaryText.length > 0
                        ? githubFacade.summaryText
                        : "Waiting for a GitHub snapshot."
                    color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                    font.family: root.tokens ? root.tokens.sansFamily : font.family
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 14

                    FilterGroup {
                        Layout.fillWidth: true
                        tokens: root.tokens
                        title: "Category"

                        ComboBox {
                            id: categoryCombo
                            Layout.fillWidth: true
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
                        title: "Language"

                        ComboBox {
                            id: languageCombo
                            Layout.fillWidth: true
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
                        Layout.preferredWidth: 140
                        tokens: root.tokens
                        title: "Min Stars"

                        SpinBox {
                            id: minStarsSpin
                            Layout.fillWidth: true
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
                        title: "Trend"

                        ComboBox {
                            id: trendCombo
                            Layout.fillWidth: true
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
                        title: "Sort"

                        ComboBox {
                            id: sortCombo
                            Layout.fillWidth: true
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

                    FilterGroup {
                        Layout.fillWidth: true
                        tokens: root.tokens
                        title: "Search"

                        TextField {
                            id: searchField
                            Layout.fillWidth: true
                            placeholderText: "Search repo or summary"
                            onTextChanged: if (githubFacade) githubFacade.setSearchQuery(text)
                            Binding {
                                target: searchField
                                property: "text"
                                value: githubFacade ? githubFacade.searchQuery : ""
                                when: !searchField.activeFocus
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
                Layout.preferredWidth: 280
                Layout.fillHeight: true
                tokens: root.tokens
                heading: "Snapshot Archive"
                supportingText: "Switch the trending snapshot by date."

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
                        text: "No GitHub snapshots yet."
                        color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                        font.family: root.tokens ? root.tokens.sansFamily : font.family
                    }
                }
            }

            SectionCard {
                Layout.fillWidth: true
                Layout.fillHeight: true
                tokens: root.tokens
                heading: "Project List"
                supportingText: "Keep filtered repositories readable and calm."

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
                            ? "No projects for the active filters."
                            : "Select a GitHub snapshot first."
                        color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                        font.family: root.tokens ? root.tokens.sansFamily : font.family
                    }
                }
            }

            SectionCard {
                Layout.preferredWidth: 360
                Layout.fillHeight: true
                tokens: root.tokens
                heading: "Detail Panel"
                supportingText: "Read details from the current model selection only."

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
                                : "Select a repository"
                            color: root.tokens ? root.tokens.inkStrong : "#2E261D"
                            font.family: root.tokens ? root.tokens.serifFamily : font.family
                            font.pixelSize: 22
                            font.weight: Font.DemiBold
                            wrapMode: Text.WordWrap
                        }

                        Label {
                            Layout.fillWidth: true
                            text: githubFacade && githubFacade.hasSelection
                                ? githubFacade.selectedProjectDescription
                                : "The current selection will drive this detail panel."
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

                        DetailField { tokens: root.tokens; label: "Language"; value: root.selectedProject.language || "" }
                        DetailField { tokens: root.tokens; label: "Category"; value: root.selectedProject.category || "" }
                        DetailField { tokens: root.tokens; label: "Trend"; value: root.selectedProject.trend || "" }
                        DetailField { tokens: root.tokens; label: "Updated"; value: root.selectedProject.updatedAt || "" }
                        DetailField { tokens: root.tokens; label: "License"; value: root.selectedProject.license || "" }
                        DetailField {
                            tokens: root.tokens
                            label: "Forks"
                            value: githubFacade && githubFacade.hasSelection ? String(root.selectedProject.forks || 0) : ""
                        }
                    }
                }

                Button {
                    id: openRepoButton
                    objectName: "githubOpenRepoButton"
                    Layout.alignment: Qt.AlignLeft
                    text: "Open Repository"
                    enabled: githubFacade ? githubFacade.hasSelection && githubFacade.selectedProjectUrl.length > 0 : false
                    onClicked: if (githubFacade) githubFacade.openSelectedRepo()
                }
            }
        }
    }
}
