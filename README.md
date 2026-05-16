# 🚀 FastAPI Real-Time Chat (Arquitectura Contenerizada con Nginx & Redis)

Un sistema de chat distribuido y de alto rendimiento construido bajo una arquitectura de microservicios utilizando **FastAPI**, **WebSockets**, **Redis** y **Nginx**. El proyecto está completamente contenerizado, garantizando un despliegue inmediato, aislamiento de servicios y escalabilidad horizontal nativa sin depender de configuraciones locales del sistema operativo.

## ✨ Características Destacadas

* **Comunicación Bidireccional:** Tiempo real puro y de baja latencia mediante el protocolo WebSocket.
* **Arquitectura de Microservicios:** Componentes del sistema completamente independientes y comunicados de forma aislada mediante redes virtuales de Docker.
* **Proxy Inverso con Nginx:** Unifica el Frontend y el Backend bajo el mismo puerto estándar (`80`). Esto elimina problemas de CORS por completo, oculta los puertos internos expuestos y gestiona el *Handshake* del WebSocket de manera eficiente.
* **Resiliencia y Escalabilidad Horizontal (Redis Pub/Sub):**
  * **Con Redis Activo:** Los mensajes se sincronizan globalmente entre múltiples réplicas o instancias del backend, permitiendo escalar la infraestructura horizontalmente de forma masiva.
  * **Modo de Respaldo (*Fallback*):** Si el servidor de Redis experimenta una caída, el sistema aplica una degradación sutil (*Graceful Degradation*) conmutando automáticamente a memoria local sin interrumpir las sesiones activas de los usuarios.
* **Asincronismo Total:** Uso intensivo de la programación asíncrona de Python mediante `async/await` y tareas en segundo plano (`asyncio.create_task`) para escuchar eventos de Redis sin bloquear peticiones entrantes.

---

## 🛠️ Tecnologías Utilizadas

* **API Gateway / Web Server:** Nginx (Alpine-based) actuando como Proxy Inverso.
* **Backend:** Python 3.12+, FastAPI, Uvicorn.
* **Mensajería / Broker:** Redis (Alpine-based) a través de `redis.asyncio`.
* **Frontend:** HTML5, CSS3 (Bootstrap 5), Vanilla JavaScript (WebSockets API nativa).
* **Orquestación y Entorno:** Docker y Docker Compose (Totalmente compatible con entornos Windows/WSL2 y Linux).

---

## 📂 Estructura del Proyecto

La arquitectura está estructurada para centralizar los contextos de desarrollo y facilitar la portabilidad en la nube:

```text
FASTAPI-CHAT-WS/
├── app/                        # Contexto principal del Backend y Código de la App
│   ├── main.py                 # Endpoints de la API y manejo de conexiones WebSocket
│   ├── manager.py              # Lógica del ConnectionManager e integración asíncrona de Redis
│   ├── requirements.txt        # Dependencias del proyecto Python
│   ├── Dockerfile              # Receta de Docker para empaquetar el microservicio de FastAPI
│   │
│   ├── frontend/               # Código del cliente estático servido por Nginx
│   │   ├── index.html          # Interfaz de usuario responsiva
│   │   ├── app.js              # Manejo del WebSocket con detección dinámica de host
│   │   └── styles.css          # Estilos personalizados
│   │
│   └── nginx/                  # Infraestructura de enrutamiento
│       ├── default.conf        # Configuración del Reverse Proxy y reglas de WebSockets
│       └── Dockerfile          # Receta de Docker para inyectar la configuración en Nginx
│
└── docker-compose.yml          # Orquestador maestro de los contenedores locales
```

---

## 🛡️ Detalles de Arquitectura y Flujo de Datos

### 📡 El Rol de Nginx como Proxy Inverso
Nginx se ubica en la frontera del sistema escuchando públicamente en el puerto `80`. Cuando llega una solicitud externa:
* **Si la ruta solicitada es la raíz `/`:** Sirve de manera estática e inmediata los archivos alojados en la carpeta `frontend/`.
* **Si la ruta inicia con `/ws/`:** Intercepta la petición HTTP convencional, inyecta las cabeceras requeridas de actualización (`Upgrade` y `Connection "Upgrade"`) y delega el flujo de datos de forma transparente al contenedor de FastAPI en su puerto interno `8000`.

### 🧩 Sincronización Global con Pub/Sub
Para soportar escalabilidad distribuida:
* **Publish:** Cuando un cliente envía un mensaje, la instancia del backend que lo recibe lo publica inmediatamente en el canal global `"chat_global"` de Redis.
* **Subscribe:** Todas las instancias del backend en ejecución se mantienen suscritas al canal de Redis mediante una tarea asíncrona dedicada (`_listen_redis`). Al recibir el impacto de Redis, cada instancia distribuye el mensaje a los WebSockets de sus clientes locales de forma simultánea.

---

## 🚀 Despliegue con Docker Compose

Toda la infraestructura se levanta y se comunica entre sí con un solo comando, abstrayendo por completo la instalación manual de bases de datos o entornos virtuales.

### Prerrequisitos
* Tener instalado **Docker Desktop** en ejecución.

### Pasos para iniciar el sistema

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/tu-usuario/fastapi-chat-ws.git](https://github.com/tu-usuario/fastapi-chat-ws.git)
   cd fastapi-chat-ws
   ```

2. **Levantar e iniciar la infraestructura:**
   Ejecuta el siguiente comando en la raíz del proyecto para compilar las imágenes locales e iniciar todos los servicios en segundo plano:
   ```bash
   docker-compose up --build -d
   ```

3. **Acceder a la aplicación:**
   Abre tu navegador web de preferencia e ingresa a:
   👉 `http://localhost` (Puerto 80 estándar de internet).

### Comandos Útiles de Monitoreo y Mantenimiento
* **Verificar el estado de los contenedores:** `docker-compose ps`
* **Inspeccionar logs del backend en tiempo real:** `docker logs chat_fastapi -f`
* **Detener y limpiar contenedores, redes y volúmenes:** `docker-compose down --rmi local --volumes`

---

## 🛠️ Roadmap / Siguientes Objetivos

Camino evolutivo trazado hacia una arquitectura de nivel empresarial:

* **[✓] Contenerización con Docker:** Dockerfiles independientes optimizados y ligeros.
* **[✓] Orquestación local:** Docker Compose configurado con inyección de variables de entorno para evitar colisiones de puertos (`REDIS_URL`).
* **[✓] Implementación de API Gateway:** Inclusión de Nginx como proxy unificador de tráfico.
* **[ ] Microservicio de Autenticación (Auth Service):** Crear un servicio independiente dedicado exclusivamente a emitir y validar JSON Web Tokens (JWT) para asegurar el acceso al canal de chat.
* **[ ] Orquestación Avanzada con Kubernetes (K8s):** Diseñar los manifiestos de despliegue (`Deployments`, `Services`, `Ingress`) para migrar la arquitectura local hacia un clúster de alta disponibilidad.
* **[ ] Persistencia de Mensajería:** Integrar una base de datos relacional (PostgreSQL) o NoSQL (MongoDB) con un patrón de repositorio para almacenar de forma permanente el historial del chat.

---
Desarrollado como proyecto de portafolio técnico enfocado en Backend de alto rendimiento, Arquitectura de Microservicios, Contenedores y Sistemas Distribuidos Asíncronos.