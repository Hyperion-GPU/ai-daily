# Codebase Audit

## Current Baseline
- Desktop entry: `desktop_main.py`
- QML host: `src/desktop/qml_app.py`
- QML shell/pages/components/resources: `src/desktop/qml/**`
- Desktop facades/models/tasks: `src/desktop/facades/**`, `src/desktop/models/**`, `src/desktop/tasks/**`
- Shared desktop async helper: `src/desktop/workers.py`
- Canonical contracts: `src/contracts/**`
- Application services: `src/services/**`

## Historical Removal Note
- The legacy QWidget runtime was deleted in Phase 6C remove execution round 2 (`2026-04-17`):
  - `src/desktop/app.py`
  - `src/desktop/widgets.py`
  - `src/desktop/theme.py`

## Code Classification

### 1. Pure Python Core Business Logic
- `main.py`
- `src/fetcher.py`
- `src/llm.py`
- `src/reporter.py`
- `src/github/**`
- `src/runtime.py`
- `src/settings.py`
- `src/utils.py`
- `src/server/loader.py`

These modules remain Qt-agnostic.

### 2. Desktop QML Runtime And UI Composition
- `desktop_main.py`
- `src/desktop/qml_app.py`
- `src/desktop/qml/**`

This is the only live desktop runtime surface.

### 3. Desktop/Business Bridging Code
- `src/services/application.py`
- `src/services/digest.py`
- `src/services/github_trending.py`
- `src/services/execution.py`
- `src/services/configuration.py`
- `src/services/desktop_sync.py`
- `src/desktop/tasks/settings_gateway.py`
- `src/desktop/tasks/digest_command_gateway.py`
- `src/desktop/tasks/github_command_gateway.py`
- `src/desktop/facades/settings.py`
- `src/desktop/facades/shell.py`
- `src/desktop/facades/digest_workspace.py`
- `src/desktop/facades/github_workspace.py`
- `src/desktop/models/**`
- `src/desktop/workers.py`

### 4. Web-Only Frontend And API Adapters
- `frontend/**`
- `src/server/api.py`
- `src/server/schemas.py`

### 5. Shared DTO / Config / Error / Task Semantics
- `src/contracts/digest.py`
- `src/contracts/github.py`
- `src/contracts/jobs.py`
- `src/contracts/settings.py`
- `src/contracts/registry.py`
- `frontend/src/types/index.ts`

## Current Vs Target

| Area | Current | Target State |
| --- | --- | --- |
| Desktop UI runtime | QML-only + Qt Quick Controls | achieved |
| Shared contract source | `src/contracts/` only | achieved |
| Desktop state ownership | facade/model owns state, QML delegate renders | achieved |
| Resource loading | `resources.qrc` manifest + `resources.rcc` runtime registration | achieved |
| Desktop tests | QML entry/packaging/runtime layered smoke plus packaged startup checks | achieved |

## Active Desktop Contract
- Runtime:
  - `desktop_main.py`
  - `src/desktop/qml_app.py`
- Packaging:
  - `build/windows/AI Daily.spec`
- Tests:
  - `tests/test_desktop_entry.py`
  - `tests/test_desktop_packaging_smoke.py`
  - `tests/test_desktop_qml_smoke.py`
  - `tests/test_desktop_qml_quick.py`
- CI:
  - `.github/workflows/desktop-qml-smoke.yml`
- Validation helper:
  - `scripts/check_packaged_desktop.py`

## What No Longer Exists
- No alternate QWidget desktop runtime
- No QWidget/QSS theme layer
- No legacy desktop smoke dedicated to the deleted shell

## Recommended Audit Boundary Going Forward
- Keep desktop runtime reviews focused on:
  - entry semantics
  - QML resource integrity
  - facade/model ownership boundaries
  - packaging behavior
- Do not reintroduce QWidget-specific recovery planning unless a new explicit product decision reopens that path.
