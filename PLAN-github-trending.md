# GitHub 热门 AI 项目资讯 — 功能计划

> 最后更新：2026-03-16
> 状态：计划阶段，待审阅

---

## 一、功能概述

在 AI Daily 现有的「每日 AI 资讯日报」基础上，新增一个独立页面 **"GitHub AI Trending"**，定期抓取 GitHub 上高 Star AI 项目的最新动态，以图文并茂、视觉丰富的卡片式布局呈现给用户。用户也可以通过页面上的**手动增量获取按钮**主动触发数据刷新，获取过程通过 iOS 风格的进度卡片实时展示。

核心价值：
- 聚焦 **AI/ML 领域**高星项目，帮助用户快速发现值得关注的开源工具、框架和模型
- 提供项目的关键指标（Stars、Forks、近期增长趋势等），让用户一目了然
- 沿用 AI Daily 的暖色调视觉风格，保持品牌一致性
- 支持已有的**深色/浅色模式切换**和**中英文切换**
- 用户可手动触发增量获取，带有精致的 iOS 风格进度反馈

---

## 二、接口契约（前后端共识）

本节定义前后端之间的数据格式和 API 接口，双方均以此为准。

### 2.1 数据模型：`GitHubProject`

```json
{
  "id": "langchain-ai/langchain",
  "full_name": "langchain-ai/langchain",
  "description": "Build context-aware reasoning applications",
  "description_zh": "构建上下文感知的推理应用",
  "html_url": "https://github.com/langchain-ai/langchain",
  "homepage": "https://langchain.com",
  "stars": 98000,
  "forks": 15600,
  "open_issues": 1200,
  "language": "Python",
  "topics": ["llm", "ai-agent", "langchain"],
  "category": "llm",
  "created_at": "2022-10-25T...",
  "updated_at": "2026-03-16T...",
  "pushed_at": "2026-03-16T...",
  "owner_avatar": "https://avatars.githubusercontent.com/...",
  "owner_type": "Organization",
  "license": "MIT",
  "stars_today": 120,
  "stars_weekly": 890,
  "trend": "rising"
}
```

`trend` 取值规则：
- `hot`：近 7 天 Star 增长 > 500
- `rising`：近 7 天 Star 增长 > 100
- `stable`：其他

`stars_today` 和 `stars_weekly` 在首次运行无历史数据时为 `null`。

### 2.2 数据模型：`trending-{date}.json` 快照格式

```json
{
  "date": "2026-03-16",
  "generated_at": "2026-03-16T10:00:00+08:00",
  "stats": {
    "total": 50,
    "by_category": {"llm": 15, "agent": 8, "cv": 10},
    "by_language": {"Python": 35, "TypeScript": 8}
  },
  "projects": [ /* GitHubProject[] */ ]
}
```

### 2.3 API 端点

| 端点 | 方法 | 说明 |
|---|---|---|
| `GET /api/github/trending` | GET | 返回最新一期的热门项目列表（支持筛选） |
| `GET /api/github/trending/{date}` | GET | 返回指定日期的快照 |
| `GET /api/github/dates` | GET | 返回所有可用的快照日期列表 |
| `POST /api/github/fetch` | POST | 手动触发一次增量抓取 |
| `GET /api/github/fetch/status` | GET | 查询抓取进度（前端以 3s 间隔轮询） |

**`GET /api/github/trending` 查询参数：**

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `category` | string | null | 按 AI 子分类筛选（llm/agent/cv/nlp/ml_framework/mlops/general） |
| `language` | string | null | 按编程语言筛选 |
| `min_stars` | int | 0 | 最低 Star 数 |
| `sort` | string | `stars` | `stars` / `stars_today` / `stars_weekly` / `updated` |
| `q` | string | null | 搜索项目名或描述 |
| `trend` | string | null | `rising` / `hot` / `stable` |

**`POST /api/github/fetch` 响应：**
- 成功启动：`200 { "status": "started" }`
- 已在运行：`409 { "detail": "Fetch is already running" }`

**`GET /api/github/fetch/status` 响应：**

```json
{
  "running": true,
  "last_run": "2026-03-16T10:00:00+08:00",
  "error": null,
  "last_outcome": null,
  "progress": {
    "stage": "searching",
    "message": "Searching topic: llm",
    "current": 3,
    "total": 12,
    "topics_done": 3,
    "topics_total": 12,
    "projects_found": 128,
    "projects_new": 15
  }
}
```

进度阶段（`stage`）取值：

| stage | 含义 | 说明 |
|---|---|---|
| `starting` | 初始化 | 加载配置和历史数据 |
| `searching` | 搜索中 | 逐 topic 调用 GitHub Search API |
| `deduplicating` | 去重合并 | 多 topic 结果去重 |
| `computing_trends` | 计算趋势 | 对比历史数据计算增长值 |
| `saving` | 写入快照 | 保存 JSON 到 output/github/ |
| `completed` | 完成 | 抓取结束 |
| `error` | 失败 | 出错终止 |

**`GET /api/github/dates` 响应：**

```json
{
  "dates": ["2026-03-16", "2026-03-15", "2026-03-14"],
  "latest": "2026-03-16"
}
```

### 2.4 AI 子分类（category）枚举

| category | 含义 | 匹配的 topics |
|---|---|---|
| `llm` | 大语言模型 | llm, large-language-model, chatgpt, gpt, langchain |
| `agent` | AI 智能体 | ai-agent, autonomous-agent, agent |
| `cv` | 计算机视觉 | computer-vision, image-generation, diffusion-model |
| `nlp` | 自然语言处理 | natural-language-processing, text-generation |
| `ml_framework` | ML 框架 | machine-learning, deep-learning, transformers |
| `mlops` | MLOps | mlops, model-serving, inference |
| `general` | 通用 AI | artificial-intelligence, generative-ai |

---

## Part A：后端实现（Python / FastAPI）

> 本部分可由后端开发者独立完成。
> 交付物：所有 API 端点按上述接口契约可正常调用。

### A.1 数据来源

使用 GitHub REST API v3 的 `/search/repositories` 接口，按 AI 相关 topics 搜索高星项目：

| 接口 | 用途 | 频率 |
|---|---|---|
| `GET /search/repositories?q=topic:artificial-intelligence+stars:>1000&sort=stars` | 搜索 AI 主题高星项目 | 每日 1 次 |
| `GET /search/repositories?q=topic:machine-learning+stars:>500&sort=updated` | 近期活跃的 ML 项目 | 每日 1 次 |
| `GET /search/repositories?q=topic:llm OR topic:large-language-model+stars:>300&sort=stars` | LLM 领域项目 | 每日 1 次 |
| `GET /search/repositories?q=topic:deep-learning+stars:>500&sort=stars` | 深度学习项目 | 每日 1 次 |

从 API 返回中提取的字段：`full_name`、`description`、`html_url`、`homepage`、`stargazers_count`、`forks_count`、`open_issues_count`、`language`、`topics`、`created_at`、`updated_at`、`pushed_at`、`owner.avatar_url`、`owner.type`、`license.spdx_id`。

无需 OAuth，公共数据即可。建议配置 Token 以避免限流（未认证 60 次/小时，认证后 5000 次/小时）。

### A.2 趋势计算

为了展示"热度趋势"，需要存储历史数据并做差值计算：
- **每日快照**：每天保存一份各项目的 `stars`、`forks` 数据
- **趋势字段**：
  - `stars_today`: 今日新增 Star = 今日 stars - 昨日 stars
  - `stars_weekly`: 近 7 天新增 Star
  - `trend`: 根据近 7 天增速判定（规则见 2.1）

### A.3 数据存储

```
output/
  github/
    trending-{date}.json     # 每日快照（格式见 2.2）
    history.json              # 最近 30 天历史（用于趋势计算）
```

### A.4 新增模块

```
src/
  github/
    __init__.py
    fetcher.py      # GitHub API 抓取与数据整合
    categories.py   # topic → category 映射规则（见 2.4 的映射表）
```

### A.5 `src/github/fetcher.py` — GitHub 数据采集器

核心类 `GitHubTrendingFetcher`：
- 从 `config.yaml` 读取 GitHub Token（可选）和搜索配置
- 调用 GitHub Search API，按 topics 列表逐个搜索
- **进度回调**：每完成一个 topic 的搜索，通过 `progress_callback` 汇报当前进度（和现有 `run_pipeline` 的 `progress_callback` 模式一致）
- 去重合并（同一 repo 可能命中多个 topic）
- 根据 `categories.py` 的映射规则为每个项目分配 `category`
- 加载历史数据，计算 `stars_today`、`stars_weekly`、`trend`
- **增量合并逻辑**：如果当天已有快照，新数据与已有数据合并（新项目追加，已有项目更新 stars 等指标），而非覆盖
- 用已有 LLM 管线为每个项目生成 `description_zh`（中文描述翻译）—— 可选优化，初版可跳过
- 写入 `output/github/trending-{date}.json`

### A.6 `config.yaml` 新增配置块

```yaml
github_trending:
  enabled: true
  token_env: "GITHUB_TOKEN"            # 可选，不设也能用（60次/小时限制）
  min_stars: 500                        # 最低 Star 门槛
  max_projects_per_day: 50              # 每日最多展示项目数
  fetch_interval_hours: 12              # 抓取间隔（避免频繁调用）
  topics:
    - artificial-intelligence
    - machine-learning
    - deep-learning
    - llm
    - large-language-model
    - natural-language-processing
    - computer-vision
    - diffusion-model
    - generative-ai
    - ai-agent
    - transformers
    - mlops
  category_map:
    llm: ["llm", "large-language-model", "chatgpt", "gpt", "langchain"]
    agent: ["ai-agent", "autonomous-agent", "agent"]
    cv: ["computer-vision", "image-generation", "diffusion-model"]
    nlp: ["natural-language-processing", "text-generation"]
    ml_framework: ["machine-learning", "deep-learning", "transformers"]
    mlops: ["mlops", "model-serving", "inference"]
    general: ["artificial-intelligence", "generative-ai"]
```

### A.7 新增 API 路由

在 `src/server/api.py` 中新增 `/api/github/*` 路由，参考现有的 `/api/pipeline/*` 模式实现。具体端点和响应格式见第二节接口契约。

关键实现点：
- `POST /api/github/fetch`：启动后台 `asyncio.Task`，使用 `asyncio.Lock` 防止并发，模式与现有 `run_pipeline_endpoint` 一致
- `GET /api/github/fetch/status`：读取模块级变量返回进度状态
- `GET /api/github/trending`：读取本地 JSON + 服务端过滤/排序（和现有 `get_digest` 模式一致）

### A.8 新增 Pydantic Schemas

在 `src/server/schemas.py` 中新增：`GitHubProject`、`GitHubTrendingResponse`、`GitHubDateListResponse`、`GitHubFetchStatusResponse`、`GitHubFetchProgressResponse` 等模型。

### A.9 新增 Loader

在 `src/server/loader.py` 中新增：
- `list_github_dates()` — 列出 `output/github/` 下所有日期
- `load_github_trending(date)` — 加载指定日期的快照 JSON

### A.10 后端实现步骤

| 步骤 | 文件 | 内容 |
|---|---|---|
| 1 | `config.yaml` | 添加 `github_trending` 配置块 |
| 2 | `src/github/__init__.py` | 空模块文件 |
| 3 | `src/github/categories.py` | topic → category 映射逻辑 |
| 4 | `src/github/fetcher.py` | 实现 `GitHubTrendingFetcher` 类（含进度回调 + 增量合并） |
| 5 | `src/server/schemas.py` | 新增 GitHub 相关 Pydantic 模型 |
| 6 | `src/server/loader.py` | 新增 `list_github_dates()`、`load_github_trending()` |
| 7 | `src/server/api.py` | 新增 `/api/github/*` 路由（5 个端点） |
| 8 | `tests/test_github_fetcher.py` | GitHub fetcher 单元测试 |
| 9 | `tests/test_api.py` | 新 API 端点测试 |

### A.11 后端注意事项

- **GitHub API 限流**：未认证 60 次/小时，认证后 5000 次/小时。建议用户配置 `GITHUB_TOKEN`。搜索 12 个 topics 约消耗 12 次请求，远在限额内。
- **Search API 结果上限**：每次最多返回 1000 条。通过多 topic 搜索 + 去重合并来覆盖更多项目。
- **增量合并**：同日多次 fetch 时合并而非覆盖，趋势数据基于当天第一次快照和最新快照的差值重新计算。
- **无需新增 Python 依赖**：`httpx`（已有）用于调用 GitHub API，`fastapi`、`pydantic`（已有）。

---

## Part B：前端实现（Vue 3 / TypeScript / Naive UI）

> 本部分可由前端开发者独立完成。
> 前提：后端 API 已按接口契约可用（或用 mock 数据开发）。

### B.1 新增路由

在 `router/index.ts` 中新增两条路由：
- `/github` → `GithubTrendingView` 组件（默认加载最新日期）
- `/github/:date` → 同一组件，通过 `props: true` 接收日期参数

### B.2 导航入口

在 `App.vue` 的 header 中添加导航链接。在现有 "AI Daily" 标题右侧、语言切换按钮左侧，增加两个文字导航链接："日报"（指向 `/`）和 "GitHub"（指向 `/github`），用分隔符分开，当前激活的链接使用主色调高亮。点击标题仍回到首页。

### B.3 新增文件清单

```
frontend/src/
  views/
    GithubTrendingView.vue     # 主页面
  components/
    ProjectCard.vue            # 项目卡片（核心视觉组件）
    TrendBadge.vue             # 趋势徽章（rising/hot/stable）
    StatsBar.vue               # Stars/Forks 统计面板
    LanguageDot.vue            # 编程语言色点标识
    FetchProgressCard.vue      # iOS 风格抓取进度卡片（含动效进度条）
  stores/
    github.ts                  # Pinia store
```

类型定义追加到现有 `frontend/src/types/index.ts` 中。
API 调用函数追加到现有 `frontend/src/api/index.ts` 中。

### B.4 页面整体布局描述

`GithubTrendingView.vue` 的页面采用与现有 `DigestView` 一致的双栏布局结构。

**顶部区域**：居中显示页面标题"GitHub AI Trending"（衬线字体，36px）和副标题描述（灰色辅助文字）。标题下方居中放置一个 primary 色的圆角大按钮"获取最新数据"，按钮样式与 HomeView 的"获取今日资讯"按钮一致。按钮下方是 FetchProgressCard 进度卡片区域（仅在抓取进行中展示，带展开/收起动画）。

**主体区域**：左右双栏。左侧是 280px 宽的筛选面板（固定宽度，粘性定位），包含：搜索输入框、AI 分类选择器（下拉，选项为：全部 / LLM / Agent / CV / NLP / ML 框架 / MLOps / 通用 AI）、编程语言选择器（下拉多选，选项从当前数据中动态提取）、Stars 范围滑块（500 ~ 200k）、趋势筛选（单选按钮组：全部 / 火热 / 上升中 / 平稳）、排序方式（单选按钮组：Stars 总数 / 今日增长 / 本周增长 / 最近更新）、底部统计卡片显示当前匹配的项目总数。右侧是项目卡片列表，纵向排列，每张卡片之间 24px 间距。

**响应式**：桌面端（>900px）左右双栏；平板端（640-900px）筛选面板折叠到顶部；手机端（<640px）单列卡片，筛选面板收起为可展开的抽屉。

### B.5 `ProjectCard.vue` — 项目卡片组件

每张项目卡片是一个 16px 圆角、带 1px 边框的容器，内部 padding 32px。整体视觉风格与现有 `ArticleCard` 保持一致（相同的阴影层级、hover 上浮效果、边框色系）。

**卡片顶部**：左侧是项目所有者的 48x48 圆形头像（加载失败时用首字母彩色圆形占位），头像右侧是两行文字——第一行是项目全名（如 `langchain-ai / langchain`），使用衬线字体、24px、加粗，可点击跳转到 GitHub；第二行是英文简介（灰色辅助文字）。卡片右上角是趋势徽章组件 `TrendBadge`。

**卡片中部**：中文描述段落（如有），使用正文字号 16px，行高 1.7。

**统计面板 `StatsBar`**：在描述下方是一个浅色背景（暗色模式下略深一层）的统计区域，内含三列数字——Stars（金色图标）、Forks（绿色图标）、Issues（紫色图标），每列包含图标 + 大数字 + 标签。统计区域下方显示今日增长（如 `+120 today`）和本周增长（如 `+890 this week`），增长数字为绿色。

**卡片底部**：左侧是一行元信息——编程语言色点（`LanguageDot`，8px 圆点使用 GitHub 官方语言颜色）+ 语言名称、许可证名、相对更新时间。底部分割线下方，左侧是 topics 标签（沿用现有 `#tag` 文本样式），右侧是"查看项目"链接按钮（外链到 GitHub）。

**动效**：Hover 时整体向上浮动 4px 并加深阴影（沿用 ArticleCard）。进入时使用 `animate-fade-up` + 交错延迟（每张卡片延迟 50ms）。

### B.6 子组件说明

**`TrendBadge.vue`**：小型圆角胶囊标签，接收 `trend` prop。`hot` 为红色渐变背景 + 白色文字，`rising` 为橙色（主色调）渐变背景 + 白色文字，`stable` 为灰色背景。

**`StatsBar.vue`**：一个圆角 12px 的面板，背景使用 `var(--n-body-color)`，三列布局显示 Stars / Forks / Issues 的数字和标签，下方显示今日/本周增量。

**`LanguageDot.vue`**：接收 `language` prop，渲染一个 8px 圆点（颜色使用 GitHub 官方语言颜色映射，如 Python=#3572A5, TypeScript=#3178c6, Rust=#dea584, C++=#f34b7d）+ 语言名称文字。

### B.7 手动增量获取按钮 + iOS 风格进度卡片

这是用户主动触发数据刷新的核心交互组件，参考现有 HomeView 的 pipeline 获取模式，但视觉上做差异化，融入 iOS 设计语言。

#### B.7.1 获取按钮

位于页面标题下方居中位置。使用 Naive UI 的 `NButton`（`type="primary" secondary round size="large"`）。空闲态显示刷新图标 + "获取最新数据"文字；运行态自动切换为 `loading` 旋转动画 + "正在获取..."文字，按钮置为禁用。如果用户在运行态重复点击，弹出 `message.warning` 提示"已在获取中"。按钮点击后调用 `POST /api/github/fetch`，如果收到 409 则开始轮询已有进度。

#### B.7.2 `FetchProgressCard.vue` — iOS 风格进度卡片

点击获取按钮后，在按钮下方展开显示进度卡片，抓取完成后自动收起隐藏。

**整体外观**：采用 iOS 毛玻璃风格的容器——半透明白色背景（`rgba(255,255,255,0.72)`），叠加 `backdrop-filter: blur(20px) saturate(180%)` 模糊效果，20px 大圆角，内侧顶部有一道微弱的白色高光（`inset 0 1px 0 rgba(255,255,255,0.5)`），外侧有柔和的多层阴影。暗色模式下背景改为半透明深色（`rgba(30,29,28,0.72)`），高光和阴影相应调暗。

**卡片内容从上到下**：

1. **标题行**：左侧一个带脉冲呼吸动画的小圆点（10px，主色调，外圈有一个从 scale(1) 到 scale(1.8) 的淡出脉冲环，2s 循环），右侧文字"正在获取 GitHub AI 项目数据..."。

2. **阶段描述**：显示当前阶段和详细信息，如"搜索中 · topic: large-language-model"，灰色辅助文字。阶段切换时文字使用 crossfade 淡入淡出过渡。

3. **进度条**：自定义 iOS 风格胶囊进度条，不使用 Naive UI 的 NProgress。轨道高度 8px，背景为极淡灰色（暗色模式下为极淡白色），圆角 4px。填充条使用从主色调 `#cc7b5d` 到金色 `#d4aa50` 的水平渐变，宽度变化使用 `cubic-bezier(0.25, 0.1, 0.25, 1)` 缓动动画（0.6s）。填充条上有一道半透明白色光泽从左到右循环扫过的 shimmer 动画（2s 循环），营造 iOS 特有的"活跃"感。进度条右侧或下方显示百分比数字。

4. **统计标签行**：显示 "3 / 12 topics" 和 "已发现 128 个项目" / "其中 15 个为新增"。数字使用 `requestAnimationFrame` 驱动的计数滚动动画（从旧值滚动到新值，使用 ease-out 三次方缓动，持续 400ms），给人数字跳动的活力感。

**展开/收起动画**：使用 Vue 的 `<Transition>` 组件。展开时从 `opacity:0, max-height:0, scale(0.97), translateY(-8px)` 弹出到正常状态，0.45s，使用 `cubic-bezier(0.32, 0.72, 0, 1)` 曲线，在 60% 处微微超过 `scale(1.005)` 后回弹——模拟 iOS 弹性动画。收起时反向播放，0.35s。

**完成态**：进度条达到 100% 后停留 1.5s，然后卡片收起，同时弹出 `message.success("数据已刷新")`，按钮恢复正常态，项目列表自动重新加载。

**错误态**：进度条变为红色，显示错误信息，停留 3s 后收起。

#### B.7.3 完整交互流程

1. 用户点击"获取最新数据"按钮
2. 调用 `POST /api/github/fetch`，如果 409 则 warning 提示并开始轮询已有进度
3. 按钮切换为 loading 态，进度卡片弹性展开
4. 每 3 秒轮询 `GET /api/github/fetch/status`
   - `starting` → 显示"正在初始化..."
   - `searching` → 显示"搜索中 · topic: {名称}"，进度条 = topics_done / topics_total
   - `deduplicating` → 显示"正在去重合并..."，进度条 85%
   - `computing_trends` → 显示"正在计算趋势数据..."，进度条 92%
   - `saving` → 显示"正在保存数据..."，进度条 98%
   - `completed` → 进度条 100%，停留 1.5s → 收起 → success toast → 刷新列表
   - `error` → 进度条变红 → 显示错误 → 3s 后收起

#### B.7.4 增量逻辑（前端视角）

- 获取完成后调用 `store.refreshTrendingData()` 刷新列表
- 用户无需手动刷新页面，列表会自动更新
- 如果页面初始化时检测到后端正在运行（status.running === true），自动展示进度卡片并开始轮询

### B.8 配色方案

沿用现有美术风格的主色调（Primary `#cc7b5d`，星级金色 `#d4aa50`），新增以下配色：

| 用途 | 浅色模式 | 深色模式 |
|---|---|---|
| Stars 高亮 | `#d4aa50` | `#d4aa50` |
| 趋势 HOT 背景 | `rgba(220, 80, 60, 0.12)` | `rgba(220, 80, 60, 0.20)` |
| 趋势 RISING 背景 | `rgba(204, 123, 93, 0.12)` | `rgba(204, 123, 93, 0.20)` |
| 增长数字（正） | `#4caf50` | `#66bb6a` |
| Forks 图标 | `#6b8e6b` | `#81a881` |
| Issue 图标 | `#827397` | `#9688ab` |
| 进度条渐变 | `#cc7b5d → #d4aa50` | 同左 |

### B.9 i18n 文案

在 `useLocale.ts` 的 `MESSAGES` 中新增 `github` 命名空间：

**英文：**
```typescript
github: {
  // 页面
  pageTitle: 'GitHub AI Trending',
  pageDescription: 'Discover the most popular AI open-source projects on GitHub.',
  // 筛选
  search: 'Search',
  searchPlaceholder: 'Search project name or description...',
  category: 'Category',
  language: 'Language',
  minStars: 'Minimum Stars',
  sort: 'Sort by',
  sortStars: 'Stars',
  sortStarsToday: 'Today',
  sortStarsWeekly: 'This week',
  sortUpdated: 'Recently updated',
  trend: 'Trend',
  trendAll: 'All',
  trendHot: 'Hot',
  trendRising: 'Rising',
  trendStable: 'Stable',
  // 卡片
  stars: 'Stars',
  forks: 'Forks',
  issues: 'Issues',
  starsToday: 'today',
  starsWeekly: 'this week',
  viewProject: 'View project',
  updatedAgo: 'Updated {time} ago',
  // 分类名
  categoryAll: 'All',
  categoryLLM: 'LLM',
  categoryAgent: 'AI Agent',
  categoryCV: 'Computer Vision',
  categoryNLP: 'NLP',
  categoryFramework: 'ML Framework',
  categoryMLOps: 'MLOps',
  categoryGeneral: 'General AI',
  // 获取操作
  fetchData: 'Fetch latest data',
  fetchRunning: 'Fetching...',
  fetchAlreadyRunning: 'Already fetching',
  fetchSuccess: 'Data refreshed.',
  fetchError: 'Fetch failed.',
  // 进度卡片
  progressTitle: 'Fetching GitHub AI project data...',
  progressStarting: 'Initializing...',
  progressSearching: 'Searching',
  progressDedup: 'Deduplicating...',
  progressTrends: 'Computing trends...',
  progressSaving: 'Saving data...',
  progressCompleted: 'Completed',
  progressError: 'Failed',
  progressTopics: 'topics',
  progressFound: 'projects found',
  progressNew: 'new',
  // 统计
  visibleResults: 'Total projects',
  items: 'projects',
  empty: 'No projects match the current filters.',
}
```

**中文：**
```typescript
github: {
  pageTitle: 'GitHub AI 热门项目',
  pageDescription: '发现 GitHub 上最值得关注的 AI 开源项目。',
  search: '搜索',
  searchPlaceholder: '搜索项目名或描述...',
  category: 'AI 分类',
  language: '编程语言',
  minStars: '最低 Stars',
  sort: '排序',
  sortStars: 'Stars 总数',
  sortStarsToday: '今日增长',
  sortStarsWeekly: '本周增长',
  sortUpdated: '最近更新',
  trend: '趋势',
  trendAll: '全部',
  trendHot: '火热',
  trendRising: '上升中',
  trendStable: '平稳',
  stars: 'Stars',
  forks: 'Forks',
  issues: 'Issues',
  starsToday: '今日',
  starsWeekly: '本周',
  viewProject: '查看项目',
  updatedAgo: '{time}前更新',
  categoryAll: '全部',
  categoryLLM: '大语言模型',
  categoryAgent: 'AI 智能体',
  categoryCV: '计算机视觉',
  categoryNLP: '自然语言处理',
  categoryFramework: 'ML 框架',
  categoryMLOps: 'MLOps',
  categoryGeneral: '通用 AI',
  fetchData: '获取最新数据',
  fetchRunning: '正在获取...',
  fetchAlreadyRunning: '已在获取中',
  fetchSuccess: '数据已刷新。',
  fetchError: '获取失败。',
  progressTitle: '正在获取 GitHub AI 项目数据...',
  progressStarting: '正在初始化...',
  progressSearching: '搜索中',
  progressDedup: '正在去重合并...',
  progressTrends: '正在计算趋势数据...',
  progressSaving: '正在保存数据...',
  progressCompleted: '已完成',
  progressError: '失败',
  progressTopics: '个 topic',
  progressFound: '个项目已发现',
  progressNew: '个为新增',
  visibleResults: '项目总数',
  items: '个项目',
  empty: '当前筛选条件下没有匹配的项目。',
}
```

### B.10 前端实现步骤

| 步骤 | 文件 | 内容 |
|---|---|---|
| 1 | `frontend/src/types/index.ts` | 新增 `GitHubProject`、`GitHubTrendingData`、`GitHubFetchStatus` 等类型 |
| 2 | `frontend/src/api/index.ts` | 新增 `getGithubTrending()`、`getGithubDates()`、`triggerGithubFetch()`、`getGithubFetchStatus()` |
| 3 | `frontend/src/stores/github.ts` | 新增 Pinia store（参考现有 `digest.ts` 的结构） |
| 4 | `frontend/src/composables/useLocale.ts` | 在 MESSAGES 中添加 `github` 命名空间 |
| 5 | `frontend/src/components/LanguageDot.vue` | 编程语言色点组件 |
| 6 | `frontend/src/components/TrendBadge.vue` | 趋势徽章组件 |
| 7 | `frontend/src/components/StatsBar.vue` | 统计面板组件 |
| 8 | `frontend/src/components/FetchProgressCard.vue` | iOS 风格进度卡片（毛玻璃 + shimmer 进度条 + 脉冲点 + 数字滚动） |
| 9 | `frontend/src/components/ProjectCard.vue` | 项目卡片主组件（组合以上子组件） |
| 10 | `frontend/src/views/GithubTrendingView.vue` | GitHub 热门主页面 |
| 11 | `frontend/src/router/index.ts` | 添加 `/github` 和 `/github/:date` 路由 |
| 12 | `frontend/src/App.vue` | 在 header 添加"日报 / GitHub"导航链接 |

### B.11 前端注意事项

- **Owner 头像加载**：GitHub 头像来自 `avatars.githubusercontent.com`，部分网络环境加载缓慢。使用 `loading="lazy"` 属性，并提供首字母彩色圆形 fallback。
- **首次数据降级**：`stars_today` / `stars_weekly` 为 `null` 时，统计面板中隐藏增长数据行，只显示绝对值。`trend` 为 `null` 时不显示趋势徽章。
- **无需新增前端依赖**：`naive-ui`（已有）、`@vicons/ionicons5`（已有）、`dayjs`（已有）均可满足需求。
- **进入页面时检测运行状态**：`onMounted` 中调用 `getGithubFetchStatus()`，如果 `running === true` 则自动展开进度卡片并开始轮询。

---

## 三、可选的后续优化

以下功能不在 MVP 范围内，但可以作为后续迭代方向：

1. **LLM 生成中文描述**：调用已有 LLM 管线，为每个项目的英文 description 生成中文翻译
2. **项目详情页**：点击卡片展开 README 预览（通过 GitHub API 获取 README.md）
3. **收藏功能**：用户可以收藏感兴趣的项目（localStorage 或后端持久化）
4. **对比视图**：支持选中多个项目进行 Star 增长曲线对比
5. **RSS 输出**：为 GitHub 趋势数据生成 RSS feed，供其他工具订阅
6. **邮件推送**：与现有日报推送集成，每日发送 GitHub AI 热门项目摘要
7. **`AI Daily.bat` 集成**：在启动脚本中自动触发 GitHub 数据采集步骤（可选）

---

## 四、总结

此功能以"独立模块"形式接入现有 AI Daily 系统：
- **后端（Part A）**：新增 `src/github/` 模块，独立于现有 RSS 管线，共享 FastAPI 服务，可由后端开发者独立完成
- **前端（Part B）**：新增 `GithubTrendingView` 页面和 5 个子组件（ProjectCard、TrendBadge、StatsBar、LanguageDot、FetchProgressCard），通过路由切换，共享 App.vue 的主题和语言控制，可由前端开发者独立完成
- **数据**：独立存储在 `output/github/` 下，不影响现有日报数据
- **依赖**：零新增依赖，完全复用现有技术栈
- **接口契约**：前后端通过第二节定义的 API 接口和数据格式对接，双方可并行开发
