import { useEffect, useState } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { api } from '../api/client'
import type { InsumoAlerta } from '../types/api'
import { Badge } from '../components/ui/Badge'
import { AlertaCardSkeleton } from '../components/ui/Skeleton'

export function Alertas() {
  const [alertas, setAlertas] = useState<InsumoAlerta[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  async function load(showRefresh = false) {
    if (showRefresh) setRefreshing(true)
    else setLoading(true)
    try {
      const { data } = await api.get<InsumoAlerta[]>('/insumos/alertas')
      setAlertas(data)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => { load() }, [])

  // Clasifica la gravedad por el deficit
  function gravedad(a: InsumoAlerta): 'danger' | 'warning' {
    return a.stock_actual === 0 || a.deficit >= a.stock_minimo ? 'danger' : 'warning'
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-black text-slate-900">Alertas de stock</h1>
          <p className="text-slate-500 text-sm mt-0.5">
            Insumos con stock igual o por debajo del mínimo establecido.
          </p>
        </div>
        <button
          onClick={() => load(true)}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200
                     text-slate-600 hover:bg-slate-100 text-sm font-semibold transition-colors"
        >
          <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
          Actualizar
        </button>
      </div>

      {/* Contador */}
      {!loading && (
        <div className="flex items-center gap-2 mb-5">
          <span className="text-sm text-slate-500">
            {alertas.length === 0
              ? 'Sin alertas activas'
              : `${alertas.length} insumo${alertas.length !== 1 ? 's' : ''} en alerta`
            }
          </span>
          {alertas.length > 0 && (
            <Badge variant="danger">{alertas.filter(a => a.stock_actual === 0).length} agotados</Badge>
          )}
        </div>
      )}

      {/* Lista */}
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => <AlertaCardSkeleton key={i} />)}
        </div>
      ) : alertas.length === 0 ? (
        <div className="bg-teal-50 border border-teal-200 rounded-2xl p-12 text-center">
          <div className="w-14 h-14 bg-teal-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <AlertTriangle size={24} className="text-teal-600" />
          </div>
          <p className="text-teal-800 font-bold">Todo el inventario está en orden</p>
          <p className="text-teal-600 text-sm mt-1">
            Ningún insumo está bajo el stock mínimo definido.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {alertas.map((a) => (
            <div
              key={a.id}
              className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm
                         hover:shadow-md hover:border-slate-300 transition-all"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-4">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                    a.stock_actual === 0 ? 'bg-rose-100' : 'bg-amber-50'
                  }`}>
                    <AlertTriangle
                      size={18}
                      className={a.stock_actual === 0 ? 'text-rose-600' : 'text-amber-500'}
                    />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-bold text-slate-900">{a.nombre}</p>
                      {a.stock_actual === 0 && (
                        <Badge variant="danger">Agotado</Badge>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {a.sala ?? 'Sin sala asignada'}
                      {a.categoria ? ` · ${a.categoria}` : ''}
                    </p>
                  </div>
                </div>
                <Badge variant={gravedad(a)}>Déficit: {a.deficit}</Badge>
              </div>

              {/* Barra de progreso de stock */}
              <div className="mt-4">
                <div className="flex justify-between text-xs text-slate-500 mb-1.5">
                  <span>Stock actual: <span className="font-bold text-slate-700">{a.stock_actual}</span></span>
                  <span>Mínimo: <span className="font-bold">{a.stock_minimo}</span></span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      a.stock_actual === 0 ? 'bg-rose-500' : 'bg-amber-400'
                    }`}
                    style={{
                      width: `${Math.min(100, (a.stock_actual / Math.max(a.stock_minimo, 1)) * 100)}%`
                    }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
