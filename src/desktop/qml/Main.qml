import QtQuick
import QtQuick.Controls

ApplicationWindow {
    id: window
    objectName: "desktopQmlWindow"
    visible: false
    width: 1440
    height: 960
    minimumWidth: 1180
    minimumHeight: 760
    title: "AI Daily"

    DesktopShell {
        id: desktopShell
        objectName: "desktopShell"
        anchors.fill: parent
        shellFacade: appShellFacade
        settingsFacade: desktopSettingsFacade
        githubFacade: desktopGithubFacade
        digestFacade: desktopDigestFacade
    }
}
