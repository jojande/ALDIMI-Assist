import os
import random
import json
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

COORDENADAS = {
 "azul" : {
 'ape1': (125, 60),
 'ape2': (125, 87),
 'nom': (125, 116),
 'nacimiento': (125, 140),
 'ubigeo': (214, 140),
 'sexo': (136, 167),
 'estado_civil': (230, 167),
 'dni': (345, 30),
 'cui': (21, 169),
 'fecha_inscripcion': (330, 66),
 'fecha_emision': (332, 100),
 'fecha_caducidad': (331, 139),
 'mrz1': (20, 195),
 'mrz2': (20, 218),
 'mrz3': (19, 239)
 },
 "amarillo" : {
 'ape1': (116, 48),
 'ape2': (115, 83),
 'nom': (114, 116),
 'nacimiento': (113, 142),
 'ubigeo': (200, 143),
 'sexo': (121, 165),
 'dni': (348, 16),
 'cui': (8, 170),
 'fecha_inscripcion': (362, 47),
 'fecha_emision': (363, 73),
 'fecha_caducidad': (362, 102),
 'mrz1': (18, 203),
 'mrz2': (18, 227),
 'mrz3': (17, 250)
 },
 "electronico" : {
 'cui': (27, 74),
 'ape1': (133, 68),
 'ape2': (134, 103),
 'nom': (135, 130),
 'sexo': (133, 166),
 'estado_civil': (228, 164),
 'nacimiento': (135, 185),
 'ubigeo': (229, 185),
 'fecha_emision': (134, 209),
 'fecha_caducidad': (228, 207),
 'grupo_votacion': (134, 232),
 'donacion_organos': (231, 232)
 },
}

def calcular_digito_mrz(cadena):
    pesos = [7, 3, 1]
    total = 0
    for i, char in enumerate(cadena):
        if char == '<':
            val = 0
        elif char.isdigit():
            val = int(char)
        elif char.isalpha():
            val = ord(char.upper()) - 55
        else:
            val = 0
        total += val * pesos[i % 3]
    return str(total % 10)

def generar_fecha_aleatoria(start_year, end_year):
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_date = start_date + timedelta(days=random_number_of_days)
    return random_date.strftime("%d %m %Y")

def generar_dataset_dni(ruta_plantilla, tipo_dni, datos, nombre_salida, ruta_carpeta):
    try:
        img = Image.open(ruta_plantilla)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        draw = ImageDraw.Draw(img)
        
        # Ajuste de fuentes
        try:
            font_datos = ImageFont.truetype("arial.ttf", 14)
            font_dni = ImageFont.truetype("arialbd.ttf", 16)
            font_mrz = ImageFont.truetype("cour.ttf", 16) # Courier para MRZ
        except:
            font_datos = ImageFont.load_default()
            font_dni = ImageFont.load_default()
            font_mrz = ImageFont.load_default()

        coords = COORDENADAS[tipo_dni]

       
        estilos = {
            'ape1': ('black', font_datos),
            'ape2': ('black', font_datos),
            'nom': ('black', font_datos),
            'nacimiento': ('black', font_datos),
            'ubigeo': ('black', font_datos),
            'sexo': ('black', font_datos),
            'estado_civil': ('black', font_datos),
            'cui': ('black', font_dni if tipo_dni == 'electronico' else font_datos),
            'dni': ((200, 0, 0), font_dni),
            'fecha_inscripcion': ('black', font_datos),
            'fecha_emision': ('black', font_datos),
            'fecha_caducidad': ((200, 0, 0) if tipo_dni == 'electronico' else 'black', font_datos),
            'grupo_votacion': ('black', font_datos),
            'donacion_organos': ('black', font_datos),
            'mrz1': ('black', font_mrz),
            'mrz2': ('black', font_mrz),
            'mrz3': ('black', font_mrz)
        }

        # Aplicar coordenadas y dibujado dinámico
        for campo, coord in coords.items():
            if campo in datos and campo in estilos:
                color, fuente = estilos[campo]
                x, y = coord
                y_ajustado = y - 4
                draw.text((x, y_ajustado), str(datos[campo]), font=fuente, fill=color)

        os.makedirs(ruta_carpeta, exist_ok=True)
        ruta_final = os.path.join(ruta_carpeta, f"{nombre_salida}.jpg")
        img.save(ruta_final, "JPEG", quality=95)
    except Exception as e:
        print(f"Error en {nombre_salida}: {e}")

plantillas = {
    "azul": "plantillas/dni/p_dniaz.png",
    "electronico": "plantillas/dni/p_dnie.png",
    "amarillo": "plantillas/dni/p_dniam.png"
}

tipos = ["azul", "electronico", "amarillo"]
estados_civiles = ["SOLTERO", "CASADO", "VIUDO", "DIVORCIADO"]

def crear_datos_dni(persona, fecha_insc, fecha_emi):
    tipo_dni = persona["tipo_dni"]
    dni_num = persona["dni"]
    nom = persona["nombres"]
    ape1 = persona["ape1"]
    ape2 = persona["ape2"]
    sexo = persona["sexo"]
    ubigeo = persona["ubigeo"]
    fecha_nac = persona["fecha_nacimiento"]

    fecha_emi_obj = datetime.strptime(fecha_emi, "%d %m %Y")
    fecha_cad_obj = fecha_emi_obj + timedelta(days=8*365)
    fecha_cad = fecha_cad_obj.strftime("%d %m %Y")
    
    fecha_nac_obj = datetime.strptime(fecha_nac, "%d %m %Y")
    nac_yymmdd = fecha_nac_obj.strftime("%y%m%d")
    cad_yymmdd = fecha_cad_obj.strftime("%y%m%d")

    check_dni = calcular_digito_mrz(dni_num)
    check_nac = calcular_digito_mrz(nac_yymmdd)
    check_cad = calcular_digito_mrz(cad_yymmdd)
    
    mrz_line1 = f"I<PER{dni_num}<{check_dni}".ljust(30, '<')
    
    mrz_line2_base = f"{nac_yymmdd}{check_nac}{sexo}{cad_yymmdd}{check_cad}PER"
    final_check_str = dni_num + check_dni + nac_yymmdd + check_nac + cad_yymmdd + check_cad
    final_check = calcular_digito_mrz(final_check_str)
    mrz_line2 = f"{mrz_line2_base}".ljust(29, '<') + final_check
    
    mrz_line3 = f"{ape1}<<{nom}".ljust(30, '<')

    return {
        'ape1': ape1,
        'ape2': ape2,
        'nom': nom,
        'nacimiento': fecha_nac,
        'ubigeo': ubigeo,
        'sexo': sexo,
        'estado_civil': random.choice(estados_civiles) if tipo_dni != "amarillo" else "",
        'cui': f"{dni_num} - {check_dni}" if tipo_dni == "electronico" else dni_num,
        'grupo_votacion': str(random.randint(100000, 999999)),
        'donacion_organos': random.choice(["SI", "NO"]),
        'fecha_inscripcion': fecha_insc,
        'fecha_emision': fecha_emi,
        'fecha_caducidad': fecha_cad,
        'dni': f"{dni_num} - {check_dni}",
        'mrz1': mrz_line1,
        'mrz2': mrz_line2,
        'mrz3': mrz_line3
    }

if __name__ == "__main__":
    ruta_json = "./datos/identidades.json"
    if not os.path.exists(ruta_json):
        print(f"Error: No se encontró el archivo {ruta_json}. Ejecuta generar_identidades.py primero.")
        exit(1)
        
    with open(ruta_json, "r", encoding="utf-8") as f:
        familias = json.load(f)
        
    random.shuffle(familias)
    split_index = int(len(familias) * 0.8)
    
    print(f"Generando DNIs para {len(familias)} familias...")
    for i, familia in enumerate(familias):
        carpeta_base = "train" if i < split_index else "val"
        
        # 1. Adulto
        adulto = familia["adulto"]
        tipo_adulto = adulto["tipo_dni"]
        datos_adulto = crear_datos_dni(
            adulto,
            fecha_insc=generar_fecha_aleatoria(2010, 2018),
            fecha_emi=generar_fecha_aleatoria(2018, 2024)
        )
        ruta_adulto = f"./datos/clasificador/{carpeta_base}/dni_adulto"
        generar_dataset_dni(plantillas[tipo_adulto], tipo_adulto, datos_adulto, f"dni_{tipo_adulto}_padre_{i:03d}", ruta_adulto)
        
        # 2. Menor
        menor = familia["menor"]
        tipo_nino = menor["tipo_dni"]
        datos_nino = crear_datos_dni(
            menor,
            fecha_insc=generar_fecha_aleatoria(2015, 2024),
            fecha_emi=generar_fecha_aleatoria(2020, 2024)
        )
        ruta_menor = f"./datos/clasificador/{carpeta_base}/dni_menor"
        generar_dataset_dni(plantillas[tipo_nino], tipo_nino, datos_nino, f"dni_{tipo_nino}_hijo_{i:03d}", ruta_menor)
        
    print(f"Completado. Se generaron {len(familias)*2} imágenes de DNI (split 80/20).")