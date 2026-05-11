import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Package, AlertTriangle, ArrowUpCircle,
  ArrowDownCircle, DoorOpen, Users, ArrowRight
} from 'lucide-react'
import { api } from '../api/client'
import type { ResumenResponse, InsumoAlerta } from '../types/api'
import { MetricCard } from '../components/ui/Card'
import { MetricCardSkeleton, AlertaCardSkeleton } from '../components/ui/Skeleton'
import { Badge } from '../components/ui/Badge'

export function Dashboard() {
  const [resumen, setResumen] = useState<ResumenResponse | null>(null)
  const [alertas, setAlertas] = useState<InsumoAlerta[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [r, a] = await Promise.all([
          api.get<ResumenResponse>('/resumen/'),
          api.get<InsumoAlerta[]>('/insumos/alertas'),
        ])
        setResumen(r.data)
        setAlertas(a.data.slice(0, 5)) // top 5 más críticos
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-black text-slate-900">Dashboard</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          Vista general del inventario — {new Date().toLocaleDateString('es-CL', {
            weekday: 'long', day: 'numeric', month: 'long'
          })}
        </p>
      </div>

      {/* Métricas */}
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
                icon={<AlertTriangle size={18} className="text-rose-500" />}
                iconBg="bg-rose-50"
                accent={resumen.insumos_bajo_stock > 0}
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
              <MetricCard
                label="Salas"
                value={resumen.total_salas}
                subtitle={`${resumen.total_usuarios} usuarios`}
                icon={<DoorOpen size={18} className="text-blue-500" />}
                iconBg="bg-blue-50"
              />
            </>
          )}
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
            <p className="text-teal-600 text-xs mt-1">Todos los insumos están sobre el mínimo.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {alertas.map((a) => (
              <div
                key={a.id}
                className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm
                           flex items-start justify-between gap-3"
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 w-8 h-8 rounded-lg bg-rose-50 flex items-center justify-center flex-shrink-0">
                    <AlertTriangle size={15} className="text-rose-500" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-slate-900">{a.nombre}</p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {a.sala ?? 'Sin sala'} · {a.categoria ?? 'Sin categoría'}
                    </p>
                    <div className="flex items-center gap-3 mt-2">
                      <span className="text-xs text-slate-500">
                        Stock: <span className="font-bold text-rose-600">{a.stock_actual}</span>
                        <span className="text-slate-400"> / mín. {a.stock_minimo}</span>
                      </span>
                    </div>
                  </div>
                </div>
                <Badge variant="danger">Déficit {a.deficit}</Badge>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
