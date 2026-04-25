import { Link, Navigate, Route, Routes } from 'react-router-dom'
import DashboardPage from './pages/DashboardPage'
import InventoryPage from './pages/InventoryPage'
import LoginPage from './pages/LoginPage'
import OrdersPage from './pages/OrdersPage'
import { useAuthStore } from './store/authStore'

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto max-w-6xl p-3">
      <nav className="mb-4 flex gap-2 overflow-auto rounded-xl bg-white p-2 shadow-sm">
        <Link className="btn" to="/">Dashboard</Link>
        <Link className="btn" to="/inventory">Номенклатура</Link>
        <Link className="btn" to="/orders">Заказы</Link>
      </nav>
      {children}
    </div>
  )
}

export default function App() {
  const token = useAuthStore((s) => s.token)
  if (!token) {
    return (
      <Routes>
        <Route path="*" element={<LoginPage />} />
      </Routes>
    )
  }
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/inventory" element={<InventoryPage />} />
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Layout>
  )
}
