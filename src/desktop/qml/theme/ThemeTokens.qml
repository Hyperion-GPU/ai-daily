import QtQuick

QtObject {
    id: root

    readonly property color windowBackground: "#F4EFE7"
    readonly property color surfaceBase: "#FBF8F2"
    readonly property color surfaceRaised: "#F7F1E8"
    readonly property color surfaceSunken: "#EEE5D8"
    readonly property color borderSubtle: "#D8CCB8"
    readonly property color textStrong: "#2E261D"
    readonly property color textMuted: "#6E6457"
    readonly property color accentText: "#73491E"
    readonly property color accentSoft: "#E6D4BF"
    readonly property int radiusLarge: 28
    readonly property int radiusMedium: 20
    readonly property int radiusSmall: 14
    readonly property int pagePadding: 32
    readonly property int sectionGap: 20
    readonly property int panelRadius: radiusMedium
    readonly property int controlRadius: radiusSmall
    readonly property color panelBackground: surfaceRaised
    readonly property color borderColor: borderSubtle
    readonly property color inkStrong: textStrong
    readonly property color inkMuted: textMuted
    readonly property color inkSoft: "#998C7C"
    readonly property color successBackground: "#EEF2E7"
    readonly property color successBorder: "#BBC8AF"
    readonly property color warningBackground: "#F7ECE2"
    readonly property color warningBorder: "#D1B8A3"
    readonly property string sansFamily: sansLoader.status === FontLoader.Ready ? sansLoader.name : "Sans Serif"
    readonly property string serifFamily: serifLoader.status === FontLoader.Ready ? serifLoader.name : "Serif"
    readonly property bool sansFontReady: sansLoader.status === FontLoader.Ready
    readonly property bool serifFontReady: serifLoader.status === FontLoader.Ready

    readonly property FontLoader sansLoader: FontLoader {
        source: "qrc:/qt/qml/AIDaily/Desktop/assets/fonts/NotoSansSC-VF.ttf"
    }

    readonly property FontLoader serifLoader: FontLoader {
        source: "qrc:/qt/qml/AIDaily/Desktop/assets/fonts/NotoSerifSC-VF.ttf"
    }
}
