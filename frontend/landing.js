// INTERACTIVIDAD DE LA LANDING PAGE DE ALDIMI

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initDonationCalculator();
    initChatWidget();
});

// 1. Menú de Navegación Móvil
function initNavigation() {
    const menuToggle = document.getElementById('menuToggle');
    const navMenu = document.getElementById('navMenu');

    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('open');
            menuToggle.classList.toggle('active');
        });
        
        // Cerrar menú al hacer clic en un enlace
        navMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('open');
                menuToggle.classList.remove('active');
            });
        });
    }

    // Cambiar enlace activo en base al scroll
    window.addEventListener('scroll', () => {
        let current = '';
        const sections = document.querySelectorAll('section');
        const navLinks = document.querySelectorAll('.nav-menu a:not(.intranet-btn)');
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (pageYOffset >= (sectionTop - 150)) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href').slice(1) === current) {
                link.classList.add('active');
            }
        });
    });
}

// 2. Control de Pestañas (Historia, Misión, Visión, Junta)
function switchTab(event, tabId) {
    // Quitar active de todos los botones de pestaña en esta sección
    const tabContainer = event.currentTarget.closest('.nosotros-tabs-container');
    tabContainer.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    
    // Ocultar todos los tab panes
    tabContainer.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
    
    // Activar el botón actual y mostrar el panel correspondiente
    event.currentTarget.classList.add('active');
    document.getElementById(tabId).classList.add('active');
}

// 3. Calculadora de Impacto de Donación
function initDonationCalculator() {
    const presetButtons = document.querySelectorAll('.preset-btn');
    const impactDisplay = document.getElementById('calcImpactDisplay');
    const donateBtn = document.getElementById('calcDonateBtn');

    // Mapeo de montos y sus descripciones de impacto en ALDIMI
    const impacts = {
        '10': '🍲 Tu donación de <strong>S/ 10</strong> cubre **1 ración de alimentación nutritiva** para un niño albergado.',
        '50': '💊 Tu donación de <strong>S/ 50</strong> cubre **medicamentos esenciales y suministros clínicos** para un día de tratamiento.',
        '100': '🛏️ Tu donación de <strong>S/ 100</strong> cubre **1 noche de hospedaje completo y asepsia** para un niño y su madre.',
        '200': '🎗️ Tu donación de <strong>S/ 200</strong> cubre **el soporte integral semanal** (vivienda, alimentación, pasajes al hospital) de un menor.',
        '500': '❤️ Tu donación de <strong>S/ 500</strong> cubre **el mantenimiento logístico completo** para dar soporte a una nueva familia que ingresa.'
    };

    // Mercado Pago Links ficticios de donación (pueden ser personalizados con los links oficiales)
    const links = {
        '10': 'https://aldimi.pe/donar-ahora/',
        '50': 'https://aldimi.pe/donar-ahora/',
        '100': 'https://aldimi.pe/donar-ahora/',
        '200': 'https://aldimi.pe/donar-ahora/',
        '500': 'https://aldimi.pe/donar-ahora/'
    };

    presetButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Quitar clase activa de botones
            presetButtons.forEach(b => b.classList.remove('active'));
            // Agregar activa a este botón
            btn.classList.add('active');

            const amount = btn.getAttribute('data-amount');
            
            // Actualizar texto descriptivo
            impactDisplay.innerHTML = impacts[amount] || '';
            
            // Actualizar botón de Mercado Pago
            donateBtn.textContent = `Donar S/ ${amount} vía Mercado Pago`;
            donateBtn.href = links[amount] || 'https://aldimi.pe/donar-ahora/';
        });
    });
}

// 4. Chatbot RAG Flotante
function initChatWidget() {
    const toggleBtn = document.getElementById('chatWidgetToggle');
    const closeBtn = document.getElementById('chatBoxClose');
    const chatBox = document.getElementById('chatWidgetBox');
    const badge = document.getElementById('chatBadge');
    
    if (toggleBtn && chatBox) {
        toggleBtn.addEventListener('click', () => {
            const isVisible = chatBox.style.display === 'flex';
            chatBox.style.display = isVisible ? 'none' : 'flex';
            
            // Ocultar la notificación cuando abran el chat por primera vez
            if (badge) {
                badge.style.display = 'none';
            }
        });
    }

    if (closeBtn && chatBox) {
        closeBtn.addEventListener('click', () => {
            chatBox.style.display = 'none';
        });
    }
}

// Manejar envío con Enter
function handleChatKey(event) {
    if (event.key === 'Enter') {
        sendWidgetMessage();
    }
}

// Enviar mensaje al Backend (API FastAPI)
async function sendWidgetMessage() {
    const inputField = document.getElementById('chatBoxInput');
    const messagesContainer = document.getElementById('chatBoxMessages');
    const text = inputField.value.trim();

    if (!text) return;

    // Agregar mensaje del usuario
    appendMessage('user', text);
    inputField.value = '';

    // Agregar indicador de escritura
    const typingDiv = document.createElement('div');
    typingDiv.className = 'msg-bubble bot';
    typingDiv.style.opacity = '0.7';
    typingDiv.innerText = 'Escribiendo...';
    typingDiv.id = 'chatWidgetTyping';
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Llamar al endpoint del Backend
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: text,
                history: getChatHistory()
            })
        });

        // Eliminar indicador de escritura
        const tIndicator = document.getElementById('chatWidgetTyping');
        if (tIndicator) tIndicator.remove();

        if (response.ok) {
            const data = await response.json();
            appendMessage('bot', data.response);
        } else {
            appendMessage('bot', 'Lo siento, no he podido procesar tu solicitud en este momento. Por favor, vuelve a intentarlo más tarde.');
        }
    } catch (error) {
        console.error('Error en fetch chat widget:', error);
        const tIndicator = document.getElementById('chatWidgetTyping');
        if (tIndicator) tIndicator.remove();
        appendMessage('bot', 'Ha ocurrido un error de conexión con el asistente virtual de ALDIMI.');
    }
}

// Auxiliar para inyectar mensajes
function appendMessage(sender, messageText) {
    const messagesContainer = document.getElementById('chatBoxMessages');
    const msgDiv = document.createElement('div');
    msgDiv.className = `msg-bubble ${sender}`;
    msgDiv.innerText = messageText;
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Obtener historial conversacional en formato de API
function getChatHistory() {
    const messagesContainer = document.getElementById('chatBoxMessages');
    const bubbles = messagesContainer.querySelectorAll('.msg-bubble');
    const history = [];
    
    // Filtrar los últimos 10 mensajes para no sobrecargar el RAG
    const startIdx = Math.max(0, bubbles.length - 10);
    
    for (let i = startIdx; i < bubbles.length; i++) {
        const bubble = bubbles[i];
        if (bubble.id === 'chatWidgetTyping') continue;
        
        const isUser = bubble.classList.contains('user');
        // Almacenar según el formato esperado por el backend
        history.push({
            role: isUser ? 'user' : 'assistant',
            content: bubble.innerText
        });
    }
    
    return history;
}
