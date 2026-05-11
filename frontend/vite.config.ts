import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/auth':      'http://localhost:8000',
      '/insumos':   'http://localhost:8000',
      '/importar':  'http://localhost:8000',
      '/resumen':   'http://localhost:8000',
      '/salas':     'http://localhost:8000',
      '/categorias':'http://localhost:8000',
      '/usuarios':  'http://localhost:8000',
      '/movimientos':'http://localhost:8000',
    },
  },
})
