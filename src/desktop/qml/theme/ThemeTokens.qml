import QtQuick

QtObject {
    id: root

    readonly property color windowBackground: "#F7F2EA"
    readonly property color surfaceBase: "#FBF8F3"
    readonly property color surfaceRaised: "#F6F0E7"
    readonly property color surfaceSunken: "#F1E8DD"
    readonly property color surfaceMuted: "#F1E9DF"
    readonly property color surfaceInteractive: "#F8F3EC"
    readonly property color borderSubtle: "#E1D7CA"
    readonly property color borderStrong: "#CDBAA5"
    readonly property color textStrong: "#2E261D"
    readonly property color textMuted: "#6E6457"
    readonly property color accentText: "#9C6F49"
    readonly property color accentSoft: "#E8DDD0"
    readonly property color accentFill: "#B9916E"
    readonly property int radiusLarge: 24
    readonly property int radiusMedium: 18
    readonly property int radiusSmall: 12
    readonly property int pagePadding: 32
    readonly property int sectionGap: 18
    readonly property int panelRadius: radiusMedium
    readonly property int controlRadius: radiusSmall
    readonly property color panelBackground: surfaceBase
    readonly property color borderColor: borderSubtle
    readonly property color inkStrong: textStrong
    readonly property color inkMuted: textMuted
    readonly property color inkSoft: "#938675"
    readonly property color successBackground: "#F3ECE3"
    readonly property color successBorder: "#D8CCBE"
    readonly property color warningBackground: "#F4E8DB"
    readonly property color warningBorder: "#D4B394"
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
