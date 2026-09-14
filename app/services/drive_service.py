from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.placement_drive import PlacementDrive
from app.schemas.drive import DriveCreate, DriveUpdate
from app.utils.exceptions import NotFoundError


def list_drives(db: Session) -> list[PlacementDrive]:
    return list(
        db.execute(select(PlacementDrive).order_by(PlacementDrive.start_date.desc())).scalars().all()
    )


def get_drive(db: Session, drive_id: int) -> PlacementDrive:
    drive = db.get(PlacementDrive, drive_id)
    if drive is None:
        raise NotFoundError("Placement drive not found")
    return drive


def create_drive(db: Session, payload: DriveCreate) -> PlacementDrive:
    drive = PlacementDrive(**payload.model_dump())
    db.add(drive)
    db.commit()
    db.refresh(drive)
    return drive


def update_drive(db: Session, drive: PlacementDrive, payload: DriveUpdate) -> PlacementDrive:
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(drive, field, value)
    db.commit()
    db.refresh(drive)
    return drive
