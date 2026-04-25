import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

export default function DashboardPage() {
  const { data } = useQuery({ queryKey: ['summary'], queryFn: async () => (await api.get('/dashboard/summary')).data })
  const cards = [
    ['Активные заказы', data?.active_orders],
    ['Ожидают позиции', data?.waiting_items_orders],
    ['Готовы к выпуску', data?.ready_to_release_orders],
    ['Выдано без подтверждения', data?.issued_not_confirmed_orders],
    ['Ниже min остатка', data?.low_stock_items],
    ['В ремонте', data?.in_repair_items],
  ]
  return <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">{cards.map(([k, v]) => <div key={k as string} className="card"><div className="text-sm text-slate-600">{k}</div><div className="text-2xl font-semibold">{v ?? '-'}</div></div>)}</div>
}
