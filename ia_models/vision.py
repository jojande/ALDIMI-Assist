import os
import cv2
import easyocr
import json
import re
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

# Global references for cached loading
_classifier = None
_ocr_pipeline = None

class DocumentClassifier:
    def __init__(self, pesos_path=None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.class_names = ['dni_adulto', 'dni_menor', 'recetas_medicas', 'recibos_donaciones']
        
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        # Configurar arquitectura MobileNetV3-Small
        self.model = models.mobilenet_v3_small(weights=None)
        num_features = self.model.classifier[3].in_features
        self.model.classifier[3] = nn.Linear(num_features, len(self.class_names))
        
        if pesos_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            pesos_path = os.path.join(current_dir, "pesos", "document_classifier.pth")
            
        if os.path.exists(pesos_path):
            self.model.load_state_dict(torch.load(pesos_path, map_location=self.device))
            print(f"pesos de clasificador MobileNetV3 cargados exitosamente de: {pesos_path}")
        else:
            print(f"Advertencia: No se encontraron pesos en {pesos_path}. El modelo usará pesos aleatorios.")
            
        self.model = self.model.to(self.device)
        self.model.eval()

    def classify(self, image_path):
        try:
            img = Image.open(image_path).convert('RGB')
            img_tensor = self.transform(img).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                outputs = self.model(img_tensor)
                _, preds = torch.max(outputs, 1)
                predicted_idx = preds.item()
                return self.class_names[predicted_idx]
        except Exception as e:
            print(f"Error al clasificar documento {image_path}: {e}")
            return "OTRO"


class ALDIMIOcrPipeline:
    def __init__(self):
        print("Cargando modelo EasyOCR (Español) en GPU/CPU...")
        # verbose=False para evitar problemas de codificación de consola en Windows
        self.reader = easyocr.Reader(['es'], gpu=torch.cuda.is_available(), verbose=False)

    def preprocess_image(self, image_path):
        """
        Aplica CLAHE y Filtro Bilateral en OpenCV para robustecer el OCR.
        """
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"No se pudo abrir la imagen: {image_path}")

        # 1. Escala de grises
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. CLAHE (Ecualización adaptativa de histograma)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(gray)

        # 3. Filtro Bilateral para remover ruido preservando bordes
        processed_img = cv2.bilateralFilter(cl, 9, 75, 75)
        
        return processed_img

    def extract_document_data(self, image_path, doc_type):
        """
        Extrae texto de la imagen y aplica el parser correspondiente.
        """
        img_prep = self.preprocess_image(image_path)
        raw_results = self.reader.readtext(img_prep, detail=1, paragraph=False)
        
        raw_lines = [item[1] for item in raw_results]
        text_joined = " ".join(raw_lines).upper()
        
        # Mapear las clases del clasificador de MobileNet a las del parser
        if doc_type in ['dni_menor', 'dni_adulto', 'DNI']:
            structured_data = self._parse_dni(raw_results, raw_lines, text_joined)
        elif doc_type in ['receta_medica', 'recetas_medicas', 'RECETA']:
            structured_data = self._parse_receta(raw_lines, text_joined)
        elif doc_type in ['recibo_donacion', 'recibos_donaciones', 'BOLETA']:
            structured_data = self._parse_recibo(raw_lines, text_joined)
        else:
            structured_data = {"error": f"Tipo desconocido: {doc_type}", "raw_text": raw_lines}
            
        return structured_data

    def _parse_dni(self, raw_results, raw_lines, text_joined):
        data = {
            "documento": "DNI",
            "apellidos": "",
            "nombres": "",
            "cui_dni": "",
            "raw_lines": raw_lines
        }
        
        # 1. CUI: 8 dígitos
        cui_encontrado = ""
        for item in raw_results:
            t = item[1].strip()
            if re.match(r'^\d{8}\s*$', t):
                cui_encontrado = re.search(r'\d{8}', t).group(0)
                break
        if not cui_encontrado:
            for item in raw_results:
                t = item[1].strip()
                if re.match(r'^\d{8}', t):
                    cui_encontrado = re.search(r'\d{8}', t).group(0)
                    break
        if not cui_encontrado:
            lineas_limpias = [item[1] for item in raw_results if not item[1].strip().startswith(('{', '[', '~'))]
            m = re.search(r'\b(\d{8})\b', " ".join(lineas_limpias))
            if m:
                cui_encontrado = m.group(1)
        data["cui_dni"] = cui_encontrado

        # 2. MRZ
        mrz_nombre_linea = None
        for item in raw_results:
            t = item[1].upper().replace(" ", "")
            if "<" in t and re.search(r'[A-ZÁÉÍÓÚÑ]{3,}', t):
                if not re.match(r'^[A-Z]{1,2}\d', t):
                    mrz_nombre_linea = t
        
        if mrz_nombre_linea:
            mrz_clean = re.sub(r'[^A-ZÁÉÍÓÚÑ<]', '', mrz_nombre_linea)
            partes = [p for p in re.split(r'<+', mrz_clean) if len(p) >= 2]
            partes = [re.sub(r'S{3,}$', '', p) for p in partes]
            partes = [p for p in partes if len(p) >= 2]
            
            def mrz_valida(partes):
                if len(partes) < 2: return False
                for p in partes:
                    if re.search(r'SS$|SS\w+$', p): return False
                    if len(p) > 15: return False
                return True
            
            if mrz_valida(partes):
                if len(partes) >= 3:
                    data["apellidos"] = f"{partes[0]} {partes[1]}"
                    data["nombres"] = " ".join(partes[2:])
                    return data
                elif len(partes) == 2:
                    data["apellidos"] = partes[0]
                    data["nombres"] = partes[1]
                    return data

        # 3. Etiquetas Fuzzy
        LABEL_KW = {
            "ape1": ["PRIMER", "PRMOR", "PRMER", "RIMOR", "APELL", "APEL"],
            "ape2": ["SEGUNDO", "SOXUND", "SEGUND", "SGUNDO", "APOLLD"],
            "nom":  ["NOMBRE", "PRENOMB", "PRE NOM", "NOMBRES", "PRE NOMBRES"],
        }
        LABEL_NOISE = re.compile(
            r'^(PRIMER|PRMOR|PRMER|SEGUNDO|SOXUND|SEGUND|APOLLD|NOMBRE|PRENOMB|NOMBRES'
            r'|APELL|APEL|UBIG|FOCHA|FOCHD|EMLE|CADUCI|CLVL|SEXA|KACIM|UBLGO|FIRMA)$',
            re.IGNORECASE
        )

        def _extraer_siguiente_valido(start_idx, lineas):
            for j in range(start_idx, min(start_idx + 4, len(lineas))):
                raw = lineas[j]
                candidato = re.sub(r'[^A-ZÁÉÍÓÚÑ\s]', '', raw.upper()).strip()
                if len(candidato) < 2: continue
                if any(ch.isdigit() for ch in raw): continue
                if LABEL_NOISE.match(candidato.strip()): continue
                if re.search(r'[A-ZÁÉÍÓÚÑ]{3,}', candidato):
                    return candidato
            return ""

        ape1 = ape2 = nom = ""
        for i, line in enumerate(raw_lines):
            lu = line.upper()
            if not ape1 and any(kw in lu for kw in LABEL_KW["ape1"]):
                ape1 = _extraer_siguiente_valido(i + 1, raw_lines)
            if not ape2 and any(kw in lu for kw in LABEL_KW["ape2"]):
                ape2 = _extraer_siguiente_valido(i + 1, raw_lines)
            if not nom and any(kw in lu for kw in LABEL_KW["nom"]):
                nom = _extraer_siguiente_valido(i + 1, raw_lines)

        if ape1 or ape2:
            data["apellidos"] = f"{ape1} {ape2}".strip()
            data["nombres"] = nom
            return data

        # 4. Columnas Geométricas (Fallback)
        if not raw_results: return data
        
        max_x = max([item[0][1][0] for item in raw_results])
        max_y = max([item[0][2][1] for item in raw_results])
        umbral_columna = max_x * 0.15
        margen_superior = max_y * 0.22
        margen_inferior = max_y * 0.70

        PATRON_ETIQUETA = re.compile(
            r'(APOLL|APELLL|SOXUND|PRENOMB|PRMOR|PRMER|UBIG|EMLE|CADUCI'
            r'|CLVLI|FOCHA|FOCHD|UBLGO|KACIM|SEXA|CLVL|ESTADO|FIRMA|HUELL)', 
            re.IGNORECASE
        )
        
        cajas_validas = []
        for item in raw_results:
            bbox, text, prob = item
            text_clean = re.sub(r'[\{\}\[\]]', '', text).strip().upper()
            
            if len(text_clean) < 3: continue
            if any(ch.isdigit() for ch in text_clean): continue
            if "<" in text_clean: continue
            if PATRON_ETIQUETA.search(text_clean): continue
            
            x_min = bbox[0][0]
            y_center = (bbox[0][1] + bbox[2][1]) / 2
            
            if y_center < margen_superior: continue
            if y_center > margen_inferior: continue
            
            texto_puro = re.sub(r'[^A-ZÁÉÍÓÚÑ\s]', '', text_clean).strip()
            if len(texto_puro) < 2: continue
            
            cajas_validas.append({
                "x_min": x_min,
                "y_center": y_center,
                "texto": texto_puro
            })
            
        if not cajas_validas: return data
        
        columnas = []
        for caja in cajas_validas:
            asignado = False
            for col in columnas:
                if abs(caja["x_min"] - col["avg_x"]) < umbral_columna:
                    col["cajas"].append(caja)
                    col["avg_x"] = sum(c["x_min"] for c in col["cajas"]) / len(col["cajas"])
                    asignado = True
                    break
            if not asignado:
                columnas.append({"avg_x": caja["x_min"], "cajas": [caja]})
        
        columna_principal = max(columnas, key=lambda c: len(c["cajas"]))
        textos = [c["texto"] for c in sorted(columna_principal["cajas"], key=lambda c: c["y_center"]) if c["texto"]]
        
        if len(textos) >= 2:
            data["apellidos"] = f"{textos[0]} {textos[1]}"
        if len(textos) >= 3:
            data["nombres"] = textos[2]
        elif len(textos) == 1:
            data["apellidos"] = textos[0]

        return data

    def _parse_receta(self, raw_lines, text_joined):
        data = {
            "documento": "Receta Médica",
            "paciente": "",
            "diagnostico": "",
            "medicamentos": [],
            "raw_lines": raw_lines
        }
        for i, line in enumerate(raw_lines):
            l_u = line.upper()
            if "PACIEN" in l_u:
                paciente_val = re.sub(r'(?i)paciente\s*:?\s*', '', line).strip()
                if not paciente_val and i + 1 < len(raw_lines):
                    paciente_val = raw_lines[i+1].strip()
                paciente_val = re.split(r'(?i)\s+(edad|fecha|diagn|rp)', paciente_val)[0].strip()
                paciente_val = re.sub(r'^[\s_\-\.\,:]+|[\s_\-\.\,:]+$', '', paciente_val).strip()
                paciente_val = re.sub(r'_+', ' ', paciente_val).strip()
                data["paciente"] = paciente_val
                
            if "DIAGN" in l_u or "DX" in l_u:
                diag_val = re.sub(r'(?i)(diagnostico|diagnóstico|dx)\s*:?\s*', '', line).strip()
                if not diag_val and i + 1 < len(raw_lines):
                    diag_val = raw_lines[i+1].strip()
                diag_val = re.split(r'(?i)\s+(fecha|edad|paciente|rp)', diag_val)[0].strip()
                diag_val = re.sub(r'^[\s_\-\.\,:]+|[\s_\-\.\,:]+$', '', diag_val).strip()
                diag_val = re.sub(r'_+', ' ', diag_val).strip()
                data["diagnostico"] = diag_val

        # Extract and merge medications
        rp_idx = -1
        for i, line in enumerate(raw_lines):
            if "RP/" in line.upper():
                rp_idx = i
                break
                
        med_lines = []
        start_idx = rp_idx + 1 if rp_idx != -1 else 0
        for i in range(start_idx, len(raw_lines)):
            line = raw_lines[i].strip()
            l_u = line.upper()
            if any(k in l_u for k in ["FIRMA", "SELLO", "DRA", "DR.", "CMP", "ATENCION", "ATENCIÓN", "EMERGENCIA"]):
                break
            if line:
                med_lines.append(line)
                
        merged_meds = []
        j = 0
        while j < len(med_lines):
            line = med_lines[j]
            l_u = line.upper()
            
            line_clean = re.sub(r'^\d+[\s\.\,\-\/]+', '', line).strip()
            
            if any(u in l_u for u in ["MG", "ML", "G", "CAPS", "TAB", "JARABE", "GOTAS", "%"]):
                if j + 1 < len(med_lines):
                    next_line = med_lines[j+1]
                    next_u = next_line.upper()
                    if not any(u in next_u for u in ["MG", "ML", "CAPS", "TAB"]) or any(k in next_u for k in ["CADA", "POR", "DIA", "HORA", "TABLETA", "CAPSULA", "TOMA"]):
                        line_clean += " - " + next_line
                        j += 1
            merged_meds.append(line_clean)
            j += 1
            
        data["medicamentos"] = merged_meds
        return data

    def _parse_recibo(self, raw_lines, text_joined):
        data = {
            "documento": "Recibo de Donación",
            "nro_recibo": "",
            "donante": "",
            "dni_ruc": "",
            "valoracion": "",
            "raw_lines": raw_lines
        }
        text_j = text_joined.replace("O", "0")
        
        # Nro Recibo
        for line in raw_lines:
            l_u = line.upper()
            if "DONACI" in l_u or "RECIB" in l_u or "N" in l_u:
                match = re.search(r'\d{3,}', l_u.replace("O", "0").replace("o", "0"))
                if match:
                    data["nro_recibo"] = match.group(0)
                    break
                    
        # DNI/RUC
        dni_ruc_val = ""
        for i, line in enumerate(raw_lines):
            l_u = line.upper()
            if "DNI" in l_u or "RUC" in l_u:
                if "ALBERGUE" not in l_u and "20508493021" not in l_u:
                    if i < 6 and "20508493021" in text_j:
                        continue
                    match = re.search(r'\b\d{8,11}\b', l_u)
                    if match and match.group(0) != "20508493021":
                        dni_ruc_val = match.group(0)
                        break
                    elif i + 1 < len(raw_lines):
                        match_next = re.search(r'\b\d{8,11}\b', raw_lines[i+1])
                        if match_next and match_next.group(0) != "20508493021":
                            dni_ruc_val = match_next.group(0)
                            break
        if not dni_ruc_val:
            for m in re.finditer(r'\b\d{8,11}\b', text_j):
                num = m.group(0)
                if num != "20508493021":
                    dni_ruc_val = num
                    break
        data["dni_ruc"] = dni_ruc_val
            
        # Donante
        for i, line in enumerate(raw_lines):
            line_u = line.upper()
            if "NOMBRE" in line_u or "RAZ" in line_u or "SOCIAL" in line_u:
                donante_val = re.sub(r'(?i)(nombre/razón social|nombre/razon social|nombre|razón social|razon social)\s*:?\s*', '', line).strip()
                if not donante_val and i + 1 < len(raw_lines):
                    donante_val = raw_lines[i+1].strip()
                donante_val = re.split(r'(?i)\s+(dirección|direccion|direccin|dni|ruc)', donante_val)[0].strip()
                donante_val = re.sub(r'^[\s_\-\.\,:]+|[\s_\-\.\,:]+$', '', donante_val).strip()
                if "DIRECCION" not in donante_val.upper() and "DIRECCIÓN" not in donante_val.upper() and "DIRECCIN" not in donante_val.upper():
                    data["donante"] = donante_val
                    break
        
        if not data["donante"]:
            for line in raw_lines:
                line_clean = re.sub(r'[^A-ZÁÉÍÓÚÑ\s]', '', line.upper()).strip()
                if len(line_clean) > 8 and not any(kw in line_clean for kw in ["ALBERGUE", "DIVINA", "MISERICORDIA", "RUC", "LIMA", "PERU", "PERÚ", "DONACION", "DONACIÓN", "INFORMACION", "INFORMACIÓN", "DONANTE", "FECHA", "DIRECCION", "DIRECCIÓN", "DETALLES", "SUMINISTROS", "CANTIDAD", "VALORACION", "VALORACIÓN", "ESTIMADA", "METODO", "MÉTODO", "EFECTIVO", "TRANSFERENCIA", "FIRMA", "RECIBIDO"]):
                    data["donante"] = line.strip()
                    break
                    
        # Valoración
        val_text = ""
        for i, line in enumerate(raw_lines):
            l_u = line.upper()
            if "VALORAC" in l_u or "ESTIMAD" in l_u or "TOTAL" in l_u:
                candidate_lines = [line]
                if i + 1 < len(raw_lines):
                    candidate_lines.append(raw_lines[i+1])
                if i + 2 < len(raw_lines):
                    candidate_lines.append(raw_lines[i+2])
                val_text = " ".join(candidate_lines)
                break
        
        if val_text:
            text_to_search = val_text.upper()
            text_to_search = re.sub(r'S/\.?\s*', '', text_to_search)
            text_to_search = re.sub(r'\b(\d+)[\.,\s]?([OouU]{2})\b', r'\1.\2', text_to_search)
            text_to_search = text_to_search.replace("O", "0").replace("U", "0").replace("o", "0").replace("u", "0")
            
            match_val = re.search(r'\d+[\.,]\d{2}', text_to_search)
            if match_val:
                val = match_val.group(0)
                if not re.search(re.escape(val) + r'[\s\*\/\.\,-]?\d{4}', text_to_search):
                    data["valoracion"] = val
            else:
                match_val_fallback = re.search(r'\d{3,}', text_to_search)
                if match_val_fallback:
                    num = match_val_fallback.group(0)
                    if num not in ["2024", "2025", "2026", "2027"]:
                        data["valoracion"] = num
        
        if not data["valoracion"]:
            for m in re.finditer(r'\b\d+[\.,]\d{2}\b', text_joined):
                val = m.group(0)
                if not re.search(re.escape(val) + r'[\s\*\/\.\,-]?\d{4}', text_joined):
                    data["valoracion"] = val
                    break
                    
            if not data["valoracion"]:
                match_val_fallback = re.findall(r'\b\d{3,}\b', text_joined)
                for num in reversed(match_val_fallback):
                    if num != data["dni_ruc"] and num != data["nro_recibo"] and len(num) < 8:
                        if num not in ["2024", "2025", "2026", "2027"]:
                            data["valoracion"] = num
                            break

        # Normalize valuation format
        val_str = data["valoracion"]
        if val_str:
            val_str = re.sub(r'[^\d\.,]', '', val_str)
            if '.' not in val_str and ',' not in val_str:
                if len(val_str) >= 4 and val_str.endswith('00'):
                    val_str = val_str[:-2] + '.' + val_str[-2:]
                else:
                    val_str = val_str + '.00'
            data["valoracion"] = val_str
            
        return data


# --- Helper initialization functions for FastAPI lifespan ---

def init_vision_models():
    """Inicializa la red convolucional y el pipeline de EasyOCR en caché global."""
    global _classifier, _ocr_pipeline
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pesos_path = os.path.join(current_dir, "pesos", "document_classifier.pth")
    
    if _classifier is None:
        _classifier = DocumentClassifier(pesos_path)
    if _ocr_pipeline is None:
        _ocr_pipeline = ALDIMIOcrPipeline()

# --- Functions for FastAPI compatible endpoints ---

def classify_document(image_path: str) -> str:
    """Clasifica el tipo de documento usando MobileNetV3."""
    global _classifier
    if _classifier is None:
        init_vision_models()
    
    predicted_class = _classifier.classify(image_path)
    # Retornar nombres simplificados legibles para el frontend
    if predicted_class in ['dni_adulto', 'dni_menor']:
        return "DNI"
    elif predicted_class == 'recetas_medicas':
        return "RECETA"
    elif predicted_class == 'recibos_donaciones':
        return "BOLETA"
    else:
        return "OTRO"

def extract_text(image_path: str) -> str:
    """Extrae texto plano de la imagen (mantiene compatibilidad de firma con TB original)."""
    global _ocr_pipeline
    if _ocr_pipeline is None:
        init_vision_models()
        
    try:
        img_prep = _ocr_pipeline.preprocess_image(image_path)
        raw_results = _ocr_pipeline.reader.readtext(img_prep, detail=0)
        return "\n".join(raw_results)
    except Exception as e:
        print(f"Error al extraer texto en vision.py: {e}")
        return ""

def extract_document_info(image_path: str, doc_type: str) -> dict:
    """Extrae la información estructurada dependiente del tipo de documento."""
    global _ocr_pipeline
    if _ocr_pipeline is None:
        init_vision_models()
        
    try:
        return _ocr_pipeline.extract_document_data(image_path, doc_type)
    except Exception as e:
        print(f"Error al extraer perfil de documento estructurado: {e}")
        return {"error": str(e)}
