import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Button {
    id: root

    required property string label
    required property string subtitle
    required property string iconSource
    property var tokens
    property bool current: false

    implicitHeight: 34
    leftPadding: 11
    rightPadding: 11
    topPadding: 7
    bottomPadding: 7
    hoverEnabled: true

    background: Rectangle {
        radius: 6
        color: root.current
            ? (root.tokens ? root.tokens.accentSoft : "#E8DDD0")
            : (root.hovered ? (root.tokens ? root.tokens.surfaceBase : "#FBF8F3") : "transparent")
        border.width: root.current ? 1 : 0
        border.color: root.tokens ? root.tokens.borderSubtle : "#E1D7CA"
    }

    contentItem: RowLayout {
        spacing: 8

        Image {
            Layout.preferredWidth: 15
            Layout.preferredHeight: 15
            source: root.iconSource
            fillMode: Image.PreserveAspectFit
            opacity: root.current ? 1 : 0.72
        }

        Label {
            Layout.fillWidth: true
            text: root.label
            color: root.current
                ? (root.tokens ? root.tokens.textStrong : "#2E261D")
                : (root.tokens ? root.tokens.textMuted : "#6E6457")
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 13
            font.weight: root.current ? Font.Medium : Font.Normal
            elide: Text.ElideRight
        }
    }
}
