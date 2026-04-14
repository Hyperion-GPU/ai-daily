from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.runtime import get_runtime_paths

from .api import router

app = FastAPI(title="AI Daily", docs_url="/api/docs")
app.include_router(router)

# 挂载 Vue 构建产物
RUNTIME_PATHS = get_runtime_paths()
FRONTEND_DIST = RUNTIME_PATHS.frontend_dist
BRAND_DIR = RUNTIME_PATHS.brand_dir

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


def _resolve_brand_asset(filename: str) -> Path | None:
    candidates = [
        FRONTEND_DIST / filename,
        BRAND_DIR / filename,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


@app.get("/favicon.svg", include_in_schema=False)
def serve_favicon_svg():
    target = _resolve_brand_asset("favicon.svg")
    if target is None:
        raise HTTPException(status_code=404, detail="Favicon not found")
    return FileResponse(target)


@app.get("/app-icon.svg", include_in_schema=False)
def serve_app_icon_svg():
    target = _resolve_brand_asset("ai-daily-mark.svg")
    if target is None:
        raise HTTPException(status_code=404, detail="App icon not found")
    return FileResponse(target)


@app.get("/favicon.ico", include_in_schema=False)
def serve_favicon_ico():
    target = _resolve_brand_asset("ai-daily.ico")
    if target is None:
        raise HTTPException(status_code=404, detail="Favicon not found")
    return FileResponse(target)


if FRONTEND_DIST.exists():
    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        """所有非 /api 路径都返回 index.html，交给 Vue Router 处理"""
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        return FileResponse(
            FRONTEND_DIST / "index.html",
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
