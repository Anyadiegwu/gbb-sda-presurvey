from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.core.security import get_current_admin
from app.features.submissions.model import BOQSubmission
from app.features.submissions.schema import (
    SubmissionCreate,
    SubmissionRead,
    SubmissionStatusUpdate,
)

public_router = APIRouter(prefix="/submissions", tags=["public: submissions"])
admin_router = APIRouter(prefix="/admin/submissions", tags=["admin: submissions"])


@public_router.post("/", response_model=SubmissionRead)
def create_submission(payload: SubmissionCreate, session: Session = Depends(get_session)):
    """Customer submits their contact details alongside the quote they
    were just given (from /quotes/resolve-address + /quotes/calculate),
    so admin gets the full picture in one record. The reference number is
    generated server-side to guarantee uniqueness."""
    submission = BOQSubmission(
        **payload.model_dump(exclude={"nrc_items", "arc_items"}),
        nrc_items=[item.model_dump(by_alias=True) for item in payload.nrc_items],
        arc_items=[item.model_dump(by_alias=True) for item in payload.arc_items],
    )
    session.add(submission)
    session.commit()
    session.refresh(submission)

    submission.reference = f"GBB-{submission.created_at.year}-{submission.id:06d}"
    session.add(submission)
    session.commit()
    session.refresh(submission)

    # TODO: notify admin (email/Slack/etc.) once a notification channel is decided.

    return submission


@admin_router.get("/", response_model=List[SubmissionRead], dependencies=[Depends(get_current_admin)])
def list_submissions(session: Session = Depends(get_session)):
    return session.exec(
        select(BOQSubmission).order_by(BOQSubmission.created_at.desc())
    ).all()


@admin_router.get("/{submission_id}", response_model=SubmissionRead, dependencies=[Depends(get_current_admin)])
def get_submission(submission_id: int, session: Session = Depends(get_session)):
    submission = session.get(BOQSubmission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission


@admin_router.patch("/{submission_id}/status", response_model=SubmissionRead, dependencies=[Depends(get_current_admin)])
def update_submission_status(
    submission_id: int, payload: SubmissionStatusUpdate, session: Session = Depends(get_session)
):
    submission = session.get(BOQSubmission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    submission.status = payload.status
    session.add(submission)
    session.commit()
    session.refresh(submission)
    return submission
