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
        ? (tokens ? tokens.surfaceRaised : "#F7F1E8")
        : (tokens ? tokens.surfaceBase : "#FBF8F2")
    border.width: 1
    border.color: isSelected
        ? (tokens ? tokens.accentText : "#73491E")
        : (tokens ? tokens.borderSubtle : "#D8CCB8")
    implicitHeight: contentColumn.implicitHeight + 20

    ColumnLayout {
        id: contentColumn
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        Label {
            text: root.fullName
            color: root.tokens ? root.tokens.inkStrong : "#2E261D"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 14
            font.weight: Font.DemiBold
            Layout.fillWidth: true
            elide: Text.ElideRight
        }

        Label {
            text: root.description.length > 0 ? root.description : "No description."
            color: root.tokens ? root.tokens.inkMuted : "#6E6457"
            font.family: root.tokens ? root.tokens.sansFamily : font.family
            font.pixelSize: 12
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Label {
                text: root.language.length > 0 ? root.language : "Language unknown"
                color: root.tokens ? root.tokens.inkSoft : "#998C7C"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 11
            }

            Label {
                text: root.category.length > 0 ? root.category : "Uncategorized"
                color: root.tokens ? root.tokens.inkSoft : "#998C7C"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 11
            }

            Label {
                text: root.trend.length > 0 ? root.trend : "Trend pending"
                color: root.tokens ? root.tokens.inkSoft : "#998C7C"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 11
            }

            Item { Layout.fillWidth: true }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Label {
                text: "Stars " + root.stars
                color: root.tokens ? root.tokens.inkStrong : "#2E261D"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 11
            }

            Label {
                text: "Today " + (root.starsToday === null || root.starsToday === undefined ? "-" : root.starsToday)
                color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 11
            }

            Label {
                text: "Week " + (root.starsWeekly === null || root.starsWeekly === undefined ? "-" : root.starsWeekly)
                color: root.tokens ? root.tokens.inkMuted : "#6E6457"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 11
            }

            Item { Layout.fillWidth: true }

            Label {
                text: root.updatedAt.length > 0 ? root.updatedAt : "Updated time unknown"
                color: root.tokens ? root.tokens.inkSoft : "#998C7C"
                font.family: root.tokens ? root.tokens.sansFamily : font.family
                font.pixelSize: 11
            }
        }
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
