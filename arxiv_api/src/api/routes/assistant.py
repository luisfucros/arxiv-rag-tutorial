from fastapi import APIRouter, Depends

from api.dependencies import get_arxiv_assistant
from services.assistant.client import ArxivAssistant
from schemas.assistant import ChatHistoryRequest, ChatResponse
from fastapi.responses import StreamingResponse
from api.dependencies import CurrentUser


router = APIRouter(prefix="/arxiv_assistant", tags=["ArxivAssistant"])


@router.post("/chat", response_model=ChatResponse)
def chat_arxiv(
    req: ChatHistoryRequest,
    session_id: str,
    current_user: CurrentUser,
    arxiv_assistant: ArxivAssistant = Depends(get_arxiv_assistant)
):
    answer = arxiv_assistant.chat(req.chat_history, current_user.id, session_id)
    return ChatResponse(answer=answer)


@router.post("/chat/stream")
def chat_arxiv_stream(
    req: ChatHistoryRequest,
    session_id: str,
    current_user: CurrentUser,
    arxiv_assistant: ArxivAssistant = Depends(get_arxiv_assistant)
):
    return StreamingResponse(
        arxiv_assistant.chat_stream(req.chat_history, current_user.id, session_id),
        media_type="text/plain",
    )
