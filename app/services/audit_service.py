"""
Audit logging.

A thin helper other services call after sensitive actions (status changes,
job creation, etc.). Never raises on its own - a logging failure should
never break the request that triggered it, so any DB error here is
swallowed after a rollback of just this insert.
"""
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.enums import AuditAction


def log_action(
    db: Session,
    *,
    user_id: Optional[int],
    action: AuditAction,
    entity_type: str,
    entity_id: Optional[int] = None,
    details: Optional[dict] = None,
) -> None:
    """
    Record an audit log entry. Call this from within an existing request's
    session - it does NOT commit; it relies on the caller's own commit so
    the audit entry is part of the same transaction as the action it
    records (e.g. an application status update and its audit row either
    both persist or both roll back together).
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details_json=details,
    )
    db.add(entry)


def list_audit_logs(db: Session, *, offset: int, limit: int) -> tuple[list[AuditLog], int]:
    total_count = db.scalar(select(func.count()).select_from(AuditLog)) or 0
    rows = (
        db.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        )
        .scalars()
        .all()
    )
    return list(rows), total_count
