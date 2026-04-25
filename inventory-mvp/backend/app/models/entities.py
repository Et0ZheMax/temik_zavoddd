from datetime import datetime, date

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import (
    InventoryStatus,
    InventoryType,
    OrderPriority,
    OrderStatus,
    RequirementStatus,
    TransactionType,
    UserRole,
)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    code: Mapped[str] = mapped_column(String(50), unique=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    username: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), index=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class InventoryItem(Base, TimestampMixin):
    __tablename__ = "inventory_items"
    __table_args__ = (
        Index("ix_inventory_items_inventory_number", "inventory_number"),
        Index("ix_inventory_items_name", "name"),
        Index("ix_inventory_items_type", "type"),
        Index("ix_inventory_items_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inventory_number: Mapped[str | None] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(120))
    type: Mapped[InventoryType] = mapped_column(Enum(InventoryType))
    specification: Mapped[str | None] = mapped_column(Text)
    drawing_number: Mapped[str | None] = mapped_column(String(100))
    manufacturer: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(120))
    material: Mapped[str | None] = mapped_column(String(120))
    unit: Mapped[str] = mapped_column(String(30), default="шт")
    total_quantity: Mapped[int] = mapped_column(Integer, default=0)
    available_quantity: Mapped[int] = mapped_column(Integer, default=0)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0)
    issued_quantity: Mapped[int] = mapped_column(Integer, default=0)
    min_stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))
    status: Mapped[InventoryStatus] = mapped_column(Enum(InventoryStatus), default=InventoryStatus.available)
    notes: Mapped[str | None] = mapped_column(Text)
    photo_url: Mapped[str | None] = mapped_column(String(255))
    qr_code: Mapped[str | None] = mapped_column(String(255))


class ProductionOrder(Base, TimestampMixin):
    __tablename__ = "production_orders"
    __table_args__ = (Index("ix_production_orders_order_number", "order_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_number: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    customer: Mapped[str | None] = mapped_column(String(120))
    product_name: Mapped[str | None] = mapped_column(String(120))
    drawing_number: Mapped[str | None] = mapped_column(String(100))
    priority: Mapped[OrderPriority] = mapped_column(Enum(OrderPriority), default=OrderPriority.normal)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.created, index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    planned_start_date: Mapped[date] = mapped_column(Date)
    planned_finish_date: Mapped[date] = mapped_column(Date)
    actual_start_date: Mapped[date | None] = mapped_column(Date)
    actual_finish_date: Mapped[date | None] = mapped_column(Date)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    released_at: Mapped[datetime | None] = mapped_column(DateTime)
    workshop_received_at: Mapped[datetime | None] = mapped_column(DateTime)
    notes: Mapped[str | None] = mapped_column(Text)

    requirements: Mapped[list["OrderRequirement"]] = relationship(back_populates="order", cascade="all,delete-orphan")


class OrderRequirement(Base):
    __tablename__ = "order_requirements"
    __table_args__ = (UniqueConstraint("order_id", "inventory_item_id", name="uq_order_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("production_orders.id"))
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"))
    required_quantity: Mapped[int] = mapped_column(Integer)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0)
    issued_quantity: Mapped[int] = mapped_column(Integer, default=0)
    returned_quantity: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[RequirementStatus] = mapped_column(Enum(RequirementStatus), default=RequirementStatus.required)
    comment: Mapped[str | None] = mapped_column(Text)

    order: Mapped[ProductionOrder] = relationship(back_populates="requirements")


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    __table_args__ = (Index("ix_inventory_transactions_created_at", "performed_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"), index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("production_orders.id"))
    from_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))
    to_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), index=True)
    performed_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    performed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    comment: Mapped[str | None] = mapped_column(Text)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str] = mapped_column(String(80))
    action: Mapped[str] = mapped_column(String(80))
    before_json: Mapped[dict | None] = mapped_column(JSON)
    after_json: Mapped[dict | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(80))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
