import { useEffect, useState, useCallback } from 'react'
import {
  Search, Package, ChevronLeft, ChevronRight,
  Plus, Pencil, Trash2, CheckCircle, ShieldAlert
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuthStore } from '../store/auth'
import type {
  InsumoResponse, SalaResponse, CategoriaResponse, PaginatedResponse
} from '../types/api'
import { Badge } from '../components/ui/Badge'
import { TableRowSkeleton } from '../components/ui/Skeleton'
import { Modal } from '../components/ui/Modal'

const PAGE_SIZE = 15
const TOTP_VALID_LEN = 6

interface FormState {
  nombre: string
  descripcion: string
  stock_actual: string
  stock_minimo: string
  sala_id: string
  categoria_id: string
}

const FORM_VACIO: FormState = {
  nombre: '', descripcion: '', stock_actual: '',
  stock_minimo: '', sala_id: '', categoria_id: ''
}

function insumoAForm(i: InsumoResponse): FormState {
  return {
    nombre: i.nombre,
    descripcion: i.descripcion ?? '',
    stock_actual: String(i.stock_actual),
    stock_minimo: String(i.stock_minimo),
    sala_id: i.sala_id != null ? String(i.sala_id) : '',
    categoria_id: i.categoria_id != null ? String(i.categoria_id) : ''
  }
}

export function Insumos() {
  const { user } = useAuthStore()
  const puedeEscribir = user?.rol === 'admin' || user?.rol === 'operador'
  const puedeEliminar = user?.rol === 'admin'

  const [insumos, setInsumos]         = useState<InsumoResponse[]>([])
  const [total, setTotal]             = useState(0)
  const [page, setPage]               = useState(0)
  const [search, setSearch]           = useState('')
  const [query, setQuery]             = useState('')
  const [loading, setLoading]         = useState(true)
  const [salas, setSalas]             = useState<SalaResponse[]>([])
  const [categorias, setCategorias]   = useState<CategoriaResponse[]>([])
  const [userHas2FA, setUserHas2FA]   = useState<boolean | null>(null)

  // Modales
  const [editTarget, setEditTarget]     = useState<InsumoResponse | null>(null)
  const [showCrear, setShowCrear]       = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<InsumoResponse | null>(null)
  const [deleteStep, setDeleteStep]     = useState<'confirm' | 'totp'>('confirm')
  const [deleteTotp, setDeleteTotp]     = useState('')
  const [form, setForm]                 = useState<FormState>(FORM_VACIO)
  const [saving, setSaving]             = useState(false)
  const [formError, setFormError]       = useState<string | null>(null)
  const [deleting, setDeleting]         = useState(false)
  const [toast, setToast]               = useState<string | null>(null)

  function showToast(msg: string) {
    setToast(msg)
    setTimeout(() => setToast(null), 3000)
  }

  useEffect(() => {
    Promise.all([
      api.get<PaginatedResponse<SalaResponse>>('/salas/', { params: { limit: 100 } }),
      api.get<PaginatedResponse<CategoriaResponse>>('/categorias/', { params: { limit: 100 } }),
      api.get<{ totp_habilitado: boolean }>('/usuarios/me')
    ]).then(([s, c, me]) => {
      setSalas(s.data.data)
      setCategorias(c.data.data)
      setUserHas2FA(me.data.totp_habilitado)
    })
  }, [])

  const load = useCallback(async (skip: number, q: string) => {
    setLoading(true)
    try {
      const { data } = await api.get<PaginatedResponse<InsumoResponse>>('/insumos/', {
        params: { skip, limit: PAGE_SIZE }
      })
      const filtrados = q
        ? data.data.filter(i => i.nombre.toLowerCase().includes(q.toLowerCase()))
        : data.data
      setInsumos(filtrados)
      setTotal(q ? filtrados.length : data.total)
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { load(page * PAGE_SIZE, query) }, [page, query, load])

  function handleSearch(e: React.FormEvent) {
    e.preventDefault(); setPage(0); setQuery(search)
  }

  function abrirCrear() {
    setForm(FORM_VACIO); setFormError(null); setShowCrear(true)
  }

  function abrirEditar(i: InsumoResponse) {
    setForm(insumoAForm(i)); setFormError(null); setEditTarget(i)
  }

  function abrirEliminar(i: InsumoResponse) {
    setDeleteTarget(i); setDeleteStep('confirm')
    setDeleteTotp(''); setFormError(null)
  }

  function cerrarModal() {
    setShowCrear(false); setEditTarget(null)
    setDeleteTarget(null); setFormError(null)
    setDeleteTotp('')
  }

  function setField(key: keyof FormState, val: string) {
    setForm(f => ({ ...f, [key]: val }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true); setFormError(null)
    const payload = {
      nombre: form.nombre.trim(),
      descripcion: form.descripcion.trim() || null,
      stock_actual: parseInt(form.stock_actual) || 0,
      stock_minimo: parseInt(form.stock_minimo) || 0,
      sala_id: form.sala_id ? parseInt(form.sala_id) : null,
      categoria_id: form.categoria_id ? parseInt(form.categoria_id) : null
    }
    try {
      if (editTarget) {
        await api.put(`/insumos/${editTarget.id}`, payload)
        showToast('Insumo actualizado correctamente')
      } else {
        await api.post('/insumos/', payload)
        showToast('Insumo creado correctamente')
      }
      cerrarModal(); load(page * PAGE_SIZE, query)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        .response?.data?.detail
      setFormError(msg ?? 'Error al guardar el insumo.')
    } finally { setSaving(false) }
  }

  async function confirmDelete() {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      // axios DELETE con body: pasar data en la config
      await api.delete(`/insumos/${deleteTarget.id}`, {
        data: { codigo_totp: deleteTotp }
      })
      showToast('Insumo eliminado')
      cerrarModal(); load(page * PAGE_SIZE, query)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        .response?.data?.detail
      setFormError(msg ?? 'Error al eliminar.')
    } finally { setDeleting(false) }
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const showModal  = showCrear || editTarget !== null

  function stockBadge(i: InsumoResponse) {
    if (i.stock_actual === 0) return <Badge variant="danger">Agotado</Badge>
    if (i.stock_actual <= i.stock_minimo) return <Badge variant="warning">Bajo stock</Badge>
    return <Badge variant="success">OK</Badge>
  }

  const inputCls = `
    w-full px-3 py-2.5 rounded-lg border border-slate-200 text-slate-900 text-sm
    focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent
    bg-slate-50 focus:bg-white placeholder:text-slate-400 transition-all
  `
  const labelCls = "block text-xs font-bold text-slate-500 uppercase tracking-wide mb-1.5"

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Toast */}
      {toast && (
        <div className="fixed top-6 right-6 z-50 flex items-center gap-2
                        bg-teal-600 text-white px-4 py-3 rounded-xl shadow-lg
                        text-sm font-semibold">
          <CheckCircle size={16} /> {toast}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-black text-slate-900">Insumos</h1>
          <p className="text-slate-500 text-sm mt-0.5">{total} insumos en inventario</p>
        </div>
        {puedeEscribir && (
          <button
            onClick={abrirCrear}
            className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700
                       text-white font-bold px-4 py-2.5 rounded-xl text-sm transition-colors"
          >
            <Plus size={16} /> Nuevo insumo
          </button>
        )}
      </div>

      {/* Busqueda */}
      <form onSubmit={handleSearch} className="mb-6">
        <div className="relative">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text" value={search}
            onChange={e => {
              setSearch(e.target.value)
              if (!e.target.value) { setQuery(''); setPage(0) }
            }}
            placeholder="Buscar insumo por nombre…"
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 bg-white
                       text-slate-900 text-sm shadow-sm focus:outline-none focus:ring-2
                       focus:ring-teal-500 focus:border-transparent placeholder:text-slate-400"
          />
        </div>
      </form>

      {/* Tabla */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              <th className="text-left px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Nombre</th>
              <th className="text-left px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Descripcion</th>
              <th className="text-center px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Stock</th>
              <th className="text-center px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Minimo</th>
              <th className="text-center px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Estado</th>
              {puedeEscribir && (
                <th className="text-center px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Acciones</th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              Array.from({ length: PAGE_SIZE }).map((_, i) => (
                <TableRowSkeleton key={i} cols={puedeEscribir ? 6 : 5} />
              ))
            ) : insumos.length === 0 ? (
              <tr>
                <td colSpan={puedeEscribir ? 6 : 5} className="text-center py-16 text-slate-400">
                  <Package size={32} className="mx-auto mb-2 opacity-30" />
                  <p className="font-semibold">Sin insumos que mostrar</p>
                  {query && (
                    <button
                      onClick={() => { setQuery(''); setSearch('') }}
                      className="text-teal-600 text-xs mt-1 font-bold"
                    >Limpiar busqueda</button>
                  )}
                </td>
              </tr>
            ) : (
              insumos.map(i => (
                <tr key={i.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3 font-semibold text-slate-900">{i.nombre}</td>
                  <td className="px-4 py-3 text-slate-500 max-w-xs truncate">
                    {i.descripcion ?? <span className="text-slate-300">—</span>}
                  </td>
                  <td className="px-4 py-3 text-center font-bold text-slate-900">{i.stock_actual}</td>
                  <td className="px-4 py-3 text-center text-slate-500">{i.stock_minimo}</td>
                  <td className="px-4 py-3 text-center">{stockBadge(i)}</td>
                  {puedeEscribir && (
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => abrirEditar(i)}
                          className="p-1.5 rounded-lg text-slate-400 hover:bg-teal-50
                                     hover:text-teal-600 transition-colors" title="Editar"
                        >
                          <Pencil size={14} />
                        </button>
                        {puedeEliminar && (
                          <button
                            onClick={() => abrirEliminar(i)}
                            className="p-1.5 rounded-lg text-slate-400 hover:bg-rose-50
                                       hover:text-rose-600 transition-colors" title="Eliminar"
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>

        {!loading && !query && totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200">
            <p className="text-xs text-slate-500">Pagina {page + 1} de {totalPages}</p>
            <div className="flex items-center gap-1">
              <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
                className="p-1.5 rounded-lg hover:bg-slate-100 disabled:opacity-40">
                <ChevronLeft size={16} className="text-slate-600" />
              </button>
              <button
                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="p-1.5 rounded-lg hover:bg-slate-100 disabled:opacity-40">
                <ChevronRight size={16} className="text-slate-600" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modal crear / editar */}
      {showModal && (
        <Modal title={editTarget ? 'Editar insumo' : 'Nuevo insumo'} onClose={cerrarModal} size="lg">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className={labelCls}>Nombre *</label>
              <input type="text" required value={form.nombre}
                onChange={e => setField('nombre', e.target.value)}
                className={inputCls} placeholder="Ej: Guantes de nitrilo talla M" />
            </div>
            <div>
              <label className={labelCls}>Descripcion</label>
              <input type="text" value={form.descripcion}
                onChange={e => setField('descripcion', e.target.value)}
                className={inputCls} placeholder="Opcional" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelCls}>Stock actual *</label>
                <input type="number" min="0" required value={form.stock_actual}
                  onChange={e => setField('stock_actual', e.target.value)} className={inputCls} />
              </div>
              <div>
                <label className={labelCls}>Stock minimo *</label>
                <input type="number" min="0" required value={form.stock_minimo}
                  onChange={e => setField('stock_minimo', e.target.value)} className={inputCls} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelCls}>Sala</label>
                <select value={form.sala_id} onChange={e => setField('sala_id', e.target.value)}
                  className={inputCls}>
                  <option value="">Sin sala</option>
                  {salas.map(s => <option key={s.id} value={s.id}>{s.nombre}</option>)}
                </select>
              </div>
              <div>
                <label className={labelCls}>Categoria</label>
                <select value={form.categoria_id}
                  onChange={e => setField('categoria_id', e.target.value)} className={inputCls}>
                  <option value="">Sin categoria</option>
                  {categorias.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
                </select>
              </div>
            </div>
            {formError && (
              <p className="text-rose-600 text-sm bg-rose-50 border border-rose-200
                            px-3 py-2 rounded-lg font-semibold">{formError}</p>
            )}
            <div className="flex gap-3 pt-2">
              <button type="button" onClick={cerrarModal}
                className="flex-1 py-2.5 rounded-xl border border-slate-200 text-slate-600
                           font-bold hover:bg-slate-50 transition-colors">Cancelar</button>
              <button type="submit" disabled={saving}
                className="flex-1 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white
                           font-bold transition-colors disabled:opacity-50">
                {saving ? 'Guardando...' : editTarget ? 'Guardar cambios' : 'Crear insumo'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {/* Modal eliminar — dos pasos: confirmar + TOTP */}
      {deleteTarget && (
        <Modal title="Eliminar insumo" onClose={cerrarModal} size="sm">
          {deleteStep === 'confirm' ? (
            <div className="text-center">
              <div className="w-14 h-14 bg-rose-100 rounded-full flex items-center
                              justify-center mx-auto mb-4">
                <Trash2 size={24} className="text-rose-600" />
              </div>
              <p className="font-bold text-slate-900 mb-1">¿Eliminar este insumo?</p>
              <p className="text-slate-500 text-sm mb-2">
                <strong>{deleteTarget.nombre}</strong> sera eliminado permanentemente.
              </p>
              {/* Aviso si no tiene 2FA */}
              {userHas2FA === false ? (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4 text-left">
                  <div className="flex items-start gap-2">
                    <ShieldAlert size={16} className="text-amber-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-amber-800 font-bold text-xs">2FA requerido para eliminar</p>
                      <p className="text-amber-700 text-xs mt-0.5">
                        Necesitas activar la verificacion en dos pasos antes de
                        poder eliminar insumos.
                      </p>
                    </div>
                  </div>
                  <Link to="/seguridad" onClick={cerrarModal}
                    className="mt-3 flex items-center justify-center gap-1.5
                               bg-amber-600 hover:bg-amber-700 text-white text-xs
                               font-bold py-2 rounded-lg transition-colors">
                    Activar 2FA ahora
                  </Link>
                </div>
              ) : (
                <>
                  <p className="text-slate-400 text-xs mb-5">
                    Necesitaras tu codigo TOTP para confirmar.
                  </p>
                  <div className="flex gap-3">
                    <button onClick={cerrarModal}
                      className="flex-1 py-2.5 rounded-xl border border-slate-200
                                 text-slate-600 font-bold hover:bg-slate-50 transition-colors">
                      Cancelar
                    </button>
                    <button onClick={() => setDeleteStep('totp')}
                      className="flex-1 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700
                                 text-white font-bold transition-colors">
                      Continuar
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : (
            <div>
              <p className="text-slate-600 text-sm mb-5 text-center">
                Ingresa tu codigo TOTP para confirmar la eliminacion de
                <strong> {deleteTarget.nombre}</strong>.
              </p>
              <input
                type="text" inputMode="numeric" maxLength={TOTP_VALID_LEN}
                value={deleteTotp}
                onChange={e => { setDeleteTotp(e.target.value.replace(/\D/g, '')); setFormError(null) }}
                className="w-full px-4 py-4 rounded-xl border-2 border-slate-200
                           text-slate-900 text-4xl text-center font-black tracking-[0.7em]
                           focus:outline-none focus:border-rose-400 bg-slate-50 mb-4
                           placeholder:text-slate-200"
                placeholder="000000" autoFocus
              />
              {formError && (
                <p className="text-rose-600 text-xs bg-rose-50 border border-rose-200
                              px-3 py-2 rounded-lg font-semibold mb-4">{formError}</p>
              )}
              <div className="flex gap-3">
                <button onClick={() => setDeleteStep('confirm')}
                  className="flex-1 py-2.5 rounded-xl border border-slate-200
                             text-slate-600 font-bold hover:bg-slate-50 transition-colors">
                  ← Volver
                </button>
                <button
                  onClick={confirmDelete}
                  disabled={deleting || deleteTotp.length !== TOTP_VALID_LEN}
                  className="flex-1 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700
                             text-white font-bold transition-colors disabled:opacity-50">
                  {deleting ? 'Eliminando...' : 'Eliminar'}
                </button>
              </div>
            </div>
          )}
        </Modal>
      )}
    </div>
  )
}
