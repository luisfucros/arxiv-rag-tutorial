from uuid import UUID

from api.dependencies import CurrentUser, get_current_user, get_feedback_repo
from fastapi import APIRouter, Depends, HTTPException, status
from repositories.feedback import FeedbackRepository
from schemas.feedback import FeedbackCreate, FeedbackResponse, FeedbackUpdate

router = APIRouter(
    prefix="/feedback",
    tags=["Feedback"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(
    body: FeedbackCreate,
    current_user: CurrentUser,
    feedback_repo: FeedbackRepository = Depends(get_feedback_repo),
):
    """Create feedback for a chat message. Message must belong to a session owned by the current user."""
    feedback = feedback_repo.create(
        user_id=current_user.id,
        message_id=body.message_id,
        value=body.value,
        comment=body.comment,
    )
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    return feedback


@router.patch("/{feedback_id}", response_model=FeedbackResponse)
def update_feedback(
    feedback_id: UUID,
    body: FeedbackUpdate,
    current_user: CurrentUser,
    feedback_repo: FeedbackRepository = Depends(get_feedback_repo),
):
    """Update feedback by id. Only value and/or comment can be updated. Succeeds only if owned by the current user."""
    if body.value is None and body.comment is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of value or comment must be provided",
        )
    feedback = feedback_repo.update(
        feedback_id,
        current_user.id,
        value=body.value,
        comment=body.comment,
    )
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )
    return feedback


@router.get("/{feedback_id}", response_model=FeedbackResponse)
def get_feedback(
    feedback_id: UUID,
    current_user: CurrentUser,
    feedback_repo: FeedbackRepository = Depends(get_feedback_repo),
):
    """Get a feedback by id. Returns only if owned by the current user."""
    feedback = feedback_repo.get(feedback_id, current_user.id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )
    return feedback


@router.get("/message/{message_id}", response_model=FeedbackResponse)
def get_feedback_by_message(
    message_id: UUID,
    current_user: CurrentUser,
    feedback_repo: FeedbackRepository = Depends(get_feedback_repo),
):
    """Get the current user's feedback for a given message, if any."""
    feedback = feedback_repo.get_by_message(message_id, current_user.id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found for this message",
        )
    return feedback


@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(
    feedback_id: UUID,
    current_user: CurrentUser,
    feedback_repo: FeedbackRepository = Depends(get_feedback_repo),
):
    """Delete feedback by id. Succeeds only if owned by the current user."""
    deleted = feedback_repo.delete(feedback_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )
