import html
import re
from html.parser import HTMLParser


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
    "Marletty. ¿Tienes alguna pregunta sobre nuestros "
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


class _SafeHTMLParser(HTMLParser):
    """Conserva formato básico y elimina atributos/etiquetas peligrosas."""

    ALLOWED_TAGS = {"strong", "em", "br", "p", "div", "a"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in self.ALLOWED_TAGS:
            return
        safe_attrs: list[str] = []
        attributes = dict(attrs)
        if tag == "div" and attributes.get("class") == "whatsapp-redirect":
            safe_attrs.append('class="whatsapp-redirect"')
        if tag == "a":
            href = attributes.get("href", "")
            if href.startswith("https://wa.me/"):
                safe_attrs.extend([
                    f'href="{html.escape(href, quote=True)}"',
                    'target="_blank"',
                    'rel="noopener noreferrer"',
                    'class="whatsapp-btn"',
                ])
        suffix = f" {' '.join(safe_attrs)}" if safe_attrs else ""
        self.parts.append(f"<{tag}{suffix}>")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.ALLOWED_TAGS and tag != "br":
            self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.parts.append(html.escape(data))


def sanitize_output(model_response: str) -> str:
    """Sanitiza HTML no confiable antes de que el frontend use innerHTML."""

    parser = _SafeHTMLParser()
    parser.feed(str(model_response))
    parser.close()
    return "".join(parser.parts).strip()
