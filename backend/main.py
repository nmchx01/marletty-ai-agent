from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR


app = FastAPI(
    title="Marletty AI Agent",
    description="Sitio web oficial + asistente IA de Panadería y Pastelería Marletty",
    version="0.1.0",
)


# CORS habilitado para desarrollo local.
# Más adelante se puede restringir al dominio real.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Servir archivos estáticos del frontend:
# /css/styles.css
# /js/chat.js
# /assets/logo.png
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")


@app.get("/")
def serve_home():
    """Sirve la página principal del sitio web."""
    index_path = FRONTEND_DIR / "index.html"

    if not index_path.exists():
        return {
            "error": "No se encontró frontend/index.html",
            "detail": "Verifica que el archivo exista en la carpeta frontend.",
        }

    return FileResponse(index_path)


@app.get("/health")
def health_check():
    """Endpoint simple para verificar que el servidor está funcionando."""
    return {
        "status": "ok",
        "project": "Marletty AI Agent",
        "model": "llama-3.1-8b-instant",
    }