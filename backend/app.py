from flask import Flask, render_template, redirect, make_response, session, jsonify
import os
import secrets
from dotenv import load_dotenv

# Cargar variables de entorno antes de crear la app
load_dotenv()

# Inicializar y poblar la base de datos con el seed automático (si está vacía).
# Centralizado en seed_db.py para mantener el código limpio y evitar ejecuciones redundantes.
from database import obtener_sesion
from models import Recorrido, Bus
from seed_db import seed as _seed_inicial
_seed_inicial(quiet=False)

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
            'usuario_email': session.get('user_email', ''),
            'usuario_rol': session.get('user_rol', 'pasajero')
        }
    return {'usuario_logueado': False}


@app.route('/')
def index():
    db = obtener_sesion()
    try:
        # Obtener ciudades únicas de origen para el buscador
        recorridos = db.query(Recorrido).all()
        origenes = sorted({r.origen for r in recorridos})
    finally:
        db.close()
    return render_template('home.html', origenes=origenes)

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

@app.route('/recuperar')
def recuperar():
    # Página para solicitar el enlace de recuperación de contraseña
    response = make_response(render_template('recuperar.html'))
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/restablecer')
def restablecer():
    # Página donde el usuario define su nueva contraseña (llega desde el correo)
    response = make_response(render_template('restablecer.html'))
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/tarifas')
def tarifas():
    db = obtener_sesion()
    try:
        recorridos = db.query(Recorrido).order_by(Recorrido.id_recorrido).all()
    finally:
        db.close()
    return render_template('tarifas.html', recorridos=recorridos)


@app.route('/quienes-somos')
def quienes_somos():
    return render_template('quienes_somos.html')


@app.route('/api/origenes')
def api_origenes():
    """Devuelve las ciudades de origen y destino disponibles en la BD."""
    db = obtener_sesion()
    try:
        recorridos = db.query(Recorrido).all()
        origenes  = sorted({r.origen  for r in recorridos})
        destinos  = sorted({r.destino for r in recorridos})
        return jsonify({'origenes': origenes, 'destinos': destinos})
    finally:
        db.close()

@app.route('/perfil')
def perfil():
    return render_template('perfil.html')

@app.route('/seleccionar-asientos')
def seleccionar_asientos():
    return render_template('seleccionar_asientos.html')

@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('user_rol') != 'admin':
        return redirect('/login')
    db = obtener_sesion()
    try:
        total_buses = db.query(Bus).count()
    finally:
        db.close()
    return render_template('admin.html', total_buses=total_buses)




if __name__ == '__main__':
    app.run(debug=True)
