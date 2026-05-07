from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
import os

app = FastAPI()

# Ruta principal (Root): Sirve la interfaz de usuario.
# Usamos FileResponse para enviar el archivo HTML estático al cliente.
@app.get("/")
async def get():
    # Asegúrate de que esta ruta coincida con tu estructura de carpetas (app/templates/)
    return FileResponse('app/templates/index.html')

#* Clase ConnectionManager:
#* Implementa el patrón de diseño "Observer" para gestionar múltiples conexiones.
#* Se encarga de rastrear quién está conectado y de distribuir los mensajes.

class ConnectionManager:
    def __init__(self):
        # Lista para almacenar los objetos WebSocket activos.
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        # Acepta el 'handshake' inicial del protocolo WebSocket para establecer la conexión.
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        # Elimina la conexión de la lista cuando el cliente se desconecta.
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        # Envía un mensaje de forma asíncrona a TODOS los clientes conectados.
        for connection in self.active_connections:
            await connection.send_text(message)

# Instanciamos el gestor para que sea único en todo el ciclo de vida de la app (Singleton).
manager = ConnectionManager()

#* Endpoint de WebSocket:
#* Maneja la comunicación bidireccional continua.

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    # Al conectarse un nuevo cliente, se registra en el manager.
    await manager.connect(websocket)
    
    # Notifica a todos que alguien entró.
    await manager.broadcast(f"Usuario {client_id} se ha unido al chat")
    
    try:
        while True:
            # Bucle infinito para escuchar mensajes entrantes del cliente.
            # 'await' permite que el servidor atienda otras conexiones mientras espera.
            data = await websocket.receive_text()
            
            # Reenvía el mensaje recibido a todos los participantes.
            await manager.broadcast(f"Usuario {client_id}: {data}")
            
    except WebSocketDisconnect:
        # Se activa automáticamente si el usuario cierra la pestaña o pierde la conexión.
        manager.disconnect(websocket)
        await manager.broadcast(f"Usuario {client_id} se fue del chat")