import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    property var tokens
    property string title: ""
    default property alias contentData: contentColumn.data

    implicitWidth: contentColumn.implicitWidth
    implicitHeight: contentColumn.implicitHeight

    ColumnLayout {
        id: contentColumn
        anchors.fill: parent
        spacing: 6

        Label {
            text: root.title
            color: root.tokens ? root.tokens.inkMuted : "#6E6457"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 10
            font.letterSpacing: 0.3
        }
    }
}
