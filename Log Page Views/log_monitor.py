from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.providers.mongo.hooks.mongo import MongoHook
from datetime import datetime, timedelta
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pymongo import InsertOne
from pymongo.errors import BulkWriteError

# Configuración por defecto del DAG
default_args = {
    'owner': 'galo_celly',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

@dag(
    dag_id='canvas_live_anomaly_detector',
    default_args=default_args,
    description='DAG para monitorear logs de Canvas en tiempo real, detectar anomalías y guardar en MongoDB',
    schedule_interval='@hourly',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['seguridad', 'etl', 'canvas', 'mongodb', 'concurrencia'],
)
def canvas_anomaly_detector_dag():

    @task()
    def get_course_users() -> list:
        """
        Extrae la lista de IDs de estudiantes inscritos en el curso.
        """
        canvas_url = Variable.get("CANVAS_BASE_URL", default_var="https://canvas.instructure.com/api/v1")
        canvas_token = Variable.get("CANVAS_API_TOKEN")
        course_id = Variable.get("MONITOR_COURSE_ID", default_var="101")
        
        headers = {"Authorization": f"Bearer {canvas_token}"}
        url = f"{canvas_url}/courses/{course_id}/users"
        params = {"enrollment_type[]": "student", "per_page": 100}
        
        logging.info(f"Obteniendo estudiantes del curso {course_id}...")
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            users = response.json()
            user_ids = [user['id'] for user in users]
            logging.info(f"Se encontraron {len(user_ids)} estudiantes para auditar.")
            return user_ids
        except requests.exceptions.RequestException as e:
            logging.error(f"Error en la extracción de usuarios: {e}")
            return []

    @task()
    def process_and_load_anomalies(user_ids: list):
        """
        Procesa concurrentemente los logs de cada usuario, 
        detecta anomalías y carga los resultados en MongoDB.
        """
        if not user_ids:
            logging.warning("No hay usuarios para procesar.")
            return

        canvas_url = Variable.get("CANVAS_BASE_URL", default_var="https://canvas.instructure.com/api/v1")
        canvas_token = Variable.get("CANVAS_API_TOKEN")
        headers = {"Authorization": f"Bearer {canvas_token}"}
        
        # Conexión a MongoDB usando MongoHook
        mongo_hook = MongoHook(mongo_conn_id='mongo_security_db')
        client = mongo_hook.get_conn()
        collection = client.canvas_security_db.api_anomalies

        def _is_anomaly(page_view: dict) -> bool:
            """Evalúa si un registro es anómalo."""
            try:
                timestamp_str = page_view.get("created_at")
                if not timestamp_str: return False
                
                log_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                time_spent = page_view.get("interaction_seconds", 0)
                
                # Regla 1: Madrugada (2 AM a 5 AM)
                if 2 <= log_time.hour <= 5:
                    page_view['anomaly_reason'] = "Acceso en madrugada"
                    return True
                    
                # Regla 2: Navegación tipo bot (< 1 seg de interacción)
                if time_spent is not None and time_spent < 1:
                    page_view['anomaly_reason'] = "Navegación anormalmente rápida"
                    return True
            except Exception as e:
                logging.debug(f"Error parseando registro: {e}")
            return False

        def process_single_user(user_id: int) -> int:
            """Consulta la API de un usuario y prepara el Bulk Write."""
            url = f"{canvas_url}/users/{user_id}/page_views"
            params = {"per_page": 50}
            
            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                page_views = response.json()
                
                anomalies = []
                for pv in page_views:
                    if _is_anomaly(pv):
                        pv['monitored_user_id'] = user_id
                        pv['inserted_at'] = datetime.now()
                        anomalies.append(InsertOne(pv))
                
                if anomalies:
                    result = collection.bulk_write(anomalies, ordered=False)
                    return result.inserted_count
                return 0
                
            except requests.exceptions.RequestException as e:
                logging.error(f"Error API usuario {user_id}: {e}")
                return 0
            except BulkWriteError as bwe:
                logging.error(f"Error Bulk Write usuario {user_id}: {bwe.details}")
                return 0

        total_anomalies = 0
        max_workers = int(Variable.get("MAX_THREAD_WORKERS", default_var="5"))
        
        logging.info(f"Procesando con {max_workers} hilos para {len(user_ids)} usuarios.")
        
        # Orquestación de hilos concurrentes
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_single_user, uid): uid for uid in user_ids}
            
            for future in as_completed(futures):
                try:
                    anomalies_found = future.result()
                    total_anomalies += anomalies_found
                except Exception as e:
                    logging.error(f"Excepción en hilo: {e}")

        logging.info(f"DAG finalizado. Total de anomalías registradas: {total_anomalies}")

    # Definición de dependencias
    users = get_course_users()
    process_and_load_anomalies(users)

# Instanciación
anomaly_dag = canvas_anomaly_detector_dag()