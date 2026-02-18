import { useQuery } from '@tanstack/react-query'
import { getPricingGaps } from '../api/analysis'
import { useSelectedStore } from '../components/layout/StoreSwitcher'
import { formatCurrency } from '../lib/utils'
import { GAP_DIRECTION_COLORS, SERVICE_CATEGORIES, COMPETITORS } from '../lib/constants'
import { useState } from 'react'
import type { PricingGap } from '../types'

function GapBadge({ direction }: { direction: string | null }) {
  const label = direction === 'underpriced' ? 'Underpriced' : direction === 'overpriced' ? 'Overpriced' : 'Competitive'
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${GAP_DIRECTION_COLORS[direction ?? 'competitive']}`}>
      {label}
    </span>
  )
}

export default function PricingGapsPage() {
  const storeId = useSelectedStore()
  const [category, setCategory] = useState('')
  const [direction, setDirection] = useState('')
  const [sortBy, setSortBy] = useState<keyof PricingGap>('revenue_impact')

  const { data: gaps = [], isLoading } = useQuery({
    queryKey: ['gaps', storeId, category, direction],
    queryFn: () => getPricingGaps({ store_id: storeId!, category: category || undefined, direction: direction || undefined }),
    enabled: !!storeId,
  })

  const sorted = [...gaps].sort((a, b) => {
    const av = parseFloat(String(a[sortBy] ?? 0))
    const bv = parseFloat(String(b[sortBy] ?? 0))
    return bv - av
  })

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Pricing Gaps</h1>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white"
        >
          <option value="">All Categories</option>
          {SERVICE_CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>
        <select
          value={direction}
          onChange={(e) => setDirection(e.target.value)}
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white"
        >
          <option value="">All Directions</option>
          <option value="underpriced">Underpriced</option>
          <option value="overpriced">Overpriced</option>
          <option value="competitive">Competitive</option>
        </select>
      </div>

      {isLoading ? (
        <div className="text-gray-400 text-sm">Loading...</div>
      ) : gaps.length === 0 ? (
        <div className="bg-gray-50 rounded-xl p-8 text-center text-gray-500">
          No pricing gaps found. Add competitor prices to start gap analysis.
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {[
                  ['Service', 'service_name'],
                  ['Category', 'service_category'],
                  ['Our Price', 'our_price'],
                  ['Competitor', 'competitor_name'],
                  ['Comp. Price', 'competitor_price'],
                  ['Gap $', 'gap_amount'],
                  ['Gap %', 'gap_pct'],
                  ['Status', 'direction'],
                  ['Volume', 'transaction_volume'],
                  ['Revenue Impact', 'revenue_impact'],
                ].map(([label, key]) => (
                  <th
                    key={key}
                    onClick={() => setSortBy(key as keyof PricingGap)}
                    className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide cursor-pointer hover:text-gray-900"
                  >
                    {label} {sortBy === key && '↓'}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sorted.map((gap) => {
                const gapPct = parseFloat(String(gap.gap_pct ?? 0)) * 100
                return (
                  <tr key={gap.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{gap.service_name ?? gap.service_code}</td>
                    <td className="px-4 py-3 capitalize text-gray-500">{gap.service_category}</td>
                    <td className="px-4 py-3">{formatCurrency(gap.our_price)}</td>
                    <td className="px-4 py-3 text-gray-600">{gap.competitor_name}</td>
                    <td className="px-4 py-3">{formatCurrency(gap.competitor_price)}</td>
                    <td className={`px-4 py-3 font-medium ${parseFloat(String(gap.gap_amount ?? 0)) > 0 ? 'text-red-600' : 'text-blue-600'}`}>
                      {formatCurrency(gap.gap_amount)}
                    </td>
                    <td className={`px-4 py-3 font-medium ${gapPct > 0 ? 'text-red-600' : 'text-blue-600'}`}>
                      {gapPct >= 0 ? '+' : ''}{gapPct.toFixed(1)}%
                    </td>
                    <td className="px-4 py-3"><GapBadge direction={gap.direction} /></td>
                    <td className="px-4 py-3 text-gray-600">{gap.transaction_volume ?? '-'}</td>
                    <td className="px-4 py-3 font-bold text-red-600">{formatCurrency(gap.revenue_impact)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
