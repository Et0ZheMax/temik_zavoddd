# Inventory MVP — учёт оснастки, инструмента, деталей и производственных заказов

Production-minded MVP для цеха/предприятия с mobile-first UI (работает на ПК и смартфонах, включая ширину 390px).

## Стек

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.x, Pydantic v2, JWT, Alembic (каркас), PostgreSQL.
- **Frontend**: React + TypeScript + Vite + Tailwind + React Router + TanStack Query + Zustand.
- **Infra**: Docker Compose, `.env`, seed-данные, backend unit-tests.

## Архитектура

### Backend layers
- `app/models` — ORM модели.
- `app/schemas` — DTO/Pydantic схемы.
- `app/services` — бизнес-логика остатков и заказов.
- `app/routers` — REST API.
- `app/auth` — JWT + роли.
- `app/audit` — аудит ключевых действий.
- `app/tests` — тесты бизнес-правил.

Ключевая идея: **изменение остатков только через сервисы + InventoryTransaction**.

### Frontend layers
- `src/api` — HTTP client.
- `src/pages` — страницы.
- `src/components` — переиспользуемые UI-компоненты.
- `src/store` — auth state.
- `src/utils` — status maps RU.

## Запуск

```bash
cd inventory-mvp
docker compose up --build
```

- Frontend: `http://localhost:4456`
- Backend: `http://localhost:8008`
- Swagger: `http://localhost:8008/docs`

## Миграции

В MVP включён каркас Alembic. На старте backend также делает `create_all()`.

```bash
docker compose exec backend alembic upgrade head
```

## Seed-данные

```bash
docker compose exec backend python -m app.seed
```

## Тестовые логины

- `admin / admin123`
- `sklad / sklad123`
- `master / master123`
- `viewer / viewer123`

## Реализованные сценарии MVP

- Создание/редактирование номенклатуры.
- Список и поиск номенклатуры.
- Создание заказа.
- Добавление требований заказа.
- Проверка наличия.
- Резервирование под заказ.
- Выпуск заказа.
- Выдача в цех.
- Подтверждение получения цехом.
- Возврат (в т.ч. с флагом повреждения).
- Ремонт/списание/потеря через транзакции.
- Dashboard summary.
- Журнал транзакций.

## Роли

- `admin`: полный доступ.
- `storekeeper`: склад, остатки, выдачи/возвраты.
- `foreman`: заказы, подтверждения.
- `worker`: просмотр.
- `viewer`: просмотр.

## Бизнес-правила

- Нельзя резервировать/выдавать сверх доступного.
- Нельзя подтвердить получение до выдачи.
- Нельзя выпустить заказ с missing-позициями.
- Списание требует комментария.
- Ключевые операции записываются в `InventoryTransaction` и `AuditLog`.

## Тесты

```bash
docker compose exec backend pytest app/tests -q
```

Покрыто минимум:
1. reserve > available запрещён;
2. issue > reserved запрещён;
3. reserve меняет available/reserved;
4. issue меняет reserved/issued;
5. return меняет issued/available;
6. missing-order нельзя release;
7. confirm received до issue запрещён;
8. операции создают InventoryTransaction.

## Известные ограничения MVP

- Нет интеграции 1С/ERP.
- Нет аппаратного сканера/печати QR.
- Нет Excel import/export.
- Нет сложных workflow согласования.
- Нет уведомлений Telegram/email.

## Что добавить следующим этапом

- Полноценные Alembic миграции.
- Более детальные ACL-политики.
- Карточка заказа с timeline и детальными действиями на фронтенде.
- Загрузка фото/чертежей.
- QR label & mobile scanning.
- Интеграция с AD/LDAP и 1С.
