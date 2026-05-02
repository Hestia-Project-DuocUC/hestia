Hola mundo, esto es Hestia Project.

1. Instalar el software base

Python 3.11+
PostgreSQL 16
Git
VSCode

2. Clonar el repositorio

git clone https://github.com/TU_USUARIO/hestia.git
cd hestia/backend

3. Crear el entorno virtual e instalar dependencias

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

4. Crear la base de datos en su PostgreSQL local
Abren pgAdmin y crean una base de datos llamada hestia_db, igual que hiciste tú.

5. Crear su propio .env

Cada uno crea su .env con sus propias credenciales locales:

DATABASE_URL=postgresql://postgres:SU_PASSWORD@localhost:5432/hestia_db
SECRET_KEY=su_propia_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

-------------------------------------------------------------------------------------

6. Arrancar el servidor

uvicorn app.main:app --reload

SQLAlchemy creará todas las tablas automáticamente. Luego ejecutan crear_admin.py para tener un usuario con el que entrar.

7. Realizar la migración con Alembic
Con Alembic, simplemente ejecutan:

alembic upgrade head


ESTA ES DE PRUEBA