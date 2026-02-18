import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import StoreSwitcher from './StoreSwitcher'
import { useAuthStore } from '../../store/authStore'

export default function AppShell() {
  const full_name = useAuthStore((s) => s.full_name)
  const role = useAuthStore((s) => s.role)
  const clearAuth = useAuthStore((s) => s.clearAuth)

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Topbar */}
        <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
          <StoreSwitcher />
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {full_name} <span className="text-xs bg-gray-100 px-2 py-0.5 rounded capitalize">{role}</span>
            </span>
            <button
              onClick={() => { clearAuth(); window.location.href = '/login' }}
              className="text-sm text-gray-500 hover:text-gray-900"
            >
              Sign out
            </button>
          </div>
        </header>
        {/* Main content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
