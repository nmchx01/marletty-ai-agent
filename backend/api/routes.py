from fastapi import APIRouter

from backend.agent.cache import clear_session_history
from backend.api.schemas import (
    ChatRequest,
    ChatResponse,
    ResetSessionRequest,
    ResetSessionResponse,
)
from backend.services.chat import chat_service


router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    return chat_service.get_health()


@router.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(**chat_service.reply(request.message, request.session_id))


@router.post("/api/reset-session", response_model=ResetSessionResponse)
def reset_session(request: ResetSessionRequest) -> ResetSessionResponse:
    was_cleared = clear_session_history(request.session_id)
    return ResetSessionResponse(
        status="cleared" if was_cleared else "not_found",
        session_id=request.session_id,
    )
