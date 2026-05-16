from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, status
import redis.asyncio as aioredis  # 👈 Usamos el cliente asíncrono que ya usa tu manager
import os
from manager import ConnectionManager

app = FastAPI()
manager = ConnectionManager()

# Conexión asíncrona a Redis para el endpoint del WebSocket
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

@app.on_event("startup")
async def startup_event():
    await manager.init_redis()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    client_id: str, 
    token: str = Query(None)
):
    # 1. Validación inmediata si falta el token
    if not token:
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token requerido")
        return

    # 2. ⚡ LECTURA DE BAJA LATENCIA EN REDIS COMPARTIDO
    try:
        # Buscamos la sesión usando el token directamente en la memoria RAM compartida
        username = await redis_client.get(f"session:{token}")
        
        # Si la clave no existe o expiró, Redis regresa None -> Rechazamos conexión
        if not username:
            await websocket.accept()
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token inválido o expirado")
            return
            
    except Exception as e:
        print(f"⚠️ Error al consultar Redis: {e}")
        # Fallback seguro: Si Redis falla por alguna razón mística, rechazamos por seguridad
        await websocket.accept()
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Error de validación interno")
        return

    # 3. Si el token existe en Redis, lo dejamos pasar usando el username verificado
    await manager.connect(websocket)
    await manager.broadcast(f"🚀 {username} se ha unido al chat legítimamente.")
    
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{username}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"❌ {username} ha dejado el chat.")