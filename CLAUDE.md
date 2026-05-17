# CLAUDE.md — Contexto técnico de Hestia

Este archivo es el punto de entrada para cualquier asistente de IA que trabaje en este repositorio. Contiene el estado real del proyecto, las convenciones establecidas y las reglas que hay que respetar.

---

## 1. Qué es Hestia

Sistema web de gestión de stock de insumos médicos para la Escuela de Salud de DuocUC, sede San Bernardo. Desarrollado por estudiantes de Informática Biomédica como proyecto de Ruta IE (innovación y emprendimiento). El sistema corre en red LAN interna; no tiene IP pública ni dominio.

**Stack completo:**
- Backend: Python 3.11 · FastAPI · PostgreSQL 16 · SQLAlchemy 2.0 · Alembic · Pydantic v2
- Frontend: React 19 · Vite · TypeScript · Tailwind CSS · Zustand · Axios · lucide-react ^0.396
- Infra: Docker Compose (3 servicios: `db`, `api`, `frontend`)
- Auth: JWT (python-jose) · bcrypt · TOTP 2FA (pyotp + QR)
- CI: GitHub Actions con flake8 en push/PR a `main` y `develop`

---

## 2. Arquitectura Docker

```
[Navegador] → :3000 (frontend/Vite) → proxy → :8000 (api/FastAPI) → db:5432 (PostgreSQL)
```

**Servicios en `docker-compose.yml`:**

| Servicio | Imagen | Puerto expuesto | Volumen |
|---|---|---|---|
| `db` | postgres:16 | ninguno (solo red interna) | `postgres_data` (named) |
| `api` | Dockerfile propio | 8000 | `./backend:/app` (bind mount dev) |
| `frontend` | Dockerfile propio | 3000 | `./frontend:/app` + `/app/node_modules` |

**Regla crítica:** el puerto 5432 de la BD NO está expuesto al host ni a la LAN. La BD solo es accesible desde el contenedor `api` por nombre de servicio (`db:5432`).

**Comandos de ciclo de vida:**
```bash
docker compose up --build     # primera vez o tras cambios en Dockerfile
docker compose up             # levantar sin reconstruir
docker compose restart api    # recargar backend (ej: cambios en config)
docker compose restart frontend  # recargar Vite (ej: cambios en vite.config.ts)
docker compose down           # apagar (datos persisten en named volume)
docker compose down -v        # apagar Y borrar la BD (irreversible)
```

**Datos de demo:**
```bash
docker compose exec api python seed_demo.py
```
Genera 8 salas, 10 categorías, 5 usuarios, 88 insumos y ~560 movimientos distribuidos en 60 días. Requiere confirmación interactiva.

---

## 3. Backend

### 3.1 Estructura

```
backend/
├── app/
│   ├── main.py            # FastAPI app, middleware, registro de routers
│   ├── database.py        # Engine, SessionLocal, Base, get_db()
│   ├── models/            # SQLAlchemy ORM
│   │   ├── usuario.py
│   │   ├── sala.py
│   │   ├── categoria.py
│   │   ├── insumo.py
│   │   ├── movimiento.py
│   │   ├── solicitud.py   # SolicitudRetiro + SolicitudItem
│   │   └── audit_log.py
│   ├── schemas/           # Pydantic v2
│   │   ├── comun.py       # PaginatedResponse[T]
│   │   ├── usuario.py
│   │   ├── insumo.py
│   │   ├── movimiento.py
│   │   ├── solicitud.py   # SolicitudCreate, SolicitudResponse, etc.
│   │   ├── sala.py
│   │   ├── categoria.py
│   │   └── audit_log.py
│   ├── routes/            # FastAPI routers (1 archivo = 1 prefix)
│   │   ├── auth.py        # /auth
│   │   ├── usuarios.py    # /usuarios
│   │   ├── insumos.py     # /insumos
│   │   ├── movimientos.py # /movimientos
│   │   ├── solicitudes.py # /solicitudes
│   │   ├── salas.py       # /salas
│   │   ├── categorias.py  # /categorias
│   │   ├── resumen.py     # /resumen
│   │   ├── importar.py    # /importar
│   │   └── audit_log.py   # /audit-log
│   └── utils/
│       ├── security.py    # hashing, JWT
│       ├── deps.py        # FastAPI dependencies (RBAC)
│       ├── rate_limit.py  # rate limiter en memoria
│       └── auditoria.py   # helper registrar() y get_ip()
├── seed_demo.py           # script de carga de datos de demo
├── crear_admin.py         # crea usuario admin inicial (entrypoint Docker)
├── .env                   # variables de entorno (NO en git)
├── .flake8                # config linter
└── requirements.txt
```

### 3.2 Modelos SQLAlchemy

**`Usuario`** (`usuarios`)
```
id · nombre · email (unique) · password_hash · rol (Enum: admin|operador|visor|docente)
totp_secret · totp_habilitado · totp_recovery_codes (JSON Text)
foto_perfil (Text, base64 PNG 256×256, nullable)
activo (Boolean, default True — soft-delete)
Relaciones: movimientos → · solicitudes →
```

**`Sala`** (`salas`)
```
id · nombre · tipo · descripcion
Relaciones: insumos →
```

**`Categoria`** (`categorias`)
```
id · nombre
Relaciones: insumos →
```

**`Insumo`** (`insumos`)
```
id · nombre · descripcion · stock_actual · stock_minimo
sala_id (FK nullable) · categoria_id (FK nullable)
Relaciones: sala ← · categoria ← · movimientos →
```

**`Movimiento`** (`movimientos`)
```
id · tipo (Enum: entrada|salida) · cantidad · motivo
fecha (DateTime timezone=True, server_default=now())
insumo_id (FK) · usuario_id (FK)
Relaciones: insumo ← · usuario ←
```

**`SolicitudRetiro`** (`solicitudes_retiro`)
```
id · docente_id (FK usuarios) · sala_id (FK salas)
fecha_clase (DateTime timezone=True) · estado (Enum: pendiente|en_preparacion|completada)
notas (Text nullable) · notas_operador (Text nullable)
fecha_creacion (DateTime timezone=True, server_default=now())
fecha_completada (DateTime timezone=True, nullable)
Relaciones: docente ← · sala ← · items →
```

**`SolicitudItem`** (`solicitud_items`)
```
id · solicitud_id (FK solicitudes_retiro, cascade delete) · insumo_id (FK insumos)
cantidad_solicitada (Integer)
Relaciones: solicitud ← · insumo ←
```
El stock se descuenta al completar la solicitud (no al crearla). Los items son inmutables tras la creación.

**`AuditLog`** (`audit_log`)
```
id · fecha (DateTime timezone=True, server_default=now())
accion (String 64, indexed) · entidad (String 64) · entidad_id
detalle (Text) · ip (String 64)
usuario_id (FK nullable, ondelete=SET NULL) · usuario_nombre (String 256, denormalizado)
```
`usuario_nombre` se almacena al momento de la acción para preservar el historial incluso si el usuario es eliminado después.

### 3.3 Registro de modelos

En `main.py`, todos los modelos se importan explícitamente antes de `Base.metadata.create_all()`:
```python
from app.models import sala, categoria, usuario, movimiento, insumo  # noqa
from app.models import audit_log  # noqa
from app.models import solicitud  # noqa
```
**Regla:** al agregar un modelo nuevo, importarlo en `main.py` antes de `create_all()`.

### 3.4 Endpoints

**`/auth`**
```
POST /auth/login                   → LoginResponse (JWT o pre_token si tiene 2FA)
POST /auth/2fa/completar-login     → JWT completo tras validar TOTP
POST /auth/2fa/recuperar-acceso    → JWT usando recovery code (desactiva 2FA)
POST /auth/2fa/setup               → QR base64 + secret (requiere JWT)
POST /auth/2fa/activar             → activa 2FA, devuelve 10 recovery codes
POST /auth/2fa/desactivar          → desactiva 2FA (requiere TOTP válido)
```

**`/usuarios`** (RBAC: admin para escritura, cualquier rol para /me)
```
GET  /usuarios/                    → PaginatedResponse[UsuarioResponse] (admin)
GET  /usuarios/me                  → UsuarioResponse (cualquier rol)
POST /usuarios/me/cambiar-password → 200 (cualquier rol)
POST /usuarios/                    → UsuarioResponse (admin)
GET  /usuarios/{id}                → UsuarioResponse (admin)
PUT  /usuarios/{id}                → UsuarioResponse; password opcional (admin)
DELETE /usuarios/{id}             → 200 (admin; no puede auto-eliminarse)
POST /usuarios/{id}/reset-2fa     → 200 (admin)
```

**`/insumos`** — rutas estáticas ANTES de `/{insumo_id}`
```
GET  /insumos/alertas              → list[InsumoAlerta] (stock <= minimo)
GET  /insumos/alertas-resueltas   → list[InsumoAlerta] ?dias=30 (subquery DISTINCT)
GET  /insumos/exportar            → StreamingResponse CSV (BOM UTF-8)
GET  /insumos/                    → PaginatedResponse[InsumoResponse] (filtros: nombre, sala_id, categoria_id, bajo_stock)
GET  /insumos/{id}                → InsumoResponse
POST /insumos/                    → InsumoResponse (operador+)
PUT  /insumos/{id}                → InsumoResponse (operador+)
DELETE /insumos/{id}             → 200 (admin + TOTP requerido)
```

**`/movimientos`**
```
GET  /movimientos/exportar         → StreamingResponse CSV o XLSX (filtros: insumo, tipo, fecha_desde, fecha_hasta)
GET  /movimientos/                 → PaginatedResponse[MovimientoEnriquecido] (mismos filtros)
POST /movimientos/                 → MovimientoResponse (operador+; actualiza stock_actual con SELECT FOR UPDATE)
GET  /movimientos/insumo/{id}      → PaginatedResponse[MovimientoEnriquecido]
GET  /movimientos/sala/{id}        → PaginatedResponse[MovimientoEnriquecido]
```

**`/solicitudes`** — flujo docente → operador
```
GET  /solicitudes/resumen-recientes → {total, pendientes} (operador+; para pop-up de bienvenida)
GET  /solicitudes/mis-solicitudes   → list[SolicitudResponse] (solo docente)
GET  /solicitudes/                  → list[SolicitudResponse] (operador+; filtro opcional ?estado=)
POST /solicitudes/                  → SolicitudResponse 201 (solo docente; valida stock pero NO descuenta)
PUT  /solicitudes/{id}/en-preparacion → SolicitudResponse (operador+)
POST /solicitudes/{id}/completar    → SolicitudResponse (operador+; descuenta stock con SELECT FOR UPDATE)
```

**`/salas`** · **`/categorias`**: CRUD estándar.

**`/resumen`**
```
GET  /resumen/                   → ResumenResponse (total_insumos, insumos_bajo_stock, insumos_agotados,
                                   movimientos_hoy, entradas_hoy, salidas_hoy, total_salas, total_usuarios)
GET  /resumen/grafico-semana     → list[DiaMovimiento] — 7 elementos con fecha/entradas/salidas
GET  /resumen/actividad-reciente → list[ActividadReciente] — últimos movimientos para feed del dashboard
GET  /resumen/top-insumos-retirados → list[TopInsumo] — insumos más retirados (últimos 30 días)
```

**`/importar`**
```
POST /importar/csv-xlsx            → resultado bulk (requiere TOTP del usuario admin)
```

**`/audit-log`** (solo admin)
```
GET  /audit-log/                   → PaginatedResponse[AuditLogResponse] ?accion=&usuario_id=
```

### 3.5 RBAC y dependencias

```python
get_usuario_actual  # cualquier JWT válido (rechaza pre_tokens de 2FA)
require_docente     # solo docente
require_operador    # admin u operador
require_admin       # solo admin
```

### 3.6 Seguridad

**Hashing de contraseñas:** SHA-256 prehash → bcrypt. Nunca usar `bcrypt.hashpw` directamente; siempre usar `hashear_password()` y `verificar_password()` de `app/utils/security.py`.

**JWT:** access token (expiración en .env) y pre_token (5 min, campo `tipo=pre_auth`). Los endpoints protegidos rechazan pre_tokens explícitamente.

**Rate limiting:** en memoria, por email (no por IP — en Docker todas las peticiones llegan desde la IP del contenedor frontend). 5 intentos en 5 min → bloqueo 15 min. Thread-safe con `threading.Lock`. Si se migra a múltiples workers, reemplazar por Redis.

**Security headers:** middleware en `main.py` que agrega `X-Content-Type-Options`, `X-Frame-Options: DENY`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy` en todas las respuestas.

**Audit log:** `registrar()` hace commit propio e inmediato para que el log persista incluso cuando la operación principal lanza `HTTPException`. Integrado en: `auth/login` (EXITOSO/FALLIDO), CRUD de usuarios, reset-2FA.

### 3.7 Convenciones flake8

Configuración en `backend/.flake8`: `max-line-length=100`. Ignorados: E302, W292, W503, E402, F401.
El CI corre `flake8 app/` en push a `main` y `develop`. **Errores que causaron fallos previos y hay que evitar:**
- E241: múltiples espacios después de `:` (no alinear valores en dicts con espacios)
- E221: múltiples espacios antes de `=` (no alinear asignaciones con espacios)

---

## 4. Frontend

### 4.1 Estructura

```
frontend/src/
├── App.tsx                # BrowserRouter + Routes (todas las rutas)
├── main.tsx
├── api/
│   └── client.ts          # Axios instance; interceptor JWT; redirect 401 → /login
├── store/
│   └── auth.ts            # Zustand: token, user (nombre+rol), login(), logout()
├── types/
│   └── api.ts             # Interfaces TS sincronizadas con schemas Pydantic
├── pages/                 # 1 archivo = 1 ruta
│   ├── Login.tsx
│   ├── Dashboard.tsx         # métricas + gráfico semanal + feed actividad + top insumos
│   ├── Alertas.tsx           # tabs Activas/Resueltas + selector 7/14/30 días
│   ├── Insumos.tsx           # tabla filtrable + CRUD + exportar CSV + autocompletado
│   ├── Movimientos.tsx       # tabla paginada + filtros + exportar CSV/XLSX
│   ├── SolicitudDocente.tsx  # carrito de retiro + historial (solo docente)
│   ├── SolicitudOperador.tsx # gestión de solicitudes pendientes (operador+)
│   ├── Salas.tsx
│   ├── Categorias.tsx
│   ├── Configuracion2FA.tsx  # setup QR, activar, desactivar, recovery codes
│   ├── ImportarInsumos.tsx   # upload CSV/XLSX con TOTP
│   ├── Perfil.tsx            # info usuario + foto de perfil + cambiar contraseña
│   ├── Usuarios.tsx          # CRUD usuarios + reset 2FA (solo admin)
│   └── AuditLog.tsx          # tabla paginada + filtro por acción (solo admin)
└── components/
    ├── layout/
    │   ├── Layout.tsx     # outlet + guard JWT + aviso 2FA
    │   └── Sidebar.tsx    # nav por rol + footer perfil/seguridad/logout
    └── ui/
        ├── Badge.tsx           # variants: default|warning|danger|success|info
        ├── Card.tsx            # MetricCard
        ├── Logo.tsx            # prop light=true para fondos oscuros (sidebar)
        ├── Modal.tsx           # size: sm|md|lg
        ├── SearchSuggestions.tsx  # dropdown de autocompletado (Insumos, Movimientos)
        └── Skeleton.tsx        # Skeleton, MetricCardSkeleton, TableRowSkeleton, AlertaCardSkeleton
```

### 4.2 Rutas

```tsx
/login             → <Login />                (pública)
/                  → redirect /dashboard      (protegida por Layout)
/dashboard         → <Dashboard />
/alertas           → <Alertas />
/insumos           → <Insumos />
/movimientos       → <Movimientos />
/solicitudes       → <SolicitudDocente />     (visible solo docente en sidebar)
/solicitudes/admin → <SolicitudOperador />    (visible solo operador+admin en sidebar)
/salas             → <Salas />
/categorias        → <Categorias />
/seguridad         → <Configuracion2FA />
/importar          → <ImportarInsumos />      (visible solo admin en sidebar)
/perfil            → <Perfil />
/usuarios          → <Usuarios />             (visible solo admin en sidebar)
/audit-log         → <AuditLog />             (visible solo admin en sidebar)
```

### 4.3 Proxy de Vite — regla crítica

Todo prefijo de ruta backend debe estar listado en `frontend/vite.config.ts`:
```typescript
proxy: {
  '/auth':        API,
  '/insumos':     API,
  '/importar':    API,
  '/resumen':     API,
  '/salas':       API,
  '/categorias':  API,
  '/usuarios':    API,
  '/movimientos': API,
  '/solicitudes': API,
  '/audit-log':   API,
}
```
**Regla:** al agregar un nuevo router en FastAPI, agregar su prefix aquí o el frontend devolverá HTML en lugar de JSON, causando página en blanco.

Tras editar `vite.config.ts`: `docker compose restart frontend`.

### 4.4 Patrones de componente

Todos los componentes de página siguen el mismo patrón:
```typescript
// 1. Estado con useState
// 2. load() con useCallback
// 3. useEffect con dependencias explícitas
// 4. try/catch/finally en TODOS los fetches (evitar página en blanco por Promise rejection)
// 5. Estado de loading → skeleton, luego datos
// 6. Toast para feedback de acciones (aparece 3 segundos)
// 7. Modal para crear/editar/eliminar
```

Las interfaces TypeScript en `src/types/api.ts` deben mantenerse sincronizadas con los schemas Pydantic. Cuando se modifique un response schema en el backend, actualizar el tipo correspondiente en `api.ts`.

### 4.5 Store de autenticación

Zustand persiste `token` y `user: {nombre, email, rol}` en localStorage bajo las claves `hestia_token` y `hestia_user`. El interceptor de Axios inyecta el JWT automáticamente. Si el backend devuelve 401, el interceptor limpia el storage y redirige a `/login`.

---

## 5. Flujo de autenticación

```
POST /auth/login
  ├─ Sin 2FA: → access_token (JWT completo) → guardar en store
  └─ Con 2FA: → pre_token (5 min, tipo=pre_auth)
                   ↓
             POST /auth/2fa/completar-login
                   ↓
             access_token → guardar en store
```

Los pre_tokens son rechazados por todos los endpoints protegidos (`get_usuario_actual` verifica `payload.tipo != 'pre_auth'`).

**Recovery codes:** 10 códigos en formato `XXXXXXXX-XXXXXXXX`, mostrados UNA sola vez al activar 2FA. Almacenados como JSON con SHA-256 hashes. Un código usado se marca `"usado": true`. Al usar un recovery code exitosamente, el 2FA se desactiva para que el usuario lo reconfigure.

---

## 6. Variables de entorno

`backend/.env` (no en git):
```
DATABASE_URL=postgresql://postgres:hestia_pass@db:5432/hestia_db
SECRET_KEY=<clave secreta JWT>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

`frontend/.env` (solo necesario en producción/despliegue externo):
```
VITE_API_URL=http://<IP_SERVIDOR>:8000
```
En desarrollo, el proxy de Vite maneja el enrutamiento; `VITE_API_URL` queda vacío.

---

## 7. CI/CD

Archivo: `.github/workflows/validacion.yml`
- Trigger: push y PR a `main` o `develop`
- Pasos: checkout → Python 3.11 → pip install (requirements.txt + flake8) → `flake8 app/ --max-line-length=100`
- El `requirements.txt` raíz es el mismo que `backend/requirements.txt` (o un symlink/copia)

No hay CI para el frontend (TypeScript, ESLint o build check). El build de Vite falla silenciosamente en PR si hay errores de tipos.

---

## 8. Funcionalidades implementadas

| Área | Funcionalidad | Estado |
|---|---|---|
| Inventario | CRUD insumos con filtros server-side | ✅ |
| Inventario | Alertas stock mínimo (activas + resueltas) | ✅ |
| Inventario | Exportación CSV con filtros | ✅ |
| Inventario | Importación masiva CSV/XLSX con TOTP | ✅ |
| Inventario | Autocompletado en búsqueda de insumos | ✅ |
| Movimientos | Registro entrada/salida + listado paginado + filtros | ✅ |
| Movimientos | Exportación CSV/XLSX con filtros | ✅ |
| Solicitudes | Flujo docente → operador (carrito + historial + gestión) | ✅ |
| Solicitudes | Descuento de stock con bloqueo pesimista (SELECT FOR UPDATE) | ✅ |
| Auth | Login + JWT + TOTP 2FA + recovery codes | ✅ |
| Auth | Rate limiting (5 intentos, 15 min bloqueo) | ✅ |
| Auth | Security headers HTTP | ✅ |
| Usuarios | RBAC admin/operador/visor/docente | ✅ |
| Usuarios | CRUD desde UI (solo admin) | ✅ |
| Usuarios | Perfil + foto de perfil + cambiar contraseña | ✅ |
| Usuarios | Reset 2FA desde admin | ✅ |
| Dashboard | Métricas + gráfico semanal + feed actividad + top insumos | ✅ |
| Audit log | Registro de acciones (login, CRUD usuarios) | ✅ parcial |
| Salas | CRUD | ✅ |
| Categorías | CRUD | ✅ |

### Pendiente / ideas para versiones futuras

| Funcionalidad | Dependencias | Complejidad |
|---|---|---|
| Audit log en insumos y movimientos | — | Baja |
| Predicción de desabastecimiento | Datos históricos suficientes | Media |
| Clasificación ABC de inventario | — | Media |
| Campo `fecha_vencimiento` en insumos | Migración Alembic + refactor UI | Alta |
| Reportes PDF para directivos | weasyprint o similar | Media |
| Gestión de lotes | Modelo Lote + refactor movimientos | Muy alta |

---

## 9. Reglas para trabajar en este repositorio

1. **Leer el código real antes de escribir.** Usar MCP de GitHub para ver los archivos actuales. Nunca asumir la estructura basándose en conversaciones anteriores.

2. **Flake8 primero.** Todo código Python debe pasar `flake8 app/ --max-line-length=100`. No usar espacios de alineación visual en dicts ni en asignaciones.

3. **Proxy de Vite.** Al agregar un router en FastAPI, agregar su prefix en `vite.config.ts`. Olvidarlo causa página en blanco.

4. **Importar modelos en `main.py`.** Al crear un modelo SQLAlchemy nuevo, importar su módulo en `main.py` antes de `create_all()`.

5. **Rutas estáticas antes que dinámicas.** En `insumos.py`, `/alertas` y `/exportar` van ANTES de `/{insumo_id}` para que FastAPI no interprete la cadena como entero.

6. **Try/catch en fetches del frontend.** Siempre incluir `catch` (no solo `finally`) en funciones `load()` asíncronas para evitar páginas en blanco por Promise rejection no manejada.

7. **Sincronizar tipos.** Al modificar un schema Pydantic en el backend, actualizar la interfaz correspondiente en `frontend/src/types/api.ts`.

8. **No exponer el puerto 5432.** El servicio `db` en `docker-compose.yml` no tiene `ports:`. No agregar esa sección en producción.

9. **Usar `hashear_password()` de `security.py`.** Nunca llamar directamente a `bcrypt.hashpw()` — el sistema usa prehash SHA-256 antes de bcrypt.

10. **`registrar()` tiene commit propio.** Llamar a `registrar()` después del commit de la operación principal, no antes. Para errores (LOGIN_FALLIDO), llamar antes del `raise HTTPException`.
