from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import InventoryItem, OrderRequirement, ProductionOrder
from app.models.enums import OrderStatus, RequirementStatus
from app.services.inventory_service import issue_item, reserve_item, return_item


def recalc_requirement_status(req: OrderRequirement, item: InventoryItem) -> None:
    if req.issued_quantity >= req.required_quantity:
        req.status = RequirementStatus.issued
        return
    if req.returned_quantity >= req.required_quantity:
        req.status = RequirementStatus.returned
        return
    if req.reserved_quantity >= req.required_quantity:
        req.status = RequirementStatus.reserved
        return
    if item.available_quantity >= req.required_quantity:
        req.status = RequirementStatus.available
    elif item.available_quantity == 0:
        req.status = RequirementStatus.missing
    else:
        req.status = RequirementStatus.partially_available


def recalc_order_status(order: ProductionOrder) -> None:
    reqs = order.requirements
    if not reqs:
        order.status = OrderStatus.created
        return
    statuses = {r.status for r in reqs}
    if RequirementStatus.missing in statuses or RequirementStatus.partially_available in statuses:
        order.status = OrderStatus.waiting_items
    elif all(s in {RequirementStatus.available, RequirementStatus.reserved, RequirementStatus.issued, RequirementStatus.returned} for s in statuses):
        if all(s in {RequirementStatus.reserved, RequirementStatus.issued, RequirementStatus.returned} for s in statuses):
            order.status = OrderStatus.ready_to_release
        else:
            order.status = OrderStatus.checking_stock


def check_stock(db: Session, order: ProductionOrder) -> None:
    for req in order.requirements:
        item = db.query(InventoryItem).filter(InventoryItem.id == req.inventory_item_id).first()
        recalc_requirement_status(req, item)
    recalc_order_status(order)


def reserve_order(db: Session, order: ProductionOrder, user_id: int) -> None:
    for req in order.requirements:
        qty_to_reserve = req.required_quantity - req.reserved_quantity
        if qty_to_reserve <= 0:
            continue
        item = db.query(InventoryItem).filter(InventoryItem.id == req.inventory_item_id).with_for_update().first()
        reserve_item(db, item, qty_to_reserve, user_id, order.id)
        req.reserved_quantity += qty_to_reserve
        req.status = RequirementStatus.reserved
    recalc_order_status(order)


def release_order(order: ProductionOrder) -> None:
    if order.status == OrderStatus.waiting_items:
        raise HTTPException(400, "Заказ с недостающими позициями нельзя выпустить")
    if any(r.status in {RequirementStatus.missing, RequirementStatus.partially_available} for r in order.requirements):
        raise HTTPException(400, "Не все позиции доступны")
    order.status = OrderStatus.released
    order.released_at = datetime.utcnow()


def issue_requirement(db: Session, order: ProductionOrder, req: OrderRequirement, quantity: int, user_id: int, to_location_id: int | None) -> None:
    if order.status not in {OrderStatus.released, OrderStatus.issued_to_workshop}:
        raise HTTPException(400, "Можно выдавать только выпущенный заказ")
    item = db.query(InventoryItem).filter(InventoryItem.id == req.inventory_item_id).with_for_update().first()
    from_reserved = req.reserved_quantity > 0
    issue_item(db, item, quantity, user_id, order.id, to_location_id, from_reserved=from_reserved)
    if from_reserved:
        req.reserved_quantity -= quantity
    req.issued_quantity += quantity
    req.status = RequirementStatus.issued
    order.status = OrderStatus.issued_to_workshop


def confirm_received(order: ProductionOrder) -> None:
    if order.status != OrderStatus.issued_to_workshop:
        raise HTTPException(400, "Подтверждение возможно только после выдачи")
    order.status = OrderStatus.received_by_workshop
    order.workshop_received_at = datetime.utcnow()


def return_requirement(db: Session, order: ProductionOrder, req: OrderRequirement, quantity: int, user_id: int, damaged: bool, comment: str | None) -> None:
    item = db.query(InventoryItem).filter(InventoryItem.id == req.inventory_item_id).with_for_update().first()
    return_item(db, item, quantity, user_id, order.id, damaged, comment)
    req.returned_quantity += quantity
    if req.returned_quantity >= req.required_quantity:
        req.status = RequirementStatus.returned
