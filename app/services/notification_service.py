from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User
from app.utils.exceptions import NotFoundError, PermissionDeniedError


def list_my_notifications(db: Session, current_user: User) -> list[Notification]:
    return list(
        db.execute(
            select(Notification)
            .where(Notification.user_id == current_user.id)
            .order_by(Notification.created_at.desc())
        )
        .scalars()
        .all()
    )


def mark_as_read(db: Session, current_user: User, notification_id: int) -> Notification:
    notification = db.get(Notification, notification_id)
    if notification is None:
        raise NotFoundError("Notification not found")
    if notification.user_id != current_user.id:
        raise PermissionDeniedError("You do not have permission to modify this notification")

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
