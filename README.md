# AI Daily

AI Daily is a Python + FastAPI + Vue 3 project that builds a daily AI digest from RSS feeds.

## What it does

- Fetches AI-related RSS feeds from research, official blogs, news, and community sources.
- Filters candidate articles with a two-stage LLM pipeline.
- Generates daily Markdown and JSON reports in `output/`.
- Serves a small web UI for browsing, searching, and filtering digests.

## Project layout

- `main.py`: pipeline entrypoint
- `src/fetcher.py`: RSS fetching, dedupe state, optional full-text extraction
- `src/llm.py`: LLM calls and JSON normalization
- `src/reporter.py`: Markdown and JSON report generation
- `src/server/`: FastAPI API and SPA serving
- `frontend/`: Vue 3 frontend
- `prompts/`: Stage 1 and Stage 2 LLM prompts
- `tests/`: pytest coverage for core helpers

## Run locally

### Backend and pipeline

```powershell
.venv\Scripts\pip install -r requirements.txt
python main.py
```

Dry run without LLM calls:

```powershell
python main.py --dry-run
```

### Web app

```powershell
cd frontend
npm install
npm run build
cd ..
.venv\Scripts\uvicorn src.server.main:app --host 127.0.0.1 --port 8000
```

Then open `http://localhost:8000`.

### Desktop app

```powershell
.venv\Scripts\pip install -r requirements-desktop.txt
.venv\Scripts\python.exe desktop_main.py
```

Desktop mode opens a native Windows window and does not rely on a browser or local HTTP server.
The desktop runtime is now `QML-only` (`PySide6 + QML + Qt Quick Controls`).
`AI_DAILY_DESKTOP_UI=widgets` is no longer supported and now fails fast with a removed-mode error.
It is kept only as a removed-mode contract check and is no longer a recoverable desktop mode.

For local desktop verification, use the pinned Python 3.12 virtual environment tools instead of bare `python`.
The desktop mainline check and the packaged-app closeout are two separate steps:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_desktop_entry.py tests\test_desktop_packaging_smoke.py tests\test_desktop_qml_smoke.py tests\test_desktop_qml_quick.py -q
```

```powershell
.venv\Scripts\pyinstaller.exe -y "build\windows\AI Daily.spec"
build\windows\build-fast-launcher.ps1
.venv\Scripts\python.exe -m pytest tests\test_desktop_packaging_smoke.py -q
.venv\Scripts\python.exe scripts\check_packaged_desktop.py --mode default-qml --localappdata-root ".\localappdata\aid-closeout-default"
.venv\Scripts\python.exe scripts\check_packaged_desktop.py --mode widgets-removed --localappdata-root ".\localappdata\aid-closeout-widgets"
```

If `.venv` starts failing with `No Python at ...`, rebuild it with Python 3.12 and reinstall the desktop, dev, and build dependencies:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements-desktop.txt -r requirements-dev.txt -r requirements-build.txt
```

User-writable data is stored under:

```text
%LOCALAPPDATA%\AI Daily\
```

This directory contains the desktop config, outputs, logs, and state files.
On startup, the desktop app also syncs existing archives from the repository `output\` and `data\state.json`
into the desktop data directory when those files are missing or older.

### Build Windows `.exe`

```powershell
.venv\Scripts\pip install -r requirements-build.txt
.venv\Scripts\pyinstaller.exe build\windows\AI Daily.spec
build\windows\build-fast-launcher.ps1
```

The default packaged entry is `dist\AI Daily.exe`. It is a small launcher that starts
the faster onedir runtime in `dist\AI Daily\`. Keep both the launcher and the
`dist\AI Daily\` folder together. If you need a portable single-file build, use
`build\windows\AI Daily Onefile.spec`, but startup is slower because PyInstaller
extracts the bundled Qt/PySide payload at launch.

## Configuration

Main configuration lives in `config.yaml`.

- `timezone`: timezone used for logs and report dates
- `pipeline.time_window_hours`: article freshness window
- `pipeline.non_arxiv_ratio`: share of non-arxiv articles kept in Stage 1 and final output
- `pipeline.fetch_full_text`: whether to fetch full article bodies for non-arxiv feeds
- `llm`: provider, model, and API key environment variable

## Environment

Create `.env` with the API key required by the configured LLM provider, for example:

```env
SILICONFLOW_API_KEY=your_key_here
```

`.env` is ignored by Git.

In desktop mode, the same non-secret configuration is written to `%LOCALAPPDATA%\AI Daily\config.yaml`, while secrets are intended to live in the system keyring when available.

## Tests

```powershell
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\pytest.exe tests -v
```
