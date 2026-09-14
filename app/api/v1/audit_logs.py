from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.audit_log import AuditLogRead
from app.schemas.common import PaginatedResponse
from app.security.dependencies import require_role
from app.services import audit_service
from app.utils.pagination import PageParams, pagination_params

router = APIRouter()


@router.get("", response_model=PaginatedResponse[AuditLogRead])
def list_audit_logs(
    page_params: PageParams = Depends(pagination_params),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
) -> PaginatedResponse:
    logs, total = audit_service.list_audit_logs(
        db, offset=page_params.offset, limit=page_params.page_size
    )
    return PaginatedResponse[AuditLogRead](
        items=logs, total=total, page=page_params.page, page_size=page_params.page_size
    )
