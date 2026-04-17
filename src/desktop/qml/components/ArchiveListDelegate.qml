import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    signal clicked()

    property var tokens
    property string date: ""
    property string label: ""
    property int articleCount: 0
    property bool isLatest: false
    property bool isSelected: false

    radius: tokens ? tokens.controlRadius : 14
    color: root.isSelected
        ? (tokens ? tokens.accentSoft : "#E6D4BF")
        : (tokens ? tokens.surfaceBase : "#F1E9DF")
    border.width: 1
    border.color: root.isSelected
        ? (tokens ? tokens.borderStrong : "#BA8A5C")
        : (tokens ? tokens.borderSubtle : "#D8CCB8")
    implicitHeight: contentColumn.implicitHeight + 14

    ColumnLayout {
        id: contentColumn
        anchors.fill: parent
        anchors.margins: 11
        spacing: 4

        RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Label {
                text: root.label
                color: root.tokens ? root.tokens.inkStrong : "#2E261D"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 13
                font.weight: Font.Medium
                Layout.fillWidth: true
                elide: Text.ElideRight
            }

            Rectangle {
                visible: root.isLatest
                radius: 8
                color: root.tokens ? root.tokens.surfaceBase : "#F7F1E8"
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
        }

        Label {
            text: root.articleCount + " articles"
            color: root.tokens ? root.tokens.inkMuted : "#6E6457"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 10
        }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
