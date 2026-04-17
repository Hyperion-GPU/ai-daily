import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    signal clicked()

    property var tokens
    property string date: ""
    property string label: ""
    property bool isSelected: false
    property bool isLatest: false
    property var projectCount: null
    property string generatedAt: ""

    radius: tokens ? tokens.controlRadius : 14
    color: isSelected
        ? (tokens ? tokens.accentSoft : "#E6D4BF")
        : (tokens ? tokens.surfaceBase : "#F1E9DF")
    border.width: 1
    border.color: isSelected
        ? (tokens ? tokens.accentText : "#73491E")
        : (tokens ? tokens.borderSubtle : "#D8CCB8")
    implicitHeight: contentColumn.implicitHeight + 14

    ColumnLayout {
        id: contentColumn
        anchors.fill: parent
        anchors.margins: 10
        spacing: 5

        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Label {
                text: root.label
                color: root.tokens ? root.tokens.inkStrong : "#2E261D"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 11
                font.weight: Font.Medium
            }

            Rectangle {
                visible: root.isLatest
                radius: 8
                color: root.tokens ? root.tokens.surfaceBase : "#FBF8F2"
                border.width: 1
                border.color: root.tokens ? root.tokens.borderSubtle : "#D8CCB8"
                implicitWidth: latestLabel.implicitWidth + 10
                implicitHeight: latestLabel.implicitHeight + 4

                Label {
                    id: latestLabel
                    anchors.centerIn: parent
                    text: "Latest"
                    color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                    font.family: root.tokens ? root.tokens.sansFamily : font.family
                    font.pixelSize: 8
                }
            }

            Item { Layout.fillWidth: true }
        }

        Label {
            text: root.projectCount === null || root.projectCount === undefined
                ? "Project count pending"
                : root.projectCount + " projects"
            color: root.tokens ? root.tokens.inkMuted : "#6E6457"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 10
        }

        Label {
            text: root.generatedAt.length > 0 ? root.generatedAt : "Generated time pending"
            color: root.tokens ? root.tokens.inkSoft : "#998C7C"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 9
            elide: Text.ElideRight
            Layout.fillWidth: true
        }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
