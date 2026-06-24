from PIL import Image, ImageDraw, ImageFont
import random
import os
import json

def crear_recibo_detallado(nombre_archivo, correlativo, nombre_donante, dni_donante):
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

    font_titulo = get_windows_font("arialbd.ttf", 18)
    font_sub = get_windows_font("arialbd.ttf", 16)
    font_texto = get_windows_font("arial.ttf", 14)
    font_mano = get_windows_font("arialbd.ttf", 16)

    # --- ESTRUCTURA VISUAL ---
    draw.rectangle([15, 15, 585, 835], outline="black", width=2)
    draw.text((40, 40), "ALBERGUE DIVINA MISERICORDIA", font=font_titulo, fill="black") 
    draw.text((40, 70), "(ALDIMI) | RUC: 20508493021 | Lima, Perú", font=font_texto, fill="black")
    
    draw.rectangle([400, 35, 560, 95], outline="red", width=2)
    draw.text((415, 45), "RECIBO DE", font=font_sub, fill="red")
    draw.text((415, 65), f"DONACIÓN N° {1000 + correlativo}", font=font_sub, fill="red")

    # --- CAMPOS DE INFORMACIÓN ---
    draw.text((40, 130), "INFORMACIÓN DEL DONANTE", font=font_sub, fill="black")
    draw.line((40, 150, 560, 150), fill="black", width=1)
    
    campos = [(40, 170, "Fecha:"), (40, 210, "Nombre/Razón Social:"), (40, 250, "Dirección:"), (40, 290, "DNI/RUC:")]
    for x, y, etiqueta in campos:
        draw.text((x, y), etiqueta, font=font_texto, fill="black")
        draw.line((x + 150, y + 22, 560, y + 22), fill="gray", width=1)

    draw.text((40, 350), "DETALLES DE LA DONACIÓN", font=font_sub, fill="black")
    draw.rectangle([40, 380, 560, 550], outline="black", width=1)
    draw.line((40, 410, 560, 410), fill="black", width=1)
    draw.text((50, 390), "Descripción de Suministros", font=font_sub, fill="black")
    draw.text((450, 390), "Cantidad", font=font_sub, fill="black")

    draw.text((40, 580), "VALORACIÓN ESTIMADA: S/.", font=font_sub, fill="black")
    draw.line((260, 595, 420, 595), fill="gray", width=1)
    
    # --- VARIABILIDAD DE DATOS ---
    direcciones = ["Av. Arequipa 1234", "Jr. Huallaga 456", "Calle Las Flores 789", "Av. Javier Prado 2020", "Urb. Los Olivos 111", "Av. El Sol 555"]
    suministros = ["Pañales Talla G", "Leche Pediasure", "Gasas estériles", "Alcohol 70%", "Mascarillas KN95", "Suero Fisiológico", "Paracetamol 500mg", "Guantes de Nitrilo", "Jabón Antibacterial", "Toallas Húmedas", "Algodón 100g", "Jeringas 5ml"]
    metodos = ["[X] Efectivo  [ ] Transferencia  [ ] Suministros", "[ ] Efectivo  [X] Transferencia  [ ] Suministros", "[ ] Efectivo  [ ] Transferencia  [X] Suministros"]

    # --- LLENADO DINÁMICO ---
    fecha = f"{random.randint(1,28):02d}/05/2026"
    draw.text((190, 170), fecha, font=font_mano, fill="blue")
    draw.text((190, 210), nombre_donante, font=font_mano, fill="blue")
    draw.text((190, 250), random.choice(direcciones), font=font_mano, fill="blue")
    draw.text((190, 290), dni_donante, font=font_mano, fill="blue")
    
    # Agregar dos filas de suministros para más realismo
    draw.text((50, 430), random.choice(suministros), font=font_mano, fill="blue")
    draw.text((470, 430), str(random.randint(1, 100)), font=font_mano, fill="blue")
    draw.text((50, 460), random.choice(suministros), font=font_mano, fill="blue")
    draw.text((470, 460), str(random.randint(1, 100)), font=font_mano, fill="blue")
    
    draw.text((280, 580), f"{random.randint(50, 2500)}.00", font=font_mano, fill="blue")
    draw.text((40, 630), f"MÉTODO: {random.choice(metodos)}", font=font_texto, fill="black")

    # --- FIRMAS ---
    draw.line((60, 780, 250, 780), fill="black", width=1)
    draw.text((100, 790), "Firma Donante", font=font_texto, fill="black")
    draw.line((350, 780, 540, 780), fill="black", width=1)
    draw.text((370, 790), "Recibido por ALDIMI", font=font_texto, fill="black")

    img.save(nombre_archivo)

# --- EJECUCIÓN ---
if __name__ == "__main__":
    ruta_json = "./datos/identidades.json"
    if not os.path.exists(ruta_json):
        print(f"Error: No se encontró el archivo {ruta_json}. Ejecuta generar_identidades.py primero.")
        exit(1)
        
    with open(ruta_json, "r", encoding="utf-8") as f:
        familias = json.load(f)
        
    random.shuffle(familias)
    split_index = int(len(familias) * 0.8)

    print(f"Generando {len(familias)} recibos (split 80/20)...")
    for i, familia in enumerate(familias):
        carpeta_base = "train" if i < split_index else "val"
        ruta_carpeta = f"./datos/clasificador/{carpeta_base}/recibos_donaciones"
        os.makedirs(ruta_carpeta, exist_ok=True)
        
        adulto = familia["adulto"]
        nombre_completo = f"{adulto['ape1']} {adulto['ape2']}, {adulto['nombres']}"
        dni = adulto["dni"]
        
        nombre_file = f"{ruta_carpeta}/recibo_donacion_{i+1:03d}.jpg"
        crear_recibo_detallado(nombre_file, i+1, nombre_completo, dni)
        
    print(f"Completado. Se generaron {len(familias)} recibos de donación en total.")