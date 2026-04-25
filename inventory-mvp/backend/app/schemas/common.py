from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    InventoryStatus,
    InventoryType,
    OrderPriority,
    OrderStatus,
    RequirementStatus,
    TransactionType,
    UserRole,
)


class APIMessage(BaseModel):
    message: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DepartmentBase(BaseModel):
    name: str
    code: str
    description: str | None = None
    is_active: bool = True


class DepartmentOut(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class LocationBase(BaseModel):
    name: str
    code: str
    department_id: int | None = None
    description: str | None = None
    is_active: bool = True


class LocationOut(LocationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class UserCreate(BaseModel):
    full_name: str
    username: str
    password: str
    role: UserRole
    department_id: int | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    username: str
    role: UserRole
    department_id: int | None
    is_active: bool


class InventoryCreate(BaseModel):
    inventory_number: str | None = None
    name: str
    category: str
    type: InventoryType
    specification: str | None = None
    drawing_number: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    material: str | None = None
    unit: str = "шт"
    total_quantity: int = Field(ge=0)
    min_stock_quantity: int = Field(default=0, ge=0)
    location_id: int | None = None
    notes: str | None = None


class InventoryUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    specification: str | None = None
    drawing_number: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    material: str | None = None
    min_stock_quantity: int | None = Field(default=None, ge=0)
    location_id: int | None = None
    status: InventoryStatus | None = None
    notes: str | None = None


class InventoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    inventory_number: str | None
    name: str
    category: str
    type: InventoryType
    unit: str
    total_quantity: int
    available_quantity: int
    reserved_quantity: int
    issued_quantity: int
    min_stock_quantity: int
    location_id: int | None
    status: InventoryStatus
    notes: str | None


class QtyPayload(BaseModel):
    quantity: int = Field(gt=0)
    comment: str | None = None
    to_location_id: int | None = None


class OrderCreate(BaseModel):
    order_number: str
    title: str
    customer: str | None = None
    product_name: str | None = None
    drawing_number: str | None = None
    priority: OrderPriority = OrderPriority.normal
    department_id: int
    planned_start_date: date
    planned_finish_date: date
    notes: str | None = None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    order_number: str
    title: str
    priority: OrderPriority
    status: OrderStatus
    department_id: int
    released_at: datetime | None
    workshop_received_at: datetime | None


class RequirementCreate(BaseModel):
    inventory_item_id: int
    required_quantity: int = Field(gt=0)
    comment: str | None = None


class RequirementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    inventory_item_id: int
    required_quantity: int
    reserved_quantity: int
    issued_quantity: int
    returned_quantity: int
    status: RequirementStatus
    comment: str | None


class OrderIssuePayload(BaseModel):
    requirement_id: int
    quantity: int = Field(gt=0)
    to_location_id: int | None = None
    comment: str | None = None


class OrderReturnPayload(BaseModel):
    requirement_id: int
    quantity: int = Field(gt=0)
    damaged: bool = False
    comment: str | None = None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    inventory_item_id: int
    order_id: int | None
    quantity: int
    transaction_type: TransactionType
    performed_by_id: int
    performed_at: datetime
    comment: str | None


class DashboardSummary(BaseModel):
    active_orders: int
    waiting_items_orders: int
    ready_to_release_orders: int
    issued_not_confirmed_orders: int
    low_stock_items: int
    in_repair_items: int
    recent_transactions: list[TransactionOut]
