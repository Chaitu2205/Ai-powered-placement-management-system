from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.skill import Skill
from app.schemas.skill import SkillCreate


def list_skills(db: Session, *, search: str | None = None) -> list[Skill]:
    stmt = select(Skill).order_by(Skill.name)
    if search:
        stmt = stmt.where(Skill.name.ilike(f"%{search}%"))
    return list(db.execute(stmt).scalars().all())


def get_or_create_skill(db: Session, name: str) -> Skill:
    """
    Used internally by job/student-skill creation so callers can pass a
    skill name without first knowing whether it exists yet.
    """
    normalized = name.strip()
    skill = db.execute(select(Skill).where(Skill.name == normalized)).scalar_one_or_none()
    if skill is None:
        skill = Skill(name=normalized)
        db.add(skill)
        db.flush()  # assign skill.id without committing the caller's transaction
    return skill


def create_skill(db: Session, payload: SkillCreate) -> Skill:
    skill = get_or_create_skill(db, payload.name)
    if payload.category and not skill.category:
        skill.category = payload.category
    db.commit()
    db.refresh(skill)
    return skill
