from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.audit.service import add_audit
from app.auth.deps import require_roles
from app.database import get_db
from app.models import InventoryItem, OrderRequirement, ProductionOrder, User
from app.models.enums import OrderStatus, RequirementStatus, UserRole
from app.schemas.common import (
    APIMessage,
    OrderCreate,
    OrderIssuePayload,
    OrderOut,
    OrderReturnPayload,
    RequirementCreate,
    RequirementOut,
)
from app.services.order_service import check_stock, confirm_received, issue_requirement, recalc_order_status, release_order, reserve_order, return_requirement

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _get_order(db: Session, order_id: int) -> ProductionOrder:
    order = db.query(ProductionOrder).options(joinedload(ProductionOrder.requirements)).filter(ProductionOrder.id == order_id).first()
    if not order:
        raise HTTPException(404, "Заказ не найден")
    return order


@router.get("", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db), q: str | None = None, status: OrderStatus | None = None, skip: int = 0, limit: int = Query(default=50, le=200), _=Depends(require_roles(UserRole.viewer, UserRole.worker, UserRole.foreman, UserRole.storekeeper, UserRole.admin))):
    query = db.query(ProductionOrder)
    if q:
        query = query.filter(ProductionOrder.order_number.ilike(f"%{q}%"))
    if status:
        query = query.filter(ProductionOrder.status == status)
    return query.order_by(ProductionOrder.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=OrderOut)
def create_order(payload: OrderCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.admin, UserRole.foreman))):
    order = ProductionOrder(**payload.model_dump(), created_by_id=user.id, status=OrderStatus.created)
    db.add(order)
    db.flush()
    add_audit(db, user_id=user.id, entity_type="order", entity_id=str(order.id), action="create", after_json=payload.model_dump(mode="json"))
    db.commit()
    db.refresh(order)
    return order


@router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db), _=Depends(require_roles(UserRole.viewer, UserRole.worker, UserRole.foreman, UserRole.storekeeper, UserRole.admin))):
    return _get_order(db, order_id)


@router.patch("/{order_id}", response_model=OrderOut)
def patch_order(order_id: int, payload: OrderCreate, db: Session = Depends(get_db), _=Depends(require_roles(UserRole.admin, UserRole.foreman))):
    order = _get_order(db, order_id)
    for k, v in payload.model_dump().items():
        setattr(order, k, v)
    db.commit()
    return order


@router.post("/{order_id}/requirements", response_model=RequirementOut)
def add_requirement(order_id: int, payload: RequirementCreate, db: Session = Depends(get_db), _=Depends(require_roles(UserRole.admin, UserRole.foreman, UserRole.storekeeper))):
    order = _get_order(db, order_id)
    item = db.query(InventoryItem).filter(InventoryItem.id == payload.inventory_item_id).first()
    if not item:
        raise HTTPException(404, "Позиция не найдена")
    req = OrderRequirement(order_id=order.id, **payload.model_dump())
    if item.available_quantity >= payload.required_quantity:
        req.status = RequirementStatus.available
    elif item.available_quantity == 0:
        req.status = RequirementStatus.missing
    else:
        req.status = RequirementStatus.partially_available
    db.add(req)
    db.flush()
    order.requirements.append(req)
    recalc_order_status(order)
    db.commit()
    db.refresh(req)
    return req


@router.patch("/{order_id}/requirements/{requirement_id}", response_model=RequirementOut)
def patch_requirement(order_id: int, requirement_id: int, payload: RequirementCreate, db: Session = Depends(get_db), _=Depends(require_roles(UserRole.admin, UserRole.foreman, UserRole.storekeeper))):
    _ = _get_order(db, order_id)
    req = db.query(OrderRequirement).filter(OrderRequirement.id == requirement_id, OrderRequirement.order_id == order_id).first()
    if not req:
        raise HTTPException(404, "Требование не найдено")
    req.required_quantity = payload.required_quantity
    req.comment = payload.comment
    db.commit()
    return req


@router.delete("/{order_id}/requirements/{requirement_id}", response_model=APIMessage)
def delete_requirement(order_id: int, requirement_id: int, db: Session = Depends(get_db), _=Depends(require_roles(UserRole.admin, UserRole.foreman))):
    req = db.query(OrderRequirement).filter(OrderRequirement.id == requirement_id, OrderRequirement.order_id == order_id).first()
    if not req:
        raise HTTPException(404, "Требование не найдено")
    db.delete(req)
    db.commit()
    return APIMessage(message="Позиция убрана из заказа")


@router.post("/{order_id}/check-stock", response_model=APIMessage)
def do_check_stock(order_id: int, db: Session = Depends(get_db), _=Depends(require_roles(UserRole.admin, UserRole.foreman, UserRole.storekeeper))):
    order = _get_order(db, order_id)
    check_stock(db, order)
    db.commit()
    return APIMessage(message="Наличие проверено")


@router.post("/{order_id}/reserve", response_model=APIMessage)
def do_reserve(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.admin, UserRole.storekeeper))):
    order = _get_order(db, order_id)
    reserve_order(db, order, user.id)
    db.commit()
    return APIMessage(message="Позиции зарезервированы")


@router.post("/{order_id}/release", response_model=APIMessage)
def do_release(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.admin, UserRole.foreman))):
    order = _get_order(db, order_id)
    release_order(order)
    add_audit(db, user_id=user.id, entity_type="order", entity_id=str(order.id), action="release")
    db.commit()
    return APIMessage(message="Заказ выпущен")


@router.post("/{order_id}/issue", response_model=APIMessage)
def do_issue(order_id: int, payload: OrderIssuePayload, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.admin, UserRole.storekeeper))):
    order = _get_order(db, order_id)
    req = db.query(OrderRequirement).filter(OrderRequirement.id == payload.requirement_id, OrderRequirement.order_id == order.id).first()
    if not req:
        raise HTTPException(404, "Требование не найдено")
    issue_requirement(db, order, req, payload.quantity, user.id, payload.to_location_id)
    add_audit(db, user_id=user.id, entity_type="order", entity_id=str(order.id), action="issue")
    db.commit()
    return APIMessage(message="Выдача выполнена")


@router.post("/{order_id}/confirm-received", response_model=APIMessage)
def do_confirm_received(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.admin, UserRole.foreman))):
    order = _get_order(db, order_id)
    confirm_received(order)
    add_audit(db, user_id=user.id, entity_type="order", entity_id=str(order.id), action="confirm_received")
    db.commit()
    return APIMessage(message="Получение подтверждено")


@router.post("/{order_id}/return", response_model=APIMessage)
def do_return(order_id: int, payload: OrderReturnPayload, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.admin, UserRole.storekeeper, UserRole.foreman))):
    order = _get_order(db, order_id)
    req = db.query(OrderRequirement).filter(OrderRequirement.id == payload.requirement_id, OrderRequirement.order_id == order.id).first()
    if not req:
        raise HTTPException(404, "Требование не найдено")
    return_requirement(db, order, req, payload.quantity, user.id, payload.damaged, payload.comment)
    db.commit()
    return APIMessage(message="Возврат зафиксирован")


@router.post("/{order_id}/complete", response_model=APIMessage)
def do_complete(order_id: int, db: Session = Depends(get_db), _=Depends(require_roles(UserRole.admin, UserRole.foreman))):
    order = _get_order(db, order_id)
    order.status = OrderStatus.completed
    db.commit()
    return APIMessage(message="Заказ завершен")


@router.post("/{order_id}/cancel", response_model=APIMessage)
def do_cancel(order_id: int, db: Session = Depends(get_db), _=Depends(require_roles(UserRole.admin, UserRole.foreman))):
    order = _get_order(db, order_id)
    order.status = OrderStatus.cancelled
    db.commit()
    return APIMessage(message="Заказ отменен")
