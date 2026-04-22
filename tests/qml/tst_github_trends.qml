import QtQuick
import QtTest
import AIDaily.Desktop

TestCase {
    id: testCase
    name: "GithubTrendsPage"
    when: true

    Component {
        id: shellComponent

        DesktopShell {
            width: 1320
            height: 860
            shellFacade: appShellFacade
            settingsFacade: desktopSettingsFacade
            githubFacade: desktopGithubFacade
        }
    }

    function init() {
        appShellFacade.selectWorkspace("settings")
        if (desktopTestSetup) {
            desktopTestSetup.resetGithubFetchState()
        }
        if (desktopGithubFacade) {
            desktopGithubFacade.setCategoryFilter("")
            desktopGithubFacade.setSelectedLanguages([])
            desktopGithubFacade.setMinStars(0)
            desktopGithubFacade.setSortKey("stars")
            desktopGithubFacade.setSearchQuery("")
            desktopGithubFacade.setTrendFilter("")
            desktopGithubFacade.selectDate("")
            desktopGithubFacade.markStale()
        }
    }

    function test_switchingToGithubLoadsWorkbenchStructure() {
        const shell = createTemporaryObject(shellComponent, testCase)
        verify(shell !== null)

        appShellFacade.selectWorkspace("github-trends")
        wait(50)

        verify(findChild(shell, "githubTrendsPage") !== null)
        verify(findChild(shell, "githubSnapshotList") !== null)
        verify(findChild(shell, "githubProjectList") !== null)
        verify(findChild(shell, "githubDetailPanel") !== null)
        compare(desktopGithubFacade.snapshotModel.count, 2)
        compare(desktopGithubFacade.projectModel.count, 2)

        shell.destroy()
    }

    function test_applyAndClearFiltersUseFacadeState() {
        const shell = createTemporaryObject(shellComponent, testCase)
        verify(shell !== null)

        appShellFacade.selectWorkspace("github-trends")
        wait(50)

        desktopGithubFacade.setTrendFilter("rising")
        compare(desktopGithubFacade.stale, true)
        compare(desktopGithubFacade.projectModel.count, 2)

        desktopGithubFacade.reload()
        compare(desktopGithubFacade.stale, false)
        compare(desktopGithubFacade.projectModel.count, 1)

        desktopGithubFacade.clearFilters()
        compare(desktopGithubFacade.stale, false)
        compare(desktopGithubFacade.projectModel.count, 2)
        verify(findChild(shell, "githubApplyFiltersButton") !== null)
        verify(findChild(shell, "githubClearFiltersButton") !== null)

        shell.destroy()
    }

    function test_projectSelectionUpdatesDetailFromModel() {
        const shell = createTemporaryObject(shellComponent, testCase)
        verify(shell !== null)

        appShellFacade.selectWorkspace("github-trends")
        wait(50)

        compare(desktopGithubFacade.selectedProjectName, "acme/alpha")
        desktopGithubFacade.selectProjectRow(1)
        wait(20)

        compare(desktopGithubFacade.selectedProjectName, "acme/beta")
        compare(desktopGithubFacade.projectModel.selectedItem.fullName, "acme/beta")
        verify(findChild(shell, "githubOpenRepoButton") !== null)

        shell.destroy()
    }

    function test_degradedFetchShowsWarningBannerWithoutSuccessCopy() {
        const shell = createTemporaryObject(shellComponent, testCase)
        verify(shell !== null)

        appShellFacade.selectWorkspace("github-trends")
        wait(50)

        compare(desktopGithubFacade.currentDate, "2026-04-15")
        compare(desktopGithubFacade.projectModel.count, 2)
        desktopTestSetup.configureGithubFetchResult("degraded", "rate_limit")

        const progressBar = findChild(shell, "githubProgressBar")
        verify(progressBar !== null)

        desktopGithubFacade.runFetch()
        verify(desktopGithubFacade.fetchProgressValue > 0)
        tryCompare(desktopGithubFacade, "lastFetchOutcome", "degraded", 3000)
        compare(desktopGithubFacade.fetchProgressValue, 100)
        tryCompare(
            desktopGithubFacade,
            "noticeMessage",
            "GitHub 抓取受限，已保留当前正式快照；恢复 GITHUB_TOKEN 后重试。",
            3000
        )
        tryCompare(desktopGithubFacade, "statusTone", "warning", 3000)

        const banner = findChild(shell, "githubStatusBanner")
        const outcomeProbe = findChild(shell, "githubFetchOutcomeProbe")
        const toneProbe = findChild(shell, "githubStatusToneProbe")
        verify(banner !== null)
        verify(outcomeProbe !== null)
        verify(toneProbe !== null)
        tryCompare(outcomeProbe, "text", "degraded", 3000)
        tryCompare(toneProbe, "text", "warning", 3000)
        compare(desktopGithubFacade.currentDate, "2026-04-15")
        compare(desktopGithubFacade.projectModel.count, 2)
        verify(desktopGithubFacade.noticeMessage !== "GitHub 趋势快照已刷新。")

        shell.destroy()
    }
}
