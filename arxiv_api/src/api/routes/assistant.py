from fastapi import APIRouter, Depends

from api.dependencies import get_arxiv_assistant
from assistant.main import ArxivAssistant
from schemas.assistant import ChatHistoryRequest, ChatResponse

router = APIRouter(prefix="/arxiv_assistant", tags=["ArxivAssistant"])


@router.post("/chat", response_model=ChatResponse)
def chat_arxiv(
    req: ChatHistoryRequest,
    arxiv_assistant: ArxivAssistant = Depends(get_arxiv_assistant),
):
    answer = arxiv_assistant.chat(req.chat_history)
    return ChatResponse(answer=answer)
