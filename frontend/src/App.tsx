import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import AppShell from './components/layout/AppShell'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import PricingGapsPage from './pages/PricingGapsPage'
import UpsellPage from './pages/UpsellPage'
import CompetitorPricingPage from './pages/CompetitorPricingPage'
import UploadPage from './pages/UploadPage'
import RevenueOpportunityPage from './pages/RevenueOpportunityPage'
import MultiStorePage from './pages/MultiStorePage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated())
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="pricing-gaps" element={<PricingGapsPage />} />
          <Route path="upsells" element={<UpsellPage />} />
          <Route path="competitor-pricing" element={<CompetitorPricingPage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="revenue-opportunity" element={<RevenueOpportunityPage />} />
          <Route path="multi-store" element={<MultiStorePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
