from uuid import UUID

from api.dependencies import CurrentUser, get_chat_repo, get_current_user
from fastapi import APIRouter, Depends, HTTPException, Query, status
from repositories.chat_history import ChatRepository
from schemas.chat_history import ChatMessageResponse, ChatSessionResponse

router = APIRouter(
    prefix="/chat_history",
    tags=["ChatHistory"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/sessions", response_model=list[ChatSessionResponse])
def list_sessions(
    current_user: CurrentUser,
    chat_repo: ChatRepository = Depends(get_chat_repo),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List chat sessions for the current user."""
    sessions = chat_repo.list_sessions(owner_id=current_user.id, limit=limit, offset=offset)
    return sessions


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
def list_messages(
    session_id: UUID,
    current_user: CurrentUser,
    chat_repo: ChatRepository = Depends(get_chat_repo),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List messages for a session. Session must be owned by the current user."""
    session = chat_repo.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    messages = chat_repo.list_messages(session_id=session_id, limit=limit, offset=offset)
    return messages
