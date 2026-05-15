import { useEffect, useState } from 'react'
import { AlertTriangle, CheckCircle2, RefreshCw } from 'lucide-react'
import { api } from '../api/client'
import type { InsumoAlerta } from '../types/api'
import { Badge } from '../components/ui/Badge'
import { AlertaCardSkeleton } from '../components/ui/Skeleton'

type Tab = 'activas' | 'resueltas'
const DIAS_OPTIONS = [7, 14, 30] as const

function formatAntiguedad(fecha: Date): string {
  const diff = Math.floor((Date.now() - fecha.getTime()) / 1000)
  if (diff < 60) return 'Actualizado hace un momento'
  if (diff < 3600) return `Actualizado hace ${Math.floor(diff / 60)} min`
  return `Actualizado el ${fecha.toLocaleString('es-CL', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })}`
}

export function Alertas() {
  const [tab, setTab]           = useState<Tab>('activas')
  const [dias, setDias]         = useState<number>(30)
  const [refetchKey, setRefetchKey] = useState(0)
  const [activas, setActivas]   = useState<InsumoAlerta[]>([])
  const [resueltas, setResueltas] = useState<InsumoAlerta[]>([])
  const [loading, setLoading]   = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  // Re-ejecuta cuando cambia tab, dias o se presiona "Actualizar"
  useEffect(() => {
    setLoading(true)
    const url = tab === 'activas'
      ? '/insumos/alertas'
      : `/insumos/alertas-resueltas?dias=${dias}`

    api.get<InsumoAlerta[]>(url)
      .then(({ data }) => {
        if (tab === 'activas') setActivas(data)
        else setResueltas(data)
        setLastUpdated(new Date())
      })
      .finally(() => {
        setLoading(false)
        setRefreshing(false)
      })
  }, [tab, dias, refetchKey])

  function refresh() {
    setRefreshing(true)
    setRefetchKey(k => k + 1)
  }

  function gravedad(a: InsumoAlerta): 'danger' | 'warning' {
    return a.stock_actual === 0 || a.deficit >= a.stock_minimo ? 'danger' : 'warning'
  }

  const items = tab === 'activas' ? activas : resueltas

  return (
    <div className="p-8 max-w-4xl mx-auto">

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-black text-slate-900">Alertas de stock</h1>
          <p className="text-slate-500 text-sm mt-0.5">
            {tab === 'activas'
              ? 'Insumos con stock igual o por debajo del mínimo establecido.'
              : 'Insumos que superaron el mínimo y recibieron entradas recientemente.'}
          </p>
          {lastUpdated && (
            <p className="text-xs text-slate-400 mt-0.5">{formatAntiguedad(lastUpdated)}</p>
          )}
        </div>
        <button
          onClick={refresh}
          disabled={refreshing || loading}
          className="flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200
                     text-slate-600 hover:bg-slate-100 text-sm font-semibold transition-colors"
        >
          <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
          Actualizar
        </button>
      </div>

      {/* Tabs Activas / Resueltas */}
      <div className="flex items-center gap-1 p-1 bg-slate-100 rounded-xl mb-5 w-fit">
        {(['activas', 'resueltas'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-5 py-1.5 rounded-lg text-sm font-semibold transition-colors capitalize
              ${ tab === t
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
              }`}
          >
            {t === 'activas' ? 'Activas' : 'Resueltas'}
          </button>
        ))}
      </div>

      {/* Selector de días (solo tab resueltas) */}
      {tab === 'resueltas' && (
        <div className="flex items-center gap-2 mb-5">
          <span className="text-sm text-slate-500">Entradas en los últimos:</span>
          {DIAS_OPTIONS.map((d) => (
            <button
              key={d}
              onClick={() => setDias(d)}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-colors
                ${ dias === d
                  ? 'bg-teal-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
            >
              {d} días
            </button>
          ))}
        </div>
      )}

      {/* Contador */}
      {!loading && (
        <div className="flex items-center gap-2 mb-5">
          <span className="text-sm text-slate-500">
            {items.length === 0
              ? (tab === 'activas' ? 'Sin alertas activas' : 'Sin alertas resueltas en este período')
              : `${items.length} insumo${items.length !== 1 ? 's' : ''} ${tab === 'activas' ? 'en alerta' : 'resuelto' + (items.length !== 1 ? 's' : '')}`
            }
          </span>
          {tab === 'activas' && activas.length > 0 && (
            <Badge variant="danger">
              {activas.filter(a => a.stock_actual === 0).length} agotados
            </Badge>
          )}
        </div>
      )}

      {/* Lista */}
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => <AlertaCardSkeleton key={i} />)}
        </div>
      ) : items.length === 0 ? (
        <div className={`border rounded-2xl p-12 text-center ${
          tab === 'activas'
            ? 'bg-teal-50 border-teal-200'
            : 'bg-slate-50 border-slate-200'
        }`}>
          <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4 ${
            tab === 'activas' ? 'bg-teal-100' : 'bg-slate-100'
          }`}>
            {tab === 'activas'
              ? <AlertTriangle size={24} className="text-teal-600" />
              : <CheckCircle2 size={24} className="text-slate-400" />
            }
          </div>
          <p className={`font-bold ${
            tab === 'activas' ? 'text-teal-800' : 'text-slate-700'
          }`}>
            {tab === 'activas'
              ? 'Todo el inventario está en orden'
              : `Sin alertas resueltas en los últimos ${dias} días`}
          </p>
          <p className={`text-sm mt-1 ${
            tab === 'activas' ? 'text-teal-600' : 'text-slate-500'
          }`}>
            {tab === 'activas'
              ? 'Ningún insumo está bajo el stock mínimo definido.'
              : 'No hubo insumos que superaran el mínimo en este período.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((a) => (
            <div
              key={a.id}
              className={`bg-white rounded-xl border p-5 shadow-sm
                          hover:shadow-md transition-all ${
                tab === 'resueltas'
                  ? 'border-teal-200 hover:border-teal-300'
                  : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-4">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                    tab === 'resueltas' ? 'bg-teal-50' :
                    a.stock_actual === 0 ? 'bg-rose-100' : 'bg-amber-50'
                  }`}>
                    {tab === 'resueltas'
                      ? <CheckCircle2 size={18} className="text-teal-600" />
                      : <AlertTriangle
                          size={18}
                          className={a.stock_actual === 0 ? 'text-rose-600' : 'text-amber-500'}
                        />
                    }
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-bold text-slate-900">{a.nombre}</p>
                      {tab === 'resueltas'
                        ? <Badge variant="success">Resuelto</Badge>
                        : a.stock_actual === 0 && <Badge variant="danger">Agotado</Badge>
                      }
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {a.sala ?? 'Sin sala asignada'}
                      {a.categoria ? ` · ${a.categoria}` : ''}
                    </p>
                  </div>
                </div>

                {tab === 'activas'
                  ? <Badge variant={gravedad(a)}>Déficit: {a.deficit}</Badge>
                  : <span className="text-xs text-teal-600 font-bold whitespace-nowrap">
                      Stock: {a.stock_actual} / mín {a.stock_minimo}
                    </span>
                }
              </div>

              {/* Barra de progreso */}
              <div className="mt-4">
                <div className="flex justify-between text-xs text-slate-500 mb-1.5">
                  <span>Stock actual: <span className="font-bold text-slate-700">{a.stock_actual}</span></span>
                  <span>Mínimo: <span className="font-bold">{a.stock_minimo}</span></span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      tab === 'resueltas' ? 'bg-teal-500' :
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
