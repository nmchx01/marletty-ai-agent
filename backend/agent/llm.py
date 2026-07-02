from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from backend.agent.prompts import build_system_prompt
from backend.core.config import get_settings


def get_llm() -> ChatGroq:
    """Crea el cliente de Groq."""

    settings = get_settings()
    settings.require_groq_api_key()

    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0.35,
        max_tokens=700,
    )


def generate_agent_response(
    user_message: str,
    context: str,
    chat_history: str,
) -> str:
    """
    Genera una respuesta de Marlette usando Groq.

    user_message:
        Mensaje actual del cliente.

    context:
        Contexto recuperado desde FAISS/RAG.

    chat_history:
        Historial formateado de la sesión.
    """

    llm = get_llm()

    system_prompt = build_system_prompt(
        context=context,
        chat_history=chat_history,
    )

    response = llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]
    )

    content = response.content

    if isinstance(content, list):
        content = " ".join(str(item) for item in content)

    clean_response = str(content).strip()

    if not clean_response:
        return (
            "Solo puedo ayudarte con información sobre Panadería "
            "y Pastelería Marletty. ¿En qué te puedo ayudar?"
        )

    return clean_response
