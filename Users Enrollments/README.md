# Canvas LMS Mass Enrollments Sync

Este proyecto implementa un pipeline ETL de alto rendimiento en **Apache Airflow** diseñado para extraer masivamente datos de matriculaciones (enrolamientos) desde la API de Canvas LMS hacia un Data Lake en **MongoDB**.

El pipeline está optimizado para entornos institucionales masivos donde un solo usuario puede estar inscrito en docenas de cursos históricos y actuales, generando volúmenes de datos profundamente anidados.

## 🚀 Arquitectura y Optimizaciones Clave

1. **Paginación Absoluta (Deep Pagination):** La API de Canvas restringe los resultados por página. Este DAG implementa algoritmos de paginación recursiva mediante el análisis de cabeceras HTTP (`response.links['next']`) tanto a nivel de Subcuenta (para descubrir usuarios) como a nivel de Usuario (para descubrir todos sus enrolamientos).
2. **Procesamiento Concurrente (I/O Bound):** Para evitar que el proceso demore horas extrayendo usuario por usuario, se utiliza `ThreadPoolExecutor`. Múltiples hilos consultan la API simultáneamente, maximizando el uso del ancho de banda y minimizando el tiempo de espera (latencia de red).
3. **Escritura por Lotes (Memory Control):** Los resultados de los hilos se acumulan en la memoria principal del DAG. Una vez que el bloque alcanza los 2000 registros, se ejecuta una operación `insert_many` hacia MongoDB. Esto previene desbordamientos de memoria (Out of Memory - OOM) y reduce drásticamente las conexiones transaccionales hacia la base de datos.
4. **Programación Timezone-Aware:** El DAG utiliza la librería `pendulum` para programar sus ejecuciones estrictamente a las 08:00 AM (Hora de Ecuador - UTC-5), garantizando que los datos estén frescos al inicio de la jornada laboral y evitando conflictos por cambios de horario de verano.

## ⚙️ Configuración en Apache Airflow

Para desplegar este DAG, configura los siguientes elementos en tu entorno de Airflow:

### 1. Variables Globales (`Admin -> Variables`)
* `CANVAS_BASE_URL`: `https://tu-institucion.instructure.com/api/v1`
* `CANVAS_API_TOKEN`: `tu_token_de_acceso` *(Marcar como secreto)*
* `CANVAS_SUBACCOUNT_ID`: `1` (ID de la subcuenta o cuenta raíz a sincronizar)
* `MAX_THREAD_WORKERS`: `10` (Ajusta la cantidad de hilos según las cuotas de Rate Limit de tu servidor Canvas).

### 2. Conexión de Base de Datos (`Admin -> Connections`)
* **Connection Id:** `mongo_edtech_db`
* **Connection Type:** `MongoDB`
* **Host / Port:** Configuración de tu clúster de MongoDB.

## ▶️ Despliegue
Copia el script de Python dentro de la carpeta `dags/` de tu servidor Airflow. El DAG se activará automáticamente a la hora programada.