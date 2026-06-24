import json
import random
import os
from datetime import datetime, timedelta

def generar_fecha_aleatoria(year_start, year_end):
    start_date = datetime(year_start, 1, 1)
    end_date = datetime(year_end, 12, 31)
    delta = end_date - start_date
    random_days = random.randrange(delta.days)
    return (start_date + timedelta(days=random_days)).strftime("%d %m %Y")

nombres_ej = [
    "LUCAS", "MATIAS", "NICO", "JOSE", "YEISON", "MARIA", "LUCIA", "ANA", "CARLOS", "JUAN",
    "LUIS", "JORGE", "VICTOR", "MANUEL", "ROSA", "CARMEN", "JULIA", "PEDRO", "MIGUEL", "ANGEL",
    "DIEGO", "ALONSO", "SEBASTIAN", "VALENTINA", "CAMILA", "VALERIA", "DANIELA", "SOFIA", "ISABELLA",
    "GABRIEL", "MATEO", "LEONARDO", "ALEJANDRO", "ANDREA", "MARIANA", "FERNANDA", "PAULA", "DANIEL",
    "JOAQUIN", "EMILIO", "RODRIGO", "ARTURO", "RICARDO", "EDUARDO", "ALBERTO", "ENRIQUE", "RAUL",
    "PABLO", "DAVID", "MARTIN"
]

apellidos_ej = [
    "PERALTA", "TORRES", "MOSTO", "GIBU", "PEREZ", "GARCIA", "LOPEZ", "CHAVEZ", "QUISPE",
    "RODRIGUEZ", "GONZALES", "FLORES", "GOMEZ", "SANCHEZ", "DIAZ", "RAMIREZ", "CRUZ", "MENDOZA",
    "CASTRO", "RUIZ", "MAMANI", "ROJAS", "SILVA", "VILLANUEVA", "ROMERO", "HUAMAN", "CONDORI",
    "RIVERA", "ESPINOZA", "REYES", "ALVAREZ", "FERNANDEZ", "HUANCA", "GUTIERREZ", "SALAZAR",
    "VARGAS", "AGUILAR", "SUAREZ", "CASTILLO", "ORTEGA", "MORALES", "DELGADO", "ORTIZ", "NUNEZ",
    "CORDOVA", "RAMOS", "MEDINA", "VEGA", "PINTO", "PAREDES", "CABRERA"
]

def generar_identidades(cantidad_familias=150):
    familias = []
    
    for _ in range(cantidad_familias):
        apellido_padre = random.choice(apellidos_ej)
        apellido_madre = random.choice(apellidos_ej)
        ubigeo_familiar = str(random.randint(100000, 999999))
        
        # Generar Adulto
        dni_adulto = str(random.randint(10000000, 99999999))
        tipo_adulto = random.choice(["azul", "electronico"])
        adulto = {
            "dni": dni_adulto,
            "nombres": random.choice(nombres_ej),
            "ape1": apellido_padre,
            "ape2": random.choice(apellidos_ej),
            "fecha_nacimiento": generar_fecha_aleatoria(1950, 2005),
            "sexo": "M",
            "ubigeo": ubigeo_familiar,
            "tipo_dni": tipo_adulto
        }
        
        # Generar Menor
        dni_menor = str(random.randint(10000000, 99999999))
        menor = {
            "dni": dni_menor,
            "nombres": random.choice(nombres_ej),
            "ape1": apellido_padre,
            "ape2": apellido_madre,
            "fecha_nacimiento": generar_fecha_aleatoria(2008, 2024),
            "sexo": random.choice(["M", "F"]),
            "ubigeo": ubigeo_familiar,
            "tipo_dni": "amarillo"
        }
        
        familias.append({"adulto": adulto, "menor": menor})

    return familias

if __name__ == "__main__":
    # La carpeta actual debería ser scripts_generacion, así que subimos un nivel para ir a datos
    ruta_datos = os.path.join(os.path.dirname(__file__), "..", "datos")
    os.makedirs(ruta_datos, exist_ok=True)
    
    familias_generadas = generar_identidades(150)
    
    ruta_json = os.path.join(ruta_datos, "identidades.json")
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(familias_generadas, f, ensure_ascii=False, indent=4)
        
    print(f"Se generaron {len(familias_generadas)} identidades familiares en {ruta_json}")
