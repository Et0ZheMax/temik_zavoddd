from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.deps import require_roles
from app.database import get_db
from app.models import InventoryItem, InventoryTransaction, ProductionOrder
from app.models.enums import InventoryStatus, OrderStatus, UserRole
from app.schemas.common import DashboardSummary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db), _=Depends(require_roles(UserRole.viewer, UserRole.worker, UserRole.foreman, UserRole.storekeeper, UserRole.admin))):
    active_orders = db.query(func.count(ProductionOrder.id)).filter(ProductionOrder.status.notin_([OrderStatus.completed, OrderStatus.cancelled])).scalar() or 0
    waiting_items = db.query(func.count(ProductionOrder.id)).filter(ProductionOrder.status == OrderStatus.waiting_items).scalar() or 0
    ready = db.query(func.count(ProductionOrder.id)).filter(ProductionOrder.status == OrderStatus.ready_to_release).scalar() or 0
    issued_not_confirmed = db.query(func.count(ProductionOrder.id)).filter(ProductionOrder.status == OrderStatus.issued_to_workshop).scalar() or 0
    low_stock = db.query(func.count(InventoryItem.id)).filter(InventoryItem.available_quantity <= InventoryItem.min_stock_quantity).scalar() or 0
    in_repair = db.query(func.count(InventoryItem.id)).filter(InventoryItem.status == InventoryStatus.in_repair).scalar() or 0
    recent_transactions = db.query(InventoryTransaction).order_by(InventoryTransaction.performed_at.desc()).limit(10).all()
    return DashboardSummary(
        active_orders=active_orders,
        waiting_items_orders=waiting_items,
        ready_to_release_orders=ready,
        issued_not_confirmed_orders=issued_not_confirmed,
        low_stock_items=low_stock,
        in_repair_items=in_repair,
        recent_transactions=recent_transactions,
    )
