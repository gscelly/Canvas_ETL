import boto3
import json
import logging
import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Configuración de logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)

class CanvasLiveEventsConsumer:
    """
    Consumidor de streaming de datos que lee eventos en tiempo real 
    desde Amazon SQS (Canvas Live Events) y los almacena en MongoDB.
    """
    def __init__(self, queue_url: str, aws_region: str, mongo_uri: str, db_name: str, collection_name: str):
        self.queue_url = queue_url
        
        # Cliente de AWS SQS
        self.sqs = boto3.client('sqs', region_name=aws_region)
        
        # Cliente de MongoDB
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[db_name]
        self.collection = self.db[collection_name]
        
        logging.info("Consumidor inicializado y conectado a SQS y MongoDB.")

    def poll_and_process(self):
        """
        Inicia un ciclo infinito de Long Polling para escuchar eventos en la cola SQS.
        """
        logging.info(f"Iniciando escucha de eventos en la cola: {self.queue_url}")
        
        try:
            while True:
                # Long Polling: Espera hasta 20 segundos a que llegue un mensaje
                response = self.sqs.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=10, # Procesa en lotes de 10 para mayor eficiencia
                    WaitTimeSeconds=20,
                    AttributeNames=['All']
                )

                messages = response.get('Messages', [])
                
                if not messages:
                    # No hay mensajes nuevos, el ciclo continúa
                    continue
                    
                logging.info(f"Se recibieron {len(messages)} eventos en tiempo real.")
                self._process_batch(messages)

        except KeyboardInterrupt:
            logging.info("Servicio detenido por el usuario.")
        except Exception as e:
            logging.critical(f"Error crítico en el consumidor: {e}")
        finally:
            self.mongo_client.close()

    def _process_batch(self, messages: list):
        """
        Procesa el lote de mensajes, los inserta en MongoDB y 
        los elimina de la cola SQS para evitar duplicados.
        """
        for msg in messages:
            receipt_handle = msg['ReceiptHandle']
            try:
                # Canvas envía el cuerpo del mensaje en formato JSON String
                body = json.loads(msg['Body'])
                
                # Extraemos metadatos útiles de Canvas Live Events si existen
                event_name = body.get('attributes', {}).get('event_name', 'unknown_event')
                event_time = body.get('attributes', {}).get('event_time', '')
                
                # Enriquecemos el payload con la fecha de ingesta en nuestro sistema
                document = {
                    "canvas_event_name": event_name,
                    "canvas_event_time": event_time,
                    "raw_payload": body, # Guardamos el JSON íntegro por flexibilidad
                    "ingested_at": boto3.session.Session().region_name # o datetime.now()
                }

                # Inserción en MongoDB
                self.collection.insert_one(document)
                logging.info(f"Evento '{event_name}' almacenado correctamente.")

                # Si la inserción fue exitosa, eliminamos el mensaje de la cola SQS
                self.sqs.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=receipt_handle
                )

            except json.JSONDecodeError:
                logging.error("El mensaje recibido no es un JSON válido. Se descarta.")
                self.sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=receipt_handle)
            except PyMongoError as db_error:
                # Si falla la BD, NO eliminamos el mensaje de la cola SQS.
                # SQS lo volverá a hacer visible más tarde (Retry mechanism automático).
                logging.error(f"Error al guardar en MongoDB: {db_error}")

# --- Bloque de ejecución principal ---
if __name__ == "__main__":
    # Variables de entorno para seguridad de infraestructura
    SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456789012/canvas-live-events-queue")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    
    # IMPORTANTE: Para que boto3 funcione, AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY 
    # deben estar configuradas en el entorno del sistema operativo.
    
    consumer = CanvasLiveEventsConsumer(
        queue_url=SQS_QUEUE_URL,
        aws_region=AWS_REGION,
        mongo_uri=MONGO_URI,
        db_name="canvas_streaming_db",
        collection_name="live_events"
    )
    
    # Iniciar el proceso como un daemon (servicio continuo)
    consumer.poll_and_process()