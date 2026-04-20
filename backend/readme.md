# Script para ingresar a las variables de entorno.
venv\Scripts\activate

# Script para levantar el localhost en Uvicorn.
uvicorn app.main:app --reload