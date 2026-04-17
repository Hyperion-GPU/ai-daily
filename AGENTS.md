# AI Daily Repo Guidance

本仓库的桌面主线已经收口为 `PySide6 + QML + Qt Quick Controls`。
桌面 UI 目标仍是 `quiet editorial desktop product UI`：安静、克制、可阅读，像思考空间与编辑工作台，而不是通用 SaaS 后台。

## Desktop Baseline
- 桌面运行时是 `QML-only`，不再保留 QWidget 运行时回退路径。
- `AI_DAILY_DESKTOP_UI=widgets` 只保留 removed-contract，用于 fail-fast 验证；不要把它当作可恢复模式。
- 桌面入口在 `desktop_main.py`。
- QML 宿主在 `src/desktop/qml_app.py`。
- 壳、页面、组件、资源在 `src/desktop/qml/**`。
- 桌面状态与命令桥接在 `src/desktop/facades/**`、`src/desktop/models/**`、`src/desktop/tasks/**`、`src/desktop/workers.py`。
- 旧 QWidget 运行时文件 `src/desktop/app.py`、`src/desktop/widgets.py`、`src/desktop/theme.py` 已删除，不要按这些路径继续开发。

## Long-Term Constraints
- 桌面验收尽量走隔离运行环境，不碰全局配置。
- GitHub token 不写进 `config.yaml`，继续走 `github_trending.token_env: GITHUB_TOKEN`。
- 不要改三工作区 QML 页面，除非任务明确要求。
- 不要动 Web、server、GitHub fetch/save/status 链路，除非任务明确要求。

## Visual Direction
- 只做暖中性色浅色主题：warm white / parchment / oat / muted stone。
- 优先用字体层级、留白、轻边框和面层关系建立信息层次，不靠强阴影和大色块。
- 页面应像阅读工作台，不像 KPI 卡片墙、管理后台或营销着陆页。
- 导航、摘要条、筛选区、列表、详情面板要共享一致的节奏、圆角、边框和状态语言。

## Screen Rules
- `AI Daily` 与 `GitHub Trends` 优先保持 workbench 结构：页头、安静摘要条、筛选/列表/详情。
- 列表要去表格化、去卡片化，强调标题、元信息、摘要节奏与安静 tag。
- 详情面板应像阅读面，而不是操作面板；底部动作清晰但不过分抢眼。
- `Settings` 使用分组表单与稳定的 action row，避免大面积空白 hero。

## Change Discipline
- 优先在共享 QML token、共享组件和 facade/model 边界上建立统一规则，再做页面级编排。
- 不要为视觉重构改动 `src/services/`、抓取逻辑、配置语义或 signal-slot 行为，除非任务明确要求。
- 尽量保留已有 `objectName`、页面 key、页面切换和 smoke/quick test 可验证的 UI 契约；若必须调整，连同测试一起更新。
- 当前主线桌面合同以 `desktop_main.py`、`src/desktop/qml_app.py`、`tests/test_desktop_entry.py`、`tests/test_desktop_packaging_smoke.py`、`tests/test_desktop_qml_smoke.py`、`tests/test_desktop_qml_quick.py`、`build/windows/AI Daily.spec`、`.github/workflows/desktop-qml-smoke.yml` 为准。
