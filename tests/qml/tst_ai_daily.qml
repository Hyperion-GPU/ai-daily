import QtQuick
import QtTest
import AIDaily.Desktop

TestCase {
    id: testCase
    name: "AIDailyPage"
    when: true

    Component {
        id: shellComponent

        DesktopShell {
            width: 1320
            height: 860
            shellFacade: appShellFacade
            settingsFacade: desktopSettingsFacade
            digestFacade: desktopDigestFacade
            githubFacade: desktopGithubFacade
        }
    }

    function init() {
        appShellFacade.selectWorkspace("settings")
        if (desktopTestSetup) {
            desktopTestSetup.resetDigestState()
        }
        if (desktopDigestFacade) {
            desktopDigestFacade.markStale()
        }
    }

    function test_switchingToAIDailyLoadsWorkbenchStructure() {
        const shell = createTemporaryObject(shellComponent, testCase)
        verify(shell !== null)

        appShellFacade.selectWorkspace("ai-daily")
        wait(50)

        verify(findChild(shell, "aiDailyWorkspace") !== null)
        verify(findChild(shell, "aiDailyArchiveList") !== null)
        verify(findChild(shell, "aiDailyArticleList") !== null)
        verify(findChild(shell, "aiDailyDetailPanel") !== null)
        compare(desktopDigestFacade.archiveModel.count, 2)
        compare(desktopDigestFacade.articleModel.count, 2)

        shell.destroy()
    }

    function test_filtersAndTagsDriveFacadeStateImmediately() {
        const shell = createTemporaryObject(shellComponent, testCase)
        verify(shell !== null)

        appShellFacade.selectWorkspace("ai-daily")
        wait(50)

        desktopDigestFacade.setCategoryFilter("official")
        compare(desktopDigestFacade.filteredArticleCount, 1)

        desktopDigestFacade.toggleTagSelection("OpenAI")
        compare(desktopDigestFacade.selectedTags.length, 1)
        compare(desktopDigestFacade.articleModel.count, 1)

        desktopDigestFacade.clearFilters()
        compare(desktopDigestFacade.selectedTags.length, 0)
        compare(desktopDigestFacade.categoryFilter, "")
        compare(desktopDigestFacade.articleModel.count, 2)

        shell.destroy()
    }

    function test_articleSelectionUpdatesDetailFromModel() {
        const shell = createTemporaryObject(shellComponent, testCase)
        verify(shell !== null)

        appShellFacade.selectWorkspace("ai-daily")
        wait(50)

        compare(desktopDigestFacade.selectedArticle.title, "OpenAI updates desktop workflow")
        desktopDigestFacade.selectArticleRow(1)
        wait(20)

        compare(desktopDigestFacade.selectedArticle.title, "Agent tooling roundup")
        verify(findChild(shell, "aiDailyOpenArticleButton") !== null)

        shell.destroy()
    }

    function test_detailOpenArticleButtonScrollsIntoViewInShortWindow() {
        const shell = createTemporaryObject(shellComponent, testCase)
        verify(shell !== null)

        shell.height = 620
        appShellFacade.selectWorkspace("ai-daily")
        wait(50)

        const detailPanel = findChild(shell, "aiDailyDetailPanel")
        const detailColumn = findChild(shell, "aiDailyDetailColumn")
        const openButton = findChild(shell, "aiDailyOpenArticleButton")
        verify(detailPanel !== null)
        verify(detailColumn !== null)
        verify(openButton !== null)
        verify(detailPanel.height > 0)
        verify(detailPanel.contentHeight >= detailColumn.y + detailColumn.implicitHeight)
        verify(detailPanel.contentHeight > detailPanel.height)

        detailPanel.contentItem.contentY = Math.max(0, detailPanel.contentHeight - detailPanel.height)
        wait(20)

        const buttonBottomInPanel = openButton.mapToItem(detailPanel, 0, openButton.height).y
        verify(buttonBottomInPanel > 0)
        verify(buttonBottomInPanel <= detailPanel.height)

        shell.destroy()
    }

    function test_fetchSuccessSelectsLatestArchive() {
        const shell = createTemporaryObject(shellComponent, testCase)
        verify(shell !== null)

        appShellFacade.selectWorkspace("ai-daily")
        wait(50)

        desktopDigestFacade.selectDate("2026-04-14")
        compare(desktopDigestFacade.currentDate, "2026-04-14")

        const progressBar = findChild(shell, "aiDailyProgressBar")
        verify(progressBar !== null)

        desktopDigestFacade.runFetch()
        verify(desktopDigestFacade.pipelineProgressValue > 0)
        tryCompare(desktopDigestFacade, "lastFetchOutcome", "success", 3000)
        tryCompare(desktopDigestFacade, "currentDate", "2026-04-16", 3000)
        compare(desktopDigestFacade.pipelineProgressValue, 100)
        compare(desktopDigestFacade.selectedArticle.title, "Fresh digest after fetch")

        shell.destroy()
    }
}
