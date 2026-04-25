from enum import StrEnum


class UserRole(StrEnum):
    admin = "admin"
    storekeeper = "storekeeper"
    foreman = "foreman"
    worker = "worker"
    viewer = "viewer"


class InventoryType(StrEnum):
    fixture = "fixture"
    cutting_tool = "cutting_tool"
    turning_tool = "turning_tool"
    milling_tool = "milling_tool"
    measuring_tool = "measuring_tool"
    part = "part"
    consumable = "consumable"
    other = "other"


class InventoryStatus(StrEnum):
    available = "available"
    reserved = "reserved"
    issued = "issued"
    in_repair = "in_repair"
    written_off = "written_off"
    lost = "lost"
    needs_check = "needs_check"


class OrderPriority(StrEnum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class OrderStatus(StrEnum):
    draft = "draft"
    created = "created"
    checking_stock = "checking_stock"
    waiting_items = "waiting_items"
    ready_to_release = "ready_to_release"
    released = "released"
    issued_to_workshop = "issued_to_workshop"
    received_by_workshop = "received_by_workshop"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class RequirementStatus(StrEnum):
    required = "required"
    available = "available"
    partially_available = "partially_available"
    reserved = "reserved"
    issued = "issued"
    returned = "returned"
    missing = "missing"


class TransactionType(StrEnum):
    receipt = "receipt"
    reserve = "reserve"
    unreserve = "unreserve"
    issue = "issue"
    return_ = "return"
    move = "move"
    repair_start = "repair_start"
    repair_finish = "repair_finish"
    write_off = "write_off"
    lost = "lost"
    adjustment = "adjustment"
