import os
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from dotenv import load_dotenv

load_dotenv()

class AldimiChatbot:
    def __init__(self):
        # Configuración de Ollama (IA Local)
        # Timeout corto de 2 segundos para evitar retrasos si no está activo
        self.llm = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3"),
            base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            timeout=2.0
        )
        
        self.system_prompt = """
        Eres el asistente virtual de ALDIMI, un albergue que brinda alojamiento, alimentación y soporte emocional a niños con cáncer y sus familias.
        Responde las preguntas de manera clara, amable, empática y en ESPAÑOL.
        Utiliza el contexto provisto del reglamento para responder.
        """
        
        # Ruta de reglamento normativo de ALDIMI
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.reglamento_path = os.path.abspath(os.path.join(current_dir, "..", "datos", "nlp", "reglamento_aldimi.txt"))
        self.corpus_paragraphs = []
        self.vectorizer = None
        self.corpus_tfidf = None
        
        self.load_knowledge_base()

    def load_knowledge_base(self):
        """Carga y vectoriza los párrafos del reglamento de ALDIMI (Hito 7)."""
        if not os.path.exists(self.reglamento_path):
            print(f"Advertencia: No se encontró el reglamento en {self.reglamento_path}")
            return
            
        try:
            with open(self.reglamento_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.corpus_paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
            
            if self.corpus_paragraphs:
                self.vectorizer = TfidfVectorizer()
                self.corpus_tfidf = self.vectorizer.fit_transform(self.corpus_paragraphs)
                print(f"Reglamento ALDIMI indexado para búsqueda semántica: {len(self.corpus_paragraphs)} párrafos.")
        except Exception as e:
            print(f"Error al indexar reglamento ALDIMI: {e}")

    def retrieve_context(self, query: str):
        """
        Busca el párrafo más relevante usando similitud del coseno sobre TF-IDF 
        con boosting basado en palabras clave para garantizar la precisión (Hito 10).
        """
        if not self.corpus_paragraphs or self.vectorizer is None:
            return None, 0.0
            
        try:
            # 1. Similitud de coseno base
            query_tfidf = self.vectorizer.transform([query])
            similarities = cosine_similarity(query_tfidf, self.corpus_tfidf)[0].copy()
            
            # 2. Lógica de Keyword Boosting
            query_clean = re.sub(r'[^\w\s]', '', query.lower())
            words = query_clean.split()
            
            boosts = {
                0: ["direccion", "dirección", "ubicacion", "ubicación", "donde", "dónde", "queda", "mision", "misión", "surquillo", "kandinsky"],
                1: ["suministros", "inventario", "pañales", "pediasure", "leche", "insumos", "víveres", "viveres", "comida", "alimentos", "donar", "necesita"],
                2: ["campaña", "campana", "corazon", "corazón", "proyecto", "camas", "neutropenia", "expansion", "expansión"],
                3: ["admision", "admisión", "ingresar", "ingreso", "requisitos", "admitir", "documentacion", "documentación", "entrar", "perfil"],
                4: ["visita", "visitas", "horario", "horarios", "sábado", "sabado", "domingo", "tarde", "semana"],
                5: ["comida", "comidas", "desayuno", "almuerzo", "cena", "servir", "comedor", "7"]
            }
            
            for idx, keywords in boosts.items():
                if idx < len(similarities):
                    match_count = sum(1 for w in words if w in keywords)
                    if match_count > 0:
                        similarities[idx] += 0.35 * match_count  # boost por coincidencia
            
            best_idx = np.argmax(similarities)
            best_score = similarities[best_idx]
            
            return self.corpus_paragraphs[best_idx], best_score
        except Exception as e:
            print(f"Error en recuperación semántica con boosting: {e}")
            return None, 0.0

    def get_response(self, user_message: str, history=[]):
        """
        Genera la respuesta del chatbot por RAG (Búsqueda semántica + Ollama).
        Cuenta con plan de contingencia offline.
        """
        # 1. Recuperación semántica
        context, score = self.retrieve_context(user_message)
        
        # Umbral mínimo de coincidencia semántica
        threshold = 0.15
        if context is None or score < threshold:
            return "Lo siento, como asistente inteligente de ALDIMI solo tengo información sobre nuestros protocolos institucionales, admisión, suministros, campañas y horarios. Por favor, formula una pregunta relacionada a nuestras políticas."

        # 2. Generación aumentada por recuperación (RAG)
        prompt_rag = f"""
        Utiliza el siguiente fragmento de información oficial del reglamento para responder la pregunta del usuario. 
        Si no encuentras la respuesta en el fragmento provisto, responde de forma neutra y cortés que no tienes información exacta sobre ello.

        Fragmento del reglamento:
        "{context}"

        Pregunta: "{user_message}"
        """
        
        messages = [SystemMessage(content=self.system_prompt)]
        
        # Inyectar historial de conversación (Manejo de Contexto - RF-IAN-03)
        for msg in history:
            role = msg.get('role')
            content = msg.get('content')
            if role == 'user':
                messages.append(HumanMessage(content=content))
            elif role in ['bot', 'assistant']:
                messages.append(AIMessage(content=content))
                
        messages.append(HumanMessage(content=prompt_rag))
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            # Fallback offline: devolver el contexto oficial directamente
            print(f"Ollama no disponible ({e}). Fallback a búsqueda semántica pura.")
            return f"{context} (Nota: Esta información es un extracto directo del reglamento oficial de ALDIMI)."

    def analyze_sentiment(self, text: str):
        """
        Analiza el riesgo psicosocial del texto de forma híbrida:
        Heurística de diccionario (TB) + Análisis cognitivo de Ollama (si está activo).
        """
        texto_lower = text.lower()
        
        # Categorías del TB para riesgos psicosociales
        categorias = {
            "Ideación Suicida": ["mató", "mato", "matar", "morir", "suicid", "no seguir", "quitarse la vida", "fin a mi vida"],
            "Tristeza / Depresión": ["lloró", "lloro", "llorar", "triste", "pena", "deprim", "lament", "sufriendo", "llorando"],
            "Aislamiento": ["encerrado", "encerro", "rechazó", "rechazo", "no participó", "no habla", "solo", "aislado"],
            "Alimentación": ["no comió", "no comio", "sin apetito", "rechazó comida", "no quiere comer"]
        }
        
        indicadores = []
        contador_otras_categorias = 0
        ideacion_detectada = False
        
        for categoria, palabras in categorias.items():
            for palabra in palabras:
                if palabra in texto_lower:
                    item = f"'{palabra}'"
                    if item not in indicadores:
                        indicadores.append(item)
                        if categoria == "Ideación Suicida":
                            ideacion_detectada = True
                        else:
                            contador_otras_categorias += 1

        # Análisis cognitivo Ollama
        ollama_alert = False
        try:
            prompt_risk = f"Analiza si el siguiente reporte sobre la evolución de un niño indica un riesgo psicosocial (tristeza extrema, aislamiento, agresión, ideación suicida, abandono). Responde con la palabra 'ALERTA' o 'NORMAL': {text}"
            response = self.llm.invoke([HumanMessage(content=prompt_risk)])
            res_val = response.content.strip().upper()
            if "ALERTA" in res_val:
                ollama_alert = True
                print("Alerta psicosocial detectada por análisis cognitivo de Ollama.")
        except Exception as e:
            print(f"Ollama no disponible para análisis de sentimiento ({e}).")

        # Regla de decisión para alertas psicosociales (HU04 / RF-IAN-04)
        if ideacion_detectada or contador_otras_categorias >= 2 or ollama_alert:
            return "ALERTA"
            
        return "NORMAL"

chatbot = AldimiChatbot()
