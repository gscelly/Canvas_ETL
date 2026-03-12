from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.providers.mongo.hooks.mongo import MongoHook
from datetime import timedelta
import pendulum
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuración de zona horaria de Ecuador (UTC-5) solicitada mediante Pendulum
local_tz = pendulum.timezone("America/Guayaquil")

default_args = {
    'owner': 'galo_celly',
    'depends_on_past': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}


@dag(
    dag_id='canvas_subaccount_enrollments_sync',
    default_args=default_args,
    description='Extrae enrolamientos masivos de usuarios usando concurrencia y los guarda en MongoDB',
    schedule_interval='0 8 * * *',  # Ejecución diaria a las 08:00 AM
    start_date=pendulum.datetime(2023, 1, 1, tz=local_tz),
    catchup=False,
    tags=['edtech', 'canvas', 'mongodb', 'concurrencia'],
)
def canvas_enrollments_sync():
    @task()
    def get_subaccount_users() -> list:
        """
        Extrae todos los usuarios de la subcuenta 1 manejando la paginación oficial de Canvas.
        """
        canvas_url = Variable.get("CANVAS_BASE_URL", default_var="https://canvas.instructure.com/api/v1")
        canvas_token = Variable.get("CANVAS_API_TOKEN")
        subaccount_id = Variable.get("CANVAS_SUBACCOUNT_ID", default_var="1")

        headers = {"Authorization": f"Bearer {canvas_token}"}
        url = f"{canvas_url}/accounts/{subaccount_id}/users"
        params = {"per_page": 100}

        user_ids = []
        logging.info(f"Iniciando extracción de usuarios para la subcuenta {subaccount_id}...")

        # Bucle de paginación para obtener TODOS los usuarios
        while url:
            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                users = response.json()

                user_ids.extend([user['id'] for user in users])

                # Manejo del header 'Link' para la siguiente página
                if 'next' in response.links:
                    url = response.links['next']['url']
                    params = {}  # La nueva URL ya incluye los parámetros necesarios
                else:
                    url = None

            except requests.exceptions.RequestException as e:
                logging.error(f"Error al paginar usuarios: {e}")
                break

        logging.info(f"Total de usuarios extraídos: {len(user_ids)}")
        return user_ids

    @task()
    def extract_and_load_enrollments(user_ids: list):
        """
        Consulta concurrentemente los enrolamientos de cada usuario (manejando paginación interna)
        y utiliza inserciones por lotes (insert_many) en MongoDB.
        """
        if not user_ids:
            logging.warning("No hay usuarios para procesar.")
            return

        canvas_url = Variable.get("CANVAS_BASE_URL", default_var="https://canvas.instructure.com/api/v1")
        canvas_token = Variable.get("CANVAS_API_TOKEN")
        headers = {"Authorization": f"Bearer {canvas_token}"}

        # Conexión a MongoDB usando el Hook oficial de Airflow
        mongo_hook = MongoHook(mongo_conn_id='mongo_edtech_db')
        client = mongo_hook.get_conn()
        collection = client.canvas_data.user_enrollments

        def fetch_user_enrollments(user_id: int) -> list:
            """Función aislada para ser ejecutada por los hilos. Maneja su propia paginación."""
            url = f"{canvas_url}/users/{user_id}/enrollments"
            params = {"per_page": 100}
            enrollments = []

            while url:
                try:
                    response = requests.get(url, headers=headers, params=params)
                    response.raise_for_status()
                    data = response.json()
                    enrollments.extend(data)

                    if 'next' in response.links:
                        url = response.links['next']['url']
                        params = {}
                    else:
                        url = None
                except Exception as e:
                    logging.error(f"Error extrayendo enrolamientos del usuario {user_id}: {e}")
                    break

            return enrollments

        # Configuración de concurrencia y lotes de base de datos
        max_workers = int(Variable.get("MAX_THREAD_WORKERS", default_var="10"))
        batch_size = 2000  # Insertamos en MongoDB cada 2000 registros para no saturar la RAM
        current_batch = []
        total_inserted = 0

        logging.info(f"Iniciando ThreadPoolExecutor con {max_workers} hilos para {len(user_ids)} usuarios.")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Lanzamos todas las tareas al pool de hilos
            futures = {executor.submit(fetch_user_enrollments, uid): uid for uid in user_ids}

            # Procesamos los resultados conforme se van completando (as_completed)
            for future in as_completed(futures):
                try:
                    user_enrollments = future.result()
                    if user_enrollments:
                        # Enriquecemos el dato con una marca de tiempo de ingesta
                        ingested_at = pendulum.now(local_tz)
                        for record in user_enrollments:
                            record['etl_ingested_at'] = ingested_at
                            current_batch.append(record)

                    # Si el lote alcanza el tamaño límite, insertamos en MongoDB
                    if len(current_batch) >= batch_size:
                        collection.insert_many(current_batch)
                        total_inserted += len(current_batch)
                        logging.info(f"Lote insertado. Total acumulado: {total_inserted} enrolamientos.")
                        current_batch = []  # Vaciamos la lista en memoria

                except Exception as e:
                    logging.error(f"Excepción recolectando datos del hilo: {e}")

        # Insertar los registros remanentes que no alcanzaron a llenar el último lote
        if current_batch:
            collection.insert_many(current_batch)
            total_inserted += len(current_batch)

        logging.info(f"Sincronización finalizada con éxito. Se insertaron {total_inserted} enrolamientos en MongoDB.")

    # Orquestación (Dependencias del DAG)
    users = get_subaccount_users()
    extract_and_load_enrollments(users)


# Instanciación del DAG
sync_dag = canvas_enrollments_sync()