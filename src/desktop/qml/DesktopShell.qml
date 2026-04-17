import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    objectName: "desktopShellRoot"
    property QtObject shellFacade: null
    property QtObject settingsFacade: null
    property QtObject githubFacade: null
    property QtObject digestFacade: null

    ThemeTokens {
        id: tokens
    }

    Rectangle {
        anchors.fill: parent
        color: tokens.windowBackground
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 20

        Pane {
            id: navigationPane
            objectName: "navigationPane"
            Layout.preferredWidth: 260
            Layout.fillHeight: true
            padding: 20

            background: Rectangle {
                color: tokens.surfaceRaised
                radius: tokens.radiusLarge
                border.color: tokens.borderSubtle
            }

            ColumnLayout {
                anchors.fill: parent
                spacing: 18

                RowLayout {
                    spacing: 14

                    Rectangle {
                        Layout.preferredWidth: 44
                        Layout.preferredHeight: 44
                        radius: 14
                        color: tokens.accentSoft

                        Image {
                            anchors.centerIn: parent
                            width: 28
                            height: 28
                            fillMode: Image.PreserveAspectFit
                            source: "qrc:/qt/qml/AIDaily/Desktop/assets/branding/ai-daily-icon.png"
                        }
                    }

                    ColumnLayout {
                        spacing: 2

                        Label {
                            text: "AI Daily"
                            font.family: tokens.serifFamily
                            font.pixelSize: 24
                            font.weight: Font.DemiBold
                            color: tokens.textStrong
                        }

                        Label {
                            text: "QML migration workbench"
                            font.family: tokens.sansFamily
                            font.pixelSize: 12
                            color: tokens.textMuted
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: tokens.borderSubtle
                    opacity: 0.9
                }

                Label {
                    text: "工作区"
                    font.family: tokens.sansFamily
                    font.pixelSize: 12
                    font.letterSpacing: 1.2
                    color: tokens.textMuted
                }

                ColumnLayout {
                    id: navColumn
                    objectName: "workspaceNavList"
                    Layout.fillWidth: true
                    spacing: 10

                    Repeater {
                        model: root.shellFacade ? root.shellFacade.workspaces : []

                        delegate: NavigationRailButton {
                            required property var modelData

                            Layout.fillWidth: true
                            objectName: "workspaceNavButton_" + modelData.key
                            label: modelData.title
                            subtitle: modelData.subtitle
                            iconSource: modelData.iconSource
                            current: root.shellFacade && root.shellFacade.currentWorkspace === modelData.key
                            onClicked: if (root.shellFacade) root.shellFacade.selectWorkspace(modelData.key)
                        }
                    }
                }

                Item {
                    Layout.fillHeight: true
                }

                Pane {
                    Layout.fillWidth: true
                    padding: 16

                    background: Rectangle {
                        color: tokens.surfaceSunken
                        radius: tokens.radiusMedium
                        border.color: tokens.borderSubtle
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 8

                        Label {
                            text: "阶段 2 目标"
                            font.family: tokens.sansFamily
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                            color: tokens.textStrong
                        }

                        Label {
                            text: "先固定资源系统、QML 宿主和测试分层，再逐页接入 facade / model / command gateway。"
                            wrapMode: Text.WordWrap
                            font.family: tokens.sansFamily
                            font.pixelSize: 12
                            color: tokens.textMuted
                        }
                    }
                }
            }
        }

        Pane {
            id: workspacePane
            objectName: "workspacePane"
            Layout.fillWidth: true
            Layout.fillHeight: true
            padding: 24

            background: Rectangle {
                color: tokens.surfaceBase
                radius: tokens.radiusLarge
                border.color: tokens.borderSubtle
            }

            ColumnLayout {
                anchors.fill: parent
                spacing: 22

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 20

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        Label {
                            id: workspaceTitleLabel
                            objectName: "workspaceTitleLabel"
                            text: {
                                const item = root.shellFacade ? root.shellFacade.workspace(root.shellFacade.currentWorkspace) : ({})
                                return item.title || "AI Daily"
                            }
                            font.family: tokens.serifFamily
                            font.pixelSize: 34
                            font.weight: Font.DemiBold
                            color: tokens.textStrong
                        }

                        Label {
                            objectName: "workspaceSubtitleLabel"
                            text: {
                                const item = root.shellFacade ? root.shellFacade.workspace(root.shellFacade.currentWorkspace) : ({})
                                return item.description || ""
                            }
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            font.family: tokens.sansFamily
                            font.pixelSize: 14
                            color: tokens.textMuted
                        }
                    }

                    Pane {
                        padding: 14

                        background: Rectangle {
                            color: tokens.accentSoft
                            radius: tokens.radiusMedium
                        }

                        Label {
                            text: "Qt Quick Controls 2"
                            font.family: tokens.sansFamily
                            font.pixelSize: 12
                            font.weight: Font.DemiBold
                            color: tokens.accentText
                        }
                    }
                }

                StackLayout {
                    id: workspaceStack
                    objectName: "workspaceStack"
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    currentIndex: root.shellFacade ? root.shellFacade.currentIndex : 0

                    AIDailyPage {
                        tokens: tokens
                        digestFacade: root.digestFacade
                    }

                    GithubTrendsPage {
                        objectName: "githubTrendsPage"
                        tokens: tokens
                        githubFacade: root.githubFacade
                    }

                    SettingsPage {
                        objectName: "settingsPage"
                        tokens: tokens
                        settingsFacade: root.settingsFacade
                    }
                }
            }
        }
    }
}
