import axios from 'axios'

// En desarrollo, Vite proxea las rutas al backend (ver vite.config.ts).
// En producción se usa VITE_API_URL del .env.
const BASE_URL = import.meta.env.VITE_API_URL ?? ''

export const api = axios.create({ baseURL: BASE_URL })

// Interceptor de request: inyecta el JWT en cada llamada automáticamente
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('hestia_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Interceptor de response: si la API devuelve 401 (token expirado/invalido)
// limpia la sesión y redirige al login.
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('hestia_token')
      localStorage.removeItem('hestia_user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
