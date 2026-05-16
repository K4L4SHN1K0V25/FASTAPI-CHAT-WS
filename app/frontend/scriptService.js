/**
 * Generación de ID de cliente:
 * Usamos Date.now() para generar un ID único basado en el timestamp actual,
 * evitando colisiones si abres varias pestañas.
 */
const client_id = Date.now();

/**
 * Inicialización de WebSocket:
 * 'window.location.host' detecta dinámicamente si estás en localhost o en una IP de red (Parrot OS),
 * haciendo que el código sea portable entre entornos de desarrollo.
 */
// Apuntamos directamente al puerto 8000 donde vive el microservicio del Chat
const ws = new WebSocket(`ws://${window.location.host}/ws/${client_id}`);

/**
 * Evento onmessage:
 * Se dispara cada vez que el servidor FastAPI envía un mensaje (broadcast).
 */
ws.onmessage = function (event) {
  const messages = document.getElementById("messages");
  const message = document.createElement("div");

  // Estilización simple para cada línea de mensaje
  message.className = "border-bottom mb-1";
  message.textContent = event.data; // Insertamos el texto plano para evitar ataques XSS

  messages.appendChild(message);

  // Auto-scroll: Mueve el scroll al final para que el último mensaje siempre sea visible
  messages.scrollTop = messages.scrollHeight;
};

/**
 * Función sendMessage:
 * Envía el texto capturado en el input a través del túnel WebSocket abierto.
 */
function sendMessage(event) {
  const input = document.getElementById("messageText");

  // Solo enviamos si el input no está vacío
  if (input.value.trim() !== "") {
    ws.send(input.value);
    input.value = ""; // Limpiamos el campo tras el envío
  }

  // Evita que el formulario recargue la página (comportamiento por defecto de HTML)
  event.preventDefault();
}
