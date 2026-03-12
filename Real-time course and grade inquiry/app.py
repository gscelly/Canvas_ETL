from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import config
from datetime import datetime

# Importamos concurrencia para acelerar peticiones masivas a la API de Canvas
from concurrent.futures import ThreadPoolExecutor, as_completed

# Imports de seguridad para el manejo de sesiones
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash

app = Flask(__name__)
# Llave secreta para firmar las cookies de sesión (Debe ser variables de entorno en producción)
app.secret_key = 'secreto_super_seguro_cambia_esto_por_algo_aleatorio'

# ==========================================
# CONFIGURACIÓN FLASK-LOGIN
# ==========================================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Ruta de redirección si un usuario no autenticado intenta acceder


# Modelo de usuario básico requerido por Flask-Login
class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(user_id):
    """Carga el usuario desde la configuración simulando una base de datos."""
    if user_id in config.USERS:
        return User(user_id)
    return None


# Headers globales para autenticarse con la API de Canvas
HEADERS = {"Authorization": f"Bearer {config.API_KEY}"}
TARGET_TERM_ID = 329  # ID del periodo académico actual a filtrar


# ==========================================
# FUNCIONES AUXILIARES Y FILTROS JINJA
# ==========================================

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    """Filtro personalizado de Jinja para formatear fechas ISO de Canvas a un formato legible."""
    if not value: return "-"
    try:
        dt = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
        return dt.strftime(format)
    except ValueError:
        return value


def get_all_pages(endpoint, params):
    """
    Maneja la paginación de la API de Canvas.
    Canvas devuelve resultados limitados por página y provee la URL de la siguiente
    página en los headers ('links'). Esta función itera hasta obtener todos los datos.
    """
    if params is None: params = {}
    params['per_page'] = 100
    all_data = []
    url = f"{config.API_URL}/{endpoint}"

    while url:
        try:
            response = requests.get(url, headers=HEADERS, params=params)
            response.raise_for_status()
            all_data.extend(response.json())

            # Revisar cabeceras de enlace para la paginación
            links = response.links
            if 'next' in links:
                url = links['next']['url']
                params = {}  # Limpiamos params porque la nueva URL ya los incluye
            else:
                url = None
        except Exception:
            break
    return all_data


def canvas_request(endpoint, params=None):
    """Función envoltura para realizar peticiones GET estándar a Canvas."""
    if params is None: params = {}
    params['per_page'] = 100
    try:
        response = requests.get(f"{config.API_URL}/{endpoint}", headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error Canvas: {e}")
        return []


def fetch_submissions_batch(course_id, student_ids):
    """Obtiene entregas de un lote específico de estudiantes (usado para concurrencia)."""
    endpoint = f"courses/{course_id}/students/submissions"
    params = {
        'student_ids[]': student_ids,
        'include[]': ['assignment', 'user', 'submission_history', 'submission_comments'],
        'per_page': 100
    }
    return get_all_pages(endpoint, params)


# ==========================================
# RUTAS DE AUTENTICACIÓN
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja el inicio de sesión validando credenciales hasheadas."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in config.USERS:
            # Compara la contraseña en texto plano con el hash guardado
            if check_password_hash(config.USERS[username], password):
                user = User(username)
                login_user(user)
                flash('Has iniciado sesión correctamente.', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            else:
                flash('Contraseña incorrecta.', 'danger')
        else:
            flash('Usuario no encontrado.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Cierra la sesión del usuario actual."""
    logout_user()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('login'))


# ==========================================
# RUTAS PRINCIPALES PROTEGIDAS
# ==========================================

@app.route('/', methods=['GET'])
@login_required
def index():
    """Página de inicio (Dashboard de búsqueda)."""
    return render_template('index.html')


@app.route('/search', methods=['POST'])
@login_required
def search_users():
    """Busca usuarios en Canvas basándose en un término (nombre, correo o ID)."""
    search_term = request.form.get('search_term')
    role_intent = request.form.get('role_intent')

    if not search_term:
        flash('Ingresa un término', 'warning')
        return redirect(url_for('index'))

    # Búsqueda global en la cuenta de Canvas
    users = canvas_request('accounts/self/users', {'search_term': search_term})
    if not users:
        flash('No se encontraron usuarios.', 'danger')
        return redirect(url_for('index'))

    return render_template('user_results.html', users=users, role_intent=role_intent)


@app.route('/user/<int:user_id>/courses')
@login_required
def user_courses(user_id):
    """Obtiene y filtra los cursos activos de un usuario para un periodo específico."""
    role = request.args.get('role')
    user_info = canvas_request(f'users/{user_id}/profile')

    params = {
        'enrollment_state': 'active',
        'enrollment_type': role,
        'include[]': ['term', 'sections', 'teachers']
    }
    raw_courses = canvas_request(f'users/{user_id}/courses', params)

    # Filtrar solo cursos del periodo académico objetivo
    filtered_courses = [c for c in raw_courses if c.get('enrollment_term_id') == TARGET_TERM_ID]

    if role == 'teacher':
        return render_template('teacher_courses.html', courses=filtered_courses, user=user_info, term_id=TARGET_TERM_ID)
    else:
        return render_template('student_courses.html', courses=filtered_courses, user=user_info, term_id=TARGET_TERM_ID)


@app.route('/user/<int:user_id>/course/<int:course_id>/grades')
@login_required
def student_grades(user_id, course_id):
    """Extrae las calificaciones detalladas y feedback de un estudiante en un curso."""
    course_info = canvas_request(f'courses/{course_id}')

    # Obtener grupos de tareas para categorizar
    groups_data = canvas_request(f'courses/{course_id}/assignment_groups')
    group_map = {g['id']: g['name'] for g in groups_data} if groups_data else {}

    params = {
        'student_ids[]': user_id,
        'include[]': ['assignment', 'submission_history', 'submission_comments']
    }
    submissions = canvas_request(f'courses/{course_id}/students/submissions', params)

    # Filtrar solo entradas que tengan una tarea asignada válida
    valid_submissions = [s for s in submissions if s.get('assignment')]

    return render_template('grades.html', submissions=valid_submissions, course=course_info, user_id=user_id,
                           group_map=group_map)


@app.route('/teacher/course/<int:course_id>/students')
@login_required
def teacher_view_students(course_id):
    """
    Vista compleja para profesores:
    Utiliza ThreadPoolExecutor para extraer paralelamente las calificaciones
    de todos los alumnos de un curso sin bloquear el servidor.
    """
    course_info = canvas_request(f'courses/{course_id}')
    groups_data = canvas_request(f'courses/{course_id}/assignment_groups')
    group_map = {g['id']: g['name'] for g in groups_data} if groups_data else {}

    # 1. Obtener todos los estudiantes del curso
    users_endpoint = f"courses/{course_id}/users"
    users_params = {'enrollment_type[]': ['student'], 'per_page': 100}
    all_students = get_all_pages(users_endpoint, users_params)
    student_ids = [u['id'] for u in all_students]

    # 2. Dividir IDs en "chunks" (lotes) de 10 para no saturar la API
    chunk_size = 10
    chunks = [student_ids[i:i + chunk_size] for i in range(0, len(student_ids), chunk_size)]
    all_submissions = []

    # 3. Procesamiento Concurrente de las llamadas a la API
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_chunk = {executor.submit(fetch_submissions_batch, course_id, chunk): chunk for chunk in chunks}
        for future in as_completed(future_to_chunk):
            try:
                data = future.result()
                all_submissions.extend(data)
            except Exception as e:
                print(f"Error en hilo de ejecución: {e}")

    # 4. Agrupar los resultados extraídos por ID de estudiante
    students_data = {}
    for student in all_students:
        students_data[student['id']] = {'user_info': student, 'submissions': []}

    for sub in all_submissions:
        if not sub.get('assignment') or not sub.get('user'): continue
        uid = sub['user']['id']
        if uid in students_data:
            students_data[uid]['submissions'].append(sub)

    return render_template('teacher_grades.html', course=course_info, students_data=students_data, group_map=group_map)


if __name__ == '__main__':
    app.run(debug=True, port=5000)