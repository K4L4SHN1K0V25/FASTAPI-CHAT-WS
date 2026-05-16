from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, status
import redis.asyncio as aioredis
import os
from manager import ConnectionManager
# 📊 IMPORTACIONES DE MONITOREO
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Gauge 

app = FastAPI(title="Chat Service (Monitored)")

# 🚀 1. INICIALIZAR INSTRUMENTADOR
# Le configuramos el endpoint con el prefijo correcto para que enganche con tu ruteo de Nginx
Instrumentator().instrument(app).expose(app, endpoint="/chat/metrics")

# 📈 2. CREAR MÉTRICA PERSONALIZADA (Mide conexiones activas en tiempo real)
WEBSOCKETS_ACTIVE = Gauge(
    "chat_websockets_active_total", 
    "Cantidad total de conexiones WebSocket activas en el Chat Service"
)

manager = ConnectionManager()
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

@app.on_event("startup")
async def startup_event():
    await manager.init_redis()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, token: str = Query(None)):
    if not token:
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token requerido")
        return

    try:
        username = await redis_client.get(f"session:{token}")
        if not username:
            await websocket.accept()
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token inválido o expirado")
            return
            
    except Exception as e:
        print(f"⚠️ Error al consultar Redis: {e}")
        await websocket.accept()
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Error de validación interno")
        return

    # ➕ ALTA EXITOSA: El usuario se conecta legítimamente, sumamos 1 a la métrica
    await manager.connect(websocket)
    WEBSOCKETS_ACTIVE.inc() 
    await manager.broadcast(f"🚀 {username} se ha unido al chat legítimamente.")
    
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{username}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # ➖ BAJA: El usuario se va del chat, restamos 1 a la métrica
        WEBSOCKETS_ACTIVE.dec() 
        await manager.broadcast(f"❌ {username} ha dejado el chat.")