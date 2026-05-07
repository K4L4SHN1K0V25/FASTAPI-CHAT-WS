import asyncio
import redis.asyncio as aioredis  # Cliente asíncrono para no bloquear el event loop de Python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        # Almacena objetos WebSocket activos en la memoria RAM de ESTA instancia.
        self.active_connections: list[WebSocket] = []
        
        # Referencias para el cliente Redis y el objeto Pub/Sub (inicialmente nulas).
        self.redis = None
        self.pubsub = None

    async def init_redis(self):
        """
        Lógica de conexión elástica a Redis.
        Si Redis está caído, la app entra en 'Graceful Degradation' (funciona solo local).
        """
        try:
            # decode_responses=True convierte automáticamente bytes de Redis a strings de Python.
            self.redis = aioredis.from_url("redis://localhost:6379", decode_responses=True)
            self.pubsub = self.redis.pubsub()
            
            # Suscripción al canal global para recibir mensajes de otras instancias.
            await self.pubsub.subscribe("chat_global")
            
            # asyncio.create_task: Crea una tarea concurrente no bloqueante. 
            # El servidor sigue corriendo mientras esta función escucha a Redis en segundo plano.
            asyncio.create_task(self._listen_redis())
            print("🚀 Redis conectado y escuchando canal 'chat_global'")
        except Exception as e:
            self.redis = None
            print(f"⚠️ Redis no disponible (usando modo local): {e}")

    async def _listen_redis(self):
        """
        Loop infinito de escucha (Background Worker).
        Cuando llega un mensaje al canal 'chat_global', lo reenvía a los clientes locales.
        """
        async for message in self.pubsub.listen():
            # Filtramos solo mensajes de tipo 'message' (ignorando confirmaciones de suscripción).
            if message["type"] == "message":
                await self._broadcast_local(message["data"])

    async def connect(self, websocket: WebSocket):
        """Acepta la conexión WebSocket y la registra en el pool local."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Elimina la referencia del WebSocket al cerrarse la conexión."""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        """
        Puente de comunicación (Middleware):
        Si Redis está activo, publica el mensaje globalmente (para todas las instancias).
        Si no, se limita a los usuarios de la instancia actual.
        """
        try:
            if self.redis:
            # Publicar en Redis desencadena que TODOS los suscriptores reciban el mensaje.
                await self.redis.publish("chat_global", message)
            else:
                await self._broadcast_local(message)
        except Exception as e:
            # Si Redis falla en pleno vuelo, cambiamos a modo local automáticamente
            print(f"🚨 Redis falló durante el broadcast: {e}")
            self.redis = None # Desactivamos Redis para futuras llamadas
            await self._broadcast_local(message)

    async def _broadcast_local(self, message: str):
        """Itera sobre la lista de WebSockets de esta instancia y envía el texto."""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Silenciamos errores de conexiones que se cerraron abruptamente sin avisar.
                pass 

manager = ConnectionManager()

# Lifecycle hook: Se ejecuta una sola vez al arrancar el servidor.
@app.on_event("startup")
async def startup_event():
    await manager.init_redis()

@app.get("/")
async def get():
    """Sirve el cliente web (HTML/JS) al entrar a la raíz de la app."""
    return FileResponse('app/templates/index.html')

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    """
    Gestión del ciclo de vida de la conexión WebSocket individual.
    - Handshake inicial.
    - Loop de recepción de datos.
    - Manejo de desconexión.
    """
    await manager.connect(websocket)
    await manager.broadcast(f"Usuario {client_id} se unió")
    try:
        while True:
            # Espera asíncrona a que el cliente envíe texto.
            data = await websocket.receive_text()
            await manager.broadcast(f"Usuario {client_id}: {data}")
    except WebSocketDisconnect:
        # Se activa si el cliente cierra la pestaña o pierde internet.
        manager.disconnect(websocket)
        await manager.broadcast(f"Usuario {client_id} salió")