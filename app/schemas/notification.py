from datetime import datetime

from app.schemas.common import ORMBase


class NotificationRead(ORMBase):
    id: int
    user_id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime
