from flask import Flask, render_template, redirect, make_response, session
import os
import secrets
from dotenv import load_dotenv

# Cargar variables de entorno antes de crear la app
load_dotenv()

# Inicializar la base de datos: crea el archivo .db y todas las tablas
# si no existen. Esto permite que cualquier colaborador que clone el repo
# pueda ejecutar la app directamente sin pasos manuales adicionales.
from database import crear_tablas
crear_tablas()

from routes import routes

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Si hay SECRET_KEY en .env se usa esa (útil para producción con sesiones persistentes).
# En desarrollo, se genera una clave aleatoria en cada arranque → invalida todas
# las cookies de sesión anteriores al reiniciar el servidor.
app.secret_key = os.getenv('SECRET_KEY') or secrets.token_hex(32)

# Registrar el Blueprint de rutas API
app.register_blueprint(routes)


@app.context_processor
def inject_usuario():
    """Hace disponible la info del usuario logueado en TODOS los templates."""
    if 'user_id' in session:
        return {
            'usuario_logueado': True,
            'usuario_nombre': session.get('user_nombre', ''),
            'usuario_email': session.get('user_email', '')
        }
    return {'usuario_logueado': False}


@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login')
def login():
    # Ruta solo para invitados: si ya hay sesión activa, redirigir al home
    if 'user_id' in session:
        return redirect('/')
    # no-store: le dice al navegador que nunca guarde esta página en caché,
    # así el botón "volver" no puede mostrar una versión obsoleta con datos del formulario
    response = make_response(render_template('login.html'))
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/registro')
def registro():
    # Ruta solo para invitados: si ya hay sesión activa, redirigir al home
    if 'user_id' in session:
        return redirect('/')
    response = make_response(render_template('registro.html'))
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/perfil')
def perfil():
    return render_template('perfil.html')

@app.route('/seleccionar-asientos')
def seleccionar_asientos():
    return render_template('seleccionar_asientos.html')


if __name__ == '__main__':
    app.run(debug=True)
