from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.enums import UserRole
from app.schemas.skill import SkillCreate, SkillRead
from app.security.dependencies import get_current_user, require_role
from app.services import skill_service

router = APIRouter()


@router.get("", response_model=list[SkillRead])
def list_skills(
    search: Optional[str] = Query(default=None, description="Filter by partial skill name"),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
) -> list:
    return skill_service.list_skills(db, search=search)


@router.post("", response_model=SkillRead, status_code=status.HTTP_201_CREATED)
def create_skill(
    payload: SkillCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_role(UserRole.ADMIN)),
) -> SkillRead:
    return skill_service.create_skill(db, payload)
