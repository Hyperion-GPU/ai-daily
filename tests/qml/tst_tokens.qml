import QtQuick
import QtTest
import AIDaily.Desktop

TestCase {
    name: "ThemeTokens"
    when: true

    Component {
        id: tokensComponent

        ThemeTokens {
        }
    }

    function test_fontsLoadFromQrc() {
        const tokens = createTemporaryObject(tokensComponent, null)
        verify(tokens !== null)
        tryVerify(function() {
            return tokens.sansFontReady && tokens.serifFontReady
        }, 5000)
        compare(tokens.windowBackground, "#f4efe7")
        tokens.destroy()
    }
}

