import QtQuick
import QtTest
import AIDaily.Desktop

TestCase {
    id: testCase
    name: "DesktopShell"
    when: true

    function init() {
        appShellFacade.selectWorkspace("settings")
    }

    function test_contextPropertyExists() {
        verify(appShellFacade !== undefined)
    }

    Component {
        id: shellComponent

        DesktopShell {
            width: 1320
            height: 860
            shellFacade: appShellFacade
        }
    }

    function test_shellComponentCreates() {
        const shell = createTemporaryObject(shellComponent, testCase)
        verify(shell !== null)
        const stack = findChild(shell, "workspaceStack")
        const title = findChild(shell, "workspaceTitleLabel")
        verify(stack !== null)
        verify(title !== null)
        compare(stack.currentIndex, appShellFacade.currentIndex)
        compare(title.text, "Settings")
        shell.destroy()
    }

    function test_shellFollowsFacadeSelection() {
        const shell = createTemporaryObject(shellComponent, testCase)
        verify(shell !== null)
        const stack = findChild(shell, "workspaceStack")
        verify(stack !== null)

        appShellFacade.selectWorkspace("github-trends")
        compare(stack.currentIndex, 1)
        appShellFacade.selectWorkspace("settings")
        compare(stack.currentIndex, 2)

        shell.destroy()
    }

}
