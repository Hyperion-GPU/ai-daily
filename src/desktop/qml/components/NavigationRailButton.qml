import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Button {
    id: root
    required property string label
    required property string subtitle
    required property string iconSource
    property bool current: false

    implicitHeight: 72
    leftPadding: 14
    rightPadding: 14
    topPadding: 12
    bottomPadding: 12
    hoverEnabled: true

    background: Rectangle {
        radius: 18
        color: root.current ? "#E6D4BF" : (root.hovered ? "#F5EFE5" : "transparent")
        border.color: root.current ? "#BA8A5C" : "#D8CCB8"
        border.width: 1
    }

    contentItem: RowLayout {
        spacing: 12

        Rectangle {
            Layout.preferredWidth: 38
            Layout.preferredHeight: 38
            radius: 12
            color: root.current ? "#F7EBDD" : "#F3EEE7"

            Image {
                anchors.centerIn: parent
                width: 18
                height: 18
                source: root.iconSource
                fillMode: Image.PreserveAspectFit
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 1

            Label {
                text: root.label
                font.family: "Noto Sans SC"
                font.pixelSize: 14
                font.weight: Font.DemiBold
                color: "#2E261D"
            }

            Label {
                text: root.subtitle
                Layout.fillWidth: true
                elide: Text.ElideRight
                font.family: "Noto Sans SC"
                font.pixelSize: 11
                color: "#6E6457"
            }
        }
    }
}

