import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    signal clicked()

    property var tokens
    property string label: ""
    property bool selected: false
    property bool interactive: true
    property bool muted: false

    radius: tokens ? tokens.controlRadius : 14
    color: root.selected
        ? (tokens ? tokens.accentSoft : "#E6D4BF")
        : (tokens ? tokens.surfaceBase : "#FBF8F2")
    border.width: 1
    border.color: root.selected
        ? (tokens ? tokens.accentText : "#73491E")
        : (tokens ? tokens.borderSubtle : "#D8CCB8")
    implicitWidth: chipLabel.implicitWidth + 18
    implicitHeight: chipLabel.implicitHeight + 10
    opacity: root.muted ? 0.72 : 1

    Label {
        id: chipLabel
        anchors.centerIn: parent
        text: root.label
        color: root.selected
            ? (tokens ? tokens.accentText : "#73491E")
            : (tokens ? tokens.inkMuted : "#6E6457")
        font.family: root.tokens ? root.tokens.sansFamily : font.family
        font.pixelSize: 12
        font.weight: root.selected ? Font.DemiBold : Font.Normal
    }

    MouseArea {
        anchors.fill: parent
        enabled: root.interactive
        cursorShape: root.interactive ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: root.clicked()
    }
}
