import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    property var tokens
    property string label: ""
    property string value: ""

    implicitWidth: layout.implicitWidth
    implicitHeight: layout.implicitHeight

    ColumnLayout {
        id: layout
        anchors.fill: parent
        spacing: 2

        Label {
            text: root.label
            color: root.tokens ? root.tokens.inkSoft : "#998C7C"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 11
        }

        Label {
            text: root.value.length > 0 ? root.value : "-"
            color: root.tokens ? root.tokens.inkStrong : "#2E261D"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 13
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }
    }
}
