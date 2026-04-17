import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQml

import "../components"

Item {
    id: root

    property var tokens
    property var settingsFacade
    readonly property int pagePaddingValue: root.tokens ? root.tokens.pagePadding : 32
    readonly property int sectionGapValue: root.tokens ? root.tokens.sectionGap : 20
    readonly property int panelRadiusValue: root.tokens ? root.tokens.panelRadius : 20
    readonly property color pagePanelBackground: root.tokens ? root.tokens.panelBackground : "#fbf8f3"
    readonly property color pageBorderColor: root.tokens ? root.tokens.borderColor : "#d9cfbf"
    readonly property color pageInkStrong: root.tokens ? root.tokens.inkStrong : "#2d251d"
    readonly property color pageInkMuted: root.tokens ? root.tokens.inkMuted : "#6f6558"
    readonly property color pageInkSoft: root.tokens ? root.tokens.inkSoft : "#998c7c"
    readonly property string pageSansFamily: root.tokens ? root.tokens.sansFamily : "Sans Serif"
    readonly property int wideRailWidth: 340
    readonly property int wideCardsGap: root.sectionGapValue
    readonly property int widePrimaryMinWidth: 600
    // Keep the breakpoint tied to the real two-column budget, with enough
    // headroom for packaged client-area loss at a 1440px outer window.
    readonly property int compactBreakpoint: root.wideRailWidth + root.wideCardsGap + root.widePrimaryMinWidth
    readonly property real effectiveLayoutWidth: {
        const contentWidth = settingsScrollHost && settingsScrollHost.width > 0 ? settingsScrollHost.width : 0
        return contentWidth > 0 ? contentWidth : root.width
    }
    // Use the actual scroll viewport width so wide/compact mode follows the same geometry source as the cards themselves.
    readonly property bool compactCards: root.effectiveLayoutWidth < root.compactBreakpoint
    readonly property bool githubSectionOnNextRow: githubSection ? githubSection.y > llmSection.y : false
    readonly property string geometryProbeSummary: "page=" + Math.round(root.width)
        + "x" + Math.round(root.height)
        + " scrollHost=" + Math.round(settingsScrollHost ? settingsScrollHost.width : 0)
        + " compact=" + (root.compactCards ? "true" : "false")
        + " llm=(" + Math.round(llmSection ? llmSection.x : 0) + "," + Math.round(llmSection ? llmSection.y : 0) + "," + Math.round(llmSection ? llmSection.width : 0) + ")"
        + " pipeline=(" + Math.round(pipelineSection ? pipelineSection.x : 0) + "," + Math.round(pipelineSection ? pipelineSection.y : 0) + "," + Math.round(pipelineSection ? pipelineSection.width : 0) + ")"
        + " github=(" + Math.round(githubSection ? githubSection.x : 0) + "," + Math.round(githubSection ? githubSection.y : 0) + "," + Math.round(githubSection ? githubSection.width : 0) + ")"
        + " githubNextRow=" + (root.githubSectionOnNextRow ? "true" : "false")
    readonly property bool geometryProbeEnabled: {
        try {
            return Qt.application.arguments.indexOf("--settings-geometry-probe") !== -1
        } catch (error) {
            return false
        }
    }

    property alias providerCombo: providerCombo
    property alias timezoneField: timezoneField
    property alias baseUrlField: baseUrlField
    property alias modelField: modelField
    property alias llmApiKeyField: llmApiKeyField
    property alias githubTokenField: githubTokenField
    property alias validateButton: validateButton
    property alias saveButton: saveButton
    property alias openDirButton: openDirButton
    property alias statusBannerRef: settingsStatusBanner
    property alias settingsScrollViewRef: settingsScrollView
    property alias settingsScrollHostRef: settingsScrollHost
    property alias settingsTopCardsLayoutRef: settingsTopCards
    property alias llmSectionCard: llmSection
    property alias pipelineSectionCard: pipelineSection
    property alias githubSectionCard: githubSection

    objectName: "settingsWorkspace"

    function providerIndexFor(value) {
        for (let index = 0; index < providerCombo.model.length; index += 1) {
            if (providerCombo.model[index].value === value) {
                return index
            }
        }
        return 0
    }

    Component.onCompleted: {
        if (settingsFacade) {
            settingsFacade.reload()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: root.pagePaddingValue
        spacing: root.sectionGapValue

        PageHeader {
            Layout.fillWidth: true
            tokens: root.tokens
            eyebrow: "AI Daily / Settings"
            title: "Settings"
            subtitle: "先把 provider、密钥、pipeline 参数和工作目录收敛到 facade，再逐步接入更多工作区刷新与错误恢复语义。"
        }

        StatusBanner {
            id: settingsStatusBanner
            objectName: "settingsStatusBanner"
            Layout.fillWidth: true
            tokens: root.tokens
            busy: settingsFacade ? settingsFacade.busy : false
            tone: (settingsFacade && (settingsFacade.errorMessage || settingsFacade.validationSummary)) ? "error" : "neutral"
            text: {
                if (!settingsFacade) {
                    return ""
                }
                if (settingsFacade.errorMessage) {
                    return settingsFacade.errorMessage
                }
                if (settingsFacade.validationSummary) {
                    return settingsFacade.validationSummary
                }
                return settingsFacade.noticeMessage
            }
        }

        Label {
            id: settingsGeometryProbe
            objectName: "settingsGeometryProbe"
            visible: root.geometryProbeEnabled
            Layout.fillWidth: true
            text: root.geometryProbeSummary
            color: root.pageInkSoft
            font.family: root.pageSansFamily
            font.pixelSize: 11
            wrapMode: Text.WrapAnywhere
        }

        ScrollView {
            id: settingsScrollView
            objectName: "settingsScrollView"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth

            Item {
                id: settingsScrollHost
                objectName: "settingsScrollHost"
                width: settingsScrollView.availableWidth
                height: settingsScrollContent.implicitHeight
                implicitWidth: settingsScrollView.availableWidth
                implicitHeight: settingsScrollContent.implicitHeight

                ColumnLayout {
                    id: settingsScrollContent
                    width: parent.width
                    spacing: root.sectionGapValue

                    Item {
                        id: settingsTopCards
                        objectName: "settingsTopCards"
                        Layout.fillWidth: true
                        implicitHeight: root.compactCards
                            ? llmSection.height + root.sectionGapValue + pipelineSection.height
                            : Math.max(llmSection.height, pipelineSection.height)

                    SectionCard {
                        id: llmSection
                        objectName: "settingsLlmSection"
                        x: 0
                        y: 0
                        width: root.compactCards
                            ? settingsTopCards.width
                            : Math.max(0, settingsTopCards.width - root.wideRailWidth - root.wideCardsGap)
                        tokens: root.tokens
                        heading: "LLM 设置"
                        supportingText: "稳定优先。当前默认走 Basic/Fusion 风格底座，先把 provider、endpoint、key 与 temperature 对齐到 facade。"

                        GridLayout {
                            columns: 2
                            rowSpacing: 12
                            columnSpacing: 16
                            Layout.fillWidth: true

                            Label { text: "Provider"; color: root.pageInkMuted }
                            ComboBox {
                                id: providerCombo
                                Layout.fillWidth: true
                                model: [
                                    { text: "siliconflow", value: "siliconflow" },
                                    { text: "newapi", value: "newapi" }
                                ]
                                textRole: "text"
                                valueRole: "value"
                                onActivated: if (settingsFacade) settingsFacade.setProvider(currentValue)
                                Binding {
                                    target: providerCombo
                                    property: "currentIndex"
                                    value: root.providerIndexFor(settingsFacade ? settingsFacade.provider : "siliconflow")
                                }
                            }

                            Label { text: "Timezone"; color: root.pageInkMuted }
                            TextField {
                                id: timezoneField
                                Layout.fillWidth: true
                                placeholderText: "Asia/Shanghai"
                                onEditingFinished: if (settingsFacade) settingsFacade.setTimezone(text)
                                Binding {
                                    target: timezoneField
                                    property: "text"
                                    value: settingsFacade ? settingsFacade.timezone : "Asia/Shanghai"
                                    when: !timezoneField.activeFocus
                                }
                            }

                            Label { text: "Base URL"; color: root.pageInkMuted }
                            TextField {
                                id: baseUrlField
                                Layout.fillWidth: true
                                placeholderText: "https://api.siliconflow.cn/v1"
                                onEditingFinished: if (settingsFacade) settingsFacade.setBaseUrl(text)
                                Binding {
                                    target: baseUrlField
                                    property: "text"
                                    value: settingsFacade ? settingsFacade.baseUrl : ""
                                    when: !baseUrlField.activeFocus
                                }
                            }

                            Label { text: "Model"; color: root.pageInkMuted }
                            TextField {
                                id: modelField
                                Layout.fillWidth: true
                                placeholderText: "deepseek-ai/DeepSeek-V3.2"
                                onEditingFinished: if (settingsFacade) settingsFacade.setModel(text)
                                Binding {
                                    target: modelField
                                    property: "text"
                                    value: settingsFacade ? settingsFacade.model : ""
                                    when: !modelField.activeFocus
                                }
                            }

                            Label { text: "LLM API Key"; color: root.pageInkMuted }
                            RowLayout {
                                Layout.fillWidth: true

                                TextField {
                                    id: llmApiKeyField
                                    Layout.fillWidth: true
                                    echoMode: settingsFacade && settingsFacade.llmApiKeyVisible ? TextInput.Normal : TextInput.Password
                                    onEditingFinished: if (settingsFacade) settingsFacade.setLlmApiKey(text)
                                    Binding {
                                        target: llmApiKeyField
                                        property: "text"
                                        value: settingsFacade ? settingsFacade.llmApiKey : ""
                                        when: !llmApiKeyField.activeFocus
                                    }
                                }

                                Button {
                                    text: settingsFacade && settingsFacade.llmApiKeyVisible ? "隐藏" : "显示"
                                    onClicked: if (settingsFacade) settingsFacade.toggleLlmApiKeyVisible()
                                }
                            }

                            Label { text: "Temperature"; color: root.pageInkMuted }
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 4

                                Slider {
                                    id: temperatureSlider
                                    Layout.fillWidth: true
                                    from: 0
                                    to: 100
                                    stepSize: 1
                                    onMoved: if (settingsFacade) settingsFacade.setTemperature(value)
                                    Binding {
                                        target: temperatureSlider
                                        property: "value"
                                        value: settingsFacade ? settingsFacade.temperature : 30
                                        when: !temperatureSlider.pressed
                                    }
                                }

                                Label {
                                    text: Math.round(temperatureSlider.value) + " / 100"
                                    color: root.pageInkMuted
                                }
                            }

                            Label { text: "Max Tokens"; color: root.pageInkMuted }
                            SpinBox {
                                id: maxTokensSpin
                                Layout.fillWidth: true
                                from: 1
                                to: 100000
                                editable: true
                                onValueModified: if (settingsFacade) settingsFacade.setMaxTokens(value)
                                Binding {
                                    target: maxTokensSpin
                                    property: "value"
                                    value: settingsFacade ? settingsFacade.maxTokens : 1500
                                    when: !maxTokensSpin.activeFocus
                                }
                            }
                        }
                    }

                    SectionCard {
                        id: pipelineSection
                        objectName: "settingsPipelineSection"
                        x: root.compactCards ? 0 : settingsTopCards.width - width
                        y: root.compactCards ? llmSection.height + root.sectionGapValue : 0
                        width: root.compactCards ? settingsTopCards.width : root.wideRailWidth
                        tokens: root.tokens
                        heading: "Pipeline 设置"
                        supportingText: "这一块保持 Python 业务逻辑不动，只迁移桌面端的配置交互与状态归属。"

                        GridLayout {
                            columns: 2
                            rowSpacing: 12
                            columnSpacing: 16
                            Layout.fillWidth: true

                            Label { text: "时间窗口（小时）"; color: root.pageInkMuted }
                            SpinBox {
                                id: timeWindowSpin
                                Layout.fillWidth: true
                                from: 1
                                to: 720
                                editable: true
                                onValueModified: if (settingsFacade) settingsFacade.setTimeWindowHours(value)
                                Binding {
                                    target: timeWindowSpin
                                    property: "value"
                                    value: settingsFacade ? settingsFacade.timeWindowHours : 48
                                    when: !timeWindowSpin.activeFocus
                                }
                            }

                            Label { text: "日推上限"; color: root.pageInkMuted }
                            SpinBox {
                                id: maxArticlesSpin
                                Layout.fillWidth: true
                                from: 1
                                to: 500
                                editable: true
                                onValueModified: if (settingsFacade) settingsFacade.setMaxArticlesPerDay(value)
                                Binding {
                                    target: maxArticlesSpin
                                    property: "value"
                                    value: settingsFacade ? settingsFacade.maxArticlesPerDay : 30
                                    when: !maxArticlesSpin.activeFocus
                                }
                            }

                            Label { text: "Stage2 上限"; color: root.pageInkMuted }
                            SpinBox {
                                id: stage2Spin
                                Layout.fillWidth: true
                                from: 1
                                to: 1000
                                editable: true
                                onValueModified: if (settingsFacade) settingsFacade.setMaxArticlesToStage2(value)
                                Binding {
                                    target: stage2Spin
                                    property: "value"
                                    value: settingsFacade ? settingsFacade.maxArticlesToStage2 : 50
                                    when: !stage2Spin.activeFocus
                                }
                            }

                            Label { text: "Stage1 Batch"; color: root.pageInkMuted }
                            SpinBox {
                                id: stage1Spin
                                Layout.fillWidth: true
                                from: 1
                                to: 1000
                                editable: true
                                onValueModified: if (settingsFacade) settingsFacade.setStage1BatchSize(value)
                                Binding {
                                    target: stage1Spin
                                    property: "value"
                                    value: settingsFacade ? settingsFacade.stage1BatchSize : 50
                                    when: !stage1Spin.activeFocus
                                }
                            }
                        }
                    }
                }

                SectionCard {
                    id: githubSection
                    objectName: "settingsGithubSection"
                    Layout.fillWidth: true
                    tokens: root.tokens
                    heading: "GitHub Trends 设置"
                    supportingText: "GitHub 工作区的主体迁移稍后再做，这里先把 token 与抓取上限收进 facade。"

                    GridLayout {
                        columns: 2
                        rowSpacing: 12
                        columnSpacing: 16
                        Layout.fillWidth: true

                        Label { text: "启用 GitHub Trending"; color: root.pageInkMuted }
                        Switch {
                            id: githubEnabledSwitch
                            text: checked ? "已启用" : "未启用"
                            onToggled: if (settingsFacade) settingsFacade.setGithubEnabled(checked)
                            Binding {
                                target: githubEnabledSwitch
                                property: "checked"
                                value: settingsFacade ? settingsFacade.githubEnabled : false
                            }
                        }

                        Label { text: "GitHub Token"; color: root.pageInkMuted }
                        RowLayout {
                            Layout.fillWidth: true

                            TextField {
                                id: githubTokenField
                                Layout.fillWidth: true
                                echoMode: settingsFacade && settingsFacade.githubTokenVisible ? TextInput.Normal : TextInput.Password
                                onEditingFinished: if (settingsFacade) settingsFacade.setGithubToken(text)
                                Binding {
                                    target: githubTokenField
                                    property: "text"
                                    value: settingsFacade ? settingsFacade.githubToken : ""
                                    when: !githubTokenField.activeFocus
                                }
                            }

                            Button {
                                text: settingsFacade && settingsFacade.githubTokenVisible ? "隐藏" : "显示"
                                onClicked: if (settingsFacade) settingsFacade.toggleGithubTokenVisible()
                            }
                        }

                        Label { text: "最小 Stars"; color: root.pageInkMuted }
                        SpinBox {
                            id: githubMinStarsSpin
                            Layout.fillWidth: true
                            from: 0
                            to: 1000000
                            editable: true
                            onValueModified: if (settingsFacade) settingsFacade.setGithubMinStars(value)
                            Binding {
                                target: githubMinStarsSpin
                                property: "value"
                                value: settingsFacade ? settingsFacade.githubMinStars : 500
                                when: !githubMinStarsSpin.activeFocus
                            }
                        }

                        Label { text: "每日项目上限"; color: root.pageInkMuted }
                        SpinBox {
                            id: githubMaxProjectsSpin
                            Layout.fillWidth: true
                            from: 1
                            to: 500
                            editable: true
                            onValueModified: if (settingsFacade) settingsFacade.setGithubMaxProjects(value)
                            Binding {
                                target: githubMaxProjectsSpin
                                property: "value"
                                value: settingsFacade ? settingsFacade.githubMaxProjects : 50
                                when: !githubMaxProjectsSpin.activeFocus
                            }
                        }
                    }
                }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            radius: root.panelRadiusValue
            color: root.pagePanelBackground
            border.width: 1
            border.color: root.pageBorderColor
            implicitHeight: footerRow.implicitHeight + 24

            RowLayout {
                id: footerRow
                anchors.fill: parent
                anchors.margins: 12
                spacing: 12

                Label {
                    Layout.fillWidth: true
                    text: settingsFacade && settingsFacade.stale ? "有未保存改动。" : "当前配置与 facade 已同步。"
                    color: root.pageInkMuted
                    font.family: root.pageSansFamily
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                }

                Button {
                    id: openDirButton
                    objectName: "settingsOpenDirButton"
                    text: "打开数据目录"
                    enabled: !settingsFacade || !settingsFacade.busy
                    onClicked: if (settingsFacade) settingsFacade.openDataDir()
                }

                Button {
                    id: validateButton
                    objectName: "settingsValidateButton"
                    text: "检查配置"
                    enabled: !settingsFacade || !settingsFacade.busy
                    onClicked: if (settingsFacade) settingsFacade.validate()
                }

                Button {
                    id: saveButton
                    objectName: "settingsSaveButton"
                    text: settingsFacade && settingsFacade.busy ? "保存中..." : "保存设置"
                    enabled: settingsFacade ? (!settingsFacade.busy && settingsFacade.stale) : false
                    onClicked: if (settingsFacade) settingsFacade.save()
                }
            }
        }

    }
}
