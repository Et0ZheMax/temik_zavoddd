from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import InventoryItem, InventoryTransaction
from app.models.enums import InventoryStatus, TransactionType


def _assert_positive(quantity: int) -> None:
    if quantity <= 0:
        raise HTTPException(400, "Количество должно быть больше 0")


def create_transaction(
    db: Session,
    *,
    item_id: int,
    user_id: int,
    tx_type: TransactionType,
    quantity: int,
    order_id: int | None = None,
    from_location_id: int | None = None,
    to_location_id: int | None = None,
    comment: str | None = None,
) -> None:
    db.add(
        InventoryTransaction(
            inventory_item_id=item_id,
            order_id=order_id,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            quantity=quantity,
            transaction_type=tx_type,
            performed_by_id=user_id,
            comment=comment,
        )
    )


def reserve_item(db: Session, item: InventoryItem, quantity: int, user_id: int, order_id: int) -> None:
    _assert_positive(quantity)
    if item.available_quantity < quantity:
        raise HTTPException(400, "Нельзя зарезервировать больше доступного")
    item.available_quantity -= quantity
    item.reserved_quantity += quantity
    if item.available_quantity == 0:
        item.status = InventoryStatus.reserved
    create_transaction(db, item_id=item.id, user_id=user_id, tx_type=TransactionType.reserve, quantity=quantity, order_id=order_id)


def issue_item(
    db: Session,
    item: InventoryItem,
    quantity: int,
    user_id: int,
    order_id: int,
    to_location_id: int | None,
    from_reserved: bool,
) -> None:
    _assert_positive(quantity)
    if from_reserved:
        if item.reserved_quantity < quantity:
            raise HTTPException(400, "Недостаточно резерва")
        item.reserved_quantity -= quantity
    else:
        if item.available_quantity < quantity:
            raise HTTPException(400, "Недостаточно доступного остатка")
        item.available_quantity -= quantity
    item.issued_quantity += quantity
    item.status = InventoryStatus.issued
    create_transaction(
        db,
        item_id=item.id,
        user_id=user_id,
        tx_type=TransactionType.issue,
        quantity=quantity,
        order_id=order_id,
        to_location_id=to_location_id,
    )


def return_item(db: Session, item: InventoryItem, quantity: int, user_id: int, order_id: int, damaged: bool, comment: str | None) -> None:
    _assert_positive(quantity)
    if item.issued_quantity < quantity:
        raise HTTPException(400, "Нельзя вернуть больше, чем выдано")
    item.issued_quantity -= quantity
    if damaged:
        item.status = InventoryStatus.needs_check
    else:
        item.available_quantity += quantity
        item.status = InventoryStatus.available
    create_transaction(
        db,
        item_id=item.id,
        user_id=user_id,
        tx_type=TransactionType.return_,
        quantity=quantity,
        order_id=order_id,
        comment=comment,
    )


def write_off_item(db: Session, item: InventoryItem, quantity: int, user_id: int, comment: str | None) -> None:
    _assert_positive(quantity)
    if not comment:
        raise HTTPException(400, "Для списания обязателен комментарий")
    if item.available_quantity < quantity:
        raise HTTPException(400, "Недостаточно количества для списания")
    item.available_quantity -= quantity
    item.total_quantity -= quantity
    item.status = InventoryStatus.written_off
    create_transaction(db, item_id=item.id, user_id=user_id, tx_type=TransactionType.write_off, quantity=quantity, comment=comment)
