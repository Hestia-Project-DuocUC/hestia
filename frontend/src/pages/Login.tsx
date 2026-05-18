import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuthStore } from '../store/auth'
import { Logo } from '../components/ui/Logo'
import type { LoginResponse } from '../types/api'

type Modo2FA = 'totp' | 'recovery'

// ── Modal: Acerca de ──
function ModalAcercaDe({ onClose }: { onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4
                 bg-black/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-slate-800 rounded-2xl border border-slate-700 shadow-2xl
                   max-w-sm w-full p-7 relative"
        onClick={e => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-500 hover:text-slate-300
                     text-xl leading-none transition-colors"
          aria-label="Cerrar"
        >
          ×
        </button>

        <div className="flex flex-col items-center mb-6">
          <Logo className="w-16 h-16 mb-3" />
          <h2 className="text-xl font-black text-white tracking-tight">Hestia</h2>
          <p className="text-teal-400 text-xs font-semibold mt-1">
            Sistema de gestión de insumos médicos
          </p>
        </div>

        <div className="space-y-3 text-xs text-slate-400">
          <div className="bg-slate-900/60 rounded-xl border border-slate-700 px-4 py-3 space-y-2">
            <p>
              <span className="text-slate-300 font-semibold">Institución</span>
              <br />DuocUC — Sede San Bernardo
            </p>
            <p>
              <span className="text-slate-300 font-semibold">Escuela</span>
              <br />Escuela de Salud
            </p>
            <p>
              <span className="text-slate-300 font-semibold">Carrera</span>
              <br />Informática Biomédica
            </p>
            <p>
              <span className="text-slate-300 font-semibold">Tipo de proyecto</span>
              <br />Proyecto de Título · Desarrollo de Software
            </p>
            <p>
              <span className="text-slate-300 font-semibold">Período</span>
              <br />2026 - 1 semestre
            </p>
          </div>

          <div className="bg-slate-900/60 rounded-xl border border-slate-700 px-4 py-3">
            <p className="text-slate-300 font-semibold mb-2">Stack tecnológico</p>
            <div className="flex flex-wrap gap-1.5">
              {['FastAPI', 'PostgreSQL', 'React 19', 'TypeScript',
                'Tailwind CSS', 'Docker'].map(t => (
                <span key={t}
                  className="bg-slate-700 text-slate-300 px-2 py-0.5 rounded-md
                             font-mono text-[10px]">
                  {t}
                </span>
              ))}
            </div>
          </div>
        </div>

        <p className="text-center text-slate-600 text-[10px] mt-5">
          <strong className="text-slate-500">H</strong>ospitalidad·
          <strong className="text-slate-500">E</strong>ficacia·
          <strong className="text-slate-500">S</strong>ervicio·
          <strong className="text-slate-500">T</strong>ransparencia·
          <strong className="text-slate-500">I</strong>nsumos·
          <strong className="text-slate-500">A</strong>postolado
        </p>
      </div>
    </div>
  )
}

// ── Componente principal ──
export function Login() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [totp, setTotp] = useState('')
  const [recovery, setRecovery] = useState('')
  const [preToken, setPreToken] = useState<string | null>(null)
  const [modo2FA, setModo2FA] = useState<Modo2FA>('totp')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [isForgot, setIsForgot] = useState(false)
  const [forgotEmail, setForgotEmail] = useState('')
  const [forgotLoading, setForgotLoading] = useState(false)
  const [forgotError, setForgotError] = useState<string | null>(null)
  const [forgotOk, setForgotOk] = useState(false)

  const [showAbout, setShowAbout] = useState(false)

  const is2FA = preToken !== null

  function formatRecoveryCode(input: string) {
    const clean = input.toUpperCase().replace(/[^A-F0-9]/g, '').slice(0, 16)
    return clean.length <= 8 ? clean : `${clean.slice(0, 8)}-${clean.slice(8)}`
  }

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
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
      setError(msg ?? 'Error al iniciar sesión')
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
      setError(msg ?? 'Código incorrecto')
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
        navigate('/seguridad')
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        .response?.data?.detail
      setError(msg ?? 'Código de recuperación inválido')
    } finally { setLoading(false) }
  }

  async function handleForgot(e: React.FormEvent) {
    e.preventDefault()
    setForgotLoading(true)
    setForgotError(null)
    try {
      await api.post('/auth/recuperar-password', { email: forgotEmail })
      setForgotOk(true)
    } catch {
      setForgotError('No fue posible procesar la solicitud. Intenta de nuevo.')
    } finally { setForgotLoading(false) }
  }

  function volverAlLogin() {
    setPreToken(null); setError(null); setTotp(''); setRecovery('')
  }

  function abrirForgot() {
    setIsForgot(true); setForgotEmail(email); setForgotError(null); setForgotOk(false)
  }

  function cerrarForgot() {
    setIsForgot(false); setForgotEmail(''); setForgotError(null); setForgotOk(false)
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
  const footerBtnCls = `
    text-xs font-semibold text-slate-600 hover:text-slate-300
    transition-colors duration-150 px-1 py-0.5 rounded
    hover:bg-slate-800/60 focus:outline-none focus-visible:ring-2
    focus-visible:ring-teal-500
  `

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_#134e4a22_0%,_transparent_60%)]" />

      {showAbout && <ModalAcercaDe onClose={() => setShowAbout(false)} />}

      <div className="relative w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-32 h-32 mb-4">
            <Logo className="w-32 h-32" />
          </div>
          <h1 className="text-4xl font-black text-white tracking-tight">Hestia</h1>
        </div>

        <div className="bg-slate-800 rounded-2xl border border-slate-700 shadow-2xl p-7">

          {/* ── Vista: Login ── */}
          {!is2FA && !isForgot ? (
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
              <button
                type="button"
                onClick={abrirForgot}
                className="w-full mt-4 text-xs text-slate-500 hover:text-slate-300
                           font-semibold transition-colors"
              >
                ¿Olvidaste tu contraseña?
              </button>
            </>

          ) : !is2FA && isForgot ? (
            /* ── Vista: Recuperar contraseña ── */
            <>
              <button onClick={cerrarForgot}
                className="text-slate-400 hover:text-slate-200 text-sm font-semibold
                           mb-4 flex items-center gap-1">
                ← Volver
              </button>
              {forgotOk ? (
                <div className="text-center py-2">
                  <div className="w-12 h-12 rounded-full bg-teal-900 border border-teal-700
                                  flex items-center justify-center mx-auto mb-4 text-2xl">
                    ✉️
                  </div>
                  <h2 className="text-base font-bold text-white mb-2">Revisa tu correo</h2>
                  <p className="text-slate-400 text-xs mb-5">
                    Si el email{' '}
                    <span className="text-teal-400 font-semibold">{forgotEmail}</span>{' '}
                    está registrado, recibirás un enlace para restablecer tu contraseña.
                    El enlace es válido por 1 hora.
                  </p>
                  <button onClick={cerrarForgot} className={btnCls}>
                    Volver al inicio de sesión
                  </button>
                </div>
              ) : (
                <>
                  <h2 className="text-base font-bold text-white mb-1">Recuperar contraseña</h2>
                  <p className="text-slate-400 text-xs mb-5">
                    Ingresa tu correo y te enviaremos un enlace para crear una nueva contraseña.
                  </p>
                  <form onSubmit={handleForgot} className="space-y-4">
                    <div>
                      <label className={labelCls}>Correo electrónico</label>
                      <input
                        type="email" value={forgotEmail}
                        onChange={e => { setForgotEmail(e.target.value); setForgotError(null) }}
                        className={inputCls} placeholder="usuario@hestia.duoc.cl"
                        required autoFocus
                      />
                    </div>
                    {forgotError && (
                      <p className="text-rose-400 text-xs bg-rose-950 border border-rose-800
                                    px-3 py-2 rounded-lg font-semibold">{forgotError}</p>
                    )}
                    <button
                      type="submit"
                      disabled={forgotLoading || !forgotEmail}
                      className={btnCls}
                    >
                      {forgotLoading ? 'Enviando...' : 'Enviar enlace de recuperación'}
                    </button>
                  </form>
                </>
              )}
            </>

          ) : modo2FA === 'totp' ? (
            /* ── Vista: 2FA TOTP ── */
            <>
              <button onClick={volverAlLogin}
                className="text-slate-400 hover:text-slate-200 text-sm font-semibold
                           mb-4 flex items-center gap-1">
                ← Volver
              </button>
              <h2 className="text-base font-bold text-white mb-1">Verificación 2FA</h2>
              <p className="text-slate-400 text-xs mb-5">
                Ingresa el código de 6 dígitos de Google Authenticator.
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
                  {loading ? 'Verificando...' : 'Confirmar código'}
                </button>
              </form>
              <button
                onClick={() => { setModo2FA('recovery'); setError(null) }}
                className="w-full mt-4 text-xs text-slate-500 hover:text-slate-300
                           font-semibold transition-colors"
              >
                Perdí acceso a mi app — usar código de recuperación
              </button>
            </>

          ) : (
            /* ── Vista: 2FA Recovery Code ── */
            <>
              <button
                onClick={() => { setModo2FA('totp'); setError(null) }}
                className="text-slate-400 hover:text-slate-200 text-sm font-semibold
                           mb-4 flex items-center gap-1">
                ← Volver
              </button>
              <h2 className="text-base font-bold text-white mb-1">Código de recuperación</h2>
              <p className="text-slate-400 text-xs mb-5">
                Ingresa uno de tus códigos de un solo uso.
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
                  {loading ? 'Verificando...' : 'Acceder con código de recuperación'}
                </button>
              </form>
            </>
          )}
        </div>

        {/* ── Pie de página con botones Acerca de / Soporte ── */}
        <div className="flex items-center justify-between mt-5 px-1">
          <button
            type="button"
            onClick={() => setShowAbout(true)}
            className={footerBtnCls}
          >
            Acerca de
          </button>
          <span className="text-slate-700 text-xs select-none">
            Escuela de Salud — DuocUC
          </span>
          <a
            href="mailto:hestia.soporte.cc@gmail.com"
            className={footerBtnCls}
          >
            Soporte
          </a>
        </div>
      </div>
    </div>
  )
}
