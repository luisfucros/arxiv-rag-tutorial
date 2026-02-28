from uuid import UUID

from api.dependencies import CurrentUser, get_arxiv_assistant
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from schemas.assistant import ChatHistoryRequest, ChatResponse
from services.assistant.client import ArxivAssistant

router = APIRouter(prefix="/arxiv_assistant", tags=["ArxivAssistant"])


@router.post("/chat", response_model=ChatResponse)
def chat_arxiv(
    req: ChatHistoryRequest,
    session_id: str,
    current_user: CurrentUser,
    arxiv_assistant: ArxivAssistant = Depends(get_arxiv_assistant),
):
    answer, message_id = arxiv_assistant.chat(req.chat_history, current_user.id, UUID(session_id))
    return ChatResponse(answer=answer, message_id=message_id)


@router.post("/chat/stream")
def chat_arxiv_stream(
    req: ChatHistoryRequest,
    session_id: str,
    current_user: CurrentUser,
    arxiv_assistant: ArxivAssistant = Depends(get_arxiv_assistant),
):
    return StreamingResponse(
        arxiv_assistant.chat_stream(req.chat_history, current_user.id, UUID(session_id)),
        media_type="text/plain",
    )
