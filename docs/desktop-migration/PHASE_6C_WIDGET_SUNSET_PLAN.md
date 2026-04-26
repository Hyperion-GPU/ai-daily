# Phase 6C Widget Sunset Plan

## Summary
- Phase 6C is complete.
- The desktop runtime is now QML-only.
- `AI_DAILY_DESKTOP_UI=widgets` is no longer supported at runtime.
- The legacy QWidget shell has been physically deleted from the repository.

## Historical Timeline
- Execution readiness baseline (`2026-04-17`)
  - confirmed the pre-removal desktop baseline
  - evidence: `output/phase6c-baseline/`
- Soft retirement round 1 (`2026-04-17`)
  - downgraded `widgets` from supported fallback to deprecated fallback
  - evidence: `output/phase6c-soft-retirement-round1/`
- Soft retirement round 2 (`2026-04-17`)
  - slimmed legacy observation and separated packaging smoke from legacy smoke
  - evidence: `output/phase6c-soft-retirement-round2/`
- Remove execution round 1 (`2026-04-17`)
  - removed the runtime contract
  - kept old code parked for final deletion
  - evidence: `output/phase6c-remove-execution-round1/`
- Remove execution round 2 (`2026-04-17`)
  - physically deleted the old QWidget runtime
  - removed the last active legacy smoke and rewrote the migration docs to QML-only
  - evidence: `output/phase6c-remove-execution-round2/`

## Round 2 Final Reference Audit

### Deleted Runtime Files
- `src/desktop/app.py`
- `src/desktop/widgets.py`
- `src/desktop/theme.py`

### Deleted Legacy Test Contract
- `tests/test_desktop_ui_smoke.py`

### Updated Remaining Entry Surface
- `src/desktop/__init__.py`
  - now exports QML runtime helpers instead of the deleted QWidget launcher
- `tests/test_desktop_entry.py`
  - remains the runtime entry contract for QML-only behavior and removed `widgets` semantics

### Packaging / CI Surface
- `build/windows/AI Daily.spec`
  - remains QML-only and did not require a new QWidget cleanup branch
- `.github/workflows/desktop-qml-smoke.yml`
  - remains QML-only and continues to represent the active CI contract

## Round 2 Validation (2026-04-17)
- `.\\.venv\\Scripts\\python.exe -m pytest tests\\test_desktop_entry.py tests\\test_desktop_packaging_smoke.py -q`
  - `12 passed in 0.03s`
- `.\\.venv\\Scripts\\python.exe -m pytest tests -q -rA`
  - `132 passed in 8.24s`
- `.\\.venv\\Scripts\\python.exe scripts\\export_contracts.py --check`
  - passed
- `.\\.venv\\Scripts\\pyinstaller.exe -y "build\\windows\\AI Daily.spec"`
  - passed

## Round 2 Observation Evidence
- `output/phase6c-remove-execution-round2/remove-execution-round2-summary.json`
  - `defaultQmlStable=true`
  - `widgetsRuntimeRemoved=true`
  - `qwidgetRuntimeDeleted=true`
- `output/phase6c-remove-execution-round2/source-default-qml.png`
- `output/phase6c-remove-execution-round2/dist-default-qml.png`
- `output/phase6c-remove-execution-round2/source-widgets-removed.txt`
- `output/phase6c-remove-execution-round2/dist-widgets-removed.txt`

## Notes
- Source lane observation still uses child-process window probing.
  - Python source launch spawns a wrapper interpreter process before the visible desktop window appears.
- Dist removed-contract evidence was captured from redirected stderr.
  - The packaged process emitted the expected removed message before it self-terminated, so the evidence was captured and the process was then cleaned up by the probe.

## Out Of Scope
- No change to the three QML workspace pages
- No change to Web/server code
- No change to GitHub fetch/save/status product logic
- No new desktop features

## Closeout State
- There is no remaining QWidget runtime contract.
- There is no parked QWidget runtime code left in the repo.
- Any future desktop iteration should start from the QML-only baseline, not from fallback or sunset planning.
