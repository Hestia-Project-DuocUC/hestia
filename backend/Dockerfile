# Imagen base oficial de Python 3.11 (versión ligera)
FROM python:3.11-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos primero solo el requirements para aprovechar la caché de Docker.
# Si no cambia requirements.txt, Docker no reinstala las librerías en cada build.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ahora sí copiamos el resto del código
COPY . .

# Dar permisos de ejecución al script de arranque
RUN chmod +x start.sh

# Puerto que expone la API
EXPOSE 8000

# Usar el script de arranque en vez de llamar a uvicorn directamente
CMD ["sh", "start.sh"]
