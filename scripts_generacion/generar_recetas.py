from PIL import Image, ImageDraw, ImageFont
import random
import os
import json
from datetime import datetime, timedelta

# --- DATOS FICTICIOS PARA RECETAS MÉDICAS ---
doctores = [
    "Dr. Armando Mendoza - CMP 12345",
    "Dra. Beatriz Pinzon - CMP 54321",
    "Dr. Hugo Lombardi - CMP 98765",
    "Dra. Marcela Valencia - CMP 56789",
    "Dr. Carlos Rojas - CMP 11223"
]

diagnosticos = [
    "Faringitis aguda", "Bronquitis leve", "Gastroenteritis", "Migrana",
    "Amigdalitis", "Conjuntivitis", "Dermatitis", "Infeccion Urinaria",
    "Resfriado Comun", "Sinusitis aguda", "Asma bronquial"
]

medicamentos_db = [
    "Paracetamol 500mg - 1 tableta cada 8 horas por 5 dias.",
    "Amoxicilina 500mg - 1 capsula cada 8 horas por 7 dias.",
    "Ibuprofeno 400mg - 1 tableta cada 8 horas si hay dolor.",
    "Loratadina 10mg - 1 tableta al dia por 5 dias.",
    "Azitromicina 500mg - 1 tableta diaria por 3 dias.",
    "Omeprazol 20mg - 1 capsula en ayunas por 14 dias.",
    "Ciprofloxacino 500mg - 1 tableta cada 12 horas por 5 dias.",
    "Diclofenaco 50mg - 1 tableta cada 8 horas por 3 dias.",
    "Salbutamol Inhalador - 2 puff cada 8 horas.",
    "Clorfenamina 4mg - 1 tableta cada 8 horas."
]

def generar_fecha_aleatoria(year_start=2024, year_end=2026):
    start_date = datetime(year_start, 1, 1)
    end_date = datetime(year_end, 12, 31)
    delta = end_date - start_date
    random_days = random.randrange(delta.days)
    return (start_date + timedelta(days=random_days)).strftime("%d/%m/%Y")

def generar_receta_detallada(nombre_archivo, correlativo, nombre_paciente, edad_paciente):
    # 1. Configuración del lienzo
    ancho, alto = 600, 850
    img = Image.new('RGB', (ancho, alto), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    def get_windows_font(font_name, size):
        paths = [
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", font_name),
            font_name
        ]
        for p in paths:
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
        return ImageFont.load_default()

    font_titulo = get_windows_font("arialbd.ttf", 24)
    font_sub = get_windows_font("arialbd.ttf", 16)
    font_texto = get_windows_font("arial.ttf", 14)
    font_datos = get_windows_font("arial.ttf", 16)
    font_doctor = get_windows_font("cour.ttf", 16)

    # --- ESTRUCTURA VISUAL (PLANTILLA DIBUJADA EN VIVO) ---
    # Borde principal
    draw.rectangle([15, 15, 585, 835], outline="darkblue", width=2)
    
    # Encabezado
    draw.text((120, 30), "CLÍNICA SAN JUAN BAUTISTA", font=font_titulo, fill="darkblue") 
    draw.text((150, 60), "Av. Salud 123, Lima | Tel: (01) 555-1234", font=font_texto, fill="black")
    draw.line((30, 90, 570, 90), fill="darkblue", width=2)

    # Título Receta
    draw.text((200, 110), "RECETA MÉDICA", font=font_titulo, fill="darkred")
    draw.text((450, 115), f"N° {1000 + correlativo}", font=font_sub, fill="darkred")

    # Etiquetas del paciente
    draw.text((40, 160), "Paciente:", font=font_sub, fill="black")
    draw.line((120, 182, 420, 182), fill="black", width=1)
    
    draw.text((440, 160), "Edad:", font=font_sub, fill="black")
    draw.line((490, 182, 560, 182), fill="black", width=1)
    
    draw.text((40, 200), "Fecha:", font=font_sub, fill="black")
    draw.line((100, 222, 220, 222), fill="black", width=1)

    draw.text((40, 240), "Diagnóstico:", font=font_sub, fill="black")
    draw.line((140, 262, 560, 262), fill="black", width=1)

    draw.text((40, 300), "Rp./", font=font_titulo, fill="black")

    # Líneas para recetas
    y_offset = 370
    for _ in range(4):
        draw.line((60, y_offset, 560, y_offset), fill="gray", width=1)
        y_offset += 60

    # Firma y pie
    draw.line((330, 750, 550, 750), fill="black", width=1)
    draw.text((390, 760), "Firma y Sello", font=font_texto, fill="black")
    
    draw.line((30, 800, 570, 800), fill="darkblue", width=2)
    draw.text((130, 810), "Atención todos los días - Emergencias 24h", font=font_sub, fill="darkblue")

    # --- INSERTAR DATOS ---
    fecha = generar_fecha_aleatoria()
    diagnostico = random.choice(diagnosticos)
    doctor = random.choice(doctores)

    # Posicionar texto encima de las líneas dibujadas
    draw.text((130, 160), nombre_paciente, fill="darkblue", font=font_datos)
    draw.text((500, 160), edad_paciente, fill="darkblue", font=font_datos)
    draw.text((110, 200), fecha, fill="darkblue", font=font_datos)
    draw.text((150, 240), diagnostico, fill="darkblue", font=font_datos)

    # Insertar medicamentos en las líneas
    num_meds = random.randint(1, 4)
    meds_recetados = random.sample(medicamentos_db, num_meds)
    
    y_med = 340
    for i, med in enumerate(meds_recetados):
        draw.text((70, y_med), f"{i+1}. {med}", fill="darkblue", font=font_datos)
        y_med += 60

    # Insertar sello del doctor
    draw.text((310, 730), doctor, fill="darkblue", font=font_doctor)

    # Guardar
    img.save(nombre_archivo, "JPEG", quality=95)
    print(f"Documento generado: {nombre_archivo}")

# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    ruta_json = "./datos/identidades.json"
    if not os.path.exists(ruta_json):
        print(f"Error: No se encontró el archivo {ruta_json}. Ejecuta generar_identidades.py primero.")
        exit(1)
        
    with open(ruta_json, "r", encoding="utf-8") as f:
        familias = json.load(f)
        
    random.shuffle(familias)
    split_index = int(len(familias) * 0.8)

    print(f"Generando {len(familias)} recetas (split 80/20)...")
    for i, familia in enumerate(familias):
        carpeta_base = "train" if i < split_index else "val"
        ruta_carpeta = f"./datos/clasificador/{carpeta_base}/recetas_medicas"
        os.makedirs(ruta_carpeta, exist_ok=True)
        
        menor = familia["menor"]
        nombre_completo = f"{menor['ape1']} {menor['ape2']}, {menor['nombres']}"
        
        # Calcular edad aproximada asumiendo año base 2026
        fecha_nac = menor["fecha_nacimiento"]
        ano_nac = int(fecha_nac.split()[2])
        edad_aprox = max(1, 2026 - ano_nac)
        
        nombre_archivo = f"{ruta_carpeta}/receta_{i:03d}.jpg"
        generar_receta_detallada(nombre_archivo, i+1, nombre_completo, f"{edad_aprox} años")
    
    print(f"Completado. Se generaron {len(familias)} recetas en total.")