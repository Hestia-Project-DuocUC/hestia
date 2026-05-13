import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// En desarrollo local el proxy apunta a localhost:8000.
// Dentro de Docker Compose, la variable API_URL se inyecta como http://api:8000
// (nombre del servicio en el compose) para que el contenedor frontend
// pueda alcanzar el contenedor backend por la red interna de Docker.
const API = process.env.API_URL ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,   // escucha en 0.0.0.0 — necesario para Docker
    proxy: {
      '/auth':        API,
      '/insumos':     API,
      '/importar':    API,
      '/resumen':     API,
      '/salas':       API,
      '/categorias':  API,
      '/usuarios':    API,
      '/movimientos': API,
      '/audit-log':   API,
    },
  },
})
