import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getUpsells, dismissUpsell } from '../api/analysis'
import { useSelectedStore } from '../components/layout/StoreSwitcher'
import { formatCurrency } from '../lib/utils'
import { PRIORITY_COLORS } from '../lib/constants'
import { MessageSquare, X } from 'lucide-react'
import type { UpsellOpportunity } from '../types'

function UpsellDrawer({ opp, onClose }: { opp: UpsellOpportunity; onClose: () => void }) {
  const qc = useQueryClient()
  const dismiss = useMutation({
    mutationFn: () => dismissUpsell(opp.id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['upsells'] }); onClose() },
  })

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1 bg-black/30" onClick={onClose} />
      <div className="w-96 bg-white h-full shadow-xl overflow-y-auto p-6 space-y-5">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-lg">Upsell Opportunity</h2>
          <button onClick={onClose}><X size={20} /></button>
        </div>

        <div className="space-y-4">
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide">Trigger</p>
            <p className="font-medium capitalize">{opp.trigger_service} transaction</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wide">Recommendation</p>
            <p className="font-medium">{opp.recommended_service}</p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-400">Price Delta</p>
              <p className="font-bold text-green-600">{formatCurrency(opp.price_delta)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400">Conversion Rate</p>
              <p className="font-bold">{((parseFloat(opp.conversion_rate_est ?? '0')) * 100).toFixed(0)}%</p>
            </div>
            <div>
              <p className="text-xs text-gray-400">Monthly Volume</p>
              <p className="font-bold">{opp.monthly_volume ?? '-'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400">Monthly Impact</p>
              <p className="font-bold text-green-600">{formatCurrency(opp.monthly_impact_est)}</p>
            </div>
          </div>

          {opp.staff_script && (
            <div className="bg-brand-gold/10 border border-brand-gold rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <MessageSquare size={14} className="text-brand-brown" />
                <span className="text-xs font-semibold text-brand-brown uppercase tracking-wide">Staff Talking Point</span>
              </div>
              <p className="text-sm text-gray-800">"{opp.staff_script}"</p>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              onClick={() => dismiss.mutate()}
              disabled={dismiss.isPending}
              className="flex-1 border border-gray-300 rounded-lg py-2 text-sm text-gray-600 hover:bg-gray-50"
            >
              Dismiss
            </button>
            <button
              onClick={onClose}
              className="flex-1 bg-brand-brown text-white rounded-lg py-2 text-sm font-medium"
            >
              Keep Active
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function UpsellPage() {
  const storeId = useSelectedStore()
  const [priority, setPriority] = useState('')
  const [category, setCategory] = useState('')
  const [selected, setSelected] = useState<UpsellOpportunity | null>(null)

  const { data: upsells = [], isLoading } = useQuery({
    queryKey: ['upsells', storeId, priority, category],
    queryFn: () => getUpsells({ store_id: storeId!, priority: priority || undefined, category: category || undefined }),
    enabled: !!storeId,
  })

  const totalImpact = upsells.reduce((sum, u) => sum + parseFloat(u.monthly_impact_est ?? '0'), 0)

  return (
    <div className="space-y-4">
      {selected && <UpsellDrawer opp={selected} onClose={() => setSelected(null)} />}

      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Upsell Opportunities</h1>
        <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-2 text-sm">
          Total potential: <span className="font-bold text-green-700">{formatCurrency(totalImpact)}/mo</span>
        </div>
      </div>

      <div className="flex gap-3">
        <select value={priority} onChange={(e) => setPriority(e.target.value)}
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white">
          <option value="">All Priorities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select value={category} onChange={(e) => setCategory(e.target.value)}
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white">
          <option value="">All Categories</option>
          <option value="shipping">Shipping</option>
          <option value="printing">Printing</option>
          <option value="mailbox">Mailbox</option>
          <option value="packing">Packing</option>
        </select>
      </div>

      {isLoading ? (
        <div className="text-gray-400 text-sm">Loading...</div>
      ) : upsells.length === 0 ? (
        <div className="bg-gray-50 rounded-xl p-8 text-center text-gray-500">
          No upsell opportunities found. Upload transaction data to see suggestions.
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {['Priority', 'Type', 'Category', 'Recommend', 'Price Delta', 'Volume/mo', 'Monthly Impact', 'Script'].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {upsells.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => setSelected(u)}>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${PRIORITY_COLORS[u.priority ?? 'low']}`}>
                      {u.priority}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 capitalize">{u.opportunity_type.replace('_', ' ')}</td>
                  <td className="px-4 py-3 capitalize text-gray-500">{u.trigger_category}</td>
                  <td className="px-4 py-3 font-medium">{u.recommended_service}</td>
                  <td className="px-4 py-3 text-green-600 font-medium">{formatCurrency(u.price_delta)}</td>
                  <td className="px-4 py-3">{u.monthly_volume ?? '-'}</td>
                  <td className="px-4 py-3 font-bold text-green-600">{formatCurrency(u.monthly_impact_est)}</td>
                  <td className="px-4 py-3">
                    {u.staff_script && <MessageSquare size={14} className="text-brand-gold" />}
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
