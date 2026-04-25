export const inventoryStatusMap: Record<string, string> = {
  available: 'В наличии', reserved: 'Зарезервировано', issued: 'Выдано', in_repair: 'В ремонте', written_off: 'Списано', lost: 'Потеряно', needs_check: 'Требует проверки'
}
export const orderStatusMap: Record<string, string> = {
  draft: 'Черновик', created: 'Создан', checking_stock: 'Проверка наличия', waiting_items: 'Ожидает позиции', ready_to_release: 'Готов к выпуску', released: 'Выпущен', issued_to_workshop: 'Выдан в цех', received_by_workshop: 'Получен цехом', in_progress: 'В работе', completed: 'Завершён', cancelled: 'Отменён'
}
