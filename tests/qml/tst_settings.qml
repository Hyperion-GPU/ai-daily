import QtQuick
import QtTest
import AIDaily.Desktop

TestCase {
    id: testCase
    name: "SettingsPage"
    when: true

    Component {
        id: tokensComponent

        ThemeTokens {
        }
    }

    Component {
        id: settingsComponent

        SettingsPage {
            tokens: themeTokens
            settingsFacade: desktopSettingsFacade
        }
    }

    Component {
        id: shellComponent

        DesktopShell {
            width: 1440
            height: 960
            shellFacade: appShellFacade
            settingsFacade: desktopSettingsFacade
            githubFacade: desktopGithubFacade
            digestFacade: desktopDigestFacade
        }
    }

    property var themeTokens: null

    function init() {
        themeTokens = createTemporaryObject(tokensComponent, null)
        verify(themeTokens !== null)
        desktopSettingsFacade.reload()
    }

    function cleanup() {
        if (themeTokens) {
            themeTokens.destroy()
            themeTokens = null
        }
    }

    function createSettingsShell(width, height) {
        const shell = createTemporaryObject(shellComponent, testCase)
        verify(shell !== null)
        shell.width = width
        shell.height = height
        appShellFacade.selectWorkspace("settings")
        wait(50)
        return shell
    }

    function createSizedPage(width, height) {
        const page = createTemporaryObject(settingsComponent, testCase)
        verify(page !== null)
        page.width = width
        page.height = height
        wait(50)
        return page
    }

    function test_settingsPageLoadsFacadeState() {
        const page = createTemporaryObject(settingsComponent, null)
        verify(page !== null)
        compare(page.providerCombo.currentValue, "siliconflow")
        compare(page.baseUrlField.text, "https://api.siliconflow.cn/v1")
        compare(page.saveButton.enabled, false)
        page.destroy()
    }

    function test_settingsPageReflectsFacadeStaleState() {
        const page = createTemporaryObject(settingsComponent, null)
        verify(page !== null)

        desktopSettingsFacade.setBaseUrl("https://example.com/v1")
        compare(desktopSettingsFacade.stale, true)
        compare(page.baseUrlField.text, "https://example.com/v1")
        compare(page.saveButton.enabled, true)

        page.destroy()
    }

    function test_providerSwitchUsesTargetDefaultsAndPreservesOverride() {
        const page = createTemporaryObject(settingsComponent, null)
        verify(page !== null)

        desktopSettingsFacade.setProvider("newapi")
        compare(page.providerCombo.currentValue, "newapi")
        compare(page.baseUrlField.text, "https://example.com/newapi")
        compare(page.modelField.text, "deepseek-chat")

        desktopSettingsFacade.setBaseUrl("https://custom.newapi/v1")
        desktopSettingsFacade.setModel("custom-chat")
        desktopSettingsFacade.setProvider("siliconflow")
        compare(page.baseUrlField.text, "https://api.siliconflow.cn/v1")
        compare(page.modelField.text, "deepseek-ai/DeepSeek-V3.2")

        desktopSettingsFacade.setProvider("newapi")
        compare(page.baseUrlField.text, "https://custom.newapi/v1")
        compare(page.modelField.text, "custom-chat")

        page.destroy()
    }

    function test_settingsPageKeepsCardsWideAtDesktopWidth() {
        const shell = createSettingsShell(1440, 960)
        const page = findChild(shell, "settingsPage")
        verify(page !== null)
        const scrollView = page.settingsScrollViewRef
        const llmSection = page.llmSectionCard
        const pipelineSection = page.pipelineSectionCard
        const githubSection = page.githubSectionCard

        verify(scrollView !== null)
        verify(llmSection !== null)
        verify(pipelineSection !== null)
        verify(githubSection !== null)
        verify(scrollView.width > 780)
        verify(llmSection.width >= 320)
        verify(pipelineSection.width >= 320)
        verify(githubSection.width > 780)
        compare(pipelineSection.y, llmSection.y)
        verify(pipelineSection.x > llmSection.x)
        verify(githubSection.y > llmSection.y)

        shell.destroy()
    }

    function test_settingsPageStacksTopCardsOnNarrowWidth() {
        const shell = createSettingsShell(1180, 760)
        const page = findChild(shell, "settingsPage")
        verify(page !== null)
        const llmSection = page.llmSectionCard
        const pipelineSection = page.pipelineSectionCard
        const githubSection = page.githubSectionCard

        verify(llmSection !== null)
        verify(pipelineSection !== null)
        verify(githubSection !== null)
        verify(pipelineSection.y > llmSection.y)
        compare(pipelineSection.x, llmSection.x)
        verify(githubSection.y > pipelineSection.y)
        verify(llmSection.width > 700)
        verify(pipelineSection.width > 700)

        shell.destroy()
    }
}
