import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from backend.api.auth import require_user


class AuthTests(unittest.IsolatedAsyncioTestCase):
    @patch("backend.api.auth.get_settings")
    async def test_missing_bearer_token_is_rejected(self, get_settings) -> None:
        get_settings.return_value.supabase_enabled = True
        with self.assertRaises(HTTPException) as context:
            await require_user(None)
        self.assertEqual(context.exception.status_code, 401)

    @patch("backend.api.auth.get_settings")
    async def test_missing_configuration_is_reported(self, get_settings) -> None:
        get_settings.return_value.supabase_enabled = False
        with self.assertRaises(HTTPException) as context:
            await require_user("Bearer token")
        self.assertEqual(context.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
