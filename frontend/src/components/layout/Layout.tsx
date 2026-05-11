import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { useAuthStore } from '../../store/auth'
import { Navigate } from 'react-router-dom'

// Layout principal: sidebar fijo a la izquierda + contenido a la derecha.
// Outlet es el placeholder donde React Router renderiza la pagina activa.
export function Layout() {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
