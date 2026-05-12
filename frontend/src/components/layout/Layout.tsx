import { Outlet, Navigate } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { useAuthStore } from '../../store/auth'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ShieldAlert, X } from 'lucide-react'
import { api } from '../../api/client'
import type { UsuarioMe } from '../../types/api'

const SESSION_KEY = 'hestia_2fa_warning_dismissed'

export function Layout() {
  const token    = useAuthStore((s) => s.token)
  const navigate = useNavigate()
  const [show2FAWarning, setShow2FAWarning] = useState(false)

  useEffect(() => {
    if (!token) return
    // Si ya fue descartado en esta sesion, no mostrar de nuevo
    if (sessionStorage.getItem(SESSION_KEY)) return
    api.get<UsuarioMe>('/usuarios/me').then(({ data }) => {
      if (!data.totp_habilitado) setShow2FAWarning(true)
    }).catch(() => {})
  }, [token])

  function dismissWarning() {
    sessionStorage.setItem(SESSION_KEY, '1')
    setShow2FAWarning(false)
  }

  function goToSecurity() {
    dismissWarning()
    navigate('/seguridad')
  }

  if (!token) return <Navigate to="/login" replace />

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>

      {/* Popup de advertencia 2FA — aparece una vez por sesion si no esta activo */}
      {show2FAWarning && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center
                        justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-7">
            <div className="flex items-start justify-between mb-4">
              <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center
                              justify-center flex-shrink-0">
                <ShieldAlert size={24} className="text-amber-600" />
              </div>
              <button
                onClick={dismissWarning}
                className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center
                           justify-center text-slate-400 hover:text-slate-600"
              >
                <X size={16} />
              </button>
            </div>
            <h2 className="text-lg font-black text-slate-900 mb-2">
              Activa la verificacion en dos pasos
            </h2>
            <p className="text-slate-500 text-sm mb-4">
              Sin el 2FA activo, algunas funciones criticas no estaran disponibles:
            </p>
            <ul className="space-y-2 mb-6">
              {[
                'Importar insumos desde CSV o XLSX',
                'Eliminar insumos del inventario',
              ].map(item => (
                <li key={item} className="flex items-center gap-2 text-sm">
                  <span className="w-5 h-5 rounded-full bg-amber-100 text-amber-700
                                   flex items-center justify-center text-xs flex-shrink-0">
                    !
                  </span>
                  <span className="text-slate-700 font-semibold">{item}</span>
                </li>
              ))}
            </ul>
            <button
              onClick={goToSecurity}
              className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold
                         py-2.5 rounded-xl transition-colors mb-2"
            >
              Configurar 2FA ahora
            </button>
            <button
              onClick={dismissWarning}
              className="w-full py-2 text-sm text-slate-400 hover:text-slate-600
                         font-semibold transition-colors"
            >
              Recordar mas tarde
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
