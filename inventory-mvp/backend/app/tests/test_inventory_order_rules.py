from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Department, InventoryItem, OrderRequirement, ProductionOrder, User
from app.models.entities import Base
from app.models.enums import InventoryStatus, InventoryType, OrderStatus, RequirementStatus, UserRole
from app.services.inventory_service import reserve_item
from app.services.order_service import confirm_received, issue_requirement, release_order, return_requirement


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    dep = Department(name="D", code="D")
    user = User(full_name="U", username="u", password_hash="x", role=UserRole.admin)
    item = InventoryItem(name="I", category="C", type=InventoryType.fixture, unit="шт", total_quantity=10, available_quantity=10)
    order = ProductionOrder(order_number="O-1", title="T", department_id=1, planned_start_date=date.today(), planned_finish_date=date.today(), created_by_id=1, status=OrderStatus.released)
    session.add_all([dep, user, item])
    session.flush()
    order.department_id = dep.id
    order.created_by_id = user.id
    session.add(order)
    session.flush()
    req = OrderRequirement(order_id=order.id, inventory_item_id=item.id, required_quantity=5, status=RequirementStatus.reserved, reserved_quantity=5)
    session.add(req)
    session.commit()
    try:
        yield session
    finally:
        session.close()


def test_cannot_reserve_more_than_available(db: Session):
    item = db.query(InventoryItem).first()
    with pytest.raises(HTTPException):
        reserve_item(db, item, 999, 1, 1)


def test_reserve_changes_quantities(db: Session):
    item = db.query(InventoryItem).first()
    reserve_item(db, item, 2, 1, 1)
    assert item.available_quantity == 8
    assert item.reserved_quantity == 2


def test_issue_cannot_exceed_reserved(db: Session):
    order = db.query(ProductionOrder).first()
    req = db.query(OrderRequirement).first()
    with pytest.raises(HTTPException):
        issue_requirement(db, order, req, 99, 1, None)


def test_issue_changes_quantities(db: Session):
    order = db.query(ProductionOrder).first()
    req = db.query(OrderRequirement).first()
    item = db.query(InventoryItem).first()
    issue_requirement(db, order, req, 3, 1, None)
    assert req.reserved_quantity == 2
    assert req.issued_quantity == 3
    assert item.issued_quantity == 3


def test_return_changes_quantities(db: Session):
    order = db.query(ProductionOrder).first()
    req = db.query(OrderRequirement).first()
    issue_requirement(db, order, req, 3, 1, None)
    item = db.query(InventoryItem).first()
    return_requirement(db, order, req, 2, 1, False, "ok")
    assert item.issued_quantity == 1
    assert item.available_quantity == 7


def test_order_with_missing_cannot_release(db: Session):
    order = db.query(ProductionOrder).first()
    order.status = OrderStatus.waiting_items
    with pytest.raises(HTTPException):
        release_order(order)


def test_confirm_received_requires_issue(db: Session):
    order = db.query(ProductionOrder).first()
    order.status = OrderStatus.released
    with pytest.raises(HTTPException):
        confirm_received(order)


def test_operations_create_transactions(db: Session):
    order = db.query(ProductionOrder).first()
    req = db.query(OrderRequirement).first()
    issue_requirement(db, order, req, 1, 1, None)
    txs = db.execute("SELECT COUNT(*) FROM inventory_transactions").scalar()
    assert txs >= 1
