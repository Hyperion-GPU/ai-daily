import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    property var tokens
    property string label: ""
    property string value: ""

    radius: tokens ? tokens.controlRadius : 14
    color: tokens ? tokens.surfaceBase : "#FBF8F2"
    border.width: 1
    border.color: tokens ? tokens.borderSubtle : "#D8CCB8"
    implicitWidth: pillRow.implicitWidth + 20
    implicitHeight: pillRow.implicitHeight + 14

    RowLayout {
        id: pillRow
        anchors.centerIn: parent
        spacing: 8

        Label {
            text: root.label
            color: root.tokens ? root.tokens.inkMuted : "#6E6457"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 12
        }

        Label {
            text: root.value
            color: root.tokens ? root.tokens.inkStrong : "#2E261D"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 13
            font.weight: Font.DemiBold
        }
    }
}
