# 🏙️ Hestia
**Sistema de gestión de insumos médicos — DuocUC**

Hestia es un sistema de stock diseñado para gestionar insumos e implementos 
en las instalaciones de salud de la Escuela de Salud de DuocUC.

---

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11 + FastAPI |
| Base de datos | PostgreSQL 16 |
| ORM | SQLAlchemy + Alembic |
| Autenticación | JWT + bcrypt |
| Contenedores | Docker + Docker Compose |

---

## Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (recomendado)
- Git

---

## 🚀 Inicio rápido con Docker (recomendado)

Esta es la forma estándar de correr el proyecto. No requiere instalar Python ni PostgreSQL manualmente.

### 1. Clonar el repositorio
```bash
git clone https://github.com/Hestia-Project-DuocUC/hestia.git
cd hestia
```

### 2. Crear el archivo de variables de entorno
```bash
cp backend/.env.example backend/.env
```
> ⚠️ Este paso es obligatorio. Sin el `.env`, el contenedor no puede conectarse a la base de datos.

El `.env` generado sirve directo para desarrollo local. No necesitas cambiar nada.

### 3. Levantar el proyecto
```bash
docker compose up --build
```

Esto automáticamente:
- Levanta PostgreSQL 16
- Instala las dependencias de Python
- Aplica las migraciones de base de datos
- Crea el usuario administrador inicial
- Levanta la API en `http://localhost:8000`

### 4. Credenciales del admin inicial

| Campo | Valor |
|---|---|
| Email | `gutierrezluis2203@hestia.cl` |
| Password | `admin123` |

### Comandos útiles

```bash
docker compose up          # levantar (sin reconstruir)
docker compose up --build  # reconstruir imagen y levantar
docker compose down        # apagar contenedores
docker compose down -v     # apagar Y borrar la base de datos
```

---

## Instalación manual (sin Docker)

Solo si necesitas correr el backend fuera de Docker.

### 1. Clonar y entrar al backend
```bash
git clone https://github.com/Hestia-Project-DuocUC/hestia.git
cd hestia/backend
```

### 2. Crear entorno virtual
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Crea `backend/.env` con:
```
DATABASE_URL=postgresql://postgres:TU_PASSWORD@localhost:5432/hestia_db
SECRET_KEY=genera_una_clave_con: python -c "import secrets; print(secrets.token_hex(32))"
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
```
> Nota: cambia el host de `db` a `localhost` si corres sin Docker.

### 5. Aplicar migraciones y crear admin
```bash
alembic upgrade head
python crear_admin.py
```

### 6. Arrancar el servidor
```bash
uvicorn app.main:app --reload
```

---

## Estructura del proyecto

```
hestia/
├── backend/
│   ├── app/
│   │   ├── models/       → Modelos SQLAlchemy
│   │   ├── schemas/      → Schemas Pydantic
│   │   ├── routes/       → Endpoints de la API
│   │   └── utils/        → Autenticación y dependencias
│   ├── alembic/          → Migraciones de base de datos
│   ├── crear_admin.py    → Script de creación de admin
│   ├── requirements.txt  → Dependencias Python
│   └── .env.example      → Plantilla de variables de entorno
└── frontend/             → (en desarrollo)
```

---

## Flujo de trabajo del equipo

- Nunca trabajar directamente en `main`
- Cada funcionalidad va en su propia rama: `feat/nombre`, `fix/nombre`, `chore/nombre`
- Abrir un Pull Request para mergear a `main`

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para más detalles.

---

## Valores del proyecto

**H**ospitalidad · **E**ficacia · **S**ervicio · **T**ransparencia · **I**nsumos · **A**postolado
