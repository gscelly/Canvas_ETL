# Canvas LMS Data Streaming: Real-Time Event Consumer

Este repositorio contiene la arquitectura de un microservicio consumidor diseñado para ingerir flujos masivos de datos en tiempo real provenientes de un entorno educativo de alta concurrencia. 

Implementa una **Arquitectura Orientada a Eventos (EDA)** integrando las opciones de **Data Streaming (Live Events)** de Canvas LMS, **Amazon SQS**, y **MongoDB**.



## 🚀 Arquitectura del Sistema

La ingesta por lotes (Batch ETL) tiene limitaciones de latencia. Administrar plataformas masivas requiere arquitecturas que respondan al instante. Este flujo soluciona ese problema:

1. **Emisor (Canvas LMS):** Dispara un payload JSON al instante cada vez que ocurre una acción en la plataforma (ej. un estudiante envía una tarea o un docente califica un foro).
2. **Message Broker (Amazon SQS):** La cola administrada de AWS recibe los eventos, actuando como un amortiguador (*buffer*) altamente escalable que previene la pérdida de datos ante picos de tráfico.
3. **Consumidor (Python Daemon):** Este script aplica la técnica de *Long Polling* para escuchar la cola SQS de manera eficiente.
4. **Data Lake / Storage (MongoDB):** Almacena el payload en crudo utilizando la flexibilidad de NoSQL, permitiendo que la estructura del JSON cambie sin romper esquemas de bases de datos relacionales.

## ⚙️ Características Técnicas Clave

* **Manejo de Fallos (Resiliencia):** Si la base de datos MongoDB cae temporalmente, el script **no** elimina el mensaje de la cola SQS. El mensaje regresa a la cola y se reintenta automáticamente, garantizando *Zero Data Loss*.
* **Schema-on-Read:** Al almacenar todo el bloque de datos en la llave `raw_payload` en MongoDB, diferimos la complejidad del modelado de datos para la fase de análisis.
* **Integración Nativa Cloud:** Uso de `boto3` para una comunicación robusta con la infraestructura de AWS.

## 🛠️ Configuración y Ejecución

Para ejecutar este consumidor localmente, necesitas configurar tus credenciales de AWS para que la librería `boto3` pueda autenticarse de forma segura.

### Paso 1: Obtener las Credenciales en AWS
1. Ingresa a la consola de AWS y dirígete al servicio **IAM (Identity and Access Management)**.
2. Crea un usuario (o usa uno existente) y asegúrate de que tenga permisos para leer SQS (ej. la política `AmazonSQSReadOnlyAccess`).
3. Ve a la pestaña **Credenciales de seguridad** de ese usuario y crea una **Clave de acceso** (Access Key). Copia el *Access Key ID* y el *Secret Access Key*.
4. Dirígete al servicio **SQS**, selecciona tu cola y copia la **URL de la cola** (Queue URL) que aparece en la sección de detalles.

### Paso 2: Exportar las Variables de Entorno
Abre tu terminal y ejecuta los siguientes comandos para inyectar las credenciales en tu entorno (reemplaza los valores entre `< >` con tus datos reales):

**Para usuarios de Linux / macOS (Bash o Zsh):**
```bash
export AWS_ACCESS_KEY_ID="<TU_ACCESS_KEY_ID>"
export AWS_SECRET_ACCESS_KEY="<TU_SECRET_ACCESS_KEY>"
export AWS_REGION="<TU_REGION_EJ_US_EAST_1>"
export SQS_QUEUE_URL="<TU_URL_DE_LA_COLA_SQS>"
export MONGO_URI="mongodb://localhost:27017/"

**Para usuarios de WIndowa / Powershell:**
```bash
$env:AWS_ACCESS_KEY_ID="<TU_ACCESS_KEY_ID>"
$env:AWS_SECRET_ACCESS_KEY="<TU_SECRET_ACCESS_KEY>"
$env:AWS_REGION="<TU_REGION_EJ_US_EAST_1>"
$env:SQS_QUEUE_URL="<TU_URL_DE_LA_COLA_SQS>"
$env:MONGO_URI="mongodb://localhost:27017/"


**Para ejecutar el script:**
```bash
pip install boto3 pymongo
python streaming_consumer.py
```