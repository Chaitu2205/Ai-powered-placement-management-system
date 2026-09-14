from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.enums import ApplicationStatus, UserRole
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationRead, ApplicationStatusUpdate
from app.schemas.common import PaginatedResponse
from app.security.dependencies import require_role
from app.services import application_service
from app.utils.pagination import PageParams, pagination_params

router = APIRouter()


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def apply_to_job(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
) -> ApplicationRead:
    return application_service.apply_to_job(db, current_user, payload)


@router.get("/my", response_model=list[ApplicationRead])
def list_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
) -> list:
    return application_service.list_my_applications(db, current_user)


@router.get("", response_model=PaginatedResponse[ApplicationRead])
def list_applications(
    job_id: Optional[int] = Query(default=None),
    status_filter: Optional[ApplicationStatus] = Query(default=None, alias="status"),
    page_params: PageParams = Depends(pagination_params),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.RECRUITER)),
) -> PaginatedResponse:
    applications, total = application_service.list_applications(
        db,
        current_user,
        offset=page_params.offset,
        limit=page_params.page_size,
        job_id=job_id,
        status_filter=status_filter,
    )
    return PaginatedResponse[ApplicationRead](
        items=applications, total=total, page=page_params.page, page_size=page_params.page_size
    )


@router.put("/{application_id}/status", response_model=ApplicationRead)
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.RECRUITER)),
) -> ApplicationRead:
    application = application_service.get_application(db, application_id)
    return application_service.update_application_status(db, current_user, application, payload)
