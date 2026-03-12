# 🎓 Canvas LMS Data Engineering & Analytics Portfolio

¡Bienvenido a mi repositorio principal de Ingeniería de Datos y Desarrollo Backend enfocado en el ecosistema EdTech! 

Este repositorio (`Canvas_ETL`) agrupa una suite completa de aplicaciones, pipelines de extracción (ETL) y microservicios de streaming diseñados para interactuar con la infraestructura de **Canvas LMS**. El objetivo de estos proyectos es demostrar cómo transformar datos educativos crudos en inteligencia de negocios, garantizar la seguridad del entorno virtual y facilitar la gestión académica mediante automatización y arquitecturas en la nube.

---

## 🚀 Proyectos Incluidos en este Repositorio

A continuación, puedes explorar cada una de las soluciones implementadas haciendo clic en sus respectivas carpetas. Cada proyecto cuenta con su propia documentación detallada y arquitectura.

### 1. 🔍 [Real-time course and grade inquiry](https://github.com/gscelly/Canvas_ETL/tree/main/Real-time%20course%20and%20grade%20inquiry)
**Aplicación Web Segura (Flask) para Consultas Académicas**
* Un dashboard interactivo desarrollado en Python/Flask que consume la API REST de Canvas LMS. 
* Implementa procesamiento concurrente (`ThreadPoolExecutor`) para extraer paralelamente calificaciones de alumnos sin bloquear el servidor. 
* Cuenta con autenticación segura (`Flask-Login` y `Werkzeug Security`) e interfaces responsivas con Bootstrap 5.

### 2. 📊 [Student Analytics](https://github.com/gscelly/Canvas_ETL/tree/main/Student%20%20Analytics)
**Pipeline ETL Automatizado para Inteligencia de Negocios**
* Un DAG orquestado con **Apache Airflow** que extrae métricas de interacción (Page Views, Participations) desde la API de Canvas.
* Maneja la paginación dinámica, limpia los datos utilizando **Pandas** y calcula *scores* de riesgo de deserción estudiantil.
* Realiza cargas transaccionales en una base de datos **PostgreSQL** preparando los datos para herramientas de Business Intelligence.

### 3. 🛡️ [Log Page Views](https://github.com/gscelly/Canvas_ETL/tree/main/Log%20Page%20Views)
**Monitor de Seguridad y Detección de Anomalías (Airflow + MongoDB)**
* Sistema de auditoría que evalúa logs transaccionales en tiempo real. 
* Orquesta hilos concurrentes para analizar el comportamiento de los usuarios directamente desde la API, detectando patrones anómalos (como navegación tipo bot o accesos en la madrugada).
* Ejecuta inserciones masivas de alto rendimiento (`Bulk Write` vía `MongoHook`) en una base de datos NoSQL (**MongoDB**).

### 4. ⚡ [Live events Streaming](https://github.com/gscelly/Canvas_ETL/tree/main/Live%20events%20Streaming)
**Consumidor de Datos en Tiempo Real (AWS SQS + MongoDB)**
* Microservicio demonio (*daemon*) diseñado para una Arquitectura Orientada a Eventos (EDA).
* Aplica la técnica de *Long Polling* usando `boto3` para escuchar eventos en vivo disparados por Canvas hacia una cola de **Amazon SQS**.
* Ingiere los payloads crudos en formato JSON de forma resiliente hacia **MongoDB**, aplicando el principio de *Schema-on-Read*.

### 5. 🔄 [Users Enrollments](https://github.com/gscelly/Canvas_ETL/tree/main/Users%20Enrollments)
**Sincronización Masiva de Enrolamientos (Airflow + MongoDB)**
* Pipeline ETL de alto rendimiento diseñado para extraer todos los usuarios de una subcuenta y sus respectivos enrolamientos históricos y activos.
* Resuelve el problema de la **paginación profunda (Deep Pagination)** nativa de Canvas API.
* Optimiza la memoria y la latencia de red combinando extracciones concurrentes (`ThreadPoolExecutor`) con inserciones en lotes (`insert_many`) en **MongoDB**.
* Programación *timezone-aware* estricta utilizando la librería `pendulum`.

---

## 🛠️ Stack Tecnológico Global

* **Orquestación y Pipelines:** Apache Airflow, Pandas, ETL/ELT.
* **Desarrollo Backend:** Python 3.x, Flask, Concurrencia (Multithreading), REST APIs.
* **Bases de Datos:** PostgreSQL (Relacional), MongoDB (NoSQL).
* **Cloud & Streaming:** Amazon Web Services (AWS SQS), Boto3, Event-Driven Architecture.
* **Dominio EdTech:** Instructure Canvas API, Canvas Live Events, LTI.

---

## 👨‍💻 Sobre el Autor

**Galo Stephano Celly Alvarado** *Data Engineer | Backend Developer | EdTech Specialist*

Ingeniero en Sistemas Informáticos y Magíster en Educación con especialización en TIC. Me apasiona unir la infraestructura de datos moderna con las necesidades del aprendizaje electrónico para crear ecosistemas educativos escalables, seguros y basados en datos.

📫 **Contacto:** [Perfil de LinkedIn](https://www.linkedin.com/in/galo-celly) | ✉️ galocelly1994@gmail.com