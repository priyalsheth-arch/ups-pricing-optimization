import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getCompetitorPrices, upsertCompetitorPrice, deleteCompetitorPrice } from '../api/pricing'
import { COMPETITORS, SERVICE_CATEGORIES } from '../lib/constants'
import { formatCurrency } from '../lib/utils'
import { Plus, Trash2 } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import type { CompetitorPrice } from '../types'

export default function CompetitorPricingPage() {
  const isManager = useAuthStore((s) => s.isManager())
  const qc = useQueryClient()
  const [activeTab, setActiveTab] = useState(COMPETITORS[0])
  const [adding, setAdding] = useState(false)
  const [form, setForm] = useState({
    competitor_name: COMPETITORS[0],
    service_code: '',
    service_category: 'shipping',
    service_name: '',
    unit: '',
    price: '',
    effective_date: new Date().toISOString().split('T')[0],
    source_notes: '',
  })

  const { data: prices = [], isLoading } = useQuery({
    queryKey: ['competitor-prices', activeTab],
    queryFn: () => getCompetitorPrices(undefined, activeTab),
  })

  const upsert = useMutation({
    mutationFn: upsertCompetitorPrice,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['competitor-prices'] }); setAdding(false) },
  })

  const remove = useMutation({
    mutationFn: deleteCompetitorPrice,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['competitor-prices'] }),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    upsert.mutate({ ...form, price: form.price })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Competitor Pricing</h1>
        {isManager && (
          <button
            onClick={() => setAdding(true)}
            className="flex items-center gap-2 bg-brand-brown text-white px-4 py-2 rounded-lg text-sm font-medium"
          >
            <Plus size={16} /> Add Price
          </button>
        )}
      </div>

      {/* Competitor tabs */}
      <div className="flex gap-2 border-b border-gray-200">
        {COMPETITORS.map((c) => (
          <button
            key={c}
            onClick={() => setActiveTab(c)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === c
                ? 'border-brand-brown text-brand-brown'
                : 'border-transparent text-gray-500 hover:text-gray-900'
            }`}
          >
            {c}
          </button>
        ))}
      </div>

      {/* Add form */}
      {adding && isManager && (
        <form onSubmit={handleSubmit} className="bg-brand-gold/10 border border-brand-gold rounded-xl p-4 space-y-3">
          <h3 className="font-semibold text-sm">Add {activeTab} Price</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-600">Service Code</label>
              <input value={form.service_code} onChange={(e) => setForm(f => ({ ...f, service_code: e.target.value, competitor_name: activeTab }))}
                className="w-full border border-gray-200 rounded px-2 py-1.5 text-sm mt-1" placeholder="e.g. UPS_GROUND" required />
            </div>
            <div>
              <label className="text-xs text-gray-600">Service Name</label>
              <input value={form.service_name} onChange={(e) => setForm(f => ({ ...f, service_name: e.target.value }))}
                className="w-full border border-gray-200 rounded px-2 py-1.5 text-sm mt-1" placeholder="e.g. FedEx Ground" required />
            </div>
            <div>
              <label className="text-xs text-gray-600">Category</label>
              <select value={form.service_category} onChange={(e) => setForm(f => ({ ...f, service_category: e.target.value }))}
                className="w-full border border-gray-200 rounded px-2 py-1.5 text-sm mt-1">
                {SERVICE_CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-600">Price ($)</label>
              <input value={form.price} onChange={(e) => setForm(f => ({ ...f, price: e.target.value }))}
                type="number" step="0.01" className="w-full border border-gray-200 rounded px-2 py-1.5 text-sm mt-1" required />
            </div>
            <div>
              <label className="text-xs text-gray-600">Effective Date</label>
              <input type="date" value={form.effective_date} onChange={(e) => setForm(f => ({ ...f, effective_date: e.target.value }))}
                className="w-full border border-gray-200 rounded px-2 py-1.5 text-sm mt-1" />
            </div>
            <div>
              <label className="text-xs text-gray-600">Source Notes</label>
              <input value={form.source_notes} onChange={(e) => setForm(f => ({ ...f, source_notes: e.target.value }))}
                className="w-full border border-gray-200 rounded px-2 py-1.5 text-sm mt-1" placeholder="e.g. fedex.com 2026-02" />
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" disabled={upsert.isPending}
              className="bg-brand-brown text-white px-4 py-2 rounded-lg text-sm font-medium">
              {upsert.isPending ? 'Saving...' : 'Save'}
            </button>
            <button type="button" onClick={() => setAdding(false)}
              className="border border-gray-300 px-4 py-2 rounded-lg text-sm">Cancel</button>
          </div>
        </form>
      )}

      {isLoading ? (
        <div className="text-gray-400 text-sm">Loading...</div>
      ) : prices.length === 0 ? (
        <div className="bg-gray-50 rounded-xl p-8 text-center text-gray-400">
          No prices entered for {activeTab} yet.
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {['Service Code', 'Service Name', 'Category', 'Unit', 'Price', 'Effective Date', 'Source', ''].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {prices.map((p: CompetitorPrice) => (
                <tr key={p.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs">{p.service_code}</td>
                  <td className="px-4 py-3 font-medium">{p.service_name}</td>
                  <td className="px-4 py-3 capitalize text-gray-500">{p.service_category}</td>
                  <td className="px-4 py-3 text-gray-400">{p.unit}</td>
                  <td className="px-4 py-3 font-bold">{formatCurrency(p.price)}</td>
                  <td className="px-4 py-3 text-gray-500">{p.effective_date}</td>
                  <td className="px-4 py-3 text-xs text-gray-400">{p.source_notes ?? '-'}</td>
                  <td className="px-4 py-3">
                    {isManager && (
                      <button onClick={() => remove.mutate(p.id)} className="text-gray-300 hover:text-red-500">
                        <Trash2 size={14} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
