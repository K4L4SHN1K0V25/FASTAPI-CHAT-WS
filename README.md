# 🚀 FastAPI Real-Time Chat (Híbrido Redis/Local)

Un sistema de chat de alto rendimiento construido con **FastAPI** y **WebSockets**. Este proyecto implementa una arquitectura híbrida que soporta escalabilidad horizontal mediante el patrón **Pub/Sub de Redis**, con un sistema de respaldo (*fallback*) automático a memoria local.

## ✨ Características Destacadas

* **Comunicación Bidireccional:** Tiempo real puro mediante el protocolo WebSocket.
* **Arquitectura Híbrida (Redis + Local):**
    * **Con Redis:** Los mensajes se sincronizan globalmente entre múltiples instancias del servidor (escalabilidad horizontal).
    * **Modo Local:** Si Redis falla o no está presente, el sistema entra en modo de *Graceful Degradation* y sigue funcionando localmente sin interrumpir el servicio.
* **Asincronismo Total:** Uso de `async/await` y `asyncio.create_task` para gestionar la escucha de mensajes en segundo plano sin bloquear el servidor.
* **Frontend Minimalista:** Interfaz responsiva construida con Vanilla JS y Bootstrap 5 (sin frameworks pesados).



## 🛠️ Tecnologías Utilizadas

* **Backend:** Python 3.12+, FastAPI, Uvicorn.
* **Mensajería:** Redis (vía `redis.asyncio`).
* **Frontend:** HTML5, CSS3 (Bootstrap), JavaScript (WebSockets API).
* **Entorno:** Compatible con Linux (Parrot OS) y Windows.

## 🚀 Instalación y Uso

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/tu-usuario/fastapi-chat-ws.git](https://github.com/tu-usuario/fastapi-chat-ws.git)
    cd fastapi-chat-ws
    ```

2.  **Configurar el entorno virtual:**
    ```bash
    python -m venv venv
    # En Linux/Parrot:
    source venv/bin/activate
    # En Windows:
    .\venv\Scripts\activate
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Ejecutar el servidor:**
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```

> **Nota:** La aplicación detectará automáticamente si tienes un servidor Redis corriendo en `localhost:6379`. Si no se encuentra, la consola mostrará un aviso y el chat funcionará en modo local.

## 📂 Estructura del Proyecto

```text
fastapi-chat-ws/
├── app/
│   ├── main.py          # Lógica central y ConnectionManager (Pub/Sub)
│   └── templates/       # Frontend (index.html)
├── .gitignore           # Exclusión de venv, __pycache__ y archivos de sistema
├── requirements.txt     # Dependencias (fastapi, uvicorn, redis, websockets)
└── README.md            # Documentación técnica
```

## 🛡️ Detalles Técnicos y Arquitectura

### 🔄 Gestión de Concurrencia
El proyecto utiliza el **Event Loop** de Python de manera eficiente. La escucha de Redis no bloquea la recepción de mensajes de los WebSockets gracias a `asyncio.create_task()`. Esto permite que el servidor procese múltiples flujos de datos simultáneamente en un solo hilo.

### 📡 Protocolo WebSocket
A diferencia de las peticiones HTTP convencionales, este sistema mantiene un **handshake** inicial que eleva la conexión a un túnel persistente. Esto reduce drásticamente la latencia y el consumo de recursos al evitar la sobrecarga de cabeceras HTTP en cada mensaje enviado.

### 🧩 Patrón Pub/Sub (Publish/Subscribe)
La integración con Redis permite que el sistema escale horizontalmente. 
1. **Publish:** Cuando un usuario envía un mensaje, el servidor lo publica en un canal de Redis.
2. **Subscribe:** Todas las instancias del servidor están suscritas a ese canal; al recibir el mensaje de Redis, lo retransmiten a sus respectivos clientes locales.



## 🛠️ Roadmap / Futuras Mejoras
Para llevar este proyecto al siguiente nivel, se podrían implementar:
* **Persistencia de Datos:** Integrar PostgreSQL o MongoDB para almacenar el historial de mensajes.
* **Autenticación:** Implementar JWT (JSON Web Tokens) para identificar a los usuarios.
* **Salas de Chat:** Modificar el `ConnectionManager` para soportar canales privados o salas temáticas.
* **Docker Compose:** Crear un archivo de orquestación para levantar FastAPI y Redis con un solo comando.

---
Desarrollado como proyecto de portafolio para demostrar habilidades en Backend, Sistemas Distribuidos y Programación Asíncrona.