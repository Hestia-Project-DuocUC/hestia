import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Package, AlertTriangle, ArrowUpCircle,
  ArrowDownCircle, DoorOpen, Users, ArrowRight,
  XCircle
} from 'lucide-react'
import { api } from '../api/client'
import type { ResumenResponse, InsumoAlerta, DiaMovimiento } from '../types/api'
import { MetricCard } from '../components/ui/Card'
import { MetricCardSkeleton, AlertaCardSkeleton } from '../components/ui/Skeleton'
import { Badge } from '../components/ui/Badge'

// ---------------------------------------------------------------------------
// Componente: grafico de barras agrupadas (entradas vs salidas)
// Construido con divs puros — sin dependencias externas.
// ---------------------------------------------------------------------------
function GraficoBarras({ datos }: { datos: DiaMovimiento[] }) {
  if (!datos.length) return null
  const max = Math.max(...datos.flatMap(d => [d.entradas, d.salidas]), 1)

  function labelDia(iso: string) {
    // iso es 'YYYY-MM-DD'; agregar T12:00:00 evita desfase de timezone
    return new Date(iso + 'T12:00:00')
      .toLocaleDateString('es-CL', { weekday: 'short' })
      .replace('.', '')
  }

  return (
    <div>
      <div className="flex items-end gap-1.5 h-28">
        {datos.map(d => (
          <div key={d.fecha} className="flex-1 flex flex-col items-center">
            <div className="flex items-end gap-0.5 h-24 w-full">
              <div
                title={`Entradas: ${d.entradas}`}
                className="flex-1 bg-teal-500 rounded-t-sm transition-all duration-500"
                style={{ height: `${(d.entradas / max) * 100}%`, minHeight: d.entradas ? 3 : 0 }}
              />
              <div
                title={`Salidas: ${d.salidas}`}
                className="flex-1 bg-amber-400 rounded-t-sm transition-all duration-500"
                style={{ height: `${(d.salidas / max) * 100}%`, minHeight: d.salidas ? 3 : 0 }}
              />
            </div>
            <span className="text-[10px] text-slate-400 mt-1 capitalize">{labelDia(d.fecha)}</span>
          </div>
        ))}
      </div>
      <div className="flex gap-4 mt-3">
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <div className="w-2.5 h-2.5 bg-teal-500 rounded-sm" /> Entradas
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <div className="w-2.5 h-2.5 bg-amber-400 rounded-sm" /> Salidas
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Componente: estado del inventario con barras horizontales proporcionales
// ---------------------------------------------------------------------------
function GraficoEstado({
  total, bajo, agotados,
}: {
  total: number, bajo: number, agotados: number
}) {
  const ok = total - bajo
  // 'bajo' del backend incluye agotados; separamos para el desglose visual
  const soloAlerta = bajo - agotados
  const base = Math.max(total, 1)

  const filas = [
    { label: 'Stock OK',      valor: ok,          pct: ok / base,          color: 'bg-teal-500',  texto: 'text-teal-700'  },
    { label: 'Bajo minimo',   valor: soloAlerta,   pct: soloAlerta / base,  color: 'bg-amber-400', texto: 'text-amber-700' },
    { label: 'Agotados',      valor: agotados,     pct: agotados / base,    color: 'bg-rose-500',  texto: 'text-rose-700'  },
  ]

  return (
    <div className="space-y-4">
      {filas.map(f => (
        <div key={f.label}>
          <div className="flex justify-between text-xs mb-1.5">
            <span className="text-slate-600 font-medium">{f.label}</span>
            <span className={`font-bold ${f.texto}`}>{f.valor}</span>
          </div>
          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full ${f.color} rounded-full transition-all duration-700`}
              style={{ width: `${f.pct * 100}%` }}
            />
          </div>
        </div>
      ))}
      <p className="text-xs text-slate-400 pt-1">{total} insumos en total</p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Pagina principal del Dashboard
// ---------------------------------------------------------------------------
export function Dashboard() {
  const [resumen, setResumen]     = useState<ResumenResponse | null>(null)
  const [alertas, setAlertas]     = useState<InsumoAlerta[]>([])
  const [semana, setSemana]       = useState<DiaMovimiento[]>([])
  const [loading, setLoading]     = useState(true)
  const [chartLoading, setChartLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [r, a] = await Promise.all([
          api.get<ResumenResponse>('/resumen/'),
          api.get<InsumoAlerta[]>('/insumos/alertas'),
        ])
        setResumen(r.data)
        setAlertas(a.data.slice(0, 5))
      } finally {
        setLoading(false)
      }
    }

    async function loadChart() {
      try {
        const { data } = await api.get<DiaMovimiento[]>('/resumen/grafico-semana')
        setSemana(data)
      } finally {
        setChartLoading(false)
      }
    }

    load()
    loadChart()
  }, [])

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-black text-slate-900">Dashboard</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          Vista general del inventario — {new Date().toLocaleDateString('es-CL', {
            weekday: 'long', day: 'numeric', month: 'long',
          })}
        </p>
      </div>

      {/* Metricas */}
      <section className="mb-8">
        <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">
          Inventario
        </h2>
        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {loading ? (
            Array.from({ length: 6 }).map((_, i) => <MetricCardSkeleton key={i} />)
          ) : resumen && (
            <>
              <MetricCard
                label="Total insumos"
                value={resumen.total_insumos}
                icon={<Package size={18} className="text-teal-600" />}
              />
              <MetricCard
                label="Bajo stock"
                value={resumen.insumos_bajo_stock}
                icon={<AlertTriangle size={18} className="text-amber-500" />}
                iconBg="bg-amber-50"
                accent={resumen.insumos_bajo_stock > 0}
              />
              <MetricCard
                label="Agotados"
                value={resumen.insumos_agotados}
                icon={<XCircle size={18} className="text-rose-500" />}
                iconBg="bg-rose-50"
                accent={resumen.insumos_agotados > 0}
              />
              <MetricCard
                label="Movimientos hoy"
                value={resumen.movimientos_hoy}
                icon={<Package size={18} className="text-slate-500" />}
                iconBg="bg-slate-100"
              />
              <MetricCard
                label="Entradas hoy"
                value={resumen.entradas_hoy}
                icon={<ArrowUpCircle size={18} className="text-teal-600" />}
              />
              <MetricCard
                label="Salidas hoy"
                value={resumen.salidas_hoy}
                icon={<ArrowDownCircle size={18} className="text-amber-500" />}
                iconBg="bg-amber-50"
              />
            </>
          )}
        </div>
      </section>

      {/* Graficos */}
      <section className="mb-8">
        <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">
          Analisis
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

          {/* Grafico de actividad semanal (ocupa 2/3) */}
          <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-bold text-slate-700">Actividad semanal</p>
              <div className="flex items-center gap-1">
                <ArrowUpCircle size={12} className="text-teal-500" />
                <ArrowDownCircle size={12} className="text-amber-400" />
                <span className="text-xs text-slate-400 ml-1">ultimos 7 dias</span>
              </div>
            </div>
            {chartLoading ? (
              <div className="h-28 flex items-end gap-1.5">
                {Array.from({ length: 7 }).map((_, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1">
                    <div
                      className="w-full bg-slate-100 rounded-t skeleton"
                      style={{ height: `${30 + Math.random() * 60}%` }}
                    />
                  </div>
                ))}
              </div>
            ) : (
              <GraficoBarras datos={semana} />
            )}
          </div>

          {/* Grafico estado del inventario (ocupa 1/3) */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-bold text-slate-700">Estado del inventario</p>
            </div>
            {loading || !resumen ? (
              <div className="space-y-4">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i}>
                    <div className="skeleton h-3 w-24 rounded mb-1.5" />
                    <div className="skeleton h-2 w-full rounded-full" />
                  </div>
                ))}
              </div>
            ) : (
              <GraficoEstado
                total={resumen.total_insumos}
                bajo={resumen.insumos_bajo_stock}
                agotados={resumen.insumos_agotados}
              />
            )}

            {/* Acceso rapido a alertas */}
            {!loading && resumen && resumen.insumos_bajo_stock > 0 && (
              <Link
                to="/alertas"
                className="mt-5 flex items-center justify-between p-3 rounded-xl
                           bg-rose-50 border border-rose-200 hover:bg-rose-100
                           transition-colors"
              >
                <div className="flex items-center gap-2">
                  <AlertTriangle size={14} className="text-rose-600" />
                  <span className="text-xs font-bold text-rose-700">
                    {resumen.insumos_bajo_stock} alertas activas
                  </span>
                </div>
                <ArrowRight size={13} className="text-rose-500" />
              </Link>
            )}
          </div>
        </div>
      </section>

      {/* Alertas recientes */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
            Alertas de stock
          </h2>
          <Link
            to="/alertas"
            className="text-xs font-bold text-teal-600 hover:text-teal-700 flex items-center gap-1"
          >
            Ver todas <ArrowRight size={13} />
          </Link>
        </div>

        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => <AlertaCardSkeleton key={i} />)}
          </div>
        ) : alertas.length === 0 ? (
          <div className="bg-teal-50 border border-teal-200 rounded-xl p-6 text-center">
            <p className="text-teal-700 font-semibold text-sm">Sin alertas activas</p>
            <p className="text-teal-600 text-xs mt-1">Todos los insumos estan sobre el minimo.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {alertas.map(a => (
              <div
                key={a.id}
                className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm
                           flex items-start justify-between gap-3"
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 w-8 h-8 rounded-lg bg-rose-50 flex items-center
                                  justify-center flex-shrink-0">
                    <AlertTriangle size={15} className="text-rose-500" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-slate-900">{a.nombre}</p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {a.sala ?? 'Sin sala'} · {a.categoria ?? 'Sin categoria'}
                    </p>
                    <div className="flex items-center gap-3 mt-2">
                      <span className="text-xs text-slate-500">
                        Stock: <span className="font-bold text-rose-600">{a.stock_actual}</span>
                        <span className="text-slate-400"> / min. {a.stock_minimo}</span>
                      </span>
                    </div>
                  </div>
                </div>
                <Badge variant={a.stock_actual === 0 ? 'danger' : 'warning'}>
                  {a.stock_actual === 0 ? 'Agotado' : `Deficit ${a.deficit}`}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Pie de pagina con acceso rapido */}
      {!loading && resumen && (
        <div className="mt-6 pt-6 border-t border-slate-200 flex items-center
                        gap-2 text-xs text-slate-400">
          <DoorOpen size={13} />
          <span>{resumen.total_salas} salas</span>
          <span className="mx-1">·</span>
          <Users size={13} />
          <span>{resumen.total_usuarios} usuarios activos</span>
        </div>
      )}
    </div>
  )
}
