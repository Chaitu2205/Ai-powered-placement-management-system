from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.notification import NotificationRead
from app.security.dependencies import get_current_user
from app.services import notification_service

router = APIRouter()


@router.get("", response_model=list[NotificationRead])
def list_my_notifications(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list:
    return notification_service.list_my_notifications(db, current_user)


@router.put("/{notification_id}/read", response_model=NotificationRead)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationRead:
    return notification_service.mark_as_read(db, current_user, notification_id)
