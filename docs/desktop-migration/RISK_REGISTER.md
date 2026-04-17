# Desktop Migration Risk Register

## Current Register

| ID | Risk | Current Status | Latest Mitigation / Note |
| --- | --- | --- | --- |
| R2 | Contract drift returns | mitigated | `scripts/export_contracts.py --check` remains in the verification set and CI. |
| R3 | Resource bundle drift | open | Keep `src/desktop/resources.qrc`, `src/desktop/resources.rcc`, `tests/test_desktop_qml_smoke.py`, and `tests/test_desktop_packaging_smoke.py` aligned in the desktop review checklist. |
| R5 | Settings touches runtime paths or secrets storage unexpectedly | mitigated | Shared runtime/settings tests and facade tests remain green. |
| R6 | QML state leaks back into delegates/pages | open | Continue enforcing facade/model state ownership and keep page code thin. |
| R7 | PyInstaller or QML packaging regresses after QWidget removal | mitigated | `.github/workflows/desktop-qml-smoke.yml`, `tests/test_desktop_packaging_smoke.py`, and `scripts/check_packaged_desktop.py` now cover packaged payload, default-qml startup, and widgets-removed checks. |
| R8 | Mixed Qt application types crash the suite | mitigated | Desktop test stack remains on the current `QApplication`-safe setup. |
| R9 | GitHub snapshot hydration or list metadata drifts | open | Keep GitHub facade/model tests and manual workspace walkthroughs in release checks. |
| R10 | GitHub stale/apply-filters semantics drift | open | Retain facade tests plus manual stale/apply verification in future desktop release passes. |
| R11 | GitHub degraded fetch semantics become unclear again | open | R19 remains the baseline for degraded/recovery behavior and should be reused if fetch logic changes. |
| R13 | AI Daily tag/filter semantics drift | open | Preserve current facade tests and avoid folding tag semantics into ad-hoc page logic. |
| R14 | AI Daily dual-query semantics regress | open | Keep current digest facade/gateway tests and avoid collapsing raw/filtered flows without explicit design. |
| R15 | Quiet editorial reading surface drifts toward dashboard UI | mitigated | Keep design review anchored to the current QML workbench baseline. |
| R17 | Settings provider switching loses provider-scoped values | mitigated | Existing settings facade tests remain the regression net. |
| R18 | Successful AI Daily fetch does not reselect the latest archive | mitigated | Existing digest workspace tests cover success / no-new-items / failure semantics. |
| R19 | GitHub authenticated fetch baseline regresses before a future release | closed | Closed on `2026-04-17`; evidence remains in `output/phase6b-round2-r19/`. |

## Phase 6C Remove Execution Round 2 Closeout (2026-04-17)
- R4 closed:
  - QWidget/QML dual-entry divergence is no longer a live risk because the runtime is now QML-only and the old QWidget shell has been deleted.
- R12 closed:
  - GitHub workspace runtime is no longer coupled to parked QWidget code because the parked code has been physically removed.
- R16 closed:
  - AI Daily no longer carries residual QWidget runtime files; round 2 removed the dead shell and its legacy smoke/doc references.
- R7 remains mitigated rather than closed:
  - packaging still needs to stay in the normal desktop regression checklist, but the current workflow and closeout script already verify packaged payload, default-qml startup, and widgets-removed behavior.

## Verification Attached To The Closeout
- GitHub-hosted clean environment:
  - `.github/workflows/desktop-qml-smoke.yml` 已真实通过打包、payload、default-qml startup、widgets-removed 这四个收官检查。
- `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_desktop_entry.py tests\\test_desktop_packaging_smoke.py -q`
  - `12 passed in 0.03s`
- `.\\.venv\\Scripts\\python.exe -m pytest tests -q -rA`
  - `132 passed in 8.24s`
- `.\\.venv\\Scripts\\python.exe scripts\\export_contracts.py --check`
  - passed
- `.\\.venv\\Scripts\\pyinstaller.exe -y "build\\windows\\AI Daily.spec"`
  - passed
- `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_desktop_packaging_smoke.py -q`
  - passed
- `.\\.venv\\Scripts\\python.exe scripts\\check_packaged_desktop.py --mode default-qml --localappdata-root ".\\localappdata\\aid-closeout-default"`
  - passed
- `.\\.venv\\Scripts\\python.exe scripts\\check_packaged_desktop.py --mode widgets-removed --localappdata-root ".\\localappdata\\aid-closeout-widgets"`
  - passed
- `output/phase6c-remove-execution-round2/remove-execution-round2-summary.json`
  - confirms default QML source/dist smoke and explicit `widgets` removed-contract evidence in source/dist
