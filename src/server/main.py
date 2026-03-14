from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import router

app = FastAPI(title="AI Daily", docs_url="/api/docs")
app.include_router(router)

# 挂载 Vue 构建产物
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    # favicon 等静态文件
    @app.get("/vite.svg")
    def serve_favicon():
        return FileResponse(FRONTEND_DIST / "vite.svg")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        """所有非 /api 路径都返回 index.html，交给 Vue Router 处理"""
        return FileResponse(FRONTEND_DIST / "index.html")
