# Desktop QML-Only Closeout

## 当前现态
- 桌面端已经收口为 `QML-only`，运行时栈是 `PySide6 + QML + Qt Quick Controls`。
- `desktop_main.py` 只解析 QML 启动器，`src/desktop/qml_app.py` 是唯一桌面宿主。
- 显式 `AI_DAILY_DESKTOP_UI=widgets` 会直接抛出 `RemovedDesktopUiModeError`；`widgets` 现在只是 removed-contract，不再是受支持模式或可恢复桌面模式。
- 资源链路已经统一为 `src/desktop/resources.qrc` 清单 + `src/desktop/resources.rcc` 运行时注册；桌面宿主通过 `QResource.registerResource(...)` 注册二进制资源包。
- 旧 QWidget 运行时代码已经删除：
  - `src/desktop/app.py`
  - `src/desktop/widgets.py`
  - `src/desktop/theme.py`
- 旧 legacy smoke 已删除：`tests/test_desktop_ui_smoke.py`

## 当前主线合同
- 入口：`desktop_main.py`
- QML 宿主：`src/desktop/qml_app.py`
- 包级导出：`src/desktop/__init__.py`
- 主线测试：
  - `tests/test_desktop_entry.py`
  - `tests/test_desktop_packaging_smoke.py`
  - `tests/test_desktop_qml_smoke.py`
  - `tests/test_desktop_qml_quick.py`
- CI：`.github/workflows/desktop-qml-smoke.yml`
- 打包：`build/windows/AI Daily.spec`
- 打包后启动检查：`scripts/check_packaged_desktop.py`

## Release Readiness
- 当前 `desktop-qml-smoke` workflow 已在 GitHub-hosted clean environment 上真实通过，桌面收官口径不再存在“待远端验证”的空白。
- 当前 workflow 覆盖：
  - `Run desktop QML mainline smoke suite`
  - `Build packaged desktop`
  - `Verify packaged desktop payload`
  - `Verify packaged desktop default QML startup`
  - `Verify packaged desktop removed widgets contract`
- 本地 closeout 仍以同一条主线复现：
  - 源码态 QML 主线 smoke
  - `pyinstaller -y "build/windows/AI Daily.spec"`
  - `python -m pytest tests/test_desktop_packaging_smoke.py -q`
  - `scripts/check_packaged_desktop.py --mode default-qml`
  - `scripts/check_packaged_desktop.py --mode widgets-removed`

## 验证快照
- `.\.venv\Scripts\python.exe -m pytest tests\test_desktop_entry.py tests\test_desktop_packaging_smoke.py -q`
  - `12 passed in 0.03s`
- `.\.venv\Scripts\python.exe -m pytest tests -q -rA`
  - `132 passed in 8.24s`
- `.\.venv\Scripts\python.exe scripts\export_contracts.py --check`
  - passed
- `.\.venv\Scripts\pyinstaller.exe -y "build\windows\AI Daily.spec"`
  - passed

Round 2 证据位于 `output/phase6c-remove-execution-round2/`，其中：
- `remove-execution-round2-summary.json`
  - `defaultQmlStable=true`
  - `widgetsRuntimeRemoved=true`
  - `qwidgetRuntimeDeleted=true`
- `source-widgets-removed.txt`
- `dist-widgets-removed.txt`

## 维护与排障
- 源码态桌面入口：`.\.venv\Scripts\python.exe desktop_main.py`
- 打包命令：`.\.venv\Scripts\pyinstaller.exe -y "build\windows\AI Daily.spec"`
- 冻结包验证：
  - `.\.venv\Scripts\python.exe -m pytest tests\test_desktop_packaging_smoke.py -q`
  - `.\.venv\Scripts\python.exe scripts\check_packaged_desktop.py --mode default-qml --localappdata-root ".\localappdata\aid-closeout-default"`
  - `.\.venv\Scripts\python.exe scripts\check_packaged_desktop.py --mode widgets-removed --localappdata-root ".\localappdata\aid-closeout-widgets"`
- 用户可写桌面数据根目录：`%LOCALAPPDATA%\AI Daily\`
  - 包含配置、输出、日志和状态文件
- 若用户报告桌面启动问题，优先核对：
  - `%LOCALAPPDATA%\AI Daily\` 下的日志与状态文件
  - `tests/test_desktop_entry.py`
  - `tests/test_desktop_packaging_smoke.py`
  - `.github/workflows/desktop-qml-smoke.yml`
  - `scripts/check_packaged_desktop.py`

## 后续策略
- 未来桌面迭代应基于 QML-only 合同，而不是继续迁移或恢复 QWidget 回退路径。
- `AI_DAILY_DESKTOP_UI` 不再作为功能开关扩展；当前仅保留 `widgets` 的 fail-fast 移除提示。
- 资源、打包、测试、CI 的维护优先级依次是：
  - 保持 `resources.qrc` 与 `resources.rcc` 一致
  - 保持 PyInstaller 打包清单包含 `src/desktop/resources.rcc`
  - 保持 `tests/test_desktop_packaging_smoke.py` 与 `scripts/check_packaged_desktop.py` 继续覆盖冻结包合同
  - 不再把 QWidget 回退路径当作发布前兜底
