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
        spacing: 6

        Label {
            text: root.eyebrow
            color: root.tokens ? root.tokens.inkSoft : "#998c7c"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 12
            font.letterSpacing: 1.2
        }

        Label {
            text: root.title
            color: root.tokens ? root.tokens.inkStrong : "#2d251d"
            font.family: root.tokens ? root.tokens.serifFamily : font.family
            font.pixelSize: 28
            font.weight: Font.DemiBold
        }

        Label {
            text: root.subtitle
            color: root.tokens ? root.tokens.inkMuted : "#6f6558"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 14
            wrapMode: Text.Wrap
            Layout.fillWidth: true
        }
    }
}
