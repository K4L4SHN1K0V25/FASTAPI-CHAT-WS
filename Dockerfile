# 1. Usamos una imagen oficial y muy ligera de Python
FROM python:3.12-slim

# 2. Le decimos a Docker en qué carpeta de su sistema interno vamos a trabajar
WORKDIR /app

# 3. Copiamos el archivo de dependencias primero (esto hace que construir la imagen sea más rápido)
COPY requirements.txt .

# 4. Instalamos FastAPI, Uvicorn, Redis, etc.
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiamos todo tu código (main.py, manager.py) adentro del contenedor
COPY . .

# 6. Exponemos el puerto para que podamos conectarnos desde afuera
EXPOSE 8000

# 7. El comando exacto que levantará tu servidor cuando el contenedor inicie
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]