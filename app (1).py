import streamlit as st
import cv2
import numpy as np
from PIL import Image
import time

st.set_page_config(page_title="ALDIMI-Assist MVP", layout="wide")

st.title("🤖 ALDIMI-Assist: Prototipo Funcional v1.0")
st.markdown("---")

tab1, tab2 = st.tabs(["📸 Visión Artificial (OCR)", "💬 Asistente NLP"])

with tab1:
    st.header("Extracción de Datos de Documentos")
    uploaded_file = st.file_uploader("Cargar DNI, Receta o Boleta", type=['png', 'jpg', 'jpeg'])

    col1, col2 = st.columns(2)

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        col1.image(image, caption="Documento Cargado", use_column_width=True)
        
        with col2:
            st.subheader("Resultado del Procesamiento")
            with st.spinner("Ejecutando Pipeline OCR Adaptativo..."):
                time.sleep(2)  # Simulación de proceso
                st.success("Extracción completada en 1.8s")
                
                datos = {
                    "Tipo de Doc": "DNI",
                    "Nombre": "Jesús Andrés Millones",
                    "Prioridad": "CRÍTICA (Leucemia)",
                    "Confianza": "92%"
                }
                st.json(datos)
                st.info("Datos listos para sincronizar con SIGDA")

with tab2:
    st.header("Chatbot de Soporte y Alerta Temprana")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Consulta sobre el reglamento o registra una bitácora"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Lógica de simulación de alertas psicosociales
            if "triste" in prompt.lower() or "no quiero comer" in prompt.lower():
                response = "⚠️ **ALERTA PSICOSOCIAL DETECTADA**: Se ha identificado un sentimiento negativo. Notificando al psicólogo de turno según Regla de Negocio RN-02."
            else:
                response = "Según la Ontología de ALDIMI, los horarios de visita son de 10:00 AM a 4:00 PM. ¿Deseas registrar esto en la bitácora del paciente?"
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})