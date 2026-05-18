import cv2
import pytesseract
import os
from dotenv import load_dotenv

load_dotenv()

# Configurar ruta de Tesseract si está en el .env
tesseract_cmd = os.getenv("TESSERACT_CMD")
if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

def preprocess_image(image_path):
    """
    Preprocesamiento básico para mejorar el OCR (RF-IAV-03).
    """
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    # Convertir a escala de grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Aplicar umbralizado para binarizar la imagen
    # Usamos el método de Otsu para determinar el umbral automáticamente
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    # Opcional: Reducción de ruido
    # denoise = cv2.medianBlur(thresh, 3)
    
    return thresh

def extract_text(image_path):
    """
    Extrae texto de una imagen usando Tesseract (RF-IAV-01).
    """
    preprocessed_img = preprocess_image(image_path)
    if preprocessed_img is None:
        return ""
    
    # Extraer texto indicando idioma español
    text = pytesseract.image_to_string(preprocessed_img, lang='spa')
    return text.strip()

def classify_document(text):
    """
    Clasifica el tipo de documento basándose en palabras clave (RF-IAV-02).
    """
    text_lower = text.lower()
    
    if "dni" in text_lower or "identidad" in text_lower or "nacimiento" in text_lower:
        return "DNI"
    elif "receta" in text_lower or "médica" in text_lower or "doctor" in text_lower or "paciente" in text_lower:
        return "RECETA"
    elif "boleta" in text_lower or "donación" in text_lower or "monto" in text_lower or "recibo" in text_lower:
        return "BOLETA"
    else:
        return "OTRO"
