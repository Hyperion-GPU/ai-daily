import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    property var tokens
    property string heading: ""
    property string supportingText: ""
    default property alias contentData: contentColumn.data
    readonly property int cardPadding: 20
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
        spacing: 14

        ColumnLayout {
            spacing: 4
            Layout.fillWidth: true

            Label {
                text: root.heading
                color: root.tokens ? root.tokens.inkStrong : "#2d251d"
                font.family: root.tokens ? root.tokens.serifFamily : font.family
                font.pixelSize: 20
                font.weight: Font.DemiBold
                Layout.fillWidth: true
            }

            Label {
                visible: text.length > 0
                text: root.supportingText
                color: root.tokens ? root.tokens.inkMuted : "#6f6558"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 13
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
        }

        ColumnLayout {
            id: contentColumn
            spacing: 12
            Layout.fillWidth: true
        }
    }
}
