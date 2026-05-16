# 🚀 FastAPI Real-Time Chat (Arquitectura Contenerizada con Nginx & Redis)

Un sistema de chat distribuido y de alto rendimiento construido bajo una arquitectura de microservicios utilizando **FastAPI**, **WebSockets**, **Redis** y **Nginx**. El proyecto está completamente contenerizado, garantizando un despliegue inmediato, aislamiento de servicios y escalabilidad horizontal nativa sin depender de configuraciones locales del sistema operativo.

## ✨ Características Destacadas

* **Comunicación Bidireccional:** Tiempo real puro y de baja latencia mediante el protocolo WebSocket.
* **Microservicio de Autenticación Independiente (Auth Service):** Emisión y gestión de **JSON Web Tokens (JWT)** independientes de la lógica del chat.
* **Seguridad y Criptografía:** Encriptación de contraseñas mediante hash nativo con **Bcrypt** antes del almacenamiento y validaciones robustas de entrada de datos con **Pydantic**.
* **Arquitectura de Microservicios:** Componentes del sistema completamente independientes y comunicados de forma aislada mediante redes virtuales de Docker.
* **Proxy Inverso con Nginx:** Unifica el Frontend y múltiples microservicios bajo el mismo puerto estándar (`80`). Esto elimina problemas de CORS por completo, oculta los puertos internos expuestos, gestiona el ruteo hacia las rutas de autenticación (`/auth/`) y administra el *Handshake* del WebSocket de manera eficiente.
* **Resiliencia y Escalabilidad Horizontal (Redis Pub/Sub):**
  * **Con Redis Activo:** Los mensajes se sincronizan globalmente entre múltiples réplicas o instancias del backend, permitiendo escalar la infraestructura horizontalmente de forma masiva.
  * **Modo de Respaldo (*Fallback*):** Si el servidor de Redis experimenta una caída, el sistema aplica una degradación sutil (*Graceful Degradation*) conmutando automáticamente a memoria local sin interrumpir las sesiones activas de los usuarios.
* **Asincronismo Total:** Uso intensivo de la programación asíncrona de Python mediante `async/await` y tareas en segundo plano (`asyncio.create_task`) para escuchar eventos de Redis sin bloquear peticiones entrantes.

---

## 🛠️ Tecnologías Utilizadas

* **API Gateway / Web Server:** Nginx (Alpine-based) actuando como Proxy Inverso y unificador de tráfico.
* **Backend Chat Service:** Python 3.12+, FastAPI, Uvicorn, Async Redis Client.
* **Backend Auth Service:** Python 3.12+, FastAPI, SQLModel (ORM), Bcrypt, PyJWT.
* **Mensajería / Broker:** Redis (Alpine-based) a través de `redis.asyncio`.
* **Persistencia de Usuarios:** SQLite (Motor embebido e integrado localmente en el contenedor de autenticación).
* **Frontend:** HTML5, CSS3 (Bootstrap 5), Vanilla JavaScript (WebSockets API nativa y Fetch API).
* **Orquestación y Entorno:** Docker y Docker Compose (Totalmente compatible con entornos Windows/WSL2 y Linux).

---

## 📂 Estructura del Proyecto

La arquitectura está estructurada para independizar los contextos de compilación de cada microservicio:

```text
FASTAPI-CHAT-WS/
├── app/                        # Contexto principal del Chat Service
│   ├── main.py                 # Endpoints del WebSocket e interceptor de validación JWT
│   ├── manager.py              # Lógica del ConnectionManager e integración asíncrona de Redis
│   ├── requirements.txt        # Dependencias del servicio de mensajería (FastAPI, Redis, HTTPX, etc.)
│   ├── Dockerfile              # Receta de Docker para empaquetar el microservicio de FastAPI
│   │
│   ├── frontend/               # Código del cliente estático servido por Nginx
│   │   ├── index.html          # Interfaz de usuario con flujos condicionales de Login y Chat
│   │   └── app.js              # Cliente asíncrono para consumo de API Auth y WebSockets
│   │
│   └── nginx/                  # Infraestructura de enrutamiento y proxy inverso
│       ├── default.conf        # Reglas de Nginx para unificar Frontend, Auth y WebSockets
│       └── Dockerfile          # Receta de Docker para inyectar la configuración en Nginx
│
├── auth_service/               # 👈 Contexto principal del Auth Service
│   ├── main.py                 # Endpoints de Registro, Login y Validación asíncrona de tokens
│   ├── auth_utils.py           # Funciones criptográficas puras (Bcrypt hashing y firmas JWT)
│   ├── database.py             # Configuración de SQLModel e inicialización de SQLite
│   ├── requirements.txt        # Dependencias de autenticación (SQLModel, PyJWT, Bcrypt, etc.)
│   └── Dockerfile              # Receta de Docker para empaquetar el microservicio de Autenticación
│
└── docker-compose.yml          # Orquestador maestro de la red de contenedores locales
```

---

## 🛡️ Detalles de Arquitectura y Flujo de Datos

### 📡 El Rol de Nginx como Proxy Inverso e Ingress local
Nginx se ubica en la frontera del sistema escuchando públicamente en el puerto `80`. Cuando llega una solicitud externa:
* **Si la ruta solicitada es la raíz `/`:** Sirve de manera estática e inmediata los archivos alojados en la carpeta `frontend/`.
* **Si la ruta inicia con `/auth/`:** Desvía de manera transparente las peticiones HTTP convencionales (Registro y Login) al contenedor del `auth-service` en su puerto interno `8001`.
* **Si la ruta inicia con `/ws/`:** Intercepta la petición HTTP convencional, inyecta las cabeceras requeridas de actualización (`Upgrade` y `Connection "Upgrade"`) y delega el flujo de datos al contenedor de `chat-backend` en su puerto interno `8000`.

### 🗄️ Arquitectura de Persistencia Embebida (SQLite & SQLModel)
A diferencia de las arquitecturas tradicionales que dependen de un servidor de base de datos independiente (como PostgreSQL o MySQL) escuchando en un puerto de red, el `auth-service` implementa una **base de datos embebida** utilizando **SQLite** a través del ORM **SQLModel**.

* **Ciclo de Vida Autónomo (*Auto-Provisioning*):** Al arrancar el contenedor por primera vez, el evento `@app.on_event("startup")` detona la función `init_db()`. Si el archivo físico `users.db` no existe en el entorno, el motor lo crea de forma transparente en ese milisegundo e inyecta la estructura de tablas definida en los modelos de Python, eliminando la necesidad de scripts de migración manuales o configuraciones previas de credenciales.
* **Persistencia entre Despliegues (Docker Volumes):** Para evitar la naturaleza efímera de los contenedores, la base de datos se almacena en la raíz del contexto de autenticación. Al estar mapeada mediante un volumen de Docker (`./auth_service:/app`), el archivo binario de la base de datos reside de forma segura en el disco duro del host. Esto garantiza que los usuarios registrados persistan intactos incluso tras la destrucción o recompilación completa de las imágenes del clúster.
* **Rendimiento de Baja Latencia:** Al no existir un socket de red intermedio para consultar los datos, las operaciones de lectura durante el Login o el Registro se ejecutan directamente en memoria/disco local dentro del mismo proceso del microservicio, reduciendo el *overhead* de red a cero.

### 🔐 Flujo Distribuido de Validación JWT (Comunicación Inter-servicio)
Para asegurar que las conexiones al WebSocket no sean anónimas:
1. El cliente hace Login en `/auth/login`, recibe un token firmado por el `auth-service` y lo almacena localmente.
2. Al abrir el WebSocket, el cliente pasa el token como un parámetro query en la URL.
3. El `chat-backend` intercepta el token y, antes de aceptar la conexión, realiza una **petición HTTP asíncrona interna** con `httpx` hacia `http://auth-service:8001/auth/validate`.
4. El `auth-service` confirma la validez de la firma digital del JWT y devuelve la identidad del usuario. Si es exitoso, el chat acepta la conexión; de lo contrario, corta el enlace inmediatamente con un código de política de seguridad (`1008`).

### ⚡ Caché Centralizada de Sesiones (Redis Compartido)
Para optimizar el rendimiento dentro de entornos con hardware restringido (como servidores VPS de 1 vCore y 1 GB de RAM), se migró el modelo de comunicación entre microservicios de un patrón síncrono acoplado por HTTP (`httpx`) a una **arquitectura de persistencia compartida en memoria RAM**.

* **Eliminación del Overhead de Red:** Cuando un usuario inicia sesión con éxito, el `auth-service` genera el JWT y guarda inmediatamente una clave temporal en Redis (`session:<token>` -> `username`) con un tiempo de expiración estricto de 1 hora (`ex=3600`).
* **Validación en Microsegundos:** Al intentar abrir un canal de WebSocket, el `chat-backend` ya no realiza peticiones HTTP externas hacia el otro contenedor. En su lugar, ejecuta un comando `GET` asíncrono y directo a la memoria compartida de Redis utilizando `redis.asyncio`. Si la clave existe, el acceso se autoriza de inmediato; si expiró o no existe, la conexión se corta bajo la política de seguridad `1008`.
* **Alta Disponibilidad y Aislamiento:** Este patrón elimina el acoplamiento crítico entre componentes. Si el contenedor del `auth-service` experimenta una caída o se detiene por mantenimiento, los usuarios autenticados previamente pueden seguir conectándose al chat y transmitiendo mensajes en tiempo real de forma ininterrumpida, ya que el estado de la sesión reside de forma independiente en el motor de caché.

### 🧩 Sincronización Global con Pub/Sub
Para soportar escalabilidad distribuida entre múltiples réplicas de mensajería:
* **Publish:** Cuando un cliente autenticado envía un mensaje, la instancia de chat que lo recibe lo publica inmediatamente en el canal global `"chat_global"` de Redis.
* **Subscribe:** Todas las instancias del backend en ejecución se mantienen suscritas al canal de Redis mediante una tarea asíncrona dedicada (`_listen_redis`). Al recibir el impacto de Redis, cada instancia distribuye el mensaje a los WebSockets de sus clientes locales de forma simultánea.

### 🔄 Pipeline de Automatización CI/CD (GitHub Actions & Docker Hub)
El proyecto implementa un flujo automatizado de **Integración Continua (CI)** y **Despliegue Continuo (CD)** mediante GitHub Actions. Este diseño desacopla por completo la etapa de compilación de la infraestructura de producción, permitiendo que servidores con recursos restringidos (como un VPS de 1 vCore y 1 GB de RAM) desplieguen actualizaciones en microsegundos sin sufrir estrés de hardware.

```text
[ Git Push ] ──> 🧪 [ Job: Pytest ] ──(Si pasa)──> 🐳 [ Job: Docker Build & Push ] ──> 🚀 [ Docker Hub ]
```

* **Calidad de Código Automatizada (CI):** Ante cada `git push` o `pull_request` hacia la rama principal, el pipeline levanta un entorno aislado de Python 3.12 en la nube de GitHub, instala las dependencias de testing y ejecuta una suite de pruebas unitarias con **Pytest**. Si alguna prueba criptográfica de hashing o validación de tokens falla, el pipeline se aborta inmediatamente para evitar la propagación de bugs.
* **Compilación Remota Aislada (CD):** Una vez que las pruebas se completan en verde, el segundo *job* del pipeline inicia sesión de forma segura en **Docker Hub** utilizando secretos encriptados del repositorio (`DOCKERHUB_TOKEN`). Utilizando un optimizador de capas (`setup-buildx-action`), GitHub compila las imágenes de Docker del `chat-backend` y del `auth-service` en paralelo y las publica automáticamente bajo el tag `:latest`.
* **Despliegue de Producción Ultra-Ligero:** Gracias a esta arquitectura, el servidor VPS no requiere clonar el código fuente, instalar entornos virtuales o compilar binarios. El despliegue se reduce a un comando `docker compose pull` y `up -d` de producción, descargando las imágenes pre-compiladas desde la nube con un consumo de CPU y memoria RAM cercano a cero durante el arranque.

### 📊 Sistema de Monitoreo, Observabilidad y Métricas (Punto 5)
Para mitigar los riesgos de operar en una infraestructura con restricciones estrictas de hardware (VPS de 1 GB de RAM), se implementó un sistema de observabilidad de alta eficiencia basado en el modelo de raspado de **Prometheus**:

* **Instrumentación Nativa:** Mediante `prometheus-fastapi-instrumentator`, ambos microservicios exponen endpoints asíncronos y aislados (`/auth/metrics` y `/chat/metrics`) que reportan telemetría del proceso en formato OpenMetrics (consumo de memoria residente, hilos de CPU y latencia de red en percentiles).
* **Métricas de Estado Persistente (WebSockets):** Se diseñó un vector personalizado de tipo `Gauge` (`chat_websockets_active_total`) acoplado al ciclo de vida de los eventos `connect` y `disconnect` del protocolo WebSocket. Esto permite auditar, en tiempo real, la densidad de conexiones concurrentes activas y predecir cuellos de botella por saturación de descriptores de archivos.
* **Agente de Recolección Centralizado:** Se integró un contenedor dedicado de **Prometheus** configurado con políticas de raspado periódico (`scrape_interval: 15s`). Este agente centraliza el almacenamiento de las series temporales, sirviendo como la fuente de verdad analítica que alimentará los tableros visuales de Grafana y las reglas de alerta del servidor.

---

## 🚀 Despliegue con Docker Compose

Toda la infraestructura se levanta y se comunica entre sí con un solo comando, abstrayendo por completo la instalación manual de bases de datos, entornos virtuales locales o configuraciones de red.

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
* **Verificar el estado de los contenedores de la red:** `docker-compose ps`
* **Inspeccionar logs del servicio de autenticación:** `docker logs auth_fastapi -f`
* **Inspeccionar logs del chat en tiempo real:** `docker logs chat_fastapi -f`
* **Detener y limpiar contenedores, redes y volúmenes:** `docker-compose down --rmi local --volumes`

---

## 🛠️ Roadmap / Siguientes Objetivos

Camino evolutivo trazado hacia una arquitectura de nivel empresarial:

* **[✓] Contenerización con Docker:** Dockerfiles independientes optimizados y ligeros.
* **[✓] Orquestación local:** Docker Compose configurado con inyección de variables de entorno para evitar colisiones de puertos (`REDIS_URL`).
* **[✓] Implementación de API Gateway:** Inclusión de Nginx como proxy unificador de tráfico.
* **[✓] Microservicio de Autenticación (Auth Service):** Servicio independiente dedicado exclusivamente a emitir y validar JSON Web Tokens (JWT) y salvaguardar los accesos con validaciones en Pydantic y Bcrypt.
* **[✓] Comunicación Avanzada de Baja Latencia:** Optimización del acoplamiento entre servicios mediante una caché centralizada de sesiones sobre Redis, reduciendo el overhead de red a cero.
* **[ ] Orquestación Avanzada con Kubernetes (K8s):** Diseñar los manifiestos de despliegue (`Deployments`, `Services`, `Ingress`) para migrar la arquitectura local hacia un clúster de alta disponibilidad.
* **[ ] Persistencia de Mensajería:** Integrar una base de datos relacional (PostgreSQL) o NoSQL (MongoDB) con un patrón de repositorio para almacenar de forma permanente el historial del chat.

---
Desarrollado como proyecto de portafolio técnico enfocado en Backend de alto rendimiento, Arquitectura de Microservicios, Contenedores y Sistemas Distribuidos Asíncronos.