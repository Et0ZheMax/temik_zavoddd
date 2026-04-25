from sqlalchemy.orm import Session, joinedload

from app.models import ProductionOrder


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_with_requirements(self, order_id: int) -> ProductionOrder | None:
        return (
            self.db.query(ProductionOrder)
            .options(joinedload(ProductionOrder.requirements))
            .filter(ProductionOrder.id == order_id)
            .first()
        )
