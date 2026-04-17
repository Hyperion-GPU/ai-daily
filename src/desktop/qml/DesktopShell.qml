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
        spacing: 0

        Rectangle {
            id: navigationPane
            objectName: "navigationPane"
            Layout.preferredWidth: 200
            Layout.fillHeight: true
            color: tokens.surfaceMuted
            border.width: 0

            Rectangle {
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.right: parent.right
                width: 1
                color: tokens.borderSubtle
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 12

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3

                    Label {
                        text: "信息流"
                        color: tokens.textStrong
                        font.family: tokens.sansFamily
                        font.pixelSize: 14
                        font.weight: Font.Medium
                    }

                    Label {
                        text: "Research Desktop"
                        color: tokens.textMuted
                        font.family: tokens.sansFamily
                        font.pixelSize: 11
                    }
                }

                ColumnLayout {
                    id: navColumn
                    objectName: "workspaceNavList"
                    Layout.fillWidth: true
                    spacing: 2

                    Repeater {
                        model: root.shellFacade ? root.shellFacade.workspaces : []

                        delegate: NavigationRailButton {
                            required property var modelData

                            Layout.fillWidth: true
                            objectName: "workspaceNavButton_" + modelData.key
                            tokens: tokens
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

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 4

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 1
                        color: tokens.borderSubtle
                    }

                    Label {
                        text: "v0.1 · 本地运行"
                        color: Qt.rgba(110 / 255, 101 / 255, 92 / 255, 0.6)
                        font.family: tokens.sansFamily
                        font.pixelSize: 11
                    }
                }
            }
        }

        Item {
            id: workspacePane
            objectName: "workspacePane"
            Layout.fillWidth: true
            Layout.fillHeight: true

            Label {
                id: workspaceTitleLabel
                objectName: "workspaceTitleLabel"
                visible: false
                text: {
                    const item = root.shellFacade ? root.shellFacade.workspace(root.shellFacade.currentWorkspace) : ({})
                    return item.title || "AI Daily"
                }
            }

            Label {
                id: workspaceSubtitleLabel
                objectName: "workspaceSubtitleLabel"
                visible: false
                text: {
                    const item = root.shellFacade ? root.shellFacade.workspace(root.shellFacade.currentWorkspace) : ({})
                    return item.description || ""
                }
            }

            StackLayout {
                id: workspaceStack
                objectName: "workspaceStack"
                anchors.fill: parent
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
