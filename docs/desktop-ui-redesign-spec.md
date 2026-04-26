# Desktop UI Redesign Spec

## Positioning
- `current screenshots = IA/function reference only`
- `target style = quiet editorial desktop product UI`
- This redesign keeps the current information architecture, data density, and feature mapping, but replaces the old backend-template visual language with a calmer reading-workspace UI.
- Art-direction source: `ui-ux-pro-max` was used as a design-intelligence reference, anchored to `Editorial Grid / Magazine`, `E-Ink / Paper`, and `Minimalism & Swiss Style`.

## Frontend Skill Thesis
- Visual thesis: a warm, trustworthy desktop workspace that feels closer to modern publishing software than an admin dashboard.
- Content plan:
  1. Page header for orientation and one primary action.
  2. Quiet summary bar for inline metrics and background task status.
  3. Three-column workspace for archive/filter rail, reading list, and report-style detail panel.
- Interaction thesis:
  1. Active navigation and selected rows use subtle fill plus fine border, not heavy highlight blocks.
  2. Progress feedback stays visible but quiet inside the summary bar.
  3. Detail panels preserve context while lists update, so the interface feels steady rather than jumpy.

## Style Guardrails
- Use warm white / parchment / oat / muted stone as the main color family.
- Prioritize typography, spacing, thin borders, and stable hierarchy over cards, shadows, and decorative effects.
- Avoid neon, strong gradients, glassmorphism, dark heavy sidebars, KPI mosaics, and marketing-style hero sections.
- Keep icons monochrome and optional; scanning should mostly come from type, grouping, and spacing.

## Color Tokens
- `paper.base`: `#f4efe7`
- `paper.canvas`: `#f8f4ed`
- `paper.surface`: `#fbf8f2`
- `paper.elevated`: `#fffdf9`
- `paper.inset`: `#eee7dc`
- `paper.strong`: `#e5ddd0`
- `line.default`: `#dad1c4`
- `line.soft`: `#e6ded1`
- `line.faint`: `#efe8dd`
- `ink.strong`: `#1f1b17`
- `ink.body`: `#49423a`
- `ink.soft`: `#756c61`
- `ink.faint`: `#958a7d`
- `ink.hint`: `#aca193`
- `accent.default`: `#b4805e`
- `accent.hover`: `#9f6f50`
- `accent.pressed`: `#895d42`
- `accent.soft`: `#f1e5d8`
- `accent.text`: `#865d45`

## Typography Scale
- Display / page title: `28px`, serif stack, semibold
- Section title: `17px`, serif stack, semibold
- Row title: `15px`, sans stack, semibold
- Body: `13px`, sans stack, regular
- Detail body: `13px`, sans stack, line-height `1.85`
- Note / supporting copy: `12px`, muted sans
- Eyebrow / meta key / metric label: `11px`, uppercase, high letter spacing

### Font stacks
- Editorial serif: `Georgia, Songti SC, Noto Serif CJK SC, serif`
- UI sans: `Segoe UI, Microsoft YaHei UI, PingFang SC, sans-serif`

## Spacing Scale
- `4`: micro spacing inside tight label stacks
- `6`: tag spacing
- `8`: row internal rhythm
- `12`: default control gap
- `14`: list item bottom gap
- `16`: compact card padding
- `18`: section internal padding
- `22`: detail / summary bar padding
- `24`: page vertical rhythm unit
- `28`: page outer margin

## Radius / Border / Elevation
- Control radius: `12`
- Panel radius: `16`
- Tag radius: `999`
- Default border: `1px solid line.soft`
- Selected border: `1px solid accent.default`
- Elevation rule: no drop shadows by default; hierarchy comes from paper tone and border contrast

## Component System

### `SidebarNav`
- Role: tool-directory navigation, not website sidebar
- Structure: brand, short subtitle, 3 page destinations
- Selected state: subtle fill + fine border
- Mapping: `QListWidget`

### `QuietButton`
- Variants: `primary`, `secondary`, `quiet`
- Primary: muted clay fill
- Secondary: paper-surface fill with border
- Quiet: transparent with light border
- Mapping: `QPushButton`

### `SearchInput`
- Quiet field chrome, clear button enabled
- Mapping: `QLineEdit`

### `InlineMetric`
- Small vertical label/value unit inside one summary bar
- No standalone KPI cards
- Mapping: `QFrame + QLabel`

### `StatusRow`
- Text plus slim progress bar for long-running tasks
- Mapping: `QFrame + QLabel + QProgressBar`

### `SectionFrame`
- Reusable panel shell for filter rail, list area, and form groups
- Mapping: `QFrame + QVBoxLayout`

### `ReadingListRow`
- Title, source/date line, short summary, 2-4 quiet tags
- Mapping: `QListWidget` item widget

### `RepoListRow`
- Repository name, description preview, quiet tags, trailing stars line
- Mapping: `QListWidget` item widget

### `DetailPanel`
- Eyebrow, large title, 2-column metadata grid, flowing body copy, one primary action
- Mapping: `QFrame + QLabel + QTextBrowser + QPushButton`

### `FormSection`
- Clear heading, short note, grouped `QFormLayout`
- Mapping: `QFrame + QFormLayout`

### `Tag`
- Monochrome / clay accent pill for category, trend, importance, topic
- Mapping: `QLabel`

## State Model
- `default`: warm paper surfaces, soft border, no shadow
- `hover`: slightly brighter paper tone
- `selected`: accent border plus subtle fill
- `disabled`: paper-strong background and hint text
- `empty`: plain explanatory copy in list/detail area, no decorative empty illustration
- `loading`: progress remains in the summary bar; workspace can keep current data visible for continuity

## Screen Specs

### 1. AI 日报
- Header:
  - Eyebrow: `AI Daily / Digest`
  - Title: `AI 日报`
  - Primary action: `抓取今日日报`
- Summary bar:
  - Metrics: `归档天数`, `当前文章`, `最新日期`
  - Status row on the right for pipeline progress
- Workspace:
  - Left rail: date archive + filters
  - Center: reading list, no table chrome
  - Right: report-style detail panel with title, meta grid,正文节奏, action

### 2. GitHub 趋势
- Header:
  - Eyebrow: `AI Daily / GitHub`
  - Title: `GitHub 趋势`
  - Primary action: `抓取最新趋势`
- Summary bar:
  - Metrics: `快照数量`, `当前项目`, `最新日期`
  - Status row for fetch progress
- Workspace:
  - Left rail: snapshot dates + filters
  - Center: repository reading list with preview text and tags
  - Right: detail panel with repository identity, trend meta, description, topics, action

### 3. 设置
- Header:
  - Eyebrow: `AI Daily / Settings`
  - Title: `设置`
- Main body:
  - Two-column top: `LLM`, `Pipeline`
  - Full-width bottom: `GitHub Trending`
  - Bottom action bar with guidance copy and three actions
- Principle:
  - No oversized blank hero
  - Form fields grouped by intent, not just by available space

## PySide6 Widget Mapping
- Sidebar nav: `QListWidget`
- Archive list / reading list / repository list: `QListWidget + setItemWidget`
- Inputs: `QLineEdit`, `QComboBox`, `QSpinBox`, `QCheckBox`
- Summary status: `QProgressBar`
- Detail body: `QTextBrowser`
- Panels / sections / summary bar: `QFrame`
- Primary actions: `QPushButton`
- Page shell switching: `QStackedWidget`
- Workspace resizing: `QSplitter`

## Acceptance Checklist
- The UI reads like a calm workbench, not a SaaS admin dashboard.
- Top-level metrics feel inline and restrained, not like KPI cards.
- Lists are scannable as reading queues rather than data grids.
- Detail panels have clear typographic rhythm and one obvious action.
- Settings uses grouped sections with minimal wasted whitespace.
- Sidebar activation is subtle and tool-like.
- Empty and loading states remain quiet and informative.
