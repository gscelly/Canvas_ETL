# 🎓 Canvas LMS Academic Viewer (Flask Web App)

Aplicación web desarrollada en Python con **Flask** diseñada para consultar, filtrar y visualizar información académica extraída directamente de la API REST de **Canvas LMS**. Permite realizar búsquedas centralizadas de perfiles de docentes y estudiantes, así como visualizar sus cursos activos, tareas y feedback de calificaciones de forma rápida.

## 🚀 Características Principales

* **Integración API RESTful:** Consumo avanzado de la API de Instructure Canvas, incluyendo manejo recursivo de **paginación** (`Link` headers).
* **Concurrencia y Optimización (Multithreading):** Implementación de `ThreadPoolExecutor` para extraer calificaciones de listas enteras de estudiantes de manera concurrente, reduciendo el tiempo de carga drásticamente (I/O Bound optimization).
* **Autenticación Segura:** Sistema de login manejado mediante `Flask-Login` con protección de rutas (`@login_required`) y contraseñas hasheadas (`Werkzeug Security`).
* **Filtros Personalizados (Jinja2):** Procesamiento en caliente de fechas formato ISO 8601 a formatos de lectura amigable.
* **Interfaz de Usuario (UI):** Diseño limpio, responsivo y accesible utilizando **Bootstrap 5** y Bootstrap Icons.

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python 3.x, Flask
* **Seguridad:** Flask-Login, Werkzeug
* **Peticiones HTTP:** Requests
* **Frontend:** HTML5, Jinja2, Bootstrap 5

## ⚙️ Instalación y Configuración Local

### 1. Clonar el repositorio y crear el entorno virtual
```bash
git clone [https://github.com/tu-usuario/canvas-academic-viewer.git](https://github.com/tu-usuario/canvas-academic-viewer.git)
cd canvas-academic-viewer
python -m venv venv

# En Windows:
venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate