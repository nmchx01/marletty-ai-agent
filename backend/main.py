import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router
from backend.core.config import get_settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

settings = get_settings()

app = FastAPI(
    title="Marletty AI Agent",
    description="Sitio web oficial + asistente IA de Panadería y Pastelería Marletty",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials="*" not in settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

app.mount("/css", StaticFiles(directory=settings.frontend_dir / "css"), name="css")
app.mount("/js", StaticFiles(directory=settings.frontend_dir / "js"), name="js")

assets_dir = settings.frontend_dir / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/", include_in_schema=False)
def serve_home() -> FileResponse:
    return FileResponse(settings.frontend_dir / "index.html")
