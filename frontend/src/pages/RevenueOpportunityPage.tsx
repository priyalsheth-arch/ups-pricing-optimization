import { useQuery } from '@tanstack/react-query'
import { getRevenueOpportunity } from '../api/analysis'
import { useSelectedStore } from '../components/layout/StoreSwitcher'
import { formatCurrency } from '../lib/utils'
import { CATEGORY_COLORS } from '../lib/constants'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function RevenueOpportunityPage() {
  const storeId = useSelectedStore()

  const { data, isLoading } = useQuery({
    queryKey: ['revenue-opportunity', storeId],
    queryFn: () => getRevenueOpportunity(storeId!, 30),
    enabled: !!storeId,
  })

  if (!storeId) return <div className="text-gray-500 text-sm">Select a store.</div>
  if (isLoading) return <div className="text-gray-400 text-sm">Loading...</div>
  if (!data) return <div className="text-gray-400 text-sm">No data available. Upload transactions and add competitor prices first.</div>

  const annualOpp = parseFloat(data.annual_opportunity)
  const monthlyOpp = parseFloat(data.total_monthly_opportunity)

  const bucketData = [
    { name: 'Pricing Gap\nCapture', value: parseFloat(data.pricing_gap_opportunity), fill: '#EF4444' },
    { name: 'Upsell\nConversions', value: parseFloat(data.upsell_opportunity), fill: '#10B981' },
    { name: 'Add-on\nAttach', value: parseFloat(data.addon_opportunity), fill: '#8B5CF6' },
  ]

  const categoryData = data.by_category.map((c) => ({
    name: c.category,
    gap: parseFloat(c.pricing_gap_opportunity),
    upsell: parseFloat(c.upsell_opportunity),
    addon: parseFloat(c.addon_opportunity),
  }))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Revenue Opportunity</h1>
        <div className="text-sm text-gray-500">Last 30 days</div>
      </div>

      {/* Hero callout */}
      <div className="bg-brand-brown text-white rounded-2xl p-6 flex items-center justify-between">
        <div>
          <p className="text-white/70 text-sm">Estimated Annual Revenue Opportunity</p>
          <p className="text-4xl font-bold mt-1">{formatCurrency(annualOpp)}</p>
          <p className="text-white/60 text-sm mt-1">at current transaction volume</p>
        </div>
        <div className="text-right">
          <p className="text-white/70 text-sm">Monthly</p>
          <p className="text-2xl font-bold text-brand-gold">{formatCurrency(monthlyOpp)}</p>
        </div>
      </div>

      {/* Bucket breakdown */}
      <div className="grid grid-cols-3 gap-4">
        {bucketData.map((b) => (
          <div key={b.name} className="bg-white border border-gray-200 rounded-xl p-5">
            <div className="w-3 h-3 rounded-full mb-3" style={{ backgroundColor: b.fill }} />
            <p className="text-sm text-gray-500 whitespace-pre-line">{b.name}</p>
            <p className="text-2xl font-bold mt-1">{formatCurrency(b.value)}/mo</p>
            <p className="text-xs text-gray-400 mt-1">{formatCurrency(b.value * 12)}/yr</p>
          </div>
        ))}
      </div>

      {/* Bar chart by bucket */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h2 className="font-semibold mb-4">Opportunity Breakdown (Monthly)</h2>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={bucketData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" tickFormatter={(v) => `$${v.toLocaleString()}`} fontSize={12} />
            <YAxis type="category" dataKey="name" width={100} fontSize={11} />
            <Tooltip formatter={(v) => formatCurrency(Number(v))} />
            <Bar dataKey="value" radius={4}>
              {bucketData.map((entry, index) => (
                <Cell key={index} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* By category table */}
      {categoryData.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100">
            <h2 className="font-semibold">By Service Category</h2>
          </div>
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                {['Category', 'Gap Capture', 'Upsell', 'Add-on', 'Total/mo', 'Annual'].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {categoryData.map((c) => (
                <tr key={c.name} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CATEGORY_COLORS[c.name] ?? '#9CA3AF' }} />
                      <span className="capitalize font-medium">{c.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-red-600">{formatCurrency(c.gap)}</td>
                  <td className="px-4 py-3 text-green-600">{formatCurrency(c.upsell)}</td>
                  <td className="px-4 py-3 text-purple-600">{formatCurrency(c.addon)}</td>
                  <td className="px-4 py-3 font-bold">{formatCurrency(c.gap + c.upsell + c.addon)}</td>
                  <td className="px-4 py-3 font-bold text-brand-brown">{formatCurrency((c.gap + c.upsell + c.addon) * 12)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Assumptions */}
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-5">
        <h2 className="font-semibold text-sm mb-3 text-gray-700">Model Assumptions</h2>
        <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
          <div>Price elasticity (volume loss on raise): <strong>{(data.assumptions.price_elasticity_factor * 100).toFixed(0)}%</strong></div>
          <div>Max price increase cap: <strong>{(data.assumptions.max_price_increase_pct * 100).toFixed(0)}%</strong></div>
          <div>Ground → 2-Day conversion: <strong>{(data.assumptions.ground_to_2day_conversion * 100).toFixed(0)}%</strong></div>
          <div>Insurance attach rate: <strong>{(data.assumptions.insurance_attach_rate * 100).toFixed(0)}%</strong></div>
          <div>Packing supplies attach: <strong>{(data.assumptions.packing_supplies_attach * 100).toFixed(0)}%</strong></div>
          <div>Printing finishing attach: <strong>{(data.assumptions.printing_finishing_attach * 100).toFixed(0)}%</strong></div>
        </div>
      </div>
    </div>
  )
}
