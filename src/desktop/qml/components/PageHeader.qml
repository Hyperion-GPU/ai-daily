import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    property var tokens
    property string eyebrow: ""
    property string title: ""
    property string subtitle: ""

    implicitHeight: copyColumn.implicitHeight

    ColumnLayout {
        id: copyColumn
        anchors.fill: parent
        spacing: 5

        Label {
            text: root.eyebrow
            color: root.tokens ? root.tokens.inkSoft : "#998c7c"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 11
            font.letterSpacing: 1.4
        }

        Label {
            text: root.title
            color: root.tokens ? root.tokens.inkStrong : "#2d251d"
            font.family: root.tokens ? root.tokens.serifFamily : font.family
            font.pixelSize: 26
            font.weight: Font.Medium
        }

        Label {
            text: root.subtitle
            color: root.tokens ? root.tokens.inkMuted : "#6f6558"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 13
            wrapMode: Text.Wrap
            Layout.fillWidth: true
        }
    }
}
