import re


BLOCKED_PATTERNS = [
    "ignore previous instructions",
    "ignore your instructions",
    "olvida tus instrucciones",
    "olvida todo",
    "nuevo rol",
    "actúa como",
    "actua como",
    "pretend you are",
    "you are now",
    "jailbreak",
    "DAN",
    "prompt injection",
    "system prompt",
    "revela tus instrucciones",
    "muéstrame el prompt",
    "muestrame el prompt",
    "what are your instructions",
]


SAFE_RESPONSE = (
    "Solo puedo ayudarte con información sobre Panadería "
    "Marletty 🍞 ¿Tienes alguna pregunta sobre nuestros "
    "productos, horarios o pedidos?"
)


def sanitize_input(user_message: str) -> dict:
    """
    Valida si el mensaje del usuario contiene intentos de prompt injection.

    Retorna:
    {
        "safe": bool,
        "message": str
    }
    """

    if not user_message or not user_message.strip():
        return {
            "safe": False,
            "message": SAFE_RESPONSE,
        }

    normalized_message = user_message.lower().strip()

    for pattern in BLOCKED_PATTERNS:
        escaped_pattern = re.escape(pattern.lower())

        if re.search(escaped_pattern, normalized_message, re.IGNORECASE):
            return {
                "safe": False,
                "message": SAFE_RESPONSE,
            }

    return {
        "safe": True,
        "message": user_message.strip(),
    }