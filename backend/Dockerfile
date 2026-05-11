FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Eliminar caracteres \r (CRLF de Windows) del script de arranque
# Esto protege el build aunque Git haya convertido los saltos de linea
RUN sed -i 's/\r//' start.sh

RUN chmod +x start.sh

EXPOSE 8000

CMD ["sh", "start.sh"]
