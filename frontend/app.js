const API_URL = 'http://localhost:8000/api';
let chatHistory = [];

async function uploadDocument() {
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const resultArea = document.getElementById('ocr-result');
    
    if (fileInput.files.length === 0) {
        alert('Por favor selecciona una imagen.');
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    uploadBtn.disabled = true;
    uploadBtn.innerText = 'Procesando...';

    try {
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Error en el servidor');

        const data = await response.json();
        
        document.getElementById('docType').innerText = data.doc_type;
        document.getElementById('extractedText').innerText = data.extracted_text;
        resultArea.style.display = 'block';

    } catch (error) {
        console.error(error);
        alert('Hubo un error al procesar el documento.');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerText = 'Cargar y Procesar';
    }
}

async function sendMessage() {
    console.log("Iniciando envío de mensaje...");
    const chatInput = document.getElementById('chatInput');
    const chatWindow = document.getElementById('chat-window');
    
    if (!chatInput || !chatWindow) {
        console.error("No se encontraron los elementos del chat en el DOM");
        return;
    }

    const message = chatInput.value.trim();
    if (!message) return;

    console.log("Mensaje a enviar:", message);

    // Agregar mensaje del usuario al UI
    addMessageToUI('user', message);
    chatInput.value = '';

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                history: chatHistory
            })
        });

        if (!response.ok) throw new Error('Error en el chat: ' + response.statusText);

        const data = await response.json();
        console.log("Respuesta recibida:", data);
        
        // Agregar mensaje del bot al UI
        addMessageToUI('bot', data.response, data.sentiment);

        // Actualizar historial local
        chatHistory.push({ role: 'user', content: message });
        chatHistory.push({ role: 'bot', content: data.response });

    } catch (error) {
        console.error("Error en sendMessage:", error);
        addMessageToUI('bot', 'Lo siento, hubo un error al procesar tu mensaje.');
    }
}

function addMessageToUI(role, content, sentiment = null) {
    const chatWindow = document.getElementById('chat-window');
    if (!chatWindow) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', role);
    
    if (sentiment === 'ALERTA') {
        messageDiv.classList.add('alert');
        content = `⚠️ [ALERTA DE RIESGO DETECTADA]\n${content}`;
    }
    
    messageDiv.innerText = content;
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Permitir enviar con Enter (envuelto para evitar errores de carga)
document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
});
