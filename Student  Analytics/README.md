# Canvas LMS to PostgreSQL: Student Analytics ETL

Este proyecto implementa un pipeline ETL automatizado utilizando **Apache Airflow** y **Python**. Extrae métricas de interacción de estudiantes desde la API REST de Canvas LMS, realiza limpieza y transformaciones con **Pandas**, y carga los datos en un esquema analítico en **PostgreSQL**.

## 🚀 Arquitectura del Proyecto

1. **Extracción (Extract):** Consumo de la API de Canvas LMS autenticado vía Bearer Token.
2. **Transformación (Transform):** Limpieza de valores nulos (NaN) y cálculo de un `engagement_score` ponderado utilizando Pandas.
3. **Carga (Load):** Inserción masiva en PostgreSQL utilizando `PostgresHook` de Airflow y SQLAlchemy.

## 🛠️ Tecnologías Utilizadas

* Python 3.9+
* Apache Airflow 2.x
* Pandas
* PostgreSQL
* REST APIs

## ⚙️ Configuración y Credenciales

Por motivos de seguridad, ninguna credencial está "hardcodeada" en el código fuente. Para ejecutar este proyecto, debes configurar lo siguiente en la interfaz gráfica de Apache Airflow (o vía CLI):

### 1. Token de la API de Canvas (Airflow Variables)
Dirígete a `Admin -> Variables` en la UI de Airflow y agrega:
* **Key:** `CANVAS_API_TOKEN`
* **Val:** `<TU_TOKEN_GENERADO_EN_CANVAS>` *(Asegúrate de marcarla como encriptada/oculta si tu entorno lo requiere)*
* **Key:** `CANVAS_BASE_URL`
* **Val:** `https://<tu_institucion>.instructure.com/api/v1`

### 2. Base de Datos PostgreSQL (Airflow Connections)
Dirígete a `Admin -> Connections` en la UI de Airflow y crea una nueva conexión:
* **Connection Id:** `postgres_analytics`
* **Connection Type:** `Postgres`
* **Host:** `localhost` (o la IP de tu servidor BD)
* **Schema:** `analytics_db` (nombre de tu base de datos)
* **Login:** `tu_usuario_postgres`
* **Password:** `tu_contraseña_postgres`
* **Port:** `5432`

## ▶️ Ejecución

1. Clona el repositorio e instala las dependencias: `pip install -r requirements.txt`.
2. Ubica el archivo `canvas_analytics_etl.py` dentro de tu carpeta de `dags/` de Airflow.
3. Activa el DAG desde la interfaz web de Airflow y desencadena un *Trigger DAG*.
