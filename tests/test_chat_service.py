import unittest
from unittest.mock import patch

from backend.agent.cache import response_cache, session_histories
from backend.agent.sanitizer import sanitize_output
from backend.services.chat import ChatService


class ChatServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        response_cache.clear()
        session_histories.clear()

    def test_output_sanitizer_removes_executable_html(self) -> None:
        result = sanitize_output(
            '<img src=x onerror=alert(1)><script>alert(2)</script><strong>OK</strong>'
        )
        self.assertNotIn("<script", result)
        self.assertNotIn("<img", result)
        self.assertIn("<strong>OK</strong>", result)

    def test_chat_does_not_duplicate_current_message_in_history_prompt(self) -> None:
        service = ChatService()
        with (
            patch("backend.services.chat.get_relevant_context", return_value="contexto"),
            patch(
                "backend.services.chat.generate_agent_response",
                return_value="Respuesta",
            ) as generate,
        ):
            result = service.reply("Hola", "session-test")

        self.assertFalse(result["error"])
        self.assertEqual(
            generate.call_args.kwargs["chat_history"], "Sin historial previo."
        )

    def test_order_intent_keeps_whatsapp_cta(self) -> None:
        service = ChatService()
        response = service._safe_response("Claro", "quiero hacer un pedido")
        self.assertIn("whatsapp-redirect", response)
        self.assertIn("noopener noreferrer", response)


if __name__ == "__main__":
    unittest.main()
