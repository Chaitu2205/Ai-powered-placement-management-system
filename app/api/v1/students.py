from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.enums import PlacementStatus, UserRole
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.student import StudentListItem, StudentRead, StudentUpdate
from app.security.dependencies import get_current_user, require_role
from app.services import student_service
from app.utils.pagination import PageParams, pagination_params

router = APIRouter()


@router.get("/me", response_model=StudentRead)
def read_own_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
) -> StudentRead:
    return student_service.get_student_by_user_id(db, current_user.id)


@router.put("/me", response_model=StudentRead)
def update_own_profile(
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.STUDENT)),
) -> StudentRead:
    student = student_service.get_student_by_user_id(db, current_user.id)
    return student_service.update_student(db, student, payload)


@router.get("", response_model=PaginatedResponse[StudentListItem])
def list_students(
    department_id: Optional[int] = Query(default=None),
    placement_status: Optional[PlacementStatus] = Query(default=None),
    search: Optional[str] = Query(default=None, description="Search by full name"),
    page_params: PageParams = Depends(pagination_params),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
) -> PaginatedResponse:
    students, total = student_service.list_students(
        db,
        offset=page_params.offset,
        limit=page_params.page_size,
        department_id=department_id,
        placement_status=placement_status,
        search=search,
    )
    return PaginatedResponse[StudentListItem](
        items=students, total=total, page=page_params.page, page_size=page_params.page_size
    )


@router.get("/{student_id}", response_model=StudentRead)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role(UserRole.ADMIN, UserRole.RECRUITER)),
) -> StudentRead:
    return student_service.get_student(db, student_id)
