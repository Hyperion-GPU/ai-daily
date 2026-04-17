import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    property var tokens
    property string heading: ""
    property string supportingText: ""
    default property alias contentData: contentColumn.data
    readonly property int cardPadding: 16
    readonly property int maxImplicitWidth: 480

    implicitWidth: Math.min(layoutColumn.implicitWidth + cardPadding * 2, maxImplicitWidth)
    implicitHeight: layoutColumn.implicitHeight + cardPadding * 2

    Rectangle {
        id: card
        anchors.fill: parent
        radius: root.tokens ? root.tokens.panelRadius : 20
        color: root.tokens ? root.tokens.panelBackground : "#fbf8f3"
        border.width: 1
        border.color: root.tokens ? root.tokens.borderColor : "#d9cfbf"
    }

    ColumnLayout {
        id: layoutColumn
        anchors.fill: parent
        anchors.margins: root.cardPadding
        spacing: 10

        ColumnLayout {
            spacing: 4
            Layout.fillWidth: true

            Label {
                text: root.heading
                color: root.tokens ? root.tokens.inkStrong : "#2d251d"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 15
                font.weight: Font.Medium
                Layout.fillWidth: true
            }

            Label {
                visible: text.length > 0
                text: root.supportingText
                color: root.tokens ? root.tokens.inkMuted : "#6f6558"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 11
                lineHeight: 1.25
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
        }

        ColumnLayout {
            id: contentColumn
            spacing: 8
            Layout.fillWidth: true
        }
    }
}
