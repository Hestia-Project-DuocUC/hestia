import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuthStore } from '../store/auth'
import { Logo } from '../components/ui/Logo'
import type { LoginResponse } from '../types/api'

type Modo2FA = 'totp' | 'recovery'

export function Login() {
  const navigate = useNavigate()
  const setAuth  = useAuthStore((s) => s.setAuth)

  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [totp,     setTotp]     = useState('')
  const [recovery, setRecovery] = useState('')
  const [preToken, setPreToken] = useState<string | null>(null)
  const [modo2FA,  setModo2FA]  = useState<Modo2FA>('totp')
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState<string | null>(null)

  const is2FA = preToken !== null

  function formatRecoveryCode(input: string) {
    const clean = input.toUpperCase().replace(/[^A-F0-9]/g, '').slice(0, 16)
    return clean.length <= 8 ? clean : `${clean.slice(0, 8)}-${clean.slice(8)}`
  }

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    // NO limpiamos el error aqui. Si habia un mensaje de "Te quedan N intentos",
    // debe permanecer visible mientras vuela la nueva peticion. El error se limpia
    // en onChange de los campos, que es el momento semanticamente correcto.
    setLoading(true)
    try {
      const form = new URLSearchParams()
      form.append('username', email)
      form.append('password', password)
      const { data } = await api.post<LoginResponse>('/auth/login', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      if (data.requires_2fa && data.pre_token) {
        setPreToken(data.pre_token)
        setModo2FA('totp')
        setError(null)
      } else if (data.access_token) {
        setAuth(data.access_token, { nombre: data.usuario!, rol: data.rol! })
        navigate('/dashboard')
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        .response?.data?.detail
      setError(msg ?? 'Error al iniciar sesion')
    } finally { setLoading(false) }
  }

  async function handleTotp(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await api.post<LoginResponse>('/auth/2fa/completar-login', {
        pre_token: preToken, codigo: totp
      })
      if (data.access_token) {
        setAuth(data.access_token, { nombre: data.usuario!, rol: data.rol! })
        navigate('/dashboard')
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        .response?.data?.detail
      setError(msg ?? 'Codigo incorrecto')
    } finally { setLoading(false) }
  }

  async function handleRecovery(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await api.post<LoginResponse>('/auth/2fa/recuperar-acceso', {
        pre_token: preToken, recovery_code: recovery
      })
      if (data.access_token) {
        setAuth(data.access_token, { nombre: data.usuario!, rol: data.rol! })
        // El 2FA fue desactivado automaticamente — redirigir a configuracion
        navigate('/seguridad')
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        .response?.data?.detail
      setError(msg ?? 'Codigo de recuperacion invalido')
    } finally { setLoading(false) }
  }

  function volverAlLogin() {
    setPreToken(null); setError(null); setTotp(''); setRecovery('')
  }

  const inputCls = `
    w-full px-3.5 py-2.5 rounded-lg border border-slate-700 bg-slate-800 text-white text-sm
    focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent
    placeholder:text-slate-500 transition-all
  `
  const btnCls = `
    w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-2.5 rounded-lg
    transition-colors disabled:opacity-50 disabled:cursor-not-allowed
  `
  const labelCls = "block text-xs font-bold text-slate-400 mb-1.5 uppercase tracking-wide"

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_#134e4a22_0%,_transparent_60%)]" />
      <div className="relative w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-32 h-32 mb-4">
            <Logo className="w-32 h-32"/>
          </div>
          <h1 className="text-4xl font-black text-white tracking-tight">Hestia</h1>
        </div>

        <div className="bg-slate-800 rounded-2xl border border-slate-700 shadow-2xl p-7">
          {!is2FA ? (
            <>
              <h2 className="text-base font-bold text-white mb-5">Iniciar sesión</h2>
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <label className={labelCls}>Correo electrónico</label>
                  <input type="email" value={email}
                    onChange={e => { setEmail(e.target.value); setError(null) }}
                    className={inputCls} placeholder="usuario@hestia.duoc.cl" required
                  />
                </div>
                <div>
                  <label className={labelCls}>Contraseña</label>
                  <input
                    type="password" value={password}
                    onChange={e => { setPassword(e.target.value); setError(null) }}
                    className={inputCls} placeholder="••••••••" required
                  />
                </div>
                {error && (
                  <p className={`text-xs px-3 py-2 rounded-lg font-semibold ${
                    error.includes('intento')
                      ? 'text-amber-400 bg-amber-950 border border-amber-800'
                      : 'text-rose-400 bg-rose-950 border border-rose-800'
                  }`}>{error}</p>
                )}
                <button type="submit" disabled={loading} className={btnCls}>
                  {loading ? 'Verificando...' : 'Ingresar'}
                </button>
              </form>
            </>
          ) : modo2FA === 'totp' ? (
            <>
              <button onClick={volverAlLogin}
                className="text-slate-400 hover:text-slate-200 text-sm font-semibold
                           mb-4 flex items-center gap-1">
                ← Volver
              </button>
              <h2 className="text-base font-bold text-white mb-1">Verificacion 2FA</h2>
              <p className="text-slate-400 text-xs mb-5">
                Ingresa el codigo de 6 digitos de Google Authenticator.
              </p>
              <form onSubmit={handleTotp} className="space-y-4">
                <input
                  type="text" inputMode="numeric" pattern="[0-9]{6}" maxLength={6}
                  value={totp}
                  onChange={e => { setTotp(e.target.value.replace(/\D/g, '')); setError(null) }}
                  className="w-full px-4 py-4 rounded-lg border border-slate-700 bg-slate-900
                             text-white text-3xl text-center font-black tracking-[0.6em]
                             focus:outline-none focus:ring-2 focus:ring-teal-500
                             placeholder:text-slate-700"
                  placeholder="000000" autoFocus required
                />
                {error && (
                  <p className="text-rose-400 text-xs bg-rose-950 border border-rose-800
                                px-3 py-2 rounded-lg font-semibold">{error}</p>
                )}
                <button type="submit" disabled={loading || totp.length !== 6} className={btnCls}>
                  {loading ? 'Verificando...' : 'Confirmar codigo'}
                </button>
              </form>
              <button
                onClick={() => { setModo2FA('recovery'); setError(null) }}
                className="w-full mt-4 text-xs text-slate-500 hover:text-slate-300
                           font-semibold transition-colors"
              >
                Perdi acceso a mi app — usar codigo de recuperacion
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => { setModo2FA('totp'); setError(null) }}
                className="text-slate-400 hover:text-slate-200 text-sm font-semibold
                           mb-4 flex items-center gap-1">
                ← Volver
              </button>
              <h2 className="text-base font-bold text-white mb-1">Codigo de recuperacion</h2>
              <p className="text-slate-400 text-xs mb-5">
                Ingresa uno de tus codigos de un solo uso.
                Formato: <code className="text-teal-400">XXXXXXXX-XXXXXXXX</code>
              </p>
              <form onSubmit={handleRecovery} className="space-y-4">
                <input
                  type="text" value={recovery}
                  onChange={e => {
                    setRecovery(formatRecoveryCode(e.target.value)); setError(null)
                  }}
                  className="w-full px-4 py-4 rounded-lg border border-slate-700 bg-slate-900
                             text-white text-lg text-center font-mono tracking-widest
                             focus:outline-none focus:ring-2 focus:ring-teal-500
                             placeholder:text-slate-700"
                  placeholder="XXXXXXXX-XXXXXXXX" maxLength={17} autoFocus
                />
                {error && (
                  <p className="text-rose-400 text-xs bg-rose-950 border border-rose-800
                                px-3 py-2 rounded-lg font-semibold">{error}</p>
                )}
                <button
                  type="submit"
                  disabled={loading || recovery.length !== 17}
                  className={btnCls}
                >
                  {loading ? 'Verificando...' : 'Acceder con codigo de recuperacion'}
                </button>
              </form>
            </>
          )}
        </div>
        <p className="text-center text-slate-600 text-xs mt-6">
          Escuela de Salud — DuocUC
        </p>
      </div>
    </div>
  )
}
