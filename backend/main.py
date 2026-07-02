import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.agent.cache import (
    add_message_to_history,
    clear_session_history,
    format_history_for_prompt,
    get_cached_response,
    set_cached_response,
)
from backend.agent.llm import generate_agent_response
from backend.agent.rag import get_relevant_context
from backend.agent.sanitizer import sanitize_input


# ==============================
# Configuración base
# ==============================

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
VECTOR_STORE_DIR = BASE_DIR / "backend" / "vector_store"
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("marletty-ai-agent")


# ==============================
# Constantes de negocio
# ==============================

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

WHATSAPP_URL = (
    "https://wa.me/573205863534?"
    "text=Hola%20Marletty%2C%20quiero%20hacer%20un%20pedido"
)

ORDER_INTENT_KEYWORDS = [
    "quiero pedir",
    "cuánto cuesta",
    "cuanto cuesta",
    "precio",
    "cotización",
    "cotizacion",
    "encargar",
    "torta para",
    "necesito una torta",
    "hacer un pedido",
    "ordenar",
    "pedido",
    "cotizar",
    "vale",
    "valor",
    "cuanto vale",
    "cuánto vale",
]


# ==============================
# App FastAPI
# ==============================

app = FastAPI(
    title="Marletty AI Agent",
    description=(
        "Sitio web oficial + asistente IA de Panadería y Pastelería Marletty"
    ),
    version="0.2.0",
)


def get_allowed_origins() -> list[str]:
    """
    Lee los orígenes permitidos desde variable de entorno.

    En desarrollo se permite '*'. En producción se recomienda definir
    ALLOWED_ORIGINS con el dominio real.
    """

    raw_origins = os.getenv("ALLOWED_ORIGINS", "*")

    if raw_origins.strip() == "*":
        return ["*"]

    return [
        origin.strip()
        for origin in raw_origins.split(",")
        if origin.strip()
    ]


allowed_origins = get_allowed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False if "*" in allowed_origins else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos del frontend.
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")


# ==============================
# Schemas
# ==============================

class ChatRequest(BaseModel):
    """Payload esperado por el endpoint del chat."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Mensaje enviado por el usuario.",
    )
    session_id: str = Field(
        ...,
        min_length=3,
        max_length=160,
        description="Identificador único de sesión generado en el frontend.",
    )


class ChatResponse(BaseModel):
    """Respuesta enviada al frontend."""

    response: str
    session_id: str
    from_cache: bool = False
    blocked: bool = False
    error: bool = False


class ResetSessionRequest(BaseModel):
    """Payload para limpiar una sesión."""

    session_id: str = Field(
        ...,
        min_length=3,
        max_length=160,
        description="Identificador de sesión a limpiar.",
    )


class ResetSessionResponse(BaseModel):
    """Respuesta del endpoint de limpieza de sesión."""

    status: str
    session_id: str


# ==============================
# Helpers
# ==============================

def is_vector_store_ready() -> bool:
    """Verifica si existe un índice FAISS válido."""

    return (
        (VECTOR_STORE_DIR / "index.faiss").exists()
        and (VECTOR_STORE_DIR / "index.pkl").exists()
    )


def has_order_intent(message: str) -> bool:
    """Detecta intención básica de pedido o cotización."""

    normalized_message = message.lower().strip()

    return any(
        keyword in normalized_message
        for keyword in ORDER_INTENT_KEYWORDS
    )


def get_whatsapp_block() -> str:
    """Retorna el bloque HTML de redirección a WhatsApp."""

    return f"""
    <div class="whatsapp-redirect">
      <p>Para cotizar tu pedido, contáctanos por WhatsApp:</p>
      <a href="{WHATSAPP_URL}" target="_blank" class="whatsapp-btn">
        💬 Cotizar por WhatsApp
      </a>
    </div>
    """


def ensure_whatsapp_redirect(response: str, user_message: str) -> str:
    """
    Asegura que toda respuesta con intención de pedido incluya
    el bloque HTML de WhatsApp.
    """

    if not has_order_intent(user_message):
        return response

    if "whatsapp-redirect" in response:
        return response

    return response + get_whatsapp_block()


def build_fallback_response(user_message: str) -> str:
    """
    Respuesta segura cuando falla Groq, Google, FAISS o cualquier parte del RAG.

    No revela detalles técnicos al usuario final.
    """

    response = (
        "En este momento no pude consultar toda la información de Marletty. "
        "Pero puedo ayudarte con productos, horarios, ubicación o pedidos. "
        "Para cotizaciones, puedes escribirnos por WhatsApp."
    )

    return ensure_whatsapp_redirect(response, user_message)


# ==============================
# Endpoints
# ==============================

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
    """Endpoint para verificar estado general de la app."""

    google_ready = bool(os.getenv("GOOGLE_API_KEY"))
    groq_ready = bool(os.getenv("GROQ_API_KEY"))
    rag_ready = is_vector_store_ready()

    status = "ok" if google_ready and groq_ready and rag_ready else "degraded"

    return {
        "status": status,
        "project": "Marletty AI Agent",
        "model": GROQ_MODEL,
        "services": {
            "google_api_key": google_ready,
            "groq_api_key": groq_ready,
            "vector_store": rag_ready,
        },
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Endpoint del chat con sanitización, caché, historial, RAG y Groq."""

    sanitized = sanitize_input(request.message)

    if not sanitized["safe"]:
        logger.warning("Mensaje bloqueado por sanitizer.")
        return ChatResponse(
            response=sanitized["message"],
            session_id=request.session_id,
            from_cache=False,
            blocked=True,
            error=False,
        )

    clean_message = sanitized["message"]

    add_message_to_history(
        session_id=request.session_id,
        role="user",
        content=clean_message,
    )

    cached_response = get_cached_response(clean_message)

    if cached_response:
        cached_response = ensure_whatsapp_redirect(
            response=cached_response,
            user_message=clean_message,
        )

        add_message_to_history(
            session_id=request.session_id,
            role="assistant",
            content=cached_response,
        )

        return ChatResponse(
            response=cached_response,
            session_id=request.session_id,
            from_cache=True,
            blocked=False,
            error=False,
        )

    try:
        chat_history = format_history_for_prompt(request.session_id)

        context = get_relevant_context(
            query=clean_message,
            top_k=3,
        )

        response = generate_agent_response(
            user_message=clean_message,
            context=context,
            chat_history=chat_history,
        )

        response = ensure_whatsapp_redirect(
            response=response,
            user_message=clean_message,
        )

        set_cached_response(clean_message, response)

        add_message_to_history(
            session_id=request.session_id,
            role="assistant",
            content=response,
        )

        return ChatResponse(
            response=response,
            session_id=request.session_id,
            from_cache=False,
            blocked=False,
            error=False,
        )

    except Exception as error:
        logger.exception("Error generando respuesta del agente: %s", error)

        fallback_response = build_fallback_response(clean_message)

        add_message_to_history(
            session_id=request.session_id,
            role="assistant",
            content=fallback_response,
        )

        return ChatResponse(
            response=fallback_response,
            session_id=request.session_id,
            from_cache=False,
            blocked=False,
            error=True,
        )


@app.post("/api/reset-session", response_model=ResetSessionResponse)
def reset_session(request: ResetSessionRequest):
    """Limpia el historial de una sesión."""

    was_cleared = clear_session_history(request.session_id)

    return ResetSessionResponse(
        status="cleared" if was_cleared else "not_found",
        session_id=request.session_id,
    )