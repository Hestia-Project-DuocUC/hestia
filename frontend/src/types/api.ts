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
}

export interface Setup2FAResponse {
  qr_code: string
  secret: string
}

export interface ActivarResponse {
  mensaje: string
  recovery_codes: string[]   // 10 codigos — mostrar UNA sola vez
}

export interface ResumenResponse {
  total_insumos: number
  insumos_bajo_stock: number
  movimientos_hoy: number
  entradas_hoy: number
  salidas_hoy: number
  total_salas: number
  total_usuarios: number
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
}

export interface SalaResponse {
  id: number
  nombre: string
  tipo: string | null
  descripcion: string | null
}

export interface CategoriaResponse {
  id: number
  nombre: string
}

export interface PaginatedResponse<T> {
  total: number
  skip: number
  limit: number
  data: T[]
}
