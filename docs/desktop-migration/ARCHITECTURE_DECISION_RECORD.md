# Desktop Migration ADR

## ADR-001: Desktop UI Direction
Decision:
- Desktop 主线采用 `PySide6 + QML + Qt Quick Controls`
- Python 继续作为桌面后端与 application service 层
- 不切到 WebView/Tauri/Electron

Why:
- 目标是原生 Windows 工作台，不是浏览器壳
- 现有 Python 内容管线、配置、keyring、打包链已成熟
- QML 更适合做导航壳、长任务状态、原生桌面交互

Consequences:
- Desktop 与 Web 共享契约和语义，不共享 UI 组件
- 需要引入 QML 宿主、QRC、Qt Quick Test

## ADR-002: Canonical Contracts
Decision:
- `src/contracts/` 是唯一 canonical schema source
- `src/server/schemas.py` 仅作 adapter/re-export
- `frontend/src/types` 由 `scripts/export_contracts.py` 生成

Why:
- 避免 Web、Desktop、FastAPI 三处字段漂移
- 让 Pydantic/JSON Schema 直接驱动前端类型和校验契约

Consequences:
- 前端类型不再长期手写
- CI 必须检查生成物是否过期

## ADR-003: Application Service Layer
Decision:
- 将 `ApplicationServices` 拆为 query/execution/configuration/sync 四类服务
- 当前桌面主线由 QML runtime 通过 gateway/facade 调用服务

Why:
- 当前旧页面过胖，混合了 view、状态、任务编排与持久化
- 迁移需要先抽出稳定调用面，避免 UI 改写牵动内容管线

Consequences:
- `src/services/` 成为 UI 之上的服务层
- `src/desktop/facades/**`、`src/desktop/models/**`、`src/desktop/tasks/**` 是当前 QML-only 桌面的桥接层
- QWidget 只保留为已结束迁移阶段的历史背景，不再是现行运行时前提

## ADR-004: QML Runtime And Resource System
Decision:
- QML 资源清单统一维护在 `src/desktop/resources.qrc`
- 宿主在 `src/desktop/qml_app.py` 中通过 `QResource.registerResource(...)` 注册 `src/desktop/resources.rcc`
- `Main.qml`、页面、组件、icons、fonts、`qtquickcontrols2.conf` 全部走 `qrc:/`

Why:
- Windows + PyInstaller + 路径含空格环境下，相对路径最不稳定
- 二进制资源包比提交超大 Python 资源模块更适合当前仓库与打包链

Consequences:
- 新增 `pyside6-rcc` 编译步骤
- 删除/新增 QML 资源时必须同步更新 `.qrc`
- PyInstaller 必须持续打包 `src/desktop/resources.rcc`
- `tests/test_desktop_qml_smoke.py` 与 `tests/test_desktop_packaging_smoke.py` 负责回归资源链路

## ADR-005: Testing Layers
Decision:
- QML 组件/页面测试使用 Qt Quick Test
- Python services/facades/models 测试继续使用 pytest
- CI 锁定 `PySide6==6.8.1.1`

Why:
- QML 页面需要真实控件层验证
- Python 逻辑更适合维持 pytest 生态

Consequences:
- 存在两层测试命令，但都纳入 CI
- 当前 workflow 还会继续覆盖 PyInstaller 构建、packaged payload、default-qml startup 和 widgets-removed 合同

## ADR-006: Theme Strategy
Decision:
- 阶段 2~4 默认 `Basic`
- `Fusion` 作为备用样式
- `FluentWinUI3` 不作为 parity 依赖

Why:
- 先追求可加载、可测试、可迁移，不抢跑视觉实验

Consequences:
- 视觉表达依赖 design tokens，而不是依赖某个复杂 style backend

## ADR-007: State Ownership
Decision:
- `selection / expanded / busy / error / stale / filters` 归 facade/model
- delegate 不存业务状态

Why:
- 旧 QWidget 页面的核心问题就是状态散落在页面对象和局部控件里
- 迁移到 QML 后必须先固化状态归属，否则列表联动和恢复机制会继续失控

Consequences:
- 后续 GitHub/Digest 迁移必须优先补 facade/model，不允许先写“聪明 delegate”
