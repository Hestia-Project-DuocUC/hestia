import { useEffect, useState, useCallback } from 'react'
import {
  ArrowUpCircle, ArrowDownCircle, Plus, RefreshCw, CheckCircle
} from 'lucide-react'
import { api } from '../api/client'
import { useAuthStore } from '../store/auth'
import type {
  MovimientoEnriquecido, MovimientoCreate,
  InsumoResponse, PaginatedResponse, TipoMovimiento
} from '../types/api'
import { Badge } from '../components/ui/Badge'
import { Modal } from '../components/ui/Modal'
import { TableRowSkeleton } from '../components/ui/Skeleton'

const PAGE_SIZE = 20

function formatFecha(fecha: string) {
  return new Date(fecha).toLocaleString('es-CL', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

function formatAntiguedad(fecha: Date): string {
  const diff = Math.floor((Date.now() - fecha.getTime()) / 1000)
  if (diff < 60) return 'Actualizado hace un momento'
  if (diff < 3600) return `Actualizado hace ${Math.floor(diff / 60)} min`
  return `Actualizado el ${fecha.toLocaleString('es-CL', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })}`
}

export function Movimientos() {
  const { user } = useAuthStore()
  const puedeRegistrar = user?.rol === 'admin' || user?.rol === 'operador'

  const [movimientos, setMovimientos] = useState<MovimientoEnriquecido[]>([])
  const [total, setTotal]             = useState(0)
  const [page, setPage]               = useState(0)
  const [filtro, setFiltro]           = useState<TipoMovimiento | 'todos'>('todos')
  const [loading, setLoading]         = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  // Modal registrar
  const [showModal, setShowModal]     = useState(false)
  const [insumos, setInsumos]         = useState<InsumoResponse[]>([])
  const [tipo, setTipo]               = useState<TipoMovimiento>('entrada')
  const [insumoId, setInsumoId]       = useState('')
  const [cantidad, setCantidad]       = useState('')
  const [motivo, setMotivo]           = useState('')
  const [saving, setSaving]           = useState(false)
  const [formError, setFormError]     = useState<string | null>(null)
  const [toast, setToast]             = useState<string | null>(null)

  function showToast(msg: string) {
    setToast(msg); setTimeout(() => setToast(null), 3000)
  }

  const load = useCallback(async (skip: number) => {
    setLoading(true)
    try {
      const { data } = await api.get<PaginatedResponse<MovimientoEnriquecido>>(
        '/movimientos/', { params: { skip, limit: PAGE_SIZE } }
      )
      setMovimientos(data.data); setTotal(data.total)
      setLastUpdated(new Date())
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { load(page * PAGE_SIZE) }, [page, load])

  async function abrirModal() {
    setTipo('entrada'); setInsumoId(''); setCantidad(''); setMotivo('')
    setFormError(null)
    if (insumos.length === 0) {
      const { data } = await api.get<PaginatedResponse<InsumoResponse>>(
        '/insumos/', { params: { limit: 200 } }
      )
      setInsumos(data.data)
    }
    setShowModal(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSaving(true); setFormError(null)
    const payload: MovimientoCreate = {
      tipo,
      insumo_id: parseInt(insumoId),
      cantidad: parseInt(cantidad),
      motivo: motivo.trim() || null
    }
    try {
      await api.post('/movimientos/', payload)
      showToast('Movimiento registrado correctamente')
      setShowModal(false)
      load(0); setPage(0)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        .response?.data?.detail
      setFormError(msg ?? 'Error al registrar el movimiento.')
    } finally { setSaving(false) }
  }

  // Filtro cliente: filtra los movimientos del listado actual por tipo
  const visibles = filtro === 'todos'
    ? movimientos
    : movimientos.filter(m => m.tipo === filtro)

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const inputCls = `w-full px-3 py-2.5 rounded-lg border border-slate-200 text-slate-900 text-sm
    focus:outline-none focus:ring-2 focus:ring-teal-500 bg-slate-50 focus:bg-white
    placeholder:text-slate-400 transition-all`
  const labelCls = "block text-xs font-bold text-slate-500 uppercase tracking-wide mb-1.5"

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {toast && (
        <div className="fixed top-6 right-6 z-50 flex items-center gap-2 bg-teal-600
                        text-white px-4 py-3 rounded-xl shadow-lg text-sm font-semibold">
          <CheckCircle size={16} />{toast}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-black text-slate-900">Movimientos</h1>
          <p className="text-slate-500 text-sm mt-0.5">
            {total} movimientos registrados
          </p>
          {lastUpdated && (
            <p className="text-xs text-slate-400 mt-0.5">{formatAntiguedad(lastUpdated)}</p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => { load(page * PAGE_SIZE) }}
            className="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-200
                       text-slate-500 hover:bg-slate-50 text-sm transition-colors">
            <RefreshCw size={14} /> Actualizar
          </button>
          {puedeRegistrar && (
            <button onClick={abrirModal}
              className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white
                         font-bold px-4 py-2.5 rounded-xl text-sm transition-colors">
              <Plus size={16} /> Registrar movimiento
            </button>
          )}
        </div>
      </div>

      {/* Filtros */}
      <div className="flex gap-2 mb-5">
        {(['todos', 'entrada', 'salida'] as const).map(f => (
          <button
            key={f}
            onClick={() => setFiltro(f)}
            className={`px-4 py-1.5 rounded-full text-sm font-bold transition-colors ${
              filtro === f
                ? 'bg-slate-900 text-white'
                : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
            }`}
          >
            {f === 'todos' ? 'Todos' : f === 'entrada' ? 'Entradas' : 'Salidas'}
          </button>
        ))}
      </div>

      {/* Tabla con scroll horizontal en pantallas pequeñas */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-x-auto">
        <table className="w-full min-w-[720px] text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              <th className="text-left px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Tipo</th>
              <th className="text-left px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Insumo</th>
              <th className="text-left px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Sala</th>
              <th className="text-center px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Cantidad</th>
              <th className="text-left px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Motivo</th>
              <th className="text-left px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide whitespace-nowrap">Fecha</th>
              <th className="text-left px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Usuario</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              Array.from({ length: 10 }).map((_, i) => <TableRowSkeleton key={i} cols={7} />)
            ) : visibles.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-16 text-slate-400">
                <ArrowUpCircle size={32} className="mx-auto mb-2 opacity-30" />
                <p className="font-semibold">Sin movimientos que mostrar</p>
              </td></tr>
            ) : visibles.map(m => (
              <tr key={m.id} className="hover:bg-slate-50 transition-colors">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    {m.tipo === 'entrada'
                      ? <ArrowUpCircle size={15} className="text-teal-600" />
                      : <ArrowDownCircle size={15} className="text-amber-500" />
                    }
                    <Badge variant={m.tipo === 'entrada' ? 'success' : 'warning'}>
                      {m.tipo}
                    </Badge>
                  </div>
                </td>
                <td className="px-4 py-3 font-semibold text-slate-900 max-w-xs truncate">
                  {m.insumo}
                </td>
                <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                  {m.sala ?? <span className="text-slate-300">—</span>}
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={`font-bold ${
                    m.tipo === 'entrada' ? 'text-teal-600' : 'text-amber-600'
                  }`}>
                    {m.tipo === 'entrada' ? '+' : '-'}{m.cantidad}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-500 max-w-xs truncate">
                  {m.motivo ?? <span className="text-slate-300">—</span>}
                </td>
                <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                  {formatFecha(m.fecha)}
                </td>
                <td className="px-4 py-3 text-slate-500 whitespace-nowrap">
                  {m.usuario}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {!loading && totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200">
            <p className="text-xs text-slate-500">Pagina {page + 1} de {totalPages}</p>
            <div className="flex gap-1">
              <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
                className="px-3 py-1 text-xs rounded-lg border border-slate-200
                           disabled:opacity-40 hover:bg-slate-50">←</button>
              <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="px-3 py-1 text-xs rounded-lg border border-slate-200
                           disabled:opacity-40 hover:bg-slate-50">→</button>
            </div>
          </div>
        )}
      </div>

      {/* Modal registrar movimiento */}
      {showModal && (
        <Modal title="Registrar movimiento" onClose={() => setShowModal(false)}>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Tipo */}
            <div>
              <label className={labelCls}>Tipo *</label>
              <div className="grid grid-cols-2 gap-3">
                {(['entrada', 'salida'] as TipoMovimiento[]).map(t => (
                  <button
                    key={t} type="button"
                    onClick={() => setTipo(t)}
                    className={`py-3 rounded-xl border-2 font-bold text-sm
                                flex items-center justify-center gap-2 transition-all ${
                      tipo === t
                        ? t === 'entrada'
                          ? 'border-teal-500 bg-teal-50 text-teal-700'
                          : 'border-amber-500 bg-amber-50 text-amber-700'
                        : 'border-slate-200 text-slate-500 hover:border-slate-300'
                    }`}
                  >
                    {t === 'entrada'
                      ? <ArrowUpCircle size={16} />
                      : <ArrowDownCircle size={16} />
                    }
                    {t.charAt(0).toUpperCase() + t.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Insumo */}
            <div>
              <label className={labelCls}>Insumo *</label>
              <select required value={insumoId}
                onChange={e => setInsumoId(e.target.value)}
                className={inputCls}>
                <option value="">Seleccionar insumo...</option>
                {insumos.map(i => (
                  <option key={i.id} value={i.id}>
                    {i.nombre} (stock: {i.stock_actual})
                  </option>
                ))}
              </select>
            </div>

            {/* Cantidad */}
            <div>
              <label className={labelCls}>Cantidad *</label>
              <input type="number" min="1" required value={cantidad}
                onChange={e => setCantidad(e.target.value)}
                className={inputCls} placeholder="0" />
            </div>

            {/* Motivo */}
            <div>
              <label className={labelCls}>Motivo</label>
              <input type="text" value={motivo}
                onChange={e => setMotivo(e.target.value)}
                className={inputCls}
                placeholder="Ej: Reposicion mensual, Uso en practica clinica..." />
            </div>

            {formError && (
              <p className="text-rose-600 text-sm bg-rose-50 border border-rose-200
                            px-3 py-2 rounded-lg font-semibold">{formError}</p>
            )}

            <div className="flex gap-3 pt-2">
              <button type="button" onClick={() => setShowModal(false)}
                className="flex-1 py-2.5 rounded-xl border border-slate-200
                           text-slate-600 font-bold hover:bg-slate-50">Cancelar</button>
              <button type="submit" disabled={saving || !insumoId || !cantidad}
                className="flex-1 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700
                           text-white font-bold disabled:opacity-50">
                {saving ? 'Registrando...' : 'Registrar'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
