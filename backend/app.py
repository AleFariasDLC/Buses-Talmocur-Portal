from flask import Flask, render_template, redirect, make_response, session, jsonify, request
import os
import secrets
from datetime import date, datetime, timezone
from dotenv import load_dotenv

# Cargar variables de entorno antes de crear la app
load_dotenv()

# Inicializar y poblar la base de datos con el seed automático (si está vacía).
# Centralizado en seed_db.py para mantener el código limpio y evitar ejecuciones redundantes.
from database import obtener_sesion
from models import Recorrido, Bus, Aviso
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




# ── AVISOS ──────────────────────────────────────────────────────


@app.route('/api/avisos', methods=['POST'])
def crear_aviso():
    """Crea un nuevo aviso. Solo accesible por administradores."""
    if session.get('user_rol') != 'admin':
        return jsonify({'error': 'Acceso denegado.'}), 403

    data = request.get_json()
    titulo       = (data.get('titulo') or '').strip()
    mensaje      = (data.get('mensaje') or '').strip()
    tipo         = data.get('tipo', 'info')
    duracion_dias = data.get('duracion_dias', 1)

    if not titulo or not mensaje:
        return jsonify({'error': 'El título y el mensaje son obligatorios.'}), 400
    if tipo not in ('alerta', 'info', 'precio', 'emergencia'):
        return jsonify({'error': 'Tipo de aviso no válido.'}), 400
    try:
        duracion_dias = int(duracion_dias)
    except (ValueError, TypeError):
        return jsonify({'error': 'La duración debe ser un número entero.'}), 400

    db = obtener_sesion()
    try:
        aviso = Aviso(
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo,
            duracion_dias=duracion_dias,
            activo=True,
            fecha_creacion=datetime.now(timezone.utc)
        )
        db.add(aviso)
        db.commit()
        db.refresh(aviso)
        return jsonify({
            'message': 'Aviso creado correctamente.',
            'aviso': {
                'id_aviso':      aviso.id_aviso,
                'titulo':        aviso.titulo,
                'mensaje':       aviso.mensaje,
                'tipo':          aviso.tipo,
                'duracion_dias': aviso.duracion_dias,
                'activo':        aviso.activo,
                'fecha_creacion': aviso.fecha_creacion.strftime('%Y-%m-%d %H:%M')
            }
        }), 201
    finally:
        db.close()


@app.route('/api/avisos', methods=['GET'])
def listar_avisos():
    """Lista todos los avisos (activos y expirados). Solo admin."""
    if session.get('user_rol') != 'admin':
        return jsonify({'error': 'Acceso denegado.'}), 403

    db = obtener_sesion()
    try:
        avisos = db.query(Aviso).order_by(Aviso.fecha_creacion.desc()).all()
        hoy = date.today()
        resultado = []
        for a in avisos:
            fecha_creacion = a.fecha_creacion
            if hasattr(fecha_creacion, 'date'):
                fecha_base = fecha_creacion.date()
            else:
                fecha_base = fecha_creacion
            from datetime import timedelta
            vigente = (fecha_base + timedelta(days=a.duracion_dias)) > hoy
            resultado.append({
                'id_aviso':       a.id_aviso,
                'titulo':         a.titulo,
                'mensaje':        a.mensaje,
                'tipo':           a.tipo,
                'duracion_dias':  a.duracion_dias,
                'activo':         a.activo,
                'vigente':        vigente,
                'fecha_creacion': a.fecha_creacion.strftime('%Y-%m-%d %H:%M')
            })
        return jsonify({'avisos': resultado}), 200
    finally:
        db.close()


@app.route('/api/avisos/activos', methods=['GET'])
def avisos_activos():
    """Devuelve los avisos vigentes para mostrar a los usuarios en el home.

    Un aviso es vigente si:
      - activo == True
      - fecha_creacion + duracion_dias > hoy
    """
    db = obtener_sesion()
    try:
        from datetime import timedelta
        hoy = date.today()
        todos = db.query(Aviso).filter(Aviso.activo == True).all()
        resultado = []
        for a in todos:
            fecha_base = a.fecha_creacion.date() if hasattr(a.fecha_creacion, 'date') else a.fecha_creacion
            if (fecha_base + timedelta(days=a.duracion_dias)) > hoy:
                resultado.append({
                    'id_aviso': a.id_aviso,
                    'titulo':   a.titulo,
                    'mensaje':  a.mensaje,
                    'tipo':     a.tipo,
                })
        return jsonify({'avisos': resultado}), 200
    finally:
        db.close()


@app.route('/api/avisos/<int:id_aviso>', methods=['PUT'])
def editar_aviso(id_aviso):
    """Edita un aviso existente. Solo admin."""
    if session.get('user_rol') != 'admin':
        return jsonify({'error': 'Acceso denegado.'}), 403

    db = obtener_sesion()
    try:
        aviso = db.query(Aviso).filter(Aviso.id_aviso == id_aviso).first()
        if not aviso:
            return jsonify({'error': 'Aviso no encontrado.'}), 404

        data = request.get_json()
        if 'titulo' in data:
            aviso.titulo = data['titulo'].strip()
        if 'mensaje' in data:
            aviso.mensaje = data['mensaje'].strip()
        if 'tipo' in data:
            if data['tipo'] not in ('alerta', 'info', 'precio', 'emergencia'):
                return jsonify({'error': 'Tipo de aviso no válido.'}), 400
            aviso.tipo = data['tipo']
        if 'duracion_dias' in data:
            aviso.duracion_dias = int(data['duracion_dias'])
        if 'activo' in data:
            aviso.activo = bool(data['activo'])

        db.commit()
        return jsonify({'message': 'Aviso actualizado correctamente.'}), 200
    finally:
        db.close()


@app.route('/api/avisos/<int:id_aviso>', methods=['DELETE'])
def eliminar_aviso(id_aviso):
    """Elimina un aviso de la BD. Solo admin."""
    if session.get('user_rol') != 'admin':
        return jsonify({'error': 'Acceso denegado.'}), 403

    db = obtener_sesion()
    try:
        aviso = db.query(Aviso).filter(Aviso.id_aviso == id_aviso).first()
        if not aviso:
            return jsonify({'error': 'Aviso no encontrado.'}), 404
        db.delete(aviso)
        db.commit()
        return jsonify({'message': 'Aviso eliminado correctamente.'}), 200
    finally:
        db.close()


if __name__ == '__main__':
    app.run(debug=True)
