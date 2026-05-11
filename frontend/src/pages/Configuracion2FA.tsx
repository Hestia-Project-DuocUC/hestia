import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield, CheckCircle, Copy, ChevronRight,
  AlertTriangle, ArrowLeft, Smartphone
} from 'lucide-react'
import { api } from '../api/client'
import type { UsuarioMe, Setup2FAResponse } from '../types/api'
import { Skeleton } from '../components/ui/Skeleton'

type Step = 'loading' | 'intro' | 'qr' | 'verify' | 'success'

const WIZARD_STEPS = ['Inicio', 'Código QR', 'Verificar']

export function Configuracion2FA() {
  const [step, setStep]                   = useState<Step>('loading')
  const [setupData, setSetupData]         = useState<Setup2FAResponse | null>(null)
  const [totp2FAEnabled, set2FAEnabled]   = useState<boolean>(false)
  const [codigo, setCodigo]               = useState('')
  const [codigoDesactivar, setCodigoDesactivar] = useState('')
  const [loading, setLoading]             = useState(false)
  const [error, setError]                 = useState<string | null>(null)
  const [copied, setCopied]               = useState(false)

  // Carga el estado actual de 2FA del usuario al montar
  useEffect(() => {
    api.get<UsuarioMe>('/usuarios/me')
      .then(({ data }) => { set2FAEnabled(data.totp_habilitado); setStep('intro') })
      .catch(() => setStep('intro'))
  }, [])

  async function handleSetup() {
    setLoading(true); setError(null)
    try {
      const { data } = await api.post<Setup2FAResponse>('/auth/2fa/setup')
      setSetupData(data)
      setStep('qr')
    } catch {
      setError('Error al generar el código QR. Inténtalo de nuevo.')
    } finally {
      setLoading(false)
    }
  }

  async function handleActivar(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true); setError(null)
    try {
      await api.post('/auth/2fa/activar', { codigo })
      set2FAEnabled(true)
      setStep('success')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
      setError(msg ?? 'Código incorrecto. Asegúrate de usar el código actual de la app.')
    } finally {
      setLoading(false)
    }
  }

  async function handleDesactivar(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true); setError(null)
    try {
      await api.post('/auth/2fa/desactivar', { codigo: codigoDesactivar })
      set2FAEnabled(false)
      setCodigoDesactivar('')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
      setError(msg ?? 'Código incorrecto')
    } finally {
      setLoading(false)
    }
  }

  function copySecret() {
    if (!setupData?.secret) return
    navigator.clipboard.writeText(setupData.secret)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Índice del paso activo para el indicador
  const activeStepIdx = step === 'qr' ? 1 : step === 'verify' || step === 'success' ? 2 : 0

  const inputCls = `
    w-full px-4 py-3 rounded-xl border-2 border-slate-200 text-slate-900
    focus:outline-none focus:border-teal-500 bg-slate-50 focus:bg-white transition-colors
  `
  const btnPrimary = `
    w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-3 rounded-xl
    transition-colors disabled:opacity-50 disabled:cursor-not-allowed
    flex items-center justify-center gap-2
  `
  const btnGhost = `w-full mt-2 py-2 text-sm text-slate-400 hover:text-slate-600 font-semibold transition-colors`

  return (
    <div className="p-8 max-w-xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <Link to="/dashboard"
          className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 font-semibold mb-4"
        >
          <ArrowLeft size={14} /> Dashboard
        </Link>
        <h1 className="text-2xl font-black text-slate-900">Verificación en dos pasos</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          Protege tu cuenta con Google Authenticator.
        </p>
      </div>

      {/* ── LOADING ── */}
      {step === 'loading' && (
        <div className="space-y-4">
          <Skeleton className="h-28 w-full rounded-2xl" />
          <Skeleton className="h-48 w-full rounded-2xl" />
        </div>
      )}

      {/* ── INTRO ── */}
      {step === 'intro' && (
        <div className="space-y-4">
          {/* Estado actual */}
          <div className={`rounded-2xl border p-5 flex items-center gap-4 ${
            totp2FAEnabled
              ? 'bg-teal-50 border-teal-200'
              : 'bg-slate-50 border-slate-200'
          }`}>
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
              totp2FAEnabled ? 'bg-teal-100' : 'bg-slate-200'
            }`}>
              <Shield size={22} className={totp2FAEnabled ? 'text-teal-600' : 'text-slate-400'} />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <p className="font-bold text-slate-900 text-sm">Verificación en dos pasos</p>
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                  totp2FAEnabled
                    ? 'bg-teal-600 text-white'
                    : 'bg-slate-300 text-slate-600'
                }`}>
                  {totp2FAEnabled ? 'Activa' : 'Inactiva'}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {totp2FAEnabled
                  ? 'Cada inicio de sesión require tu código TOTP.'
                  : 'Añade una capa extra de seguridad a tu cuenta.'
                }
              </p>
            </div>
          </div>

          {/* Panel de activación */}
          {!totp2FAEnabled && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <h2 className="font-bold text-slate-900 mb-4">¿Cómo funciona?</h2>
              <div className="space-y-4 mb-6">
                {[
                  {
                    n: '1', icon: <Smartphone size={16} className="text-teal-600" />,
                    title: 'Escaneas el código QR',
                    desc: 'Abres Google Authenticator y escaneas el QR que te mostraremos.'
                  },
                  {
                    n: '2', icon: <Shield size={16} className="text-teal-600" />,
                    title: 'La app genera códigos',
                    desc: 'Un código de 6 dígitos diferente cada 30 segundos, sin internet.'
                  },
                  {
                    n: '3', icon: <CheckCircle size={16} className="text-teal-600" />,
                    title: 'Lo usas al iniciar sesión',
                    desc: 'Además de tu contraseña, ingresa el código de la app.'
                  },
                ].map(({ n, title, desc }) => (
                  <div key={n} className="flex items-start gap-3">
                    <div className="w-7 h-7 rounded-lg bg-teal-600 text-white flex items-center justify-center text-xs font-black flex-shrink-0">
                      {n}
                    </div>
                    <div>
                      <p className="font-semibold text-slate-900 text-sm">{title}</p>
                      <p className="text-slate-500 text-xs mt-0.5">{desc}</p>
                    </div>
                  </div>
                ))}
              </div>
              {error && (
                <p className="text-rose-600 text-xs bg-rose-50 border border-rose-200 px-3 py-2 rounded-lg font-semibold mb-4">
                  {error}
                </p>
              )}
              <button onClick={handleSetup} disabled={loading} className={btnPrimary}>
                {loading ? 'Generando...' : <><Shield size={16} /> Activar verificación en dos pasos</>}
              </button>
            </div>
          )}

          {/* Panel de desactivación */}
          {totp2FAEnabled && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <div className="flex items-start gap-3 mb-5">
                <AlertTriangle size={17} className="text-amber-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-slate-900 text-sm">Desactivar 2FA</p>
                  <p className="text-slate-500 text-xs mt-0.5">
                    Tu cuenta quedará protegida solo por contraseña. Ingresa tu código TOTP actual para confirmar.
                  </p>
                </div>
              </div>
              <form onSubmit={handleDesactivar} className="space-y-3">
                <input
                  type="text" inputMode="numeric" pattern="[0-9]{6}" maxLength={6}
                  value={codigoDesactivar}
                  onChange={(e) => { setCodigoDesactivar(e.target.value.replace(/\D/g, '')); setError(null) }}
                  placeholder="Código de 6 dígitos"
                  className={`${inputCls} text-xl text-center font-bold tracking-[0.4em]`}
                />
                {error && (
                  <p className="text-rose-600 text-xs bg-rose-50 border border-rose-200 px-3 py-2 rounded-lg font-semibold">
                    {error}
                  </p>
                )}
                <button
                  type="submit"
                  disabled={loading || codigoDesactivar.length !== 6}
                  className="w-full bg-rose-600 hover:bg-rose-700 text-white font-bold py-2.5 rounded-xl transition-colors disabled:opacity-50"
                >
                  {loading ? 'Desactivando...' : 'Desactivar 2FA'}
                </button>
              </form>
            </div>
          )}
        </div>
      )}

      {/* ── WIZARD: QR + VERIFY + SUCCESS ── */}
      {(step === 'qr' || step === 'verify' || step === 'success') && (
        <>
          {/* Indicador de pasos */}
          <div className="flex items-center mb-6">
            {WIZARD_STEPS.map((label, i) => (
              <div key={label} className="flex items-center">
                <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold transition-all ${
                  i === activeStepIdx
                    ? 'bg-teal-600 text-white'
                    : i < activeStepIdx
                    ? 'bg-teal-100 text-teal-700'
                    : 'bg-slate-100 text-slate-400'
                }`}>
                  <span className={`w-4 h-4 rounded-full flex items-center justify-center text-xs font-black ${
                    i < activeStepIdx ? 'text-teal-600' : ''
                  }`}>
                    {i < activeStepIdx ? '✓' : i + 1}
                  </span>
                  {label}
                </div>
                {i < WIZARD_STEPS.length - 1 && (
                  <div className={`h-px w-5 mx-0.5 ${
                    i < activeStepIdx - 1 ? 'bg-teal-300' : 'bg-slate-200'
                  }`} />
                )}
              </div>
            ))}
          </div>

          {/* PASO 1: QR */}
          {step === 'qr' && setupData && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8">
              <h2 className="font-bold text-slate-900 mb-1">Escanea el código QR</h2>
              <p className="text-slate-500 text-sm mb-6">
                Abre <strong>Google Authenticator</strong> → toca <strong>+</strong> → <strong>Escanear código QR</strong>.
              </p>

              {/* QR Code */}
              <div className="flex justify-center mb-6">
                <div className="p-4 bg-white border-2 border-slate-200 rounded-2xl shadow-inner">
                  <img
                    src={setupData.qr_code}
                    alt="Código QR para Google Authenticator"
                    className="w-56 h-56"
                  />
                </div>
              </div>

              {/* Clave manual */}
              <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 mb-6">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">
                  Clave manual — si no puedes escanear
                </p>
                <div className="flex items-center justify-between gap-3">
                  <code className="text-sm font-mono text-slate-800 tracking-wider break-all">
                    {setupData.secret}
                  </code>
                  <button
                    onClick={copySecret}
                    className="flex-shrink-0 flex items-center gap-1 text-xs font-bold text-teal-600 hover:text-teal-800 transition-colors"
                  >
                    <Copy size={12} />
                    {copied ? '¡Copiado!' : 'Copiar'}
                  </button>
                </div>
              </div>

              <button
                onClick={() => { setStep('verify'); setCodigo(''); setError(null) }}
                className={btnPrimary}
              >
                Ya lo escaneé <ChevronRight size={16} />
              </button>
              <button onClick={() => setStep('intro')} className={btnGhost}>Cancelar</button>
            </div>
          )}

          {/* PASO 2: VERIFICAR */}
          {step === 'verify' && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8">
              <h2 className="font-bold text-slate-900 mb-1">Confirma el código</h2>
              <p className="text-slate-500 text-sm mb-6">
                Ingresa el código de 6 dígitos que muestra Google Authenticator ahora
                para confirmar que el escaneo fue exitoso.
              </p>
              <form onSubmit={handleActivar} className="space-y-4">
                <input
                  type="text" inputMode="numeric" pattern="[0-9]{6}" maxLength={6}
                  value={codigo}
                  onChange={(e) => { setCodigo(e.target.value.replace(/\D/g, '')); setError(null) }}
                  className="w-full px-4 py-5 rounded-xl border-2 border-slate-200
                             text-slate-900 text-4xl text-center font-black tracking-[0.7em]
                             focus:outline-none focus:border-teal-500 bg-slate-50 focus:bg-white
                             placeholder:text-slate-200 transition-colors"
                  placeholder="000000"
                  autoFocus
                  required
                />
                {error && (
                  <p className="text-rose-600 text-sm bg-rose-50 border border-rose-200 px-3 py-2.5 rounded-xl font-semibold">
                    {error}
                  </p>
                )}
                <button type="submit" disabled={loading || codigo.length !== 6} className={btnPrimary}>
                  {loading ? 'Activando...' : 'Activar verificación en dos pasos'}
                </button>
              </form>
              <button onClick={() => setStep('qr')} className={btnGhost}>← Volver al QR</button>
            </div>
          )}

          {/* PASO 3: ÉXITO */}
          {step === 'success' && (
            <div className="bg-white rounded-2xl border border-teal-200 shadow-sm p-10 text-center">
              <div className="w-20 h-20 bg-teal-100 rounded-full flex items-center justify-center mx-auto mb-5">
                <CheckCircle size={40} className="text-teal-600" />
              </div>
              <h2 className="text-xl font-black text-slate-900 mb-2">¡Verificación activada!</h2>
              <p className="text-slate-500 text-sm max-w-xs mx-auto mb-8">
                Tu cuenta ahora está protegida con Google Authenticator.
                Necesitarás el código TOTP en cada inicio de sesión.
              </p>
              <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 text-left mb-6">
                <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-1">Recuerda</p>
                <p className="text-xs text-slate-600">
                  Guarda la clave manual en un lugar seguro. Si pierdes acceso a Google Authenticator,
                  necesitarás contactar a un administrador.
                </p>
              </div>
              <Link
                to="/dashboard"
                className="inline-flex items-center gap-2 bg-teal-600 hover:bg-teal-700
                           text-white font-bold px-6 py-3 rounded-xl transition-colors"
              >
                Ir al Dashboard <ChevronRight size={16} />
              </Link>
            </div>
          )}
        </>
      )}
    </div>
  )
}
