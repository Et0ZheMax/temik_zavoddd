from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.audit.service import add_audit
from app.auth.deps import get_current_user, require_roles
from app.database import get_db
from app.models import InventoryItem, InventoryTransaction, OrderRequirement, User
from app.models.enums import InventoryStatus, TransactionType, UserRole
from app.schemas.common import APIMessage, InventoryCreate, InventoryOut, InventoryUpdate, QtyPayload, TransactionOut
from app.services.inventory_service import create_transaction, write_off_item

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("", response_model=list[InventoryOut])
def list_items(
    db: Session = Depends(get_db),
    q: str | None = None,
    status: InventoryStatus | None = None,
    type: str | None = None,
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    _=Depends(require_roles(UserRole.viewer, UserRole.worker, UserRole.foreman, UserRole.storekeeper, UserRole.admin)),
):
    query = db.query(InventoryItem)
    if q:
        query = query.filter(InventoryItem.name.ilike(f"%{q}%"))
    if status:
        query = query.filter(InventoryItem.status == status)
    if type:
        query = query.filter(InventoryItem.type == type)
    return query.offset(skip).limit(limit).all()


@router.post("", response_model=InventoryOut)
def create_item(payload: InventoryCreate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.admin, UserRole.storekeeper))):
    item = InventoryItem(**payload.model_dump(), available_quantity=payload.total_quantity)
    db.add(item)
    db.flush()
    create_transaction(db, item_id=item.id, user_id=user.id, tx_type=TransactionType.receipt, quantity=payload.total_quantity, comment="Initial receipt")
    add_audit(db, user_id=user.id, entity_type="inventory", entity_id=str(item.id), action="create", after_json=payload.model_dump())
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=InventoryOut)
def get_item(item_id: int, db: Session = Depends(get_db), _=Depends(require_roles(UserRole.viewer, UserRole.worker, UserRole.foreman, UserRole.storekeeper, UserRole.admin))):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Позиция не найдена")
    return item


@router.patch("/{item_id}", response_model=InventoryOut)
def patch_item(item_id: int, payload: InventoryUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.admin, UserRole.storekeeper))):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Позиция не найдена")
    before = {"name": item.name, "status": item.status.value}
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(item, k, v)
    add_audit(db, user_id=user.id, entity_type="inventory", entity_id=str(item.id), action="update", before_json=before, after_json=payload.model_dump(exclude_none=True))
    db.commit()
    return item


@router.post("/{item_id}/receipt", response_model=APIMessage)
def receipt(item_id: int, payload: QtyPayload, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.admin, UserRole.storekeeper))):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).with_for_update().first()
    if not item:
        raise HTTPException(404, "Позиция не найдена")
    item.total_quantity += payload.quantity
    item.available_quantity += payload.quantity
    item.status = InventoryStatus.available
    create_transaction(db, item_id=item.id, user_id=user.id, tx_type=TransactionType.receipt, quantity=payload.quantity, comment=payload.comment)
    db.commit()
    return APIMessage(message="Поступление отражено")


@router.post("/{item_id}/move", response_model=APIMessage)
def move(item_id: int, payload: QtyPayload, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.admin, UserRole.storekeeper))):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Позиция не найдена")
    from_location = item.location_id
    item.location_id = payload.to_location_id
    create_transaction(db, item_id=item.id, user_id=user.id, tx_type=TransactionType.move, quantity=payload.quantity, from_location_id=from_location, to_location_id=payload.to_location_id, comment=payload.comment)
    db.commit()
    return APIMessage(message="Перемещение выполнено")


@router.post("/{item_id}/repair/start", response_model=APIMessage)
def repair_start(item_id: int, payload: QtyPayload, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.admin, UserRole.storekeeper))):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).with_for_update().first()
    if not item or item.available_quantity < payload.quantity:
        raise HTTPException(400, "Недостаточно доступного количества")
    item.available_quantity -= payload.quantity
    item.status = InventoryStatus.in_repair
    create_transaction(db, item_id=item.id, user_id=user.id, tx_type=TransactionType.repair_start, quantity=payload.quantity, comment=payload.comment)
    db.commit()
    return APIMessage(message="Отправлено в ремонт")


@router.post("/{item_id}/repair/finish", response_model=APIMessage)
def repair_finish(item_id: int, payload: QtyPayload, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.admin, UserRole.storekeeper))):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(404, "Позиция не найдена")
    item.available_quantity += payload.quantity
    item.status = InventoryStatus.available
    create_transaction(db, item_id=item.id, user_id=user.id, tx_type=TransactionType.repair_finish, quantity=payload.quantity, comment=payload.comment)
    db.commit()
    return APIMessage(message="Возвращено из ремонта")


@router.post("/{item_id}/write-off", response_model=APIMessage)
def write_off(item_id: int, payload: QtyPayload, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.admin, UserRole.storekeeper))):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).with_for_update().first()
    if not item:
        raise HTTPException(404, "Позиция не найдена")
    write_off_item(db, item, payload.quantity, user.id, payload.comment)
    db.commit()
    return APIMessage(message="Списано")


@router.post("/{item_id}/lost", response_model=APIMessage)
def lost(item_id: int, payload: QtyPayload, db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.admin, UserRole.storekeeper))):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).with_for_update().first()
    if not item or item.available_quantity < payload.quantity:
        raise HTTPException(400, "Недостаточно доступного количества")
    item.available_quantity -= payload.quantity
    item.total_quantity -= payload.quantity
    item.status = InventoryStatus.lost
    create_transaction(db, item_id=item.id, user_id=user.id, tx_type=TransactionType.lost, quantity=payload.quantity, comment=payload.comment)
    db.commit()
    return APIMessage(message="Отмечено как потеря")


@router.get("/{item_id}/transactions", response_model=list[TransactionOut])
def item_transactions(item_id: int, db: Session = Depends(get_db), _=Depends(require_roles(UserRole.viewer, UserRole.worker, UserRole.foreman, UserRole.storekeeper, UserRole.admin))):
    return db.query(InventoryTransaction).filter(InventoryTransaction.inventory_item_id == item_id).order_by(InventoryTransaction.performed_at.desc()).all()
