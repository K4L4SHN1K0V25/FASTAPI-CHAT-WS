let ws = null;
let currentUsername = "";

// Al cargar la página, verificar si ya hay una sesión guardada
window.onload = () => {
    const token = localStorage.getItem("chat_token");
    const savedUser = localStorage.getItem("chat_username");
    if (token && savedUser) {
        currentUsername = savedUser;
        showChatSection(token);
    }
};

// 1. Petición de Registro
async function register() {
    const { username, password, alertEl } = getAuthInputs();
    alertEl.classList.add("d-none");

    // 🛑 VALIDACIÓN ANTES DE ENVIAR
    if (!username || !password) {
        showAlert("El usuario y la contraseña no pueden estar vacíos.");
        return;
    }

    try {
        const response = await fetch("/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();

        if (response.ok) {
            showAlert("Usuario creado. ¡Ya puedes iniciar sesión!", "success");
        } else {
            showAlert(data.detail || "Error en el registro");
        }
    } catch (err) {
        showAlert("No se pudo conectar con el servidor de autenticación.");
    }
}

// 2. Petición de Login (Manda datos como Form URL Encoded tal cual lo espera FastAPI)
async function login() {
    const { username, password, alertEl } = getAuthInputs();
    alertEl.classList.add("d-none");

    // 🛑 VALIDACIÓN ANTES DE ENVIAR
    if (!username || !password) {
        showAlert("Por favor ingresa tu usuario y contraseña.");
        return;
    }

    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    try {
        const response = await fetch("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData
        });
        const data = await response.json();

        if (response.ok) {
            localStorage.setItem("chat_token", data.access_token);
            localStorage.setItem("chat_username", username);
            currentUsername = username;
            showChatSection(data.access_token);
        } else {
            showAlert(data.detail || "Credenciales incorrectas");
        }
    } catch (err) {
        showAlert("Error al intentar iniciar sesión.");
    }
}

// 3. Conexión Protegida al WebSocket pasando el Token JWT
function connectWebSocket(token) {
    // Detecta dinámicamente si estás en localhost o en IP de red local
    const host = window.location.host;
    
    // Inyectamos el JWT en la URL como parámetro Query seguro
    ws = new WebSocket(`ws://${host}/ws/${currentUsername}?token=${token}`);

    ws.onmessage = (event) => {
        const messagesContainer = document.getElementById("messages");
        const msgDiv = document.createElement("div");
        msgDiv.className = "p-2 rounded bg-dark text-light border border-secondary align-self-start";
        msgDiv.style.maxWidth = "80%";
        msgDiv.textContent = event.data;
        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };

    ws.onclose = (event) => {
        // Si el token falló o fue rechazado por código de política (1008)
        if (event.code === 1008) {
            logout();
            alert("Tu sesión expiró o el token es inválido. Por favor inicia sesión de nuevo.");
        }
    };
}

// 4. Funciones de Control de Interfaz y Envíos
function sendMessage() {
    const input = document.getElementById("messageInput");
    if (input.value.trim() !== "" && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(input.value);
        input.value = "";
    }
}

function handleKeyPress(event) {
    if (event.key === "Enter") sendMessage();
}

function showChatSection(token) {
    document.getElementById("auth-section").style.display = "none";
    document.getElementById("chat-section").style.display = "block";
    document.getElementById("user-badge").textContent = `@${currentUsername}`;
    connectWebSocket(token);
}

function logout() {
    if (ws) ws.close();
    localStorage.clear();
    document.getElementById("chat-section").style.display = "none";
    document.getElementById("auth-section").style.display = "flex";
}

function getAuthInputs() {
    return {
        username: document.getElementById("username").value.trim(),
        password: document.getElementById("password").value,
        alertEl: document.getElementById("auth-alert")
    };
}

function showAlert(text, type = "danger") {
    const alertEl = document.getElementById("auth-alert");
    alertEl.className = `alert alert-${type} mt-3`;
    alertEl.textContent = text;
    alertEl.classList.remove("d-none");
}