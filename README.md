# Prueba de pull request
# 🏛️ Hestia
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

---

## Requisitos previos

- Python 3.11+
- PostgreSQL 16
- Git

---

## Instalación local

### 1. Clonar el repositorio
\```bash
git clone https://github.com/TU_USUARIO/hestia.git
cd hestia/backend
\```

### 2. Crear entorno virtual
\```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux
\```

### 3. Instalar dependencias
\```bash
pip install -r requirements.txt
\```

### 4. Configurar variables de entorno
Crea un archivo `.env` en `backend/` con este contenido:
\```
DATABASE_URL=postgresql://postgres:TU_PASSWORD@localhost:5432/hestia_db
SECRET_KEY=genera_una_clave_con: python -c "import secrets; print(secrets.token_hex(32))"
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
\```

### 5. Crear la base de datos
En pgAdmin, crea una base de datos llamada `hestia_db`.

### 6. Aplicar migraciones
\```bash
alembic upgrade head
\```

### 7. Crear usuario administrador
\```bash
python crear_admin.py
\```

### 8. Arrancar el servidor
\```bash
uvicorn app.main:app --reload
\```

La API estará disponible en `http://localhost:8000`  
Documentación interactiva en `http://localhost:8000/docs`

---

## Estructura del proyecto

\```
hestia/
├── backend/
│   ├── app/
│   │   ├── models/       → Modelos SQLAlchemy
│   │   ├── schemas/      → Schemas Pydantic
│   │   ├── routes/       → Endpoints de la API
│   │   └── utils/        → Autenticación y dependencias
│   ├── alembic/          → Migraciones de base de datos
│   ├── crear_admin.py    → Script de creación de admin
│   └── requirements.txt  → Dependencias Python
└── frontend/             → (en desarrollo)
\```

---

## Flujo de trabajo

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para las convenciones del equipo.

---

## Valores del proyecto

**H**ospitalidad · **E**ficacia · **S**ervicio · **T**ransparencia · **I**nsumos · **A**postolado