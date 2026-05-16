FROM python:3.12-slim

WORKDIR /app

# Copiar e instalar dependencias primero para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código del servicio
COPY . .

EXPOSE 8001

# Ejecutamos en el puerto 8001 para que no choque con FastAPI del chat
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]