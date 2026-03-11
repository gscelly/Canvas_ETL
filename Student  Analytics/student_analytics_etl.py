from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
import pandas as pd
import requests
import logging

# Configuración por defecto del DAG
default_args = {
    'owner': 'galo_celly',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

@dag(
    dag_id='canvas_student_analytics_etl',
    default_args=default_args,
    description='ETL para extraer analíticas de estudiantes desde Canvas LMS a PostgreSQL',
    schedule_interval='@daily',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['educacion', 'etl', 'canvas'],
)
def canvas_analytics_etl():

    @task()
    def extract_canvas_data() -> list:
        """
        Extrae datos de la API de Canvas.
        El token se obtiene de forma segura desde las Variables de Airflow.
        """
        # Obtenemos el token y la URL base desde las Variables de Airflow
        canvas_url = Variable.get("CANVAS_BASE_URL", default_var="https://canvas.instructure.com/api/v1")
        canvas_token = Variable.get("CANVAS_API_TOKEN")
        
        headers = {
            "Authorization": f"Bearer {canvas_token}"
        }
        
        # Endpoint simulado para obtener actividad de los estudiantes en un curso
        # En un caso real, iterarías sobre paginación
        endpoint = f"{canvas_url}/courses/101/analytics/student_summaries"
        
        logging.info(f"Extrayendo datos de: {endpoint}")
        
        # Simulación de respuesta para el portafolio (si no tienes una instancia real de Canvas conectada)
        # response = requests.get(endpoint, headers=headers)
        # response.raise_for_status()
        # return response.json()
        
        mock_data = [
            {"student_id": 1, "page_views": 150, "participations": 20, "missing_entries": 2},
            {"student_id": 2, "page_views": None, "participations": 5, "missing_entries": 10},
            {"student_id": 3, "page_views": 300, "participations": 45, "missing_entries": 0}
        ]
        return mock_data

    @task()
    def transform_data(raw_data: list) -> str:
        """
        Limpia y transforma los datos utilizando Pandas.
        """
        df = pd.DataFrame(raw_data)
        
        # Limpieza de datos: Rellenar nulos y asegurar tipos de datos
        df['page_views'] = df['page_views'].fillna(0).astype(int)
        df['participations'] = df['participations'].fillna(0).astype(int)
        
        # Creación de una métrica calculada: "engagement_score"
        df['engagement_score'] = (df['page_views'] * 0.2) + (df['participations'] * 0.8)
        df['processed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        logging.info(f"Datos transformados exitosamente: {len(df)} registros.")
        
        # Airflow XCom prefiere pasar JSON o strings entre tareas
        return df.to_json(orient='records')

    @task()
    def load_to_postgres(transformed_data: str):
        """
        Carga los datos en PostgreSQL usando PostgresHook.
        Las credenciales se gestionan en las Conexiones de Airflow.
        """
        df = pd.read_json(transformed_data)
        
        # postgres_analytics es el ID de la conexión configurada en Airflow
        pg_hook = PostgresHook(postgres_conn_id='postgres_analytics')
        engine = pg_hook.get_sqlalchemy_engine()
        
        logging.info("Cargando datos en la tabla 'student_analytics_fact'...")
        
        # Guarda el DataFrame en la base de datos
        df.to_sql(
            name='student_analytics_fact',
            con=engine,
            if_exists='append', # O 'replace' dependiendo de tu lógica de negocio
            index=False
        )
        logging.info("Carga completada con éxito.")

    # Orquestación (Dependencias)
    raw_data = extract_canvas_data()
    clean_data = transform_data(raw_data)
    load_to_postgres(clean_data)

# Instanciación del DAG
etl_dag = canvas_analytics_etl()