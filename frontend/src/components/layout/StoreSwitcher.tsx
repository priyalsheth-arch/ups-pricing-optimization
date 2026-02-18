import { useQuery } from '@tanstack/react-query'
import { getStores } from '../../api/stores'
import { useAuthStore } from '../../store/authStore'
import { useState, useEffect } from 'react'
import { Store } from 'lucide-react'

// Simple global store selection state
let _selectedStoreId: number | null = null
const _listeners: Array<(id: number | null) => void> = []

export function getSelectedStoreId() { return _selectedStoreId }
export function useSelectedStore() {
  const [storeId, setStoreId] = useState<number | null>(_selectedStoreId)
  useEffect(() => {
    _listeners.push(setStoreId)
    return () => { const i = _listeners.indexOf(setStoreId); if (i >= 0) _listeners.splice(i, 1) }
  }, [])
  return storeId
}
function setSelectedStoreId(id: number | null) {
  _selectedStoreId = id
  _listeners.forEach((l) => l(id))
}

export default function StoreSwitcher() {
  const { data: stores = [] } = useQuery({ queryKey: ['stores'], queryFn: getStores })
  const authStoreId = useAuthStore((s) => s.store_id)
  const role = useAuthStore((s) => s.role)
  const [selected, setSelected] = useState<number | null>(null)

  useEffect(() => {
    if (stores.length > 0 && selected === null) {
      const initial = authStoreId ?? stores[0]?.id ?? null
      setSelected(initial)
      setSelectedStoreId(initial)
    }
  }, [stores, authStoreId, selected])

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = parseInt(e.target.value)
    setSelected(id)
    setSelectedStoreId(id)
  }

  if (role === 'staff') {
    const store = stores.find((s) => s.id === authStoreId)
    return (
      <div className="flex items-center gap-2 text-sm font-medium">
        <Store size={16} className="text-brand-brown" />
        {store?.name ?? 'Loading...'}
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <Store size={16} className="text-brand-brown" />
      <select
        value={selected ?? ''}
        onChange={handleChange}
        className="text-sm font-medium border border-gray-200 rounded-lg px-3 py-1.5 bg-white focus:outline-none focus:ring-2 focus:ring-brand-gold"
      >
        {stores.map((s) => (
          <option key={s.id} value={s.id}>
            {s.name}
          </option>
        ))}
      </select>
    </div>
  )
}
