"""
Configuración global de la aplicación.
¡IMPORTANTE!: Nunca subas tus tokens reales a repositorios públicos como GitHub.
"""

# URL base de tu instancia de Canvas (Asegúrate de incluir /api/v1 al final)
API_URL = "https://<TU_DOMINIO>.instructure.com/api/v1"

# Token de acceso generado desde el perfil de usuario en Canvas
API_KEY = "INGRESA_TU_TOKEN_AQUI_LOCALMENTE"

# DICCIONARIO DE USUARIOS AUTORIZADOS
# Formato: "nombre_usuario": "hash_generado_con_werkzeug"
#
# NOTA PARA EL DESARROLLADOR: Para generar un hash de contraseña seguro,
# abre una terminal interactiva de Python y ejecuta:
# >>> from werkzeug.security import generate_password_hash
# >>> print(generate_password_hash('tu_contrasena_segura'))
# Copia el resultado y pégalo aquí.

USERS = {
    "admin": "scrypt:32768:8:1$TuHashGeneradoAca$TuHashGeneradoAca", # Reemplazar con hash real
}