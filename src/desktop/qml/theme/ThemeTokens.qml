import QtQuick

QtObject {
    id: root

    readonly property color windowBackground: "#F7F2EA"
    readonly property color surfaceBase: "#FBF8F3"
    readonly property color surfaceRaised: "#F3EAE0"
    readonly property color surfaceSunken: "#EEE3D6"
    readonly property color surfaceMuted: "#F1E9DF"
    readonly property color surfaceInteractive: "#F6EFE7"
    readonly property color borderSubtle: "#E1D7CA"
    readonly property color borderStrong: "#D4C5B4"
    readonly property color textStrong: "#2E261D"
    readonly property color textMuted: "#6E6457"
    readonly property color accentText: "#9C6F49"
    readonly property color accentSoft: "#E8DDD0"
    readonly property color accentFill: "#B9916E"
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
    readonly property color successBackground: "#F4EEE5"
    readonly property color successBorder: "#D8CCBE"
    readonly property color warningBackground: "#F6ECE1"
    readonly property color warningBorder: "#D8B89E"
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
