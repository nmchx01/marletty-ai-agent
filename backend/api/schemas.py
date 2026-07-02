from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., min_length=3, max_length=160)


class ChatResponse(BaseModel):
    response: str
    session_id: str
    from_cache: bool = False
    blocked: bool = False
    error: bool = False


class ResetSessionRequest(BaseModel):
    session_id: str = Field(..., min_length=3, max_length=160)


class ResetSessionResponse(BaseModel):
    status: str
    session_id: str
