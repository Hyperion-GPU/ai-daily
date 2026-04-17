import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    signal clicked()

    property var tokens
    property string fullName: ""
    property string description: ""
    property string language: ""
    property string category: ""
    property string trend: ""
    property int stars: 0
    property var starsToday: null
    property var starsWeekly: null
    property string updatedAt: ""
    property bool isSelected: false

    radius: tokens ? tokens.controlRadius : 14
    color: isSelected
        ? (tokens ? tokens.surfaceInteractive : "#F7F1E8")
        : (tokens ? tokens.surfaceBase : "#FBF8F2")
    border.width: 1
    border.color: isSelected
        ? (tokens ? tokens.borderStrong : "#73491E")
        : (tokens ? tokens.borderSubtle : "#D8CCB8")
    implicitHeight: contentColumn.implicitHeight + 16

    ColumnLayout {
        id: contentColumn
        anchors.fill: parent
        anchors.margins: 12
        spacing: 6

        Label {
            text: root.fullName
            color: root.tokens ? root.tokens.inkStrong : "#2E261D"
            font.family: root.tokens ? root.tokens.serifFamily : font.family
            font.pixelSize: 15
            font.weight: Font.Medium
            Layout.fillWidth: true
            elide: Text.ElideRight
        }

        Label {
            text: root.description.length > 0 ? root.description : "No description."
            color: root.tokens ? root.tokens.inkMuted : "#6E6457"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 11
            lineHeight: 1.25
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            maximumLineCount: 3
            elide: Text.ElideRight
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 5

            Label {
                text: root.language.length > 0 ? root.language : "Language unknown"
                color: root.tokens ? root.tokens.inkSoft : "#998C7C"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 9
            }

            Label {
                text: root.category.length > 0 ? root.category : "Uncategorized"
                color: root.tokens ? root.tokens.inkSoft : "#998C7C"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 9
            }

            Label {
                text: root.trend.length > 0 ? root.trend : "Trend pending"
                color: root.tokens ? root.tokens.inkSoft : "#998C7C"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 9
            }

            Item { Layout.fillWidth: true }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 7

            Label {
                text: "Stars " + root.stars
                color: root.tokens ? root.tokens.inkStrong : "#2E261D"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 9
            }

            Label {
                text: "Today " + (root.starsToday === null || root.starsToday === undefined ? "-" : root.starsToday)
                color: root.tokens ? root.tokens.accentText : "#6E6457"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 9
            }

            Label {
                text: "Week " + (root.starsWeekly === null || root.starsWeekly === undefined ? "-" : root.starsWeekly)
                color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 9
            }

            Item { Layout.fillWidth: true }

            Label {
                text: root.updatedAt.length > 0 ? root.updatedAt : "Updated time unknown"
                color: root.tokens ? root.tokens.inkSoft : "#998C7C"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 9
            }
        }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
