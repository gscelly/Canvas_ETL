import os
import json
import requests
import boto3
from datetime import datetime

# Configuraciones (En producción url CANVAS, con variables de entorno o Secrets Manager)
CANVAS_DOMAIN = os.getenv("CANVAS_DOMAIN", "institucion.instructure.com")
CANVAS_TOKEN = os.getenv("CANVAS_TOKEN", "tu_token_aqui")
S3_BUCKET = os.getenv("S3_BUCKET", "tu-bucket-raw-data")


def extract_courses_from_canvas():
    print(f"Iniciando extracción desde {CANVAS_DOMAIN}...")
    headers = {"Authorization": f"Bearer {CANVAS_TOKEN}"}
    url = f"https://{CANVAS_DOMAIN}/api/v1/accounts/1/courses?per_page=100"

    all_courses = []

    # Manejo de paginación de Canvas LMS
    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        cursos_pagina = response.json()
        all_courses.extend(cursos_pagina)

        # Canvas envía el link a la siguiente página en los headers
        if "next" in response.links:
            url = response.links["next"]["url"]
        else:
            url = None

    print(f"Total de cursos extraídos: {len(all_courses)}")
    return all_courses


def upload_to_s3(data):
    s3_client = boto3.client('s3')

    # Creamos una ruta estructurada por fecha: raw/canvas_courses/YYYY-MM-DD/data.json
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    s3_key = f"raw/canvas_courses/dt={fecha_hoy}/courses_extract.json"

    print(f"Subiendo datos a s3://{S3_BUCKET}/{s3_key}...")

    # Subimos el JSON directamente desde la memoria
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=json.dumps(data),
        ContentType='application/json'
    )
    print("¡Subida completada con éxito!")


if __name__ == "__main__":
    datos_canvas = extract_courses_from_canvas()
    upload_to_s3(datos_canvas)