# AI Daily Desktop Migration Plan

## Scope
- Desktop mainline is `PySide6 + QML + Qt Quick Controls`.
- The visual direction remains `quiet editorial desktop product UI`.
- `src/contracts/` remains the single contract source.
- GitHub token handling remains `github_trending.token_env: GITHUB_TOKEN`.
- Desktop acceptance continues to prefer isolated runtime roots instead of global user state.

## Status Snapshot
- Phase 0-5: completed
- Phase 6A: completed
- Phase 6B: completed, gate review passed
- R19: closed on `2026-04-17`
- Phase 6C: completed on `2026-04-17`
  - execution readiness baseline: completed
  - soft retirement round 1: completed
  - soft retirement round 2: completed
  - remove execution round 1: completed
  - remove execution round 2: completed

## Current Baseline
- Desktop runtime is now `qml-only`.
- `desktop_main.py` only resolves QML launchers.
- Explicit `AI_DAILY_DESKTOP_UI=widgets` now fails fast with `RemovedDesktopUiModeError`.
- The legacy QWidget runtime has been physically removed:
  - `src/desktop/app.py`
  - `src/desktop/widgets.py`
  - `src/desktop/theme.py`
- The active desktop contract is now:
  - runtime entry: `desktop_main.py`
  - QML host: `src/desktop/qml_app.py`
  - shell/pages/components/resources: `src/desktop/qml/**`
  - facades/models/tasks/workers: `src/desktop/facades/**`, `src/desktop/models/**`, `src/desktop/tasks/**`, `src/desktop/workers.py`
  - tests: `tests/test_desktop_entry.py`, `tests/test_desktop_packaging_smoke.py`, `tests/test_desktop_qml_smoke.py`, `tests/test_desktop_qml_quick.py`
  - CI: `.github/workflows/desktop-qml-smoke.yml`
- Product implementation boundaries remain frozen:
  - no change to the three QML workspaces
  - no change to GitHub fetch/save/status chains
  - no change to Web/server surfaces

## Phase 6C Outcome
- Remove execution round 1 retired the `widgets` runtime contract without deleting files.
- Remove execution round 2 deleted the dead QWidget runtime code and removed the last active legacy smoke.
- `tests/test_desktop_ui_smoke.py` has been removed because there is no remaining QWidget runtime contract to observe.
- `src/desktop/__init__.py` now exposes QML runtime helpers instead of the deleted QWidget launcher.

## Verification (2026-04-17)
- `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_desktop_entry.py tests\\test_desktop_packaging_smoke.py -q`
  - `12 passed in 0.03s`
- `.\\.venv\\Scripts\\python.exe -m pytest tests -q -rA`
  - `132 passed in 8.24s`
- `.\\.venv\\Scripts\\python.exe scripts\\export_contracts.py --check`
  - passed
- `.\\.venv\\Scripts\\pyinstaller.exe -y "build\\windows\\AI Daily.spec"`
  - passed
- Minimal source/dist observation after round 2:
  - source default QML smoke: passed
  - dist default QML smoke: passed
  - source explicit `AI_DAILY_DESKTOP_UI=widgets` removed-contract: passed
  - dist explicit `AI_DAILY_DESKTOP_UI=widgets` removed-contract: passed

## Evidence Directories
- `output/phase6a-review/`
- `output/phase6b-round1/`
- `output/phase6b-round2/`
- `output/phase6b-round2-r19/`
- `output/phase6c-baseline/`
- `output/phase6c-soft-retirement-round1/`
- `output/phase6c-soft-retirement-round2/`
- `output/phase6c-remove-execution-round1/`
- `output/phase6c-remove-execution-round2/`

## Round 2 Evidence
- `output/phase6c-remove-execution-round2/remove-execution-round2-summary.json`
  - `defaultQmlStable=true`
  - `widgetsRuntimeRemoved=true`
  - `qwidgetRuntimeDeleted=true`
- `output/phase6c-remove-execution-round2/source-default-qml.png`
- `output/phase6c-remove-execution-round2/dist-default-qml.png`
- `output/phase6c-remove-execution-round2/source-widgets-removed.txt`
- `output/phase6c-remove-execution-round2/dist-widgets-removed.txt`

## Immediate Next Step
- Phase 6C is closed.
- Future desktop work should stay on the QML-only contract.
- If desktop entry, packaging, or runtime behavior changes again, re-validate against:
  - `tests/test_desktop_entry.py`
  - `tests/test_desktop_packaging_smoke.py`
  - `tests/test_desktop_qml_smoke.py`
  - `tests/test_desktop_qml_quick.py`
  - minimal source/dist QML smoke
