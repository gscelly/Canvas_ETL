# Canvas LMS Live Log Monitor & Anomaly Detector (Airflow DAG)

Este proyecto implementa un pipeline de orquestación en **Apache Airflow** diseñado para conectarse directamente a la API REST de Canvas LMS. El DAG monitorea la actividad de los estudiantes (Page Views), detecta patrones anómalos en memoria utilizando procesamiento concurrente (Multithreading) y registra estas incidencias en una base de datos **MongoDB**.

## 🚀 Arquitectura y Optimizaciones en Airflow

* **Desacoplamiento Inteligente:** El DAG extrae primero la lista de IDs de estudiantes (pasándola por XCom) y luego delega la extracción intensiva de logs a una tarea concurrente, evitando saturar la base de datos de metadatos de Airflow.
* **Procesamiento Concurrente (I/O Bound):** Utiliza `ThreadPoolExecutor` dentro de la tarea principal para paralelizar las llamadas HTTP a la API de Canvas, reduciendo drásticamente el tiempo de ejecución de horas a minutos.
* **Integración Nativa (MongoHook):** Emplea el proveedor oficial de MongoDB para Airflow (`MongoHook`), manejando las conexiones de forma segura sin exponer credenciales en el código fuente.
* **Escritura Masiva (Bulk Write):** Las anomalías detectadas se acumulan en memoria por cada hilo y se insertan en MongoDB utilizando `bulk_write`, optimizando drásticamente las operaciones de red hacia la base de datos.

## ⚠️ Reglas de Detección de Anomalías Actuales

El motor de reglas actual (configurable en el código) evalúa las siguientes condiciones:
1. **Acceso Fuera de Horario:** Accesos registrados entre las 2:00 AM y las 5:00 AM.
2. **Navegación tipo Bot/Scraper:** Registros de interacción donde el tiempo de permanencia en la página (`interaction_seconds`) es menor a 1 segundo, lo que puede indicar scraping de material protegido o uso de extensiones automatizadas.

## ⚙️ Configuración de Apache Airflow

Para ejecutar este DAG, debes configurar los siguientes elementos en la UI de Airflow:

### 1. Variables de Airflow (`Admin -> Variables`)
* `CANVAS_BASE_URL`: `https://tu-institucion.instructure.com/api/v1`
* `CANVAS_API_TOKEN`: `tu_token_de_seguridad` *(Asegúrate de marcar esta variable como oculta)*
* `MONITOR_COURSE_ID`: `101` (ID del curso específico a auditar)
* `MAX_THREAD_WORKERS`: `5` (Cantidad de hilos concurrentes para consultar la API)

### 2. Conexión a MongoDB (`Admin -> Connections`)
* **Connection Id:** `mongo_security_db`
* **Connection Type:** `MongoDB`
* **Host:** `localhost` (o IP de tu servidor Mongo)
* **Port:** `27017`
* **Login/Password:** (Tus credenciales, si la base de datos requiere autenticación)

## ▶️ Despliegue

1. Asegúrate de tener instalados los proveedores necesarios de Airflow:
   ```bash
   pip install apache-airflow-providers-mongo requests pymongo