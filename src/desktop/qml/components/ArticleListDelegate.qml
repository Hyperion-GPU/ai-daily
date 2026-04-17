import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    signal clicked()

    property var tokens
    property string title: ""
    property string sourceName: ""
    property string sourceCategoryLabel: ""
    property string publishedLabel: ""
    property string summaryZh: ""
    property int importance: 0
    property var tags: []
    property bool isSelected: false

    radius: tokens ? tokens.controlRadius : 14
    color: isSelected
        ? (tokens ? tokens.surfaceInteractive : "#F7F1E8")
        : (tokens ? tokens.surfaceBase : "#FBF8F2")
    border.width: 1
    border.color: isSelected
        ? (tokens ? tokens.borderStrong : "#73491E")
        : (tokens ? tokens.borderSubtle : "#D8CCB8")
    implicitHeight: contentColumn.implicitHeight + 18

    ColumnLayout {
        id: contentColumn
        anchors.fill: parent
        anchors.margins: 13
        spacing: 7

        Label {
            text: root.title.length > 0 ? root.title : "Untitled article"
            color: root.tokens ? root.tokens.inkStrong : "#2E261D"
            font.family: root.tokens ? root.tokens.serifFamily : font.family
            font.pixelSize: 16
            font.weight: Font.Medium
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            maximumLineCount: 2
            elide: Text.ElideRight
        }

        Label {
            text: [root.sourceName, root.publishedLabel].filter(Boolean).join("  ·  ")
            visible: text.length > 0
            color: root.tokens ? root.tokens.inkMuted : "#6E6457"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 10
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
        }

        Label {
            text: root.summaryZh.length > 0 ? root.summaryZh : "No summary yet."
            color: root.tokens ? root.tokens.inkMuted : "#6E6457"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 11
            lineHeight: 1.28
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            maximumLineCount: 3
            elide: Text.ElideRight
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            TagChip {
                tokens: root.tokens
                label: root.sourceCategoryLabel.length > 0 ? root.sourceCategoryLabel : "Uncategorized"
                interactive: false
                muted: !root.isSelected
            }

            TagChip {
                tokens: root.tokens
                label: "Importance " + root.importance + "/5"
                interactive: false
                selected: root.importance >= 4
                muted: root.importance < 4
            }

            Repeater {
                model: (root.tags || []).slice(0, 2)

                TagChip {
                    required property var modelData

                    tokens: root.tokens
                    label: String(modelData)
                    interactive: false
                    muted: true
                }
            }

            Item {
                Layout.fillWidth: true
            }
        }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
