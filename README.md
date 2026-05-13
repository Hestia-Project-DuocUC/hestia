# Hestia

**Sistema de gestión de insumos médicos — Escuela de Salud DuocUC**

Hestia es una aplicación web para el control de stock de insumos e implementos en las salas clínicas de la Escuela de Salud de DuocUC, sede San Bernardo. Desarrollado por estudiantes de Informática Biomédica como proyecto de Ruta IE.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11 · FastAPI · SQLAlchemy · Pydantic v2 |
| Base de datos | PostgreSQL 16 |
| Frontend | React 19 · Vite · TypeScript · Tailwind CSS |
| Autenticación | JWT · bcrypt · TOTP 2FA (Google Authenticator) |
| Contenedores | Docker · Docker Compose |
| CI | GitHub Actions (flake8) |

---

## Funcionalidades

- **Inventario** — CRUD de insumos con filtros por nombre, sala, categoría y estado de stock
- **Movimientos** — registro de entradas y salidas con trazabilidad por usuario
- **Alertas de stock** — insumos bajo mínimo y alertas resueltas con rango configurable
- **Dashboard** — métricas en tiempo real, gráfico semanal de actividad y estado del inventario
- **Importación masiva** — carga de insumos desde CSV o XLSX con verificación TOTP
- **Exportación CSV** — descarga del inventario con los filtros activos
- **Gestión de usuarios** — CRUD desde la UI con roles admin / operador / visor
- **2FA** — setup wizard con códigos QR, códigos de recuperación y reset desde admin
- **Audit log** — historial de acciones con filtros por tipo y usuario
- **Seguridad** — rate limiting en login, security headers HTTP, BD no expuesta a la LAN

---

## Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Git

No se requiere instalar Python, Node.js ni PostgreSQL de forma manual.

---

## Inicio rápido

### 1. Clonar el repositorio

```bash
git clone https://github.com/Hestia-Project-DuocUC/hestia.git
cd hestia
```

### 2. Crear el archivo de variables de entorno

```bash
cp backend/.env.example backend/.env
```

El `.env` generado funciona directamente para desarrollo local. Sin este archivo el contenedor no puede conectarse a la base de datos.

### 3. Levantar el proyecto

```bash
docker compose up --build
```

Esto levanta los tres servicios en orden:

| Servicio | URL local |
|---|---|
| Frontend (React) | http://localhost:3000 |
| API (FastAPI) | http://localhost:8000 |
| Docs interactivos | http://localhost:8000/docs |

La base de datos se crea automáticamente al iniciar la API.

### 4. Cargar datos de demo (opcional)

Para una demo con 88 insumos médicos reales y ~560 movimientos distribuidos en 60 días:

```bash
docker compose exec api python seed_demo.py
```

El script pide confirmación antes de borrar datos existentes y muestra las credenciales generadas al finalizar.

**Credenciales de demo:**

| Email | Contraseña | Rol |
|---|---|---|
| `admin@hestia.duoc.cl` | `Admin2024!` | Administrador |
| `mgonzalez@hestia.duoc.cl` | `Oper2024!` | Operador |
| `cfuentes@hestia.duoc.cl` | `Oper2024!` | Operador |
| `amartinez@hestia.duoc.cl` | `Visor2024!` | Visor |
| `lperez@hestia.duoc.cl` | `Visor2024!` | Visor |

---

## Comandos útiles

```bash
# Ciclo de vida
docker compose up                  # levantar sin reconstruir
docker compose up --build          # reconstruir imágenes y levantar
docker compose down                # apagar (los datos persisten)
docker compose down -v             # apagar y borrar la base de datos

# Recargar un servicio tras cambios de configuración
docker compose restart api         # tras cambios en variables de entorno
docker compose restart frontend    # tras cambios en vite.config.ts

# Logs en tiempo real
docker compose logs -f api
docker compose logs -f frontend
```

---

## Despliegue en red LAN

Hestia está diseñado para correr en un servidor dentro de la red interna de DuocUC. Los clientes acceden únicamente desde su navegador; no instalan nada.

1. Ejecutar `docker compose up --build` en el servidor designado.
2. Verificar la IP del servidor en la red local (ej. `192.168.1.50`).
3. Los usuarios acceden desde `http://192.168.1.50:3000`.

Para que el frontend llame a la API correctamente desde otros equipos, crear `frontend/.env` con:

```
VITE_API_URL=http://192.168.1.50:8000
```

Y reconstruir el contenedor: `docker compose up --build frontend`.

---

## Estructura del proyecto

```
hestia/
├── backend/
│   ├── app/
│   │   ├── models/        → SQLAlchemy (usuario, insumo, sala, categoria, movimiento, audit_log)
│   │   ├── schemas/       → Pydantic v2
│   │   ├── routes/        → FastAPI routers
│   │   └── utils/         → security, deps (RBAC), rate_limit, auditoria
│   ├── seed_demo.py       → cargador de datos de demo
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/         → Dashboard, Insumos, Alertas, Movimientos, Usuarios, AuditLog …
│   │   ├── components/    → Layout, Sidebar, ui/ (Badge, Card, Modal, Skeleton, Logo)
│   │   ├── api/           → Axios client con interceptor JWT
│   │   ├── store/         → Zustand (auth)
│   │   └── types/         → interfaces TypeScript sincronizadas con el backend
│   └── public/
│       └── logo.png
├── docker-compose.yml
├── CLAUDE.md              → contexto técnico para asistentes IA
└── .github/
    ├── workflows/         → CI (validación flake8)
    ├── CONTRIBUTING.md
    └── PULL_REQUEST_TEMPLATE.md
```

---

## Flujo de trabajo del equipo

- No trabajar directamente en `main`
- Una rama por funcionalidad: `feat/nombre`, `fix/nombre`, `chore/nombre`
- Abrir Pull Request para mergear a `main`
- El CI valida automáticamente con flake8 en cada push

Ver [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md) para más detalles.

---

## Equipo

Desarrollado por estudiantes de Informática Biomédica — DuocUC San Bernardo  
Proyecto Ruta IE · Escuela de Salud · 2024–2025

---

**H**ospitalidad · **E**ficacia · **S**ervicio · **T**ransparencia · **I**nsumos · **A**postolado
