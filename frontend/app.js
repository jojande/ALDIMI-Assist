const API_URL = 'http://localhost:8000/api';
let chatHistory = [];

// Mostrar vista previa de la imagen cargada
function previewImage(event) {
    const input = event.target;
    const previewContainer = document.getElementById('image-preview-container');
    const previewImage = document.getElementById('imagePreview');
    const uploadFileName = document.getElementById('uploadFileName');

    if (input.files && input.files[0]) {
        const file = input.files[0];
        uploadFileName.innerText = `📁 ${file.name}`;
        
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImage.src = e.target.result;
            previewContainer.style.display = 'flex';
        }
        reader.readAsDataURL(file);
    }
}

// Carga y procesamiento del OCR
async function uploadDocument() {
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const resultArea = document.getElementById('ocr-result');
    const docTypeBadge = document.getElementById('docTypeBadge');
    const structuredFields = document.getElementById('structured-fields');
    const extractedText = document.getElementById('extractedText');

    if (fileInput.files.length === 0) {
        alert('Por favor, selecciona una imagen primero.');
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    uploadBtn.disabled = true;
    uploadBtn.innerText = '🧠 Procesando con IA...';
    resultArea.style.display = 'none';

    try {
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Error al procesar el documento en el servidor.');

        const data = await response.json();
        
        // Asignar insignia del tipo de documento
        const docType = data.doc_type; // DNI, RECETA, BOLETA, OTRO
        docTypeBadge.innerText = docType;
        docTypeBadge.className = `badge ${docType.toLowerCase()}`;

        // Renderizar los campos estructurados recibidos del backend
        renderStructuredProfile(docType, data.profile);

        // Rellenar el texto plano crudo
        extractedText.innerText = data.extracted_text;
        extractedText.style.display = 'none'; // mantener cerrado al inicio
        
        resultArea.style.display = 'block';

    } catch (error) {
        console.error(error);
        alert('Hubo un error al procesar el documento. Asegúrate de que el backend esté encendido.');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerText = '✨ Cargar y Procesar';
    }
}

// Renderiza perfiles structured-fields en el panel de visión
function renderStructuredProfile(docType, profile) {
    const container = document.getElementById('structured-fields');
    container.innerHTML = '';
    
    if (!profile) {
        container.innerHTML = '<div class="field-group"><span class="field-value">No se pudieron extraer variables de perfil.</span></div>';
        return;
    }

    if (docType === 'DNI') {
        const cui = profile.cui_dni || 'No detectado';
        const apellidos = profile.apellidos || 'No detectado';
        const nombres = profile.nombres || 'No detectado';

        container.innerHTML = `
            <div class="field-group">
                <span class="field-label">Nombres</span>
                <span class="field-value">${nombres}</span>
            </div>
            <div class="field-group">
                <span class="field-label">Apellidos</span>
                <span class="field-value">${apellidos}</span>
            </div>
            <div class="field-group">
                <span class="field-label">CUI / N° de Identidad</span>
                <span class="field-value">${cui}</span>
            </div>
        `;
    } 
    else if (docType === 'RECETA') {
        const paciente = profile.paciente || 'No detectado';
        const diagnostico = profile.diagnostico || 'No detectado';
        const medsStr = profile.medicamentos || '';
        
        let medsHtml = '';
        if (medsStr) {
            const medsArray = medsStr.split(',').map(m => m.trim()).filter(m => m.length > 0);
            medsHtml = medsArray.length > 0
                ? `<ul class="field-meds-list">${medsArray.map(m => `<li>${m}</li>`).join('')}</ul>`
                : '<span class="field-value">No detectados</span>';
        } else {
            medsHtml = '<span class="field-value">No detectados</span>';
        }

        container.innerHTML = `
            <div class="field-group">
                <span class="field-label">Paciente</span>
                <span class="field-value">${paciente}</span>
            </div>
            <div class="field-group">
                <span class="field-label">Diagnóstico</span>
                <span class="field-value">${diagnostico}</span>
            </div>
            <div class="field-group">
                <span class="field-label">Medicamentos e Indicaciones</span>
                ${medsHtml}
            </div>
        `;
    } 
    else if (docType === 'BOLETA') {
        const nroRecibo = profile.nro_recibo || 'S/N';
        const donante = profile.donante || 'No detectado';
        const dniRuc = profile.dni_ruc || 'No detectado';
        const valoracion = profile.valoracion || '0.00';

        container.innerHTML = `
            <div class="field-group">
                <span class="field-label">Donación Recibo N°</span>
                <span class="field-value">${nroRecibo}</span>
            </div>
            <div class="field-group">
                <span class="field-label">Donante / Razón Social</span>
                <span class="field-value">${donante} (${dniRuc})</span>
            </div>
            <div class="field-group">
                <span class="field-label">Valoración Estimada</span>
                <span class="field-value" style="color:var(--color-success);font-weight:700;">S/. ${valoracion}</span>
            </div>
        `;
    } else {
        container.innerHTML = '<div class="field-group"><span class="field-value">Documento no categorizado.</span></div>';
    }
}

// Mostrar/Ocultar acordeón de texto crudo
function toggleRawText() {
    const textPre = document.getElementById('extractedText');
    if (textPre.style.display === 'none') {
        textPre.style.display = 'block';
    } else {
        textPre.style.display = 'none';
    }
}

// Analizar la bitácora psicosocial
async function analyzeBitacora() {
    const bitacoraInput = document.getElementById('bitacoraInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const psychoResult = document.getElementById('psycho-result');
    const alertTitle = document.getElementById('alertTitle');
    const alertRecommendation = document.getElementById('alertRecommendation');
    const alertIndicators = document.getElementById('alertIndicators');
    const referBtn = document.getElementById('referBtn');
    const alertIcon = document.getElementById('alertIcon');

    const text = bitacoraInput.value.trim();
    if (!text) {
        alert('Por favor, escribe una observación del comportamiento del menor.');
        return;
    }

    analyzeBtn.disabled = true;
    analyzeBtn.innerText = '🧠 Analizando Reporte...';
    psychoResult.style.display = 'none';

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: `Reporte de observación: ${text}`,
                history: []
            })
        });

        if (!response.ok) throw new Error('Error al analizar reporte.');

        const data = await response.json();
        const sentiment = data.sentiment; // ALERTA o NORMAL

        // Identificar indicadores a nivel de frontend para etiquetar los tags
        const indicators = detectIndicators(text);

        if (sentiment === 'ALERTA' || indicators.length > 0) {
            psychoResult.className = 'result-area alert-container critico';
            alertIcon.innerText = '🚨';
            alertTitle.innerText = 'Nivel de Riesgo: CRÍTICO';
            alertRecommendation.innerText = 'Se han detectado alertas psicosociales severas. Se requiere derivación a psicología de inmediato.';
            referBtn.style.display = 'block';
        } else {
            psychoResult.className = 'result-area alert-container normal';
            alertIcon.innerText = '✅';
            alertTitle.innerText = 'Nivel de Riesgo: BAJO / NORMAL';
            alertRecommendation.innerText = 'Monitoreo emocional normal. No se identificaron patrones de riesgo.';
            referBtn.style.display = 'none';
        }

        // Renderizar etiquetas de indicadores detectados
        alertIndicators.innerHTML = '';
        if (indicators.length > 0) {
            indicators.forEach(ind => {
                const tag = document.createElement('span');
                tag.className = 'indicator-tag';
                tag.innerText = ind;
                alertIndicators.appendChild(tag);
            });
        } else {
            alertIndicators.innerHTML = '<span style="font-size:0.8rem;color:var(--text-muted);">Ningún indicador de alerta detectado.</span>';
        }

        psychoResult.style.display = 'block';

    } catch (error) {
        console.error(error);
        alert('Hubo un error al ejecutar la auditoría del reporte.');
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.innerText = '🚨 Analizar Alerta Emocional';
    }
}

// Detección de tags locales
function detectIndicators(text) {
    const t = text.toLowerCase();
    const list = [];
    
    const suicidio = ["mató", "mato", "matar", "morir", "suicid", "no seguir", "quitarse la vida", "fin a mi vida"];
    const tristeza = ["lloró", "lloro", "llorar", "triste", "pena", "deprim", "lament", "sufriendo", "llorando"];
    const aislamiento = ["encerrado", "encerro", "rechazó", "rechazo", "no participó", "no habla", "solo", "aislado"];
    const alimentacion = ["no comió", "no comio", "sin apetito", "rechazó comida", "no quiere comer"];

    if (suicidio.some(kw => t.includes(kw))) list.push('Riesgo de Autolesión / Suicidio');
    if (tristeza.some(kw => t.includes(kw))) list.push('Depresión / Tristeza Severa');
    if (aislamiento.some(kw => t.includes(kw))) list.push('Aislamiento / Rechazo');
    if (alimentacion.some(kw => t.includes(kw))) list.push('Trastorno Alimenticio / Falta de Apetito');

    return list;
}

// Acción de derivar a psicología
function triggerReferral() {
    alert('🏥 Derivación Ejecutada: El reporte y sus indicadores de alerta emocional han sido notificados al psicólogo de turno del albergue ALDIMI.');
}

// Chatbot virtual
async function sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const chatWindow = document.getElementById('chat-window');
    
    if (!chatInput || !chatWindow) return;

    const message = chatInput.value.trim();
    if (!message) return;

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

        if (!response.ok) throw new Error('Error al enviar el mensaje.');

        const data = await response.json();
        
        // Agregar respuesta a la UI
        addMessageToUI('bot', data.response, data.sentiment);

        // Actualizar historial local de contexto
        chatHistory.push({ role: 'user', content: message });
        chatHistory.push({ role: 'bot', content: data.response });
        
        // Limitar historial para no sobrecargar contexto de tokens
        if (chatHistory.length > 10) {
            chatHistory.shift();
            chatHistory.shift();
        }

    } catch (error) {
        console.error(error);
        addMessageToUI('bot', 'Lo siento, no pude comunicarme con el asistente central de IA.');
    }
}

// Trigger para chips de sugerencias rápidas
function sendSuggestedQuery(query) {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.value = query;
        sendMessage();
    }
}

// Agregar burbuja de chat a la ventana
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
    
    // Auto-scroll al fondo
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Evento de tecla Enter en el input de chat
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
