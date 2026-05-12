import { useEffect, useState } from 'react'
import { User, Lock, Shield, Mail, CheckCircle2, XCircle } from 'lucide-react'
import { api } from '../api/client'
import type { UsuarioMe } from '../types/api'
import { Badge } from '../components/ui/Badge'

export function Perfil() {
  const [usuario, setUsuario] = useState<UsuarioMe | null>(null)
  const [loading, setLoading] = useState(true)

  // Estado del formulario de cambio de contraseña
  const [form, setForm] = useState({
    password_actual: '',
    password_nueva: '',
    confirmar: '',
  })
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [exito, setExito] = useState(false)

  useEffect(() => {
    api.get<UsuarioMe>('/usuarios/me')
      .then(({ data }) => setUsuario(data))
      .finally(() => setLoading(false))
  }, [])

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }))
    setError(null)
    setExito(false)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setExito(false)

    if (form.password_nueva.length < 8) {
      setError('La contraseña nueva debe tener al menos 8 caracteres.')
      return
    }
    if (form.password_nueva !== form.confirmar) {
      setError('Las contraseñas nuevas no coinciden.')
      return
    }

    setGuardando(true)
    try {
      await api.post('/usuarios/me/cambiar-password', {
        password_actual: form.password_actual,
        password_nueva: form.password_nueva,
      })
      setExito(true)
      setForm({ password_actual: '', password_nueva: '', confirmar: '' })
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setError(detail ?? 'Error al cambiar la contraseña. Intenta de nuevo.')
    } finally {
      setGuardando(false)
    }
  }

  const rolLabel: Record<string, string> = {
    admin: 'Administrador',
    operador: 'Operador',
    visor: 'Visor',
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h1 className="text-2xl font-black text-slate-900 mb-8">Mi perfil</h1>

      {/* Tarjeta de información de cuenta */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
        <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-5">
          Información de la cuenta
        </h2>

        {loading ? (
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-5 bg-slate-100 rounded animate-pulse" />
            ))}
          </div>
        ) : usuario ? (
          <dl className="divide-y divide-slate-100">
            <InfoRow
              icon={<User size={15} />}
              label="Nombre"
              value={<span className="font-semibold text-slate-900">{usuario.nombre}</span>}
            />
            <InfoRow
              icon={<Mail size={15} />}
              label="Email"
              value={<span className="font-semibold text-slate-900">{usuario.email}</span>}
            />
            <InfoRow
              icon={<Shield size={15} />}
              label="Rol"
              value={<Badge variant="info">{rolLabel[usuario.rol] ?? usuario.rol}</Badge>}
            />
            <InfoRow
              icon={<CheckCircle2 size={15} />}
              label="Autenticación 2FA"
              value={
                usuario.totp_habilitado
                  ? <Badge variant="success">Activa</Badge>
                  : <Badge variant="warning">Inactiva</Badge>
              }
            />
          </dl>
        ) : null}
      </div>

      {/* Formulario cambiar contraseña */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-5">
          <Lock size={15} className="text-slate-400" />
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
            Cambiar contraseña
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <PasswordField
            label="Contraseña actual"
            name="password_actual"
            value={form.password_actual}
            onChange={handleChange}
          />
          <PasswordField
            label="Contraseña nueva"
            name="password_nueva"
            value={form.password_nueva}
            onChange={handleChange}
            hint="Mínimo 8 caracteres"
          />
          <PasswordField
            label="Confirmar contraseña nueva"
            name="confirmar"
            value={form.confirmar}
            onChange={handleChange}
          />

          {error && (
            <div className="flex items-center gap-2 text-rose-600 text-sm
                            bg-rose-50 border border-rose-200 rounded-lg px-4 py-2.5">
              <XCircle size={15} className="flex-shrink-0" />
              {error}
            </div>
          )}

          {exito && (
            <div className="flex items-center gap-2 text-teal-700 text-sm
                            bg-teal-50 border border-teal-200 rounded-lg px-4 py-2.5">
              <CheckCircle2 size={15} className="flex-shrink-0" />
              Contraseña actualizada correctamente.
            </div>
          )}

          <button
            type="submit"
            disabled={guardando || !form.password_actual || !form.password_nueva || !form.confirmar}
            className="w-full mt-2 py-2.5 px-4 bg-teal-600 hover:bg-teal-700
                       disabled:opacity-50 disabled:cursor-not-allowed
                       text-white text-sm font-bold rounded-xl transition-colors"
          >
            {guardando ? 'Guardando...' : 'Cambiar contraseña'}
          </button>
        </form>
      </div>
    </div>
  )
}

// ── Sub-componentes locales ──────────────────────────────────────────────────

function InfoRow({
  icon, label, value,
}: {
  icon: React.ReactNode
  label: string
  value: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-3">
      <dt className="flex items-center gap-2 text-sm text-slate-500 min-w-0">
        <span className="text-slate-400">{icon}</span>
        {label}
      </dt>
      <dd className="text-sm text-right">{value}</dd>
    </div>
  )
}

function PasswordField({
  label, name, value, onChange, hint,
}: {
  label: string
  name: string
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  hint?: string
}) {
  return (
    <div>
      <label className="block text-xs font-semibold text-slate-600 mb-1.5">
        {label}
      </label>
      <input
        type="password"
        name={name}
        value={value}
        onChange={onChange}
        autoComplete="new-password"
        className="w-full px-3 py-2.5 rounded-lg border border-slate-200 text-sm
                   focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent
                   transition"
      />
      {hint && <p className="text-xs text-slate-400 mt-1">{hint}</p>}
    </div>
  )
}
