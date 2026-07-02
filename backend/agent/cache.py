import hashlib
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional


CACHE_TTL_SECONDS = 3600
SESSION_TTL_MINUTES = 30
MAX_HISTORY_MESSAGES = 20  # 10 turnos: usuario + asistente


STATIC_CACHE_ENTRIES = {
    "horario": (
        "Nuestro horario es de domingo a domingo, de "
        "<strong>6:00 a.m. a 8:00 p.m.</strong>"
    ),
    "dirección": (
        "Estamos ubicados en "
        "<strong>Circunvalar #10-75 Esquina, Duitama, Boyacá</strong>. "
        "La dirección Carrera 32 No. 9-06 es histórica y ya no está operativa."
    ),
    "direccion": (
        "Estamos ubicados en "
        "<strong>Circunvalar #10-75 Esquina, Duitama, Boyacá</strong>. "
        "La dirección Carrera 32 No. 9-06 es histórica y ya no está operativa."
    ),
    "ubicación": (
        "Estamos ubicados en "
        "<strong>Circunvalar #10-75 Esquina, Duitama, Boyacá</strong>. "
        "La dirección Carrera 32 No. 9-06 es histórica y ya no está operativa."
    ),
    "ubicacion": (
        "Estamos ubicados en "
        "<strong>Circunvalar #10-75 Esquina, Duitama, Boyacá</strong>. "
        "La dirección Carrera 32 No. 9-06 es histórica y ya no está operativa."
    ),
    "dónde están": (
        "Estamos ubicados en "
        "<strong>Circunvalar #10-75 Esquina, Duitama, Boyacá</strong>. "
        "La dirección Carrera 32 No. 9-06 es histórica y ya no está operativa."
    ),
    "donde estan": (
        "Estamos ubicados en "
        "<strong>Circunvalar #10-75 Esquina, Duitama, Boyacá</strong>. "
        "La dirección Carrera 32 No. 9-06 es histórica y ya no está operativa."
    ),
    "whatsapp": (
        "Puedes contactarnos por WhatsApp al <strong>320 586 3534</strong>. "
        "También tenemos los teléfonos <strong>310 695 5287</strong> "
        "y <strong>321 234 7104</strong>."
    ),
    "contacto": (
        "Puedes contactarnos por WhatsApp al <strong>320 586 3534</strong>. "
        "También tenemos los teléfonos <strong>310 695 5287</strong> "
        "y <strong>321 234 7104</strong>."
    ),
    "teléfono": (
        "Puedes contactarnos por WhatsApp al <strong>320 586 3534</strong>. "
        "También tenemos los teléfonos <strong>310 695 5287</strong> "
        "y <strong>321 234 7104</strong>."
    ),
    "telefono": (
        "Puedes contactarnos por WhatsApp al <strong>320 586 3534</strong>. "
        "También tenemos los teléfonos <strong>310 695 5287</strong> "
        "y <strong>321 234 7104</strong>."
    ),
    "qué venden": (
        "En Marletty encuentras tortas personalizadas, pastel de pollo, "
        "galletas cubiertas de chocolate, pan artesanal, frutería, café, "
        "aromáticas y bebidas frías o calientes."
    ),
    "que venden": (
        "En Marletty encuentras tortas personalizadas, pastel de pollo, "
        "galletas cubiertas de chocolate, pan artesanal, frutería, café, "
        "aromáticas y bebidas frías o calientes."
    ),
    "productos": (
        "En Marletty encuentras tortas personalizadas, pastel de pollo, "
        "galletas cubiertas de chocolate, pan artesanal, frutería, café, "
        "aromáticas y bebidas frías o calientes."
    ),
    "precio": (
        "En Marletty no manejamos una lista fija de precios. "
        "Cada pedido se cotiza individualmente por WhatsApp según tamaño, "
        "diseño, ingredientes y ocasión."
    ),
    "pastel de pollo": (
        "<strong>El pastel de pollo</strong> es uno de los productos insignia "
        "de Panadería y Pastelería Marletty. Es una preparación artesanal "
        "muy representativa de nuestra identidad."
    ),
    "redes sociales": (
        "Nos encuentras en Instagram como "
        "<strong>@pasteleriamarlettyduitama</strong> y en Facebook como "
        "<strong>Panadería y Pastelería Marletty</strong>."
    ),
    "email": "Nuestro correo es <strong>marlettyduitama@gmail.com</strong>.",
    "correo": "Nuestro correo es <strong>marlettyduitama@gmail.com</strong>.",
}


response_cache: Dict[str, dict] = {}
session_histories: Dict[str, dict] = {}


def get_current_time() -> datetime:
    """Retorna la fecha y hora actual en UTC."""

    return datetime.now(timezone.utc)


def normalize_message(message: str) -> str:
    """Normaliza el mensaje para crear claves consistentes."""

    clean_message = message.lower().strip()
    clean_message = re.sub(r"\s+", " ", clean_message)

    return clean_message


def get_message_hash(message: str) -> str:
    """Genera un hash MD5 del mensaje normalizado."""

    normalized_message = normalize_message(message)

    return hashlib.md5(normalized_message.encode("utf-8")).hexdigest()


def initialize_static_cache() -> None:
    """Pre-carga respuestas frecuentes que no expiran."""

    for question, response in STATIC_CACHE_ENTRIES.items():
        cache_key = get_message_hash(question)

        response_cache[cache_key] = {
            "response": response,
            "created_at": get_current_time(),
            "static": True,
        }


def get_cached_response(message: str) -> Optional[str]:
    """Busca una respuesta en caché."""

    cache_key = get_message_hash(message)
    cached_item = response_cache.get(cache_key)

    if not cached_item:
        return None

    if cached_item.get("static"):
        return cached_item["response"]

    created_at = cached_item["created_at"]
    age = get_current_time() - created_at

    if age.total_seconds() > CACHE_TTL_SECONDS:
        response_cache.pop(cache_key, None)
        return None

    return cached_item["response"]


def set_cached_response(message: str, response: str) -> None:
    """Guarda una respuesta dinámica en caché por 1 hora."""

    cache_key = get_message_hash(message)

    response_cache[cache_key] = {
        "response": response,
        "created_at": get_current_time(),
        "static": False,
    }


def get_session_history(session_id: str) -> List[dict]:
    """Obtiene el historial de una sesión."""

    cleanup_inactive_sessions()

    session = session_histories.get(session_id)

    if not session:
        return []

    session["last_active"] = get_current_time()

    return session["messages"]


def add_message_to_history(session_id: str, role: str, content: str) -> None:
    """Agrega un mensaje al historial de sesión."""

    cleanup_inactive_sessions()

    if session_id not in session_histories:
        session_histories[session_id] = {
            "last_active": get_current_time(),
            "messages": [],
        }

    session_histories[session_id]["messages"].append(
        {
            "role": role,
            "content": content,
            "created_at": get_current_time().isoformat(),
        }
    )

    session_histories[session_id]["messages"] = session_histories[session_id][
        "messages"
    ][-MAX_HISTORY_MESSAGES:]

    session_histories[session_id]["last_active"] = get_current_time()


def clear_session_history(session_id: str) -> bool:
    """Limpia el historial de una sesión."""

    if session_id in session_histories:
        session_histories.pop(session_id)
        return True

    return False


def cleanup_inactive_sessions() -> None:
    """Elimina sesiones inactivas por más de 30 minutos."""

    now = get_current_time()
    expiration_delta = timedelta(minutes=SESSION_TTL_MINUTES)

    expired_sessions = [
        session_id
        for session_id, session_data in session_histories.items()
        if now - session_data["last_active"] > expiration_delta
    ]

    for session_id in expired_sessions:
        session_histories.pop(session_id, None)


def format_history_for_prompt(session_id: str) -> str:
    """
    Convierte el historial en texto.

    Más adelante se usará para pasarlo al system prompt del agente RAG.
    """

    history = get_session_history(session_id)

    if not history:
        return "Sin historial previo."

    formatted_messages = []

    for message in history:
        role = "Cliente" if message["role"] == "user" else "Marlette"
        formatted_messages.append(f"{role}: {message['content']}")

    return "\n".join(formatted_messages)


initialize_static_cache()
