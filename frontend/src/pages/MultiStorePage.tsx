import { useQuery } from '@tanstack/react-query'
import { getMultiStore } from '../api/analysis'
import { formatCurrency } from '../lib/utils'
import { TrendingDown, Zap, DollarSign } from 'lucide-react'

export default function MultiStorePage() {
  const { data: stores = [], isLoading } = useQuery({
    queryKey: ['multistore'],
    queryFn: () => getMultiStore(30),
  })

  if (isLoading) return <div className="text-gray-400 text-sm">Loading...</div>

  const maxOpp = Math.max(...stores.map((s) => parseFloat(s.total_opportunity)))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Multi-Store Comparison</h1>
        <span className="text-sm text-gray-400">Last 30 days</span>
      </div>

      {/* Store cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {stores.map((store) => {
          const opp = parseFloat(store.total_opportunity)
          const isTopOpportunity = opp === maxOpp && opp > 0
          return (
            <div
              key={store.store_id}
              className={`bg-white rounded-xl border p-5 ${isTopOpportunity ? 'border-red-300 ring-1 ring-red-200' : 'border-gray-200'}`}
            >
              {isTopOpportunity && (
                <div className="text-xs bg-red-100 text-red-700 rounded px-2 py-0.5 inline-block mb-3">
                  ⚠ Highest Opportunity
                </div>
              )}
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="font-bold">{store.store_name}</p>
                  <p className="text-xs text-gray-400">Store #{store.store_number}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-400">Current Revenue</p>
                  <p className="text-lg font-bold">{formatCurrency(store.current_revenue)}</p>
                </div>
              </div>

              {/* Opportunity bar */}
              <div className="mb-4">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>Monthly Opportunity</span>
                  <span className="font-bold text-green-600">{formatCurrency(opp)}</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 rounded-full"
                    style={{ width: `${maxOpp > 0 ? (opp / maxOpp) * 100 : 0}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="bg-red-50 rounded-lg p-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <TrendingDown size={12} className="text-red-600" />
                    <span className="text-xs text-red-600 font-medium">Top Gap</span>
                  </div>
                  <p className="font-medium text-gray-800 text-xs">{store.top_gap_service ?? 'None'}</p>
                  {store.top_gap_amount && (
                    <p className="text-xs text-red-600">{formatCurrency(store.top_gap_amount)}/mo</p>
                  )}
                </div>
                <div className="bg-green-50 rounded-lg p-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Zap size={12} className="text-green-600" />
                    <span className="text-xs text-green-600 font-medium">Top Upsell</span>
                  </div>
                  <p className="font-medium text-gray-800 text-xs">{store.top_upsell_service ?? 'None'}</p>
                  {store.top_upsell_impact && (
                    <p className="text-xs text-green-600">{formatCurrency(store.top_upsell_impact)}/mo</p>
                  )}
                </div>
              </div>

              <div className="mt-3 flex items-center justify-between text-xs text-gray-400">
                <span>{store.underpriced_service_count} underpriced services</span>
                <span className="font-bold text-brand-brown">{formatCurrency(opp * 12)}/yr</span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Summary table */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold">All Stores Summary</h2>
        </div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              {['Store', 'Revenue/mo', 'Opportunity/mo', 'Annual Opportunity', 'Underpriced Services'].map((h) => (
                <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {stores.map((s) => (
              <tr key={s.store_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{s.store_name}</td>
                <td className="px-4 py-3">{formatCurrency(s.current_revenue)}</td>
                <td className="px-4 py-3 text-green-600 font-medium">{formatCurrency(s.total_opportunity)}</td>
                <td className="px-4 py-3 font-bold text-brand-brown">{formatCurrency(parseFloat(s.total_opportunity) * 12)}</td>
                <td className="px-4 py-3">{s.underpriced_service_count}</td>
              </tr>
            ))}
            {stores.length > 0 && (
              <tr className="bg-gray-50 font-bold">
                <td className="px-4 py-3">All Stores Total</td>
                <td className="px-4 py-3">{formatCurrency(stores.reduce((s, r) => s + parseFloat(r.current_revenue), 0))}</td>
                <td className="px-4 py-3 text-green-600">{formatCurrency(stores.reduce((s, r) => s + parseFloat(r.total_opportunity), 0))}</td>
                <td className="px-4 py-3 text-brand-brown">{formatCurrency(stores.reduce((s, r) => s + parseFloat(r.total_opportunity) * 12, 0))}</td>
                <td className="px-4 py-3">{stores.reduce((s, r) => s + r.underpriced_service_count, 0)}</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
