from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import require_roles
from app.database import get_db
from app.models import InventoryTransaction
from app.models.enums import UserRole
from app.schemas.common import TransactionOut

router = APIRouter(tags=["transactions"])


@router.get("/api/transactions", response_model=list[TransactionOut])
def list_transactions(db: Session = Depends(get_db), _=Depends(require_roles(UserRole.viewer, UserRole.worker, UserRole.foreman, UserRole.storekeeper, UserRole.admin))):
    return db.query(InventoryTransaction).order_by(InventoryTransaction.performed_at.desc()).limit(200).all()
