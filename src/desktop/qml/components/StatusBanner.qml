import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    property var tokens
    property string text: ""
    property bool busy: false
    property string tone: "neutral"

    visible: busy || text.length > 0
    radius: tokens ? tokens.controlRadius : 14
    color: tone === "error" || tone === "warning"
        ? (tokens ? tokens.warningBackground : "#f7ece2")
        : (tokens ? tokens.successBackground : "#eef2e7")
    border.width: 1
    border.color: tone === "error" || tone === "warning"
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
            Layout.preferredWidth: 20
            Layout.preferredHeight: 20
        }

        Label {
            Layout.fillWidth: true
            text: root.busy && root.text.length === 0 ? "正在处理设置更新..." : root.text
            color: root.tokens ? root.tokens.inkStrong : "#2d251d"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 13
            wrapMode: Text.Wrap
        }
    }
}
