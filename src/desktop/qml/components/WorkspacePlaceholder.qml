import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    property var tokens
    property string objectNameValue: ""
    property string eyebrow: ""
    property string title: ""
    property string subtitle: ""
    property string bodyTitle: ""
    property string bodyText: ""

    objectName: objectNameValue

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: root.tokens ? root.tokens.pagePadding : 32
        spacing: root.tokens ? root.tokens.sectionGap : 20

        PageHeader {
            Layout.fillWidth: true
            tokens: root.tokens
            eyebrow: root.eyebrow
            title: root.title
            subtitle: root.subtitle
        }

        SectionCard {
            Layout.fillWidth: true
            Layout.fillHeight: true
            tokens: root.tokens
            title: root.bodyTitle
            note: root.bodyText

            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                implicitHeight: 360

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 10

                    Label {
                        text: "当前阶段保留 QWidget 版本的工作区可用，QML 先建立导航壳、状态归属、Qt Resource System 与测试链路。"
                        color: root.tokens ? root.tokens.inkStrong : "#2d251d"
                        font.family: root.tokens ? root.tokens.sansFamily : font.family
                        font.pixelSize: 14
                        wrapMode: Text.Wrap
                        horizontalAlignment: Text.AlignHCenter
                        Layout.maximumWidth: 520
                    }

                    Label {
                        text: "下一阶段会继续接入 facade、list model、长任务状态与错误恢复。"
                        color: root.tokens ? root.tokens.inkMuted : "#6f6558"
                        font.family: root.tokens ? root.tokens.sansFamily : font.family
                        font.pixelSize: 13
                        wrapMode: Text.Wrap
                        horizontalAlignment: Text.AlignHCenter
                        Layout.maximumWidth: 520
                    }
                }
            }
        }
    }
}
