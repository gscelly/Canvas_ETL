import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, current_timestamp, to_timestamp

# Inicialización
sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

# Cargar el nombre del bucket de S3 raw name
BUCKET_NAME = "tu-bucket-raw-data"

# 1. EXTRACT: Leer el JSON crudo de S3 (asume que un crawler o esquema infiere la estructura)
ruta_origen = f"s3://{BUCKET_NAME}/raw/canvas_courses/"
df_raw = spark.read.json(ruta_origen)

# 2. TRANSFORM: Limpieza y selección basada en la estructura real de Canvas LMS
df_limpio = df_raw.select(
    col("id").alias("course_id").cast("integer"),
    col("name").alias("course_name").cast("string"),
    col("course_code").cast("string"),
    col("account_id").alias("subaccount_id").cast("integer"),
    col("sis_course_id").cast("string"),
    col("workflow_state").alias("estado").cast("string"),
    # Convertimos la cadena ISO 8601 a un Timestamp real de Spark
    to_timestamp(col("created_at")).alias("created_at")
)

# Filtramos cursos de prueba o corruptos que no tengan nombre válido
df_limpio = df_limpio.filter(col("course_name").isNotNull())

# Añadimos marca de tiempo técnica para saber cuándo pasó por nuestro pipeline ETL
df_limpio = df_limpio.withColumn("etl_processed_at", current_timestamp())

# 3. LOAD: Guardar optimizado en formato Parquet, particionado por subcuenta y luego por estado
ruta_destino = f"s3://{BUCKET_NAME}/processed/canvas_courses_parquet/"

# Usamos mode("overwrite") y particionamos jerárquicamente
# (Primero por ID de subcuenta, luego por estado activo/inactivo)
df_limpio.write \
    .mode("overwrite") \
    .partitionBy("subaccount_id", "estado") \
    .parquet(ruta_destino)

print("¡Trabajo de AWS Glue completado! Datos convertidos a Parquet con esquema estricto.")
job.commit()