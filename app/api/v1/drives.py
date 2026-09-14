from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.drive import DriveCreate, DriveRead, DriveUpdate
from app.security.dependencies import get_current_user, require_role
from app.services import drive_service

router = APIRouter()


@router.get("", response_model=list[DriveRead])
def list_drives(db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> list:
    return drive_service.list_drives(db)


@router.post("", response_model=DriveRead, status_code=status.HTTP_201_CREATED)
def create_drive(
    payload: DriveCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
) -> DriveRead:
    return drive_service.create_drive(db, payload)


@router.get("/{drive_id}", response_model=DriveRead)
def get_drive(
    drive_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)
) -> DriveRead:
    return drive_service.get_drive(db, drive_id)


@router.put("/{drive_id}", response_model=DriveRead)
def update_drive(
    drive_id: int,
    payload: DriveUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
) -> DriveRead:
    drive = drive_service.get_drive(db, drive_id)
    return drive_service.update_drive(db, drive, payload)
