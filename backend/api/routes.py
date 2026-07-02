from fastapi import APIRouter, Depends

from backend.agent.cache import clear_session_history
from backend.api.schemas import (
    ChatRequest,
    ChatResponse,
    ResetSessionRequest,
    ResetSessionResponse,
)
from backend.services.chat import chat_service
from backend.api.auth import require_user
from backend.core.config import get_settings


router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    return chat_service.get_health()

@router.get("/api/auth-config")
def auth_config() -> dict:
    settings = get_settings()
    return {
        "enabled": settings.supabase_enabled,
        "url": settings.supabase_url,
        "anonKey": settings.supabase_anon_key,
    }

@router.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest, user: dict = Depends(require_user)) -> ChatResponse:
    return ChatResponse(**chat_service.reply(request.message, request.session_id))


@router.post("/api/reset-session", response_model=ResetSessionResponse)
def reset_session(
    request: ResetSessionRequest, user: dict = Depends(require_user)
) -> ResetSessionResponse:
    was_cleared = clear_session_history(request.session_id)
    return ResetSessionResponse(
        status="cleared" if was_cleared else "not_found",
        session_id=request.session_id,
    )
