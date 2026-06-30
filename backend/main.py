from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


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


# Servir archivos estáticos del frontend.
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")


class ChatRequest(BaseModel):
    """Modelo temporal para recibir mensajes del chat."""

    message: str
    session_id: str


class ResetSessionRequest(BaseModel):
    """Modelo temporal para limpiar una sesión."""

    session_id: str


def has_order_intent(message: str) -> bool:
    """Detecta intención básica de pedido o cotización."""

    keywords = [
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
    ]

    normalized_message = message.lower().strip()

    return any(keyword in normalized_message for keyword in keywords)


def get_whatsapp_block() -> str:
    """Retorna el bloque HTML de redirección a WhatsApp."""

    return """
    <div class="whatsapp-redirect">
      <p>Para cotizar tu pedido, contáctanos por WhatsApp:</p>
      <a href="https://wa.me/573205863534?text=Hola%20Marletty%2C%20quiero%20hacer%20un%20pedido"
         target="_blank" class="whatsapp-btn">
        💬 Cotizar por WhatsApp
      </a>
    </div>
    """


def build_mock_response(message: str) -> str:
    """
    Respuesta temporal del asistente.

    En una próxima etapa esta función será reemplazada por el pipeline RAG
    con LangChain, FAISS, Groq y Gemini embeddings.
    """

    normalized_message = message.lower().strip()

    if has_order_intent(normalized_message):
        return (
            "¡Claro! En Marletty cotizamos cada pedido de manera personalizada "
            "según tamaño, diseño, ingredientes y ocasión. "
            "Para tortas personalizadas, lo ideal es enviar una foto de referencia "
            "del diseño que tienes en mente."
            + get_whatsapp_block()
        )

    if "horario" in normalized_message or "abren" in normalized_message:
        return (
            "Nuestro horario es de domingo a domingo, de "
            "<strong>6:00 a.m. a 8:00 p.m.</strong> 🍞"
        )

    if (
        "dirección" in normalized_message
        or "direccion" in normalized_message
        or "ubicación" in normalized_message
        or "ubicacion" in normalized_message
        or "dónde están" in normalized_message
        or "donde estan" in normalized_message
    ):
        return (
            "Estamos ubicados en "
            "<strong>Circunvalar #10-75 Esquina, Duitama, Boyacá</strong>. "
            "La dirección Carrera 32 No. 9-06 es histórica y ya no está operativa."
        )

    if "cochinito" in normalized_message:
        return (
            "<strong>El Cochinito</strong> es uno de los productos insignia "
            "de Panadería y Pastelería Marletty. Es una preparación artesanal "
            "muy representativa de nuestra identidad."
        )

    if (
        "productos" in normalized_message
        or "qué venden" in normalized_message
        or "que venden" in normalized_message
        or "venden" in normalized_message
    ):
        return (
            "En Marletty encuentras tortas personalizadas, El Cochinito, "
            "galletas cubiertas de chocolate, pan artesanal, frutería, café, "
            "aromáticas y bebidas frías o calientes."
        )

    if (
        "contacto" in normalized_message
        or "whatsapp" in normalized_message
        or "teléfono" in normalized_message
        or "telefono" in normalized_message
    ):
        return (
            "Puedes contactarnos por WhatsApp al "
            "<strong>320 586 3534</strong>. También tenemos los teléfonos "
            "<strong>310 695 5287</strong> y <strong>321 234 7104</strong>."
            + get_whatsapp_block()
        )

    return (
        "Soy Marlette 🍞, asistente virtual de Panadería y Pastelería Marletty. "
        "Puedo ayudarte con información sobre productos, horarios, ubicación, "
        "contacto o cómo hacer un pedido."
    )


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


@app.post("/api/chat")
def chat(request: ChatRequest):
    """Endpoint temporal del chat."""

    response = build_mock_response(request.message)

    return {
        "response": response,
        "session_id": request.session_id,
        "from_cache": False,
    }


@app.post("/api/reset-session")
def reset_session(request: ResetSessionRequest):
    """Endpoint temporal para limpiar una sesión."""

    return {
        "status": "cleared",
        "session_id": request.session_id,
    }