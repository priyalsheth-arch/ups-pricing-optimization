import { NavLink } from 'react-router-dom'
import { LayoutDashboard, TrendingUp, Zap, Users, Upload, DollarSign, BarChart2 } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { cn } from '../../lib/utils'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/pricing-gaps', icon: TrendingUp, label: 'Pricing Gaps' },
  { to: '/upsells', icon: Zap, label: 'Upsell Opportunities' },
  { to: '/competitor-pricing', icon: Users, label: 'Competitor Pricing' },
  { to: '/upload', icon: Upload, label: 'Upload Data' },
  { to: '/revenue-opportunity', icon: DollarSign, label: 'Revenue Opportunity' },
  { to: '/multi-store', icon: BarChart2, label: 'Multi-Store View', managerOnly: true },
]

export default function Sidebar() {
  const isManager = useAuthStore((s) => s.isManager())

  return (
    <aside className="w-56 bg-brand-brown text-white flex flex-col">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-white/10">
        <div className="text-brand-gold font-bold text-lg leading-tight">UPS Pricing</div>
        <div className="text-white/60 text-xs">Intelligence Tool</div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label, managerOnly }) => {
          if (managerOnly && !isManager) return null
          return (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
                  isActive
                    ? 'bg-brand-gold text-brand-brown font-semibold'
                    : 'text-white/80 hover:bg-white/10 hover:text-white'
                )
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          )
        })}
      </nav>

      <div className="px-5 py-4 border-t border-white/10 text-xs text-white/40">
        v1.0.0
      </div>
    </aside>
  )
}
