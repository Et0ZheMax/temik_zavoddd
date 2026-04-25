from sqlalchemy.orm import Session

from app.models import AuditLog


def add_audit(
    db: Session,
    *,
    user_id: int | None,
    entity_type: str,
    entity_id: str,
    action: str,
    before_json: dict | None = None,
    after_json: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            before_json=before_json,
            after_json=after_json,
        )
    )
