from sqlalchemy.orm import Session

from app.models import InventoryItem


class InventoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id_for_update(self, item_id: int) -> InventoryItem | None:
        return self.db.query(InventoryItem).filter(InventoryItem.id == item_id).with_for_update().first()
