# AI Daily — 开发计划

> 最后更新：2026-03-03
> 目标：实现一个每日自动抓取 AI 资讯、经 LLM 两阶段筛选与摘要、生成日报，并通过 Web 界面提供历史浏览、过滤、搜索功能的完整系统。

---

## 当前状态

| 模块 | 文件 | 状态 |
|---|---|---|
| RSS 抓取器 | `src/fetcher.py` | ✅ 完成 |
| 工具函数 | `src/utils.py` | ✅ 完成 |
| Stage 1 Prompt | `prompts/stage1_filter.txt` | ✅ 完成 |
| Stage 2 Prompt | `prompts/stage2_summary.txt` | ✅ 完成 |
| 配置文件 | `config.yaml` | ✅ 完成 |
| **LLM 调用层** | `src/llm.py` | ❌ 未实现 |
| **主入口 / Pipeline** | `main.py` | ❌ 未实现 |
| **报告渲染** | `src/reporter.py` | ❌ 未实现 |
| **Web 后端** | `src/server/` | ❌ 未实现 |
| **Web 前端** | `frontend/` | ❌ 未实现 |

---

## 待办任务（按优先级）

### 🔴 P0 — 核心功能（跑通 pipeline）

#### 1. 实现 `src/llm.py` — LLM 调用层
- 封装 OpenAI 兼容 API 调用（支持 siliconflow / newapi 两个 provider）
- 从 `config.yaml` 读取 `base_url`、`api_key_env`、`model`、`temperature`、`max_tokens`
- 用 `tenacity` 做指数退避重试（网络抖动、rate limit）
- 提供两个函数：
  - `call_stage1(prompt: str) -> list[str]`：返回筛选出的 URL 列表
  - `call_stage2(prompt: str) -> dict`：返回结构化摘要 JSON
- JSON 解析失败时有容错处理（返回 None，由上层跳过该文章）

#### 2. 实现 `src/reporter.py` — Markdown 报告渲染
- 接收 Stage 2 处理完的文章列表（含 `summary_zh`、`tags`、`importance`）
- 按 `importance` 降序排列
- 生成结构化 Markdown，参考格式：
  ```
  # AI Daily — 2026-03-03

  ## ⭐ 重点关注
  ### [文章标题](url)
  > 来源：OpenAI Blog · 标签：`LLMs` · 重要性：5/5
  > 一句话摘要内容。

  ## 📰 其他值得关注
  ...
  ```
- 输出到 `output/{date}.md`

#### 3. 实现 `main.py` — 主入口与 Pipeline 编排
- 加载 `config.yaml`
- 初始化 logger（调用 `utils.setup_logger`）
- 调用 `FeedFetcher.run()` 拿到候选文章列表
- **Stage 1**：将文章标题分批（`stage1_batch_size`）渲染 prompt，调用 LLM，合并返回的 URL 列表
- 根据 Stage 1 结果过滤文章，限制数量为 `max_articles_to_stage2`
- **Stage 2**：用 `asyncio.Semaphore`（`stage2_concurrency`）并发处理每篇文章，渲染 prompt，调用 LLM
- 调用 `reporter.py` 生成最终报告
- 调用 `FeedFetcher.save_state()` 持久化已处理 URL
- 打印运行摘要（处理了多少篇、过滤掉多少、报告路径）

---

### 🟡 P1 — 重要改进（影响长期稳定性）

#### 4. 修复 `seen_urls` 无限膨胀问题
- **问题**：`data/state.json` 只追加 URL，永远不清理，长期运行后文件会很大
- **方案**：将存储格式从 `{seen_urls: [...]}` 改为 `{url: "首次见到的ISO时间戳"}`，每次加载时过滤掉超过 7 天的记录
- 改动文件：`src/fetcher.py` 的 `load_state()` 和 `save_state()`

#### 5. 添加 `--dry-run` 模式
- 只执行抓取，打印候选文章列表，不调用 LLM、不写文件
- 用于调试 RSS 源是否正常

---

### 🟢 P2 — 可选优化

#### 6. 抓取原文正文（提升 Stage 2 摘要质量）
- **问题**：RSS 的 content 字段往往只有摘要，新闻类文章尤其如此，LLM 基于 500 字片段写摘要准确性有限
- **方案**：对 `category: news` 或 `official` 的文章，用 `httpx` 抓取原文 HTML，用 `readability-lxml` 提取正文，替换 `content` 字段
- 需要新增依赖：`readability-lxml`
- 注意：Arxiv 的 abstract 已经足够，不需要抓全文

#### 7. 支持中文信息源
- 当前信息源全是英文 RSS
- 可考虑接入：
  - **微信公众号**：通过 RSSHub 自建或第三方聚合（如 FeedDD）转 RSS
  - **量子位 / 机器之心**：检查是否有官方 RSS
  - **知乎专栏**：通过 RSSHub 转换

#### 8. 邮件 / 消息推送
- 生成日报后，通过 SMTP 发送邮件，或推送到 Telegram Bot / 企业微信
- 在 `config.yaml` 里增加 `notifications` 配置块

#### 9. 添加基础测试
- `tests/test_fetcher.py`：测试 `is_within_time_window`、`apply_arxiv_prefilter`
- `tests/test_utils.py`：测试 `clean_html_tags`、`truncate_text`
- `tests/test_llm.py`：用 mock 测试 JSON 解析容错逻辑

---

## 项目最终目录结构（目标态）

```
D:\ai daily\
├── main.py                  # 主入口
├── config.yaml              # 配置（RSS源、LLM、pipeline参数）
├── requirements.txt
├── PLAN.md                  # 本文件
├── prompts/
│   ├── stage1_filter.txt
│   └── stage2_summary.txt
├── src/
│   ├── __init__.py
│   ├── fetcher.py           # RSS 抓取
│   ├── llm.py               # LLM 调用层（待实现）
│   ├── reporter.py          # 报告渲染，MD + JSON 双输出（待实现）
│   ├── utils.py             # 工具函数
│   └── server/              # Web 后端（待实现）
│       ├── __init__.py
│       ├── main.py          # FastAPI app 入口，挂载静态文件
│       ├── api.py           # 路由：/api/dates, /api/digest/{date}
│       ├── schemas.py       # Pydantic 响应模型
│       └── loader.py        # 读取 output/*.json，lru_cache 缓存
├── frontend/                # Vue 3 前端（待实现）
│   ├── package.json
│   ├── vite.config.ts       # 开发代理 /api → localhost:8000
│   └── src/
│       ├── App.vue
│       ├── router/index.ts
│       ├── stores/digest.ts # Pinia：过滤状态 + queryParams computed
│       ├── views/
│       │   ├── HomeView.vue    # 日报列表（历史浏览）
│       │   └── DigestView.vue  # 单日详情 + 左侧过滤器
│       └── components/
│           ├── ArticleCard.vue
│           ├── TagFilter.vue
│           ├── CategoryFilter.vue
│           ├── ImportanceSlider.vue
│           └── SearchBar.vue
├── data/
│   └── state.json           # 已处理 URL 去重状态（运行时生成）
├── output/                  # 运行时生成
│   ├── 2026-03-03.md
│   ├── 2026-03-03.json      # 供前端消费的结构化数据
│   └── 2026-03-03.log
└── tests/                   # 测试（P2）
    ├── test_fetcher.py
    ├── test_utils.py
    └── test_llm.py
```

---

## 运行方式（目标）

```bash
# 安装 Python 依赖（新增 fastapi、uvicorn）
pip install -r requirements.txt

# 设置 API Key（以 siliconflow 为例）
export SILICONFLOW_API_KEY=sk-xxxx

# 运行日报生成（每日执行）
python main.py

# 调试模式（只抓取，不调用 LLM）
python main.py --dry-run

# 构建前端（首次或前端代码变更后执行）
cd frontend && npm install && npm run build && cd ..

# 启动 Web 服务
uvicorn src.server.main:app --host 0.0.0.0 --port 8000
# 访问 http://localhost:8000
```

---

## Web 前端架构说明

### 整体架构

```
浏览器
  │
  ▼
FastAPI (uvicorn :8000)
  ├── /api/dates              ← 返回所有可用日期列表
  ├── /api/digest/{date}      ← 返回单日日报（支持过滤/排序/搜索）
  └── /（其余所有路径）        ← 返回 Vue SPA 的 index.html
```

### reporter.py 输出的 JSON 格式

```json
{
  "date": "2026-03-03",
  "generated_at": "2026-03-03T22:14:00+08:00",
  "stats": {
    "total": 18,
    "by_category": {"arxiv": 8, "news": 5, "official": 3, "community": 2},
    "by_tag": {"LLMs": 10, "研究": 7, "CV": 4}
  },
  "articles": [
    {
      "id": "a1b2c3",
      "title": "...",
      "url": "...",
      "published": "2026-03-03T08:00:00Z",
      "source_name": "Arxiv cs.CL",
      "source_category": "arxiv",
      "summary_zh": "...",
      "tags": ["LLMs", "研究"],
      "importance": 5
    }
  ]
}
```

### /api/digest/{date} 查询参数

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `tags` | list[str] | [] | 标签过滤，OR 关系 |
| `category` | str | null | arxiv/news/official/community |
| `min_importance` | int | 1 | 最低重要性（1-5） |
| `sort` | str | importance | importance 或 published |
| `q` | str | null | 全文搜索（title + summary_zh） |

过滤/排序/搜索逻辑全部在 Python 后端处理，前端只负责渲染。

### 前端技术选型

| 层次 | 选型 | 理由 |
|---|---|---|
| 框架 | Vue 3 + Composition API + TypeScript | 轻量，官方推荐 |
| 构建 | Vite 5 | 冷启动快，HMR 即时 |
| 路由 | Vue Router 4 | 官方标配 |
| 状态 | Pinia | 比 Vuex 简单 |
| UI | Naive UI | 中文友好，含所需组件 |
