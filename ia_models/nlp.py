from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import os
from dotenv import load_dotenv

load_dotenv()

class AldimiChatbot:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.system_prompt = """
        Eres el asistente virtual de ALDIMI, un albergue para niños. 
        Tu objetivo es ayudar a voluntarios y padres de familia con información sobre el reglamento y cuidados.
        
        REGLAMENTO INTERNO (FAQs):
        1. Horario de visitas: Lunes a Viernes de 10:00 AM a 4:00 PM.
        2. Registro: Todos los visitantes deben registrarse en recepción con su DNI.
        3. Higiene: Es obligatorio el uso de alcohol en gel al ingresar.
        4. Donaciones: Se aceptan víveres no perecederos y ropa en buen estado.
        
        Además, debes estar atento a señales de riesgo psicosocial en los comentarios sobre la evolución de los niños.
        Si detectas palabras de tristeza profunda, agresión o abandono, márcalo como alerta.
        """

    def get_response(self, user_message, history=[]):
        messages = [SystemMessage(content=self.system_prompt)]
        
        # Agregar historial para manejo de contexto (RF-IAN-03)
        for msg in history:
            if msg['role'] == 'user':
                messages.append(HumanMessage(content=msg['content']))
            else:
                messages.append(AIMessage(content=msg['content']))
        
        messages.append(HumanMessage(content=user_message))
        
        response = self.llm.invoke(messages)
        return response.content

    def analyze_sentiment(self, text):
        """
        Análisis simple de riesgo psicosocial (RF-IAN-04).
        """
        # Esto podría ser una llamada al LLM específica, pero por ahora usaremos lógica de palabras clave
        # o una llamada rápida al LLM.
        prompt = f"Analiza si el siguiente texto sobre un niño indica un riesgo psicosocial (tristeza, agresión, abandono). Responde solo con 'ALERTA' o 'NORMAL': {text}"
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip().upper()

chatbot = AldimiChatbot()
