import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    property var tokens
    property string text: ""
    property bool busy: false
    property string tone: "neutral"
    readonly property bool warningTone: tone === "error" || tone === "warning"

    visible: busy || text.length > 0
    radius: tokens ? tokens.controlRadius : 14
    color: warningTone
        ? (tokens ? tokens.warningBackground : "#f7ece2")
        : (tokens ? tokens.successBackground : "#eef2e7")
    border.width: 1
    border.color: warningTone
        ? (tokens ? tokens.warningBorder : "#d1b8a3")
        : (tokens ? tokens.successBorder : "#bbc8af")

    implicitHeight: bannerRow.implicitHeight + 24

    RowLayout {
        id: bannerRow
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        BusyIndicator {
            running: root.busy
            visible: root.busy
            Layout.preferredWidth: 18
            Layout.preferredHeight: 18
        }

        Rectangle {
            visible: !root.busy
            Layout.alignment: Qt.AlignTop
            Layout.topMargin: 4
            Layout.preferredWidth: 6
            Layout.preferredHeight: 6
            radius: 3
            color: warningTone
                ? (root.tokens ? root.tokens.accentText : "#73491E")
                : (root.tokens ? root.tokens.inkSoft : "#998C7C")
        }

        Label {
            Layout.fillWidth: true
            text: root.busy && root.text.length === 0 ? "Processing update..." : root.text
            color: root.tokens ? root.tokens.inkStrong : "#2d251d"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 12
            wrapMode: Text.Wrap
        }
    }
}
