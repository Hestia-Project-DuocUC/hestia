// ---------------------------------------------------------------------------
// Tipos TypeScript sincronizados con los schemas Pydantic del backend.
// ---------------------------------------------------------------------------

export interface LoginResponse {
  requires_2fa: boolean
  access_token: string | null
  token_type: string
  usuario: string | null
  rol: string | null
  pre_token: string | null
}

export interface UsuarioMe {
  id: number
  nombre: string
  email: string
  rol: string
  totp_habilitado: boolean
  activo: boolean
  avatar_b64: string | null
}

export interface Setup2FAResponse {
  qr_code: string
  secret: string
}

export interface ActivarResponse {
  mensaje: string
  recovery_codes: string[]
}

export interface ResumenResponse {
  total_insumos: number
  insumos_bajo_stock: number
  insumos_agotados: number
  movimientos_hoy: number
  entradas_hoy: number
  salidas_hoy: number
  total_salas: number
  total_usuarios: number
}

export interface DiaMovimiento {
  fecha: string
  entradas: number
  salidas: number
}

export interface ActividadReciente {
  id: number
  tipo: 'entrada' | 'salida'
  insumo: string
  sala: string | null
  cantidad: number
  usuario: string
  fecha: string
}

export interface TopInsumo {
  nombre: string
  total_salidas: number
  sala: string | null
}

export interface InsumoAlerta {
  id: number
  nombre: string
  stock_actual: number
  stock_minimo: number
  deficit: number
  sala: string | null
  categoria: string | null
}

export interface InsumoResponse {
  id: number
  nombre: string
  descripcion: string | null
  stock_actual: number
  stock_minimo: number
  sala_id: number | null
  categoria_id: number | null
  activo: boolean
}

export interface SalaResponse {
  id: number
  nombre: string
  tipo: string | null
  descripcion: string | null
}

export interface SalaCreate {
  nombre: string
  tipo?: string | null
  descripcion?: string | null
}

export interface CategoriaResponse {
  id: number
  nombre: string
}

export interface CategoriaCreate {
  nombre: string
}

export type TipoMovimiento = 'entrada' | 'salida'

export interface MovimientoCreate {
  tipo: TipoMovimiento
  cantidad: number
  insumo_id: number
  motivo?: string | null
}

export interface MovimientoEnriquecido {
  id: number
  tipo: TipoMovimiento
  cantidad: number
  motivo: string | null
  fecha: string
  insumo: string
  sala: string | null
  usuario: string
}

export interface AuditLogEntry {
  id: number
  fecha: string
  accion: string
  entidad: string | null
  entidad_id: number | null
  detalle: string | null
  ip: string | null
  usuario_id: number | null
  usuario_nombre: string
}

export interface PaginatedResponse<T> {
  total: number
  skip: number
  limit: number
  data: T[]
}
