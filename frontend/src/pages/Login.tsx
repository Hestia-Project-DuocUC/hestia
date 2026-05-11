import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuthStore } from '../store/auth'
import type { LoginResponse } from '../types/api'

export function Login() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [totp, setTotp] = useState('')
  const [preToken, setPreToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const is2FA = preToken !== null

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      // El backend usa OAuth2PasswordRequestForm → form-urlencoded (no JSON)
      const form = new URLSearchParams()
      form.append('username', email)
      form.append('password', password)
      const { data } = await api.post<LoginResponse>('/auth/login', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      if (data.requires_2fa && data.pre_token) {
        setPreToken(data.pre_token)
      } else if (data.access_token) {
        setAuth(data.access_token, { nombre: data.usuario!, rol: data.rol! })
        navigate('/dashboard')
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        .response?.data?.detail
      setError(msg ?? 'Error al iniciar sesión')
    } finally {
      setLoading(false)
    }
  }

  async function handleTotp(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.post<LoginResponse>('/auth/2fa/completar-login', {
        pre_token: preToken,
        codigo: totp,
      })
      if (data.access_token) {
        setAuth(data.access_token, { nombre: data.usuario!, rol: data.rol! })
        navigate('/dashboard')
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        .response?.data?.detail
      setError(msg ?? 'Código incorrecto')
    } finally {
      setLoading(false)
    }
  }

  const inputCls = `
    w-full px-3.5 py-2.5 rounded-lg border border-slate-200 text-slate-900 text-sm
    focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent
    placeholder:text-slate-400 transition-all bg-slate-50 focus:bg-white
  `
  const btnCls = `
    w-full bg-teal-600 hover:bg-teal-700 text-white font-bold
    py-2.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed
  `

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      {/* Fondo con patrón sutil */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_#134e4a22_0%,_transparent_60%)]" />

      <div className="relative w-full max-w-sm">
        {/* Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-teal-600 rounded-2xl mb-4 shadow-lg shadow-teal-900/30">
            <span className="text-white text-2xl font-black">H</span>
          </div>
          <h1 className="text-2xl font-black text-white tracking-tight">Hestia</h1>
          <p className="text-slate-400 text-sm mt-1">Sistema de Gestión de Insumos</p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-7">
          {!is2FA ? (
            <>
              <h2 className="text-base font-bold text-slate-900 mb-5">Iniciar sesión</h2>
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">
                    Correo electrónico
                  </label>
                  <input
                    type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                    className={inputCls} placeholder="usuario@hestia.cl" required
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1.5 uppercase tracking-wide">
                    Contraseña
                  </label>
                  <input
                    type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                    className={inputCls} placeholder="••••••••" required
                  />
                </div>
                {error && (
                  <p className="text-rose-600 text-xs bg-rose-50 border border-rose-200 px-3 py-2 rounded-lg font-semibold">
                    {error}
                  </p>
                )}
                <button type="submit" disabled={loading} className={btnCls}>
                  {loading ? 'Verificando...' : 'Ingresar'}
                </button>
              </form>
            </>
          ) : (
            <>
              <button
                onClick={() => { setPreToken(null); setError(null); setTotp('') }}
                className="text-slate-400 hover:text-slate-700 text-sm font-semibold mb-4 flex items-center gap-1"
              >
                ← Volver
              </button>
              <h2 className="text-base font-bold text-slate-900 mb-1">Verificación 2FA</h2>
              <p className="text-slate-500 text-xs mb-5">
                Ingresa el código de 6 dígitos de Google Authenticator.
              </p>
              <form onSubmit={handleTotp} className="space-y-4">
                <input
                  type="text" inputMode="numeric" pattern="[0-9]{6}" maxLength={6}
                  value={totp}
                  onChange={(e) => setTotp(e.target.value.replace(/\D/g, ''))}
                  className="w-full px-4 py-4 rounded-lg border border-slate-200 text-slate-900
                             text-3xl text-center font-black tracking-[0.6em]
                             focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent
                             bg-slate-50 focus:bg-white"
                  placeholder="000000" required
                />
                {error && (
                  <p className="text-rose-600 text-xs bg-rose-50 border border-rose-200 px-3 py-2 rounded-lg font-semibold">
                    {error}
                  </p>
                )}
                <button type="submit" disabled={loading || totp.length !== 6} className={btnCls}>
                  {loading ? 'Verificando...' : 'Confirmar código'}
                </button>
              </form>
            </>
          )}
        </div>

        <p className="text-center text-slate-500 text-xs mt-6">
          Escuela de Salud — DuocUC
        </p>
      </div>
    </div>
  )
}
