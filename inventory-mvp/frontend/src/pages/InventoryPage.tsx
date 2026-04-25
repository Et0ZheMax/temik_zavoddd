import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { api } from '../api/client'
import Badge from '../components/Badge'
import SearchInput from '../components/SearchInput'
import { inventoryStatusMap } from '../utils/statusMaps'

export default function InventoryPage() {
  const [q, setQ] = useState('')
  const { data = [] } = useQuery({ queryKey: ['inventory', q], queryFn: async () => (await api.get('/inventory', { params: { q } })).data })
  return (
    <div className="space-y-3">
      <SearchInput value={q} onChange={setQ} />
      <div className="hidden md:block card overflow-auto">
        <table className="w-full text-sm"><thead><tr><th>Наименование</th><th>Доступно</th><th>Резерв</th><th>Выдано</th><th>Статус</th></tr></thead>
          <tbody>{data.map((item: any) => <tr key={item.id}><td>{item.name}</td><td>{item.available_quantity}</td><td>{item.reserved_quantity}</td><td>{item.issued_quantity}</td><td><Badge text={inventoryStatusMap[item.status]} /></td></tr>)}</tbody>
        </table>
      </div>
      <div className="md:hidden space-y-2">{data.map((item: any) => <div key={item.id} className="card"><div className="font-medium">{item.name}</div><div className="text-sm">Доступно: {item.available_quantity}</div><div className="text-sm">Резерв: {item.reserved_quantity}</div><div className="text-sm">Выдано: {item.issued_quantity}</div><Badge text={inventoryStatusMap[item.status]} /></div>)}</div>
    </div>
  )
}
