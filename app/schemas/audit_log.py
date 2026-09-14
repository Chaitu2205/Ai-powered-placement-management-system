from datetime import datetime
from typing import Optional

from app.models.enums import AuditAction
from app.schemas.common import ORMBase


class AuditLogRead(ORMBase):
    id: int
    user_id: Optional[int]
    action: AuditAction
    entity_type: str
    entity_id: Optional[int]
    details_json: Optional[dict] = None
    created_at: datetime
