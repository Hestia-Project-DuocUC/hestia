import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Login }            from './pages/Login'
import { Dashboard }        from './pages/Dashboard'
import { Alertas }          from './pages/Alertas'
import { Insumos }          from './pages/Insumos'
import { Movimientos }      from './pages/Movimientos'
import { Salas }            from './pages/Salas'
import { Categorias }       from './pages/Categorias'
import { Configuracion2FA } from './pages/Configuracion2FA'
import { ImportarInsumos }  from './pages/ImportarInsumos'
import { Perfil }           from './pages/Perfil'
import { Layout }           from './components/layout/Layout'

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard"   element={<Dashboard />} />
          <Route path="alertas"     element={<Alertas />} />
          <Route path="insumos"     element={<Insumos />} />
          <Route path="movimientos" element={<Movimientos />} />
          <Route path="salas"       element={<Salas />} />
          <Route path="categorias"  element={<Categorias />} />
          <Route path="seguridad"   element={<Configuracion2FA />} />
          <Route path="importar"    element={<ImportarInsumos />} />
          <Route path="perfil"      element={<Perfil />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
