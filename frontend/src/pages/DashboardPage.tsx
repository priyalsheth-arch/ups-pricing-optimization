import { useQuery } from '@tanstack/react-query'
import { getDashboard } from '../api/analysis'
import { useSelectedStore } from '../components/layout/StoreSwitcher'
import { formatCurrency, formatNumber } from '../lib/utils'
import { GAP_DIRECTION_COLORS, PRIORITY_COLORS } from '../lib/constants'
import { TrendingDown, Zap, DollarSign, ArrowUpRight, ArrowDownRight, Upload } from 'lucide-react'
import { Link } from 'react-router-dom'

function KPICard({
  label, value, sub, icon: Icon, color,
}: {
  label: string; value: string; sub?: string; icon: React.ElementType; color: string
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold mt-1">{value}</p>
          {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
        </div>
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon size={20} />
        </div>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const storeId = useSelectedStore()

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', storeId],
    queryFn: () => getDashboard(storeId!, 30),
    enabled: !!storeId,
  })

  if (!storeId) {
    return <div className="text-gray-500 text-sm">Select a store to view dashboard.</div>
  }

  if (isLoading) return <div className="text-gray-400 text-sm">Loading dashboard...</div>

  if (error || !data) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 text-center">
        <Upload size={32} className="mx-auto text-yellow-500 mb-3" />
        <p className="font-medium text-yellow-800">No data yet for this store</p>
        <p className="text-sm text-yellow-600 mt-1">Upload a ConnectSuite CSV to get started</p>
        <Link to="/upload" className="mt-4 inline-block bg-brand-brown text-white px-4 py-2 rounded-lg text-sm font-medium">
          Upload Data
        </Link>
      </div>
    )
  }

  const revenueVsPrior = data.revenue_vs_prior_period ? parseFloat(data.revenue_vs_prior_period) : null

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Dashboard</h1>
        <span className="text-sm text-gray-400">Last 30 days • Last upload: {data.last_upload_date ?? 'None'}</span>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          label="Total Revenue"
          value={formatCurrency(data.total_revenue)}
          sub={revenueVsPrior !== null
            ? `${revenueVsPrior >= 0 ? '+' : ''}${formatCurrency(revenueVsPrior)} vs prior period`
            : undefined}
          icon={revenueVsPrior !== null && revenueVsPrior >= 0 ? ArrowUpRight : ArrowDownRight}
          color="bg-brand-gold/20 text-brand-brown"
        />
        <KPICard
          label="Revenue Opportunity"
          value={formatCurrency(data.total_opportunity_est)}
          sub="estimated / month"
          icon={DollarSign}
          color="bg-green-100 text-green-700"
        />
        <KPICard
          label="Underpriced Services"
          value={formatNumber(data.underpriced_services)}
          sub="vs. competitors"
          icon={TrendingDown}
          color="bg-red-100 text-red-700"
        />
        <KPICard
          label="High-Priority Upsells"
          value={formatNumber(data.high_priority_upsells)}
          sub="opportunities flagged"
          icon={Zap}
          color="bg-purple-100 text-purple-700"
        />
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Pricing Gaps */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900">Top Pricing Gaps</h2>
            <Link to="/pricing-gaps" className="text-xs text-brand-brown hover:underline">View all →</Link>
          </div>
          {data.top_gaps.length === 0 ? (
            <p className="text-sm text-gray-400">No gaps found. Add competitor prices to see gaps.</p>
          ) : (
            <div className="space-y-3">
              {data.top_gaps.map((gap) => (
                <div key={gap.id} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{gap.service_name ?? gap.service_code}</p>
                    <p className="text-xs text-gray-400">vs. {gap.competitor_name}</p>
                  </div>
                  <div className="text-right">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${GAP_DIRECTION_COLORS[gap.direction ?? 'competitive']}`}>
                      {gap.direction}
                    </span>
                    <p className="text-sm font-bold text-red-600 mt-1">{formatCurrency(gap.revenue_impact)}/mo</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Top Upsell Opportunities */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900">Top Upsell Opportunities</h2>
            <Link to="/upsells" className="text-xs text-brand-brown hover:underline">View all →</Link>
          </div>
          {data.top_upsells.length === 0 ? (
            <p className="text-sm text-gray-400">No upsell opportunities yet. Upload transaction data to see opportunities.</p>
          ) : (
            <div className="space-y-3">
              {data.top_upsells.map((u) => (
                <div key={u.id} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{u.recommended_service}</p>
                    <p className="text-xs text-gray-400">{u.trigger_category} → {u.opportunity_type}</p>
                  </div>
                  <div className="text-right">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${PRIORITY_COLORS[u.priority ?? 'low']}`}>
                      {u.priority}
                    </span>
                    <p className="text-sm font-bold text-green-600 mt-1">{formatCurrency(u.monthly_impact_est)}/mo</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Transactions summary */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-center gap-6">
        <div>
          <p className="text-sm text-gray-500">Transactions Analyzed</p>
          <p className="text-2xl font-bold">{formatNumber(data.transactions_analyzed)}</p>
        </div>
        <div className="h-10 w-px bg-gray-200" />
        <div>
          <p className="text-sm text-gray-500">Period</p>
          <p className="text-sm font-medium">{data.period_start} → {data.period_end}</p>
        </div>
        <div className="ml-auto">
          <Link to="/upload" className="text-sm bg-brand-brown text-white px-4 py-2 rounded-lg font-medium hover:bg-opacity-90">
            Upload New Data
          </Link>
        </div>
      </div>
    </div>
  )
}
