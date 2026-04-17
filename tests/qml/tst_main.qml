import QtQuick
import QtTest
import AIDaily.Desktop

TestCase {
    id: testCase
    name: "MainWindow"
    when: true

    readonly property var injectedShellFacade: appShellFacade

    Component {
        id: mainComponent

        Main {
        }
    }

    function test_mainWindowLoads() {
        const window = createTemporaryObject(mainComponent, null)
        verify(window !== null)
        compare(window.title, "AI Daily")
        verify(findChild(window, "desktopShell") !== null)
        window.destroy()
    }
}
