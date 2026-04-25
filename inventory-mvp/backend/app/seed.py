from datetime import date

from app.auth.security import hash_password
from app.database import SessionLocal
from app.models import Department, InventoryItem, Location, ProductionOrder, User
from app.models.enums import InventoryStatus, InventoryType, OrderPriority, OrderStatus, UserRole


def run_seed() -> None:
    db = SessionLocal()
    try:
        if db.query(User).first():
            return
        departments = [
            Department(name="Склад оснастки", code="WH-TOOL"),
            Department(name="Токарный цех", code="SHOP-TURN"),
            Department(name="Фрезерный цех", code="SHOP-MILL"),
            Department(name="Сборочный участок", code="SHOP-ASM"),
        ]
        db.add_all(departments)
        db.flush()

        users = [
            User(full_name="Администратор", username="admin", password_hash=hash_password("admin123"), role=UserRole.admin),
            User(full_name="Кладовщик", username="sklad", password_hash=hash_password("sklad123"), role=UserRole.storekeeper, department_id=departments[0].id),
            User(full_name="Мастер", username="master", password_hash=hash_password("master123"), role=UserRole.foreman, department_id=departments[1].id),
            User(full_name="Наблюдатель", username="viewer", password_hash=hash_password("viewer123"), role=UserRole.viewer),
        ]
        db.add_all(users)
        db.flush()

        locs = [
            Location(name="Склад / Стеллаж A / Ячейка 01", code="A-01", department_id=departments[0].id),
            Location(name="Склад / Стеллаж A / Ячейка 02", code="A-02", department_id=departments[0].id),
            Location(name="Инструментальная кладовая", code="TOOL-ROOM", department_id=departments[0].id),
            Location(name="Токарный цех / Пост 1", code="TURN-1", department_id=departments[1].id),
            Location(name="Фрезерный цех / Пост 1", code="MILL-1", department_id=departments[2].id),
            Location(name="Ремонтная зона", code="REPAIR"),
            Location(name="Списанное", code="SCRAP"),
        ]
        db.add_all(locs)
        db.flush()

        items = [
            ("Патрон токарный 250 мм", InventoryType.fixture, 2),
            ("Резец проходной 20x20", InventoryType.turning_tool, 20),
            ("Фреза концевая 10 мм", InventoryType.milling_tool, 15),
            ("Фреза концевая 16 мм", InventoryType.milling_tool, 12),
            ("Кондуктор сверлильный КС-001", InventoryType.fixture, 1),
            ("Штангенциркуль 0-150", InventoryType.measuring_tool, 8),
            ("Деталь ДТ-042 корпус", InventoryType.part, 50),
            ("Пластина твердосплавная CNMG", InventoryType.consumable, 200),
            ("Сверло 8.5 мм", InventoryType.cutting_tool, 40),
            ("Оправка фрезерная ISO40", InventoryType.milling_tool, 6),
        ]
        for i, (name, item_type, qty) in enumerate(items, start=1):
            db.add(
                InventoryItem(
                    inventory_number=f"INV-{i:04}",
                    name=name,
                    category="Основная",
                    type=item_type,
                    unit="шт",
                    total_quantity=qty,
                    available_quantity=qty,
                    reserved_quantity=0,
                    issued_quantity=0,
                    min_stock_quantity=max(1, qty // 5),
                    location_id=locs[0].id,
                    status=InventoryStatus.available,
                )
            )

        orders = [
            ("ЗАК-2026-001", "Изготовление корпуса"),
            ("ЗАК-2026-002", "Доработка втулки"),
            ("ЗАК-2026-003", "Партия деталей по чертежу"),
        ]
        for num, title in orders:
            db.add(
                ProductionOrder(
                    order_number=num,
                    title=title,
                    priority=OrderPriority.normal,
                    status=OrderStatus.created,
                    department_id=departments[1].id,
                    planned_start_date=date.today(),
                    planned_finish_date=date.today(),
                    created_by_id=users[0].id,
                )
            )

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
