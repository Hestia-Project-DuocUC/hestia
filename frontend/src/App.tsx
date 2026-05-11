import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Login } from './pages/Login'
import { Dashboard } from './pages/Dashboard'
import { Alertas } from './pages/Alertas'
import { Insumos } from './pages/Insumos'
import { Layout } from './components/layout/Layout'

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="alertas" element={<Alertas />} />
          <Route path="insumos" element={<Insumos />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
