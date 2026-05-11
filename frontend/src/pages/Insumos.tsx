import { useEffect, useState, useCallback } from 'react'
import { Search, Package, ChevronLeft, ChevronRight } from 'lucide-react'
import { api } from '../api/client'
import type { InsumoResponse, PaginatedResponse } from '../types/api'
import { Badge } from '../components/ui/Badge'
import { TableRowSkeleton } from '../components/ui/Skeleton'

const PAGE_SIZE = 15

export function Insumos() {
  const [insumos, setInsumos] = useState<InsumoResponse[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('') // valor comprometido al buscar
  const [loading, setLoading] = useState(true)

  const load = useCallback(async (skip: number, q: string) => {
    setLoading(true)
    try {
      const { data } = await api.get<PaginatedResponse<InsumoResponse>>('/insumos/', {
        params: { skip, limit: PAGE_SIZE },
      })
      // Filtrado local por nombre mientras el backend no tiene search.
      // Cuando el backend implemente ?nombre=, mover el filtro allá.
      const filtered = q
        ? data.data.filter((i) =>
            i.nombre.toLowerCase().includes(q.toLowerCase())
          )
        : data.data
      setInsumos(filtered)
      setTotal(q ? filtered.length : data.total)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load(page * PAGE_SIZE, query) }, [page, query, load])

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    setPage(0)
    setQuery(search)
  }

  function stockBadge(i: InsumoResponse) {
    if (i.stock_actual === 0) return <Badge variant="danger">Agotado</Badge>
    if (i.stock_actual <= i.stock_minimo) return <Badge variant="warning">Bajo stock</Badge>
    return <Badge variant="success">OK</Badge>
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-black text-slate-900">Insumos</h1>
          <p className="text-slate-500 text-sm mt-0.5">
            {total} insumos en inventario
          </p>
        </div>
      </div>

      {/* Barra de búsqueda persistente */}
      <form onSubmit={handleSearch} className="mb-6">
        <div className="relative">
          <Search
            size={16}
            className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400"
          />
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              if (e.target.value === '') { setQuery(''); setPage(0) }
            }}
            placeholder="Buscar insumo por nombre…"
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200
                       bg-white text-slate-900 text-sm shadow-sm
                       focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent
                       placeholder:text-slate-400 transition-all"
          />
          {search && (
            <button
              type="submit"
              className="absolute right-3 top-1/2 -translate-y-1/2
                         text-xs font-bold text-teal-600 hover:text-teal-800"
            >
              Buscar
            </button>
          )}
        </div>
      </form>

      {/* Tabla */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200 bg-slate-50">
              <th className="text-left px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Nombre</th>
              <th className="text-left px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Descripción</th>
              <th className="text-center px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Stock actual</th>
              <th className="text-center px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Stock mínimo</th>
              <th className="text-center px-4 py-3 text-xs font-bold text-slate-500 uppercase tracking-wide">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              Array.from({ length: PAGE_SIZE }).map((_, i) => (
                <TableRowSkeleton key={i} cols={5} />
              ))
            ) : insumos.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-center py-16 text-slate-400">
                  <Package size={32} className="mx-auto mb-2 opacity-30" />
                  <p className="font-semibold">Sin insumos que mostrar</p>
                  {query && (
                    <button
                      onClick={() => { setQuery(''); setSearch('') }}
                      className="text-teal-600 text-xs mt-1 font-bold"
                    >
                      Limpiar búsqueda
                    </button>
                  )}
                </td>
              </tr>
            ) : (
              insumos.map((i) => (
                <tr key={i.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3 font-semibold text-slate-900">{i.nombre}</td>
                  <td className="px-4 py-3 text-slate-500 max-w-xs truncate">
                    {i.descripcion ?? <span className="text-slate-300">Sin descripción</span>}
                  </td>
                  <td className="px-4 py-3 text-center font-bold text-slate-900">{i.stock_actual}</td>
                  <td className="px-4 py-3 text-center text-slate-500">{i.stock_minimo}</td>
                  <td className="px-4 py-3 text-center">{stockBadge(i)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Paginación */}
        {!loading && !query && totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200">
            <p className="text-xs text-slate-500">
              Página {page + 1} de {totalPages}
            </p>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="p-1.5 rounded-lg hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft size={16} className="text-slate-600" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="p-1.5 rounded-lg hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronRight size={16} className="text-slate-600" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
