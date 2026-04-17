import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Pane {
    id: root
    required property QtObject tokens
    required property string eyebrow
    required property string title
    required property string description
    required property var checkpoints

    padding: 0

    background: Rectangle {
        color: "transparent"
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 18

        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Label {
                text: root.eyebrow
                font.family: root.tokens.sansFamily
                font.pixelSize: 12
                font.letterSpacing: 1.2
                color: root.tokens.textMuted
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: root.tokens.borderSubtle
            }
        }

        Label {
            text: root.title
            font.family: root.tokens.serifFamily
            font.pixelSize: 26
            font.weight: Font.DemiBold
            color: root.tokens.textStrong
        }

        Label {
            Layout.fillWidth: true
            text: root.description
            wrapMode: Text.WordWrap
            font.family: root.tokens.sansFamily
            font.pixelSize: 14
            color: root.tokens.textMuted
        }

        Repeater {
            model: root.checkpoints

            Pane {
                Layout.fillWidth: true
                padding: 16

                background: Rectangle {
                    color: root.tokens.surfaceRaised
                    radius: root.tokens.radiusMedium
                    border.color: root.tokens.borderSubtle
                }

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 8

                    Label {
                        text: modelData.title
                        font.family: root.tokens.sansFamily
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                        color: root.tokens.textStrong
                    }

                    Label {
                        text: modelData.body
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        font.family: root.tokens.sansFamily
                        font.pixelSize: 12
                        color: root.tokens.textMuted
                    }
                }
            }
        }
    }
}

