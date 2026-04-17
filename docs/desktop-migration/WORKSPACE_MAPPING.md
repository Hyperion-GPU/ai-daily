# Workspace Mapping

## Workspace Overview

| Workspace | Current Modules | Current Responsibility Shape |
| --- | --- | --- |
| AI Daily | `DigestWorkspaceFacade`, `DigestArchiveListModel`, `DigestArticleListModel`, `src/desktop/qml/pages/AIDailyPage.qml`, `src/desktop/tasks/digest_command_gateway.py` (`DigestCommandGateway`) | facade/model own archive state, selection, filters, fetch outcomes, and detail data; QML page renders the reading workbench |
| GitHub Trends | `GithubWorkspaceFacade`, `GithubSnapshotListModel`, `GithubProjectListModel`, `src/desktop/qml/pages/GithubTrendsPage.qml`, `src/desktop/tasks/github_command_gateway.py` (`GithubCommandGateway`) | facade/model own snapshot state, filters, fetch outcomes, stale semantics, and selected project detail; QML page renders the three-pane workbench |
| Settings | `SettingsFacade`, `src/desktop/qml/pages/SettingsPage.qml`, `src/desktop/tasks/settings_gateway.py` (`SettingsCommandGateway`) | facade owns form state, validation, busy/error/stale semantics, and persistence actions; QML page renders grouped settings forms |

## Shared Shell / Runtime Mapping
- `src/desktop/qml_app.py`
  - creates the desktop runtime
  - wires `ApplicationServices`
  - instantiates shell/settings/digest/github facades
  - injects facade objects into the QML context
- `src/desktop/facades/shell.py`
  - owns selected workspace and shell-level metadata
- `src/desktop/qml/Main.qml`
  - boots the QML shell
- `src/desktop/qml/DesktopShell.qml`
  - hosts workspace navigation and page switching

## AI Daily Current Mapping
- Facade responsibilities:
  - current archive date
  - current article selection
  - filter state
  - busy/error/notice semantics
  - fetch success / no-new-items / failure handling
- Command gateway:
  - file: `src/desktop/tasks/digest_command_gateway.py`
  - class: `DigestCommandGateway`
- Model responsibilities:
  - archive list rows
  - article list rows
  - selection roles
- QML page responsibilities:
  - file: `src/desktop/qml/pages/AIDailyPage.qml`
  - page header
  - quiet summary bar
  - filter/list/detail workbench layout
  - actions that delegate to the facade

## GitHub Trends Current Mapping
- Facade responsibilities:
  - current snapshot date
  - current project selection
  - category/language/trend/min-stars/search/sort filters
  - stale/apply semantics
  - fetch outcome and notice tone
- Command gateway:
  - file: `src/desktop/tasks/github_command_gateway.py`
  - class: `GithubCommandGateway`
- Model responsibilities:
  - snapshot list rows
  - project list rows
  - selection and metadata roles
- QML page responsibilities:
  - file: `src/desktop/qml/pages/GithubTrendsPage.qml`
  - snapshot rail
  - filters/list/detail workbench layout
  - actions that delegate to the facade

## Settings Current Mapping
- Facade responsibilities:
  - editable settings snapshot
  - provider switching semantics
  - validation summary
  - save/test/open-dir actions
- Command gateway:
  - file: `src/desktop/tasks/settings_gateway.py`
  - class: `SettingsCommandGateway`
- QML page responsibilities:
  - file: `src/desktop/qml/pages/SettingsPage.qml`
  - grouped forms
  - stable action row
  - quiet editorial spacing and hierarchy

## Active Test Coverage
- Runtime entry:
  - `tests/test_desktop_entry.py`
- Packaging:
  - `tests/test_desktop_packaging_smoke.py`
- Source runtime and shell:
  - `tests/test_desktop_qml_smoke.py`
- Qt Quick page-level checks:
  - `tests/test_desktop_qml_quick.py`
- Workspace logic:
  - `tests/test_digest_workspace_facade.py`
  - `tests/test_github_workspace_facade.py`
  - `tests/test_settings_facade.py`

## Historical Note
- The old QWidget shell is no longer part of this mapping.
- Removed in Phase 6C remove execution round 2:
  - `src/desktop/app.py`
  - `src/desktop/widgets.py`
  - `src/desktop/theme.py`
- Deleted legacy test:
  - `tests/test_desktop_ui_smoke.py`

## Working Rule Going Forward
- Keep workspace responsibilities split across:
  - QML page for composition
  - facade for state and commands
  - models for list data and selection roles
- Page object names such as `aiDailyWorkspace`, `githubWorkspace`, and `settingsWorkspace` remain valid UI test anchors, but the authoritative page file names are `AIDailyPage.qml`, `GithubTrendsPage.qml`, and `SettingsPage.qml`.
- Do not reintroduce page-level business orchestration back into a monolithic desktop shell.
