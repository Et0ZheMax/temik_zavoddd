import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '../api/client'
import Badge from '../components/Badge'
import SearchInput from '../components/SearchInput'
import { orderStatusMap } from '../utils/statusMaps'

export default function OrdersPage() {
  const [q, setQ] = useState('')
  const { data = [] } = useQuery({ queryKey: ['orders', q], queryFn: async () => (await api.get('/orders', { params: { q } })).data })
  return (
    <div className="space-y-3">
      <SearchInput value={q} onChange={setQ} />
      <div className="space-y-2">{data.map((o: any) => <div key={o.id} className="card"><div className="font-medium">{o.order_number} — {o.title}</div><div className="mt-2"><Badge text={orderStatusMap[o.status]} /></div></div>)}</div>
    </div>
  )
}
