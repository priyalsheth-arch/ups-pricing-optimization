import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthStore {
  token: string | null
  role: string | null
  store_id: number | null
  full_name: string | null
  setAuth: (token: string, role: string, store_id: number | null, full_name: string | null) => void
  clearAuth: () => void
  isAuthenticated: () => boolean
  isManager: () => boolean
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      token: null,
      role: null,
      store_id: null,
      full_name: null,
      setAuth: (token, role, store_id, full_name) => set({ token, role, store_id, full_name }),
      clearAuth: () => set({ token: null, role: null, store_id: null, full_name: null }),
      isAuthenticated: () => !!get().token,
      isManager: () => get().role === 'manager' || get().role === 'admin',
    }),
    { name: 'ups-auth' }
  )
)
