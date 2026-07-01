import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from backend.agent.prompts import build_system_prompt


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"


def load_environment() -> None:
    """Carga variables de entorno necesarias para Groq."""

    load_dotenv(ENV_PATH)

    groq_api_key = os.getenv("GROQ_API_KEY")

    if not groq_api_key:
        raise RuntimeError(
            "No se encontró GROQ_API_KEY. "
            "Crea un archivo .env en la raíz del proyecto con tu clave de Groq."
        )


def get_llm() -> ChatGroq:
    """Crea el cliente de Groq."""

    load_environment()

    model_name = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)

    return ChatGroq(
        model=model_name,
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
            "y Pastelería Marletty 🍞 ¿En qué te puedo ayudar?"
        )

    return clean_response