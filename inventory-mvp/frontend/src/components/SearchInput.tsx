export default function SearchInput({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return <input className="w-full rounded-lg border border-slate-300 p-3" placeholder="Поиск..." value={value} onChange={(e) => onChange(e.target.value)} />
}
