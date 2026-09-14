from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.enums import UserRole
from app.schemas.department import DepartmentCreate, DepartmentRead
from app.security.dependencies import get_current_user, require_role
from app.services import department_service

router = APIRouter()


@router.get("", response_model=list[DepartmentRead])
def list_departments(db: Session = Depends(get_db), _user=Depends(get_current_user)) -> list:
    """Any authenticated user can view the department list (needed for registration/job forms)."""
    return department_service.list_departments(db)


@router.post("", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_role(UserRole.ADMIN)),
) -> DepartmentRead:
    return department_service.create_department(db, payload)
