import asyncio
import redis.asyncio as aioredis
from fastapi import WebSocket
import os

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.redis = None
        self.pubsub = None

    async def init_redis(self):
        try:
            # Lee la variable de entorno de Docker, y si no existe usa localhost
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis = aioredis.from_url(redis_url, decode_responses=True)
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe("chat_global")
            asyncio.create_task(self._listen_redis())
        except Exception as e:
            self.redis = None
            print(f"⚠️ Redis no disponible: {e}")

    async def _listen_redis(self):
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                await self._broadcast_local(message["data"])

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        try:
            if self.redis:
                await self.redis.publish("chat_global", message)
            else:
                await self._broadcast_local(message)
        except Exception as e:
            self.redis = None
            await self._broadcast_local(message)

    async def _broadcast_local(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass