import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    property var tokens
    property string text: ""
    property bool busy: false
    property string tone: "neutral"
    property int progressValue: -1
    property string progressBarObjectName: "statusProgressBar"
    readonly property bool warningTone: tone === "error" || tone === "warning"
    readonly property bool showProgress: busy && progressValue >= 0
    readonly property real progressFraction: Math.max(0, Math.min(1, progressValue / 100))

    visible: busy || text.length > 0
    radius: tokens ? tokens.controlRadius : 14
    color: warningTone
        ? (tokens ? tokens.warningBackground : "#f7ece2")
        : (tokens ? tokens.successBackground : "#eef2e7")
    border.width: 1
    border.color: warningTone
        ? (tokens ? tokens.warningBorder : "#d1b8a3")
        : (tokens ? tokens.successBorder : "#bbc8af")

    implicitHeight: bannerColumn.implicitHeight + 20

    ColumnLayout {
        id: bannerColumn
        anchors.fill: parent
        anchors.margins: 10
        spacing: 8

        RowLayout {
            id: bannerRow
            Layout.fillWidth: true
            spacing: 8

            BusyIndicator {
                running: root.busy
                visible: root.busy
                Layout.preferredWidth: 16
                Layout.preferredHeight: 16
            }

            Rectangle {
                visible: !root.busy
                Layout.alignment: Qt.AlignTop
                Layout.topMargin: 4
                Layout.preferredWidth: 5
                Layout.preferredHeight: 5
                radius: 2.5
                color: warningTone
                    ? (root.tokens ? root.tokens.accentText : "#73491E")
                    : (root.tokens ? root.tokens.inkSoft : "#998C7C")
            }

            Label {
                Layout.fillWidth: true
                text: root.busy && root.text.length === 0 ? "Processing update..." : root.text
                color: root.tokens ? root.tokens.inkStrong : "#2d251d"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 11
                lineHeight: 1.25
                wrapMode: Text.Wrap
            }
        }

        Rectangle {
            id: progressTrack
            objectName: root.progressBarObjectName
            visible: root.showProgress
            Layout.fillWidth: true
            Layout.preferredHeight: 5
            radius: 2.5
            color: Qt.rgba(225 / 255, 215 / 255, 202 / 255, 0.65)

            Rectangle {
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: root.progressFraction > 0
                    ? Math.max(parent.width * root.progressFraction, 10)
                    : 0
                radius: parent.radius
                color: root.tokens ? root.tokens.accentFill : "#B9916E"
                opacity: 0.9

                Behavior on width {
                    NumberAnimation {
                        duration: 180
                        easing.type: Easing.OutCubic
                    }
                }
            }
        }
    }
}
