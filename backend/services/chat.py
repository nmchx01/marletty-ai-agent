import logging

from backend.agent.cache import (
    add_message_to_history,
    format_history_for_prompt,
    get_cached_response,
    set_cached_response,
)
from backend.agent.llm import generate_agent_response
from backend.agent.rag import get_relevant_context
from backend.agent.sanitizer import sanitize_input, sanitize_output
from backend.core.config import get_settings


logger = logging.getLogger(__name__)

WHATSAPP_URL = (
    "https://wa.me/573205863534?"
    "text=Hola%20Marletty%2C%20quiero%20hacer%20un%20pedido"
)
ORDER_INTENT_KEYWORDS = (
    "quiero pedir", "cuánto cuesta", "cuanto cuesta", "precio",
    "cotización", "cotizacion", "encargar", "torta para",
    "necesito una torta", "hacer un pedido", "ordenar", "pedido",
    "cotizar", "vale", "valor", "cuanto vale", "cuánto vale",
)


class ChatService:
    """Orquesta el caso de uso del chat sin acoplarlo a FastAPI."""

    @staticmethod
    def _has_order_intent(message: str) -> bool:
        normalized = message.lower().strip()
        return any(keyword in normalized for keyword in ORDER_INTENT_KEYWORDS)

    def _ensure_whatsapp_redirect(self, response: str, message: str) -> str:
        if not self._has_order_intent(message) or "whatsapp-redirect" in response:
            return response
        return response + (
            '\n<div class="whatsapp-redirect">'
            "<p>Para cotizar tu pedido, contáctanos por WhatsApp:</p>"
            f'<a href="{WHATSAPP_URL}" target="_blank" rel="noopener noreferrer" '
            'class="whatsapp-btn">💬 Cotizar por WhatsApp</a></div>'
        )

    def _safe_response(self, response: str, message: str) -> str:
        return self._ensure_whatsapp_redirect(sanitize_output(response), message)

    def _fallback(self, message: str) -> str:
        response = (
            "En este momento no pude consultar toda la información de Marletty. "
            "Pero puedo ayudarte con productos, horarios, ubicación o pedidos. "
            "Para cotizaciones, puedes escribirnos por WhatsApp."
        )
        return self._safe_response(response, message)

    def get_health(self) -> dict:
        settings = get_settings()
        vector_ready = all(
            (settings.vector_store_dir / filename).exists()
            for filename in ("index.faiss", "index.pkl")
        )
        services = {
            "google_api_key": bool(settings.google_api_key),
            "groq_api_key": bool(settings.groq_api_key),
            "vector_store": vector_ready,
        }
        return {
            "status": "ok" if all(services.values()) else "degraded",
            "project": "Marletty AI Agent",
            "model": settings.groq_model,
            "services": services,
        }

    def reply(self, message: str, session_id: str) -> dict:
        sanitized = sanitize_input(message)
        if not sanitized["safe"]:
            logger.warning("Mensaje bloqueado por sanitizer.")
            return {
                "response": sanitized["message"], "session_id": session_id,
                "from_cache": False, "blocked": True, "error": False,
            }

        clean_message = sanitized["message"]
        # El historial se captura antes de agregar el turno actual para evitar
        # duplicarlo en el prompt (también se envía como HumanMessage).
        chat_history = format_history_for_prompt(session_id)
        cached_response = get_cached_response(clean_message)
        add_message_to_history(session_id, "user", clean_message)

        if cached_response:
            response = self._safe_response(cached_response, clean_message)
            add_message_to_history(session_id, "assistant", response)
            return {
                "response": response, "session_id": session_id,
                "from_cache": True, "blocked": False, "error": False,
            }

        try:
            context = get_relevant_context(query=clean_message, top_k=3)
            response = generate_agent_response(
                user_message=clean_message,
                context=context,
                chat_history=chat_history,
            )
            response = self._safe_response(response, clean_message)
            # Solo cachea respuestas sin contexto conversacional previo.
            if chat_history == "Sin historial previo.":
                set_cached_response(clean_message, response)
            add_message_to_history(session_id, "assistant", response)
            return {
                "response": response, "session_id": session_id,
                "from_cache": False, "blocked": False, "error": False,
            }
        except Exception as error:
            logger.exception("Error generando respuesta del agente: %s", error)
            response = self._fallback(clean_message)
            add_message_to_history(session_id, "assistant", response)
            return {
                "response": response, "session_id": session_id,
                "from_cache": False, "blocked": False, "error": True,
            }


chat_service = ChatService()
