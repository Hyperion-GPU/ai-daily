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
        spacing: 4

        Label {
            visible: root.eyebrow.length > 0
            text: root.eyebrow
            color: root.tokens ? root.tokens.inkSoft : "#998c7c"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 10
            font.letterSpacing: 1.1
        }

        Label {
            text: root.title
            color: root.tokens ? root.tokens.inkStrong : "#2d251d"
            font.family: root.tokens ? root.tokens.serifFamily : font.family
            font.pixelSize: 24
            font.weight: Font.Medium
            Layout.fillWidth: true
            wrapMode: Text.Wrap
        }

        Label {
            text: root.subtitle
            color: root.tokens ? root.tokens.inkMuted : "#6f6558"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 12
            lineHeight: 1.25
            wrapMode: Text.Wrap
            Layout.fillWidth: true
        }
    }
}
