"""
routes.py — Rutas API para autenticación de usuarios.

Endpoints:
    POST /api/register  — Crear una nueva cuenta
    POST /api/login     — Iniciar sesión
    POST /api/logout    — Cerrar sesión
    GET  /api/me        — Obtener datos del usuario logueado
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta, timezone
import bcrypt
import secrets

import db_sqlite as db
import utils
import email_utils

# Validez del enlace de recuperación de contraseña
TOKEN_VALIDEZ_HORAS = 1

routes = Blueprint('routes', __name__)


# ── REGISTRO ─────────────────────────────────────────────────────
@routes.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()

    # Extraer campos
    nombre = data.get('nombre', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirmPassword', '')

    # ── Validaciones ──────────────────────────────────────────
    # Nombre requerido
    if not nombre:
        return jsonify({'error': 'El nombre completo es obligatorio.'}), 400

    # Validar email
    resultado_email = utils.validar_email(email)
    if resultado_email is not True:
        return jsonify({'error': resultado_email}), 400

    # Verificar que el email no esté registrado
    if db.buscar_usuario_por_email(email):
        return jsonify({'error': 'Ya existe una cuenta con este correo electrónico.'}), 409

    # Validar contraseña
    resultado_password = utils.validar_password(password)
    if resultado_password is not True:
        return jsonify({'error': resultado_password}), 400

    # Confirmar que las contraseñas coinciden
    if password != confirm_password:
        return jsonify({'error': 'Las contraseñas no coinciden.'}), 400

    # ── Hashear contraseña y guardar ──────────────────────────
    password_hash = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    usuario = db.crear_usuario(nombre, email, password_hash)

    return jsonify({
        'message': 'Cuenta creada exitosamente.',
        'usuario': usuario
    }), 201


# ── LOGIN ────────────────────────────────────────────────────────
@routes.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Correo y contraseña son obligatorios.'}), 400

    # Buscar usuario
    usuario = db.buscar_usuario_por_email(email)
    if not usuario:
        return jsonify({'error': 'Correo o contraseña incorrectos.'}), 401

    # Verificar contraseña contra el hash
    if not bcrypt.checkpw(
        password.encode('utf-8'),
        usuario['password_hash'].encode('utf-8')
    ):
        return jsonify({'error': 'Correo o contraseña incorrectos.'}), 401

    # ── Crear sesión ──────────────────────────────────────────
    session['user_id'] = usuario['id']
    session['user_nombre'] = usuario['nombre']
    session['user_email'] = usuario['email']
    session['user_rol'] = usuario['rol']

    return jsonify({
        'message': 'Sesión iniciada correctamente.',
        'usuario': {
            'id': usuario['id'],
            'nombre': usuario['nombre'],
            'email': usuario['email'],
            'rol': usuario['rol']
        }
    }), 200


# ── LOGOUT ───────────────────────────────────────────────────────
@routes.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Sesión cerrada correctamente.'}), 200


# ── OBTENER USUARIO ACTUAL ───────────────────────────────────────
@routes.route('/api/me', methods=['GET'])
def me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'No hay sesión activa.'}), 401

    usuario = db.buscar_usuario_por_id(user_id)
    if not usuario:
        session.clear()
        return jsonify({'error': 'Usuario no encontrado.'}), 404

    return jsonify({
        'usuario': {
            'id': usuario['id'],
            'nombre': usuario['nombre'],
            'email': usuario['email'],
            'fecha_registro': usuario['fecha_registro']
        }
    }), 200

# ── EDITAR PERFIL ────────────────────────────────────────────────
@routes.route('/api/me', methods=['PUT'])
def actualizar_perfil():
    """Actualiza el nombre, email y (opcionalmente) la contraseña del usuario logueado.

    Body JSON:
        nombre           (str)  obligatorio
        email            (str)  obligatorio
        currentPassword  (str)  obligatorio SOLO si se quiere cambiar la contraseña
        password         (str)  opcional — nueva contraseña
        confirmPassword  (str)  opcional — confirmación de la nueva contraseña
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'No hay sesión activa.'}), 401

    data = request.get_json() or {}
    nombre = data.get('nombre', '').strip()
    email = data.get('email', '').strip()

    # ── Validar nombre ──
    if not nombre:
        return jsonify({'error': 'El nombre completo es obligatorio.'}), 400

    # ── Validar email ──
    resultado_email = utils.validar_email(email)
    if resultado_email is not True:
        return jsonify({'error': resultado_email}), 400

    # ── Email no puede pertenecer a OTRO usuario ──
    otro = db.buscar_usuario_por_email(email)
    if otro and otro['id'] != user_id:
        return jsonify({'error': 'Ya existe una cuenta con este correo electrónico.'}), 409

    cambios = {'nombre': nombre, 'email': email.lower()}

    # ── Cambio de contraseña (opcional) ──
    nueva_password = data.get('password', '')
    if nueva_password:
        confirm = data.get('confirmPassword', '')
        actual = data.get('currentPassword', '')

        # Verificar la contraseña actual antes de permitir el cambio
        usuario_actual = db.buscar_usuario_por_id(user_id)
        # Necesitamos el hash → lo buscamos por email (incluye hash)
        usuario_con_hash = db.buscar_usuario_por_email(usuario_actual['email'])
        if not actual or not bcrypt.checkpw(
            actual.encode('utf-8'),
            usuario_con_hash['password_hash'].encode('utf-8')
        ):
            return jsonify({'error': 'La contraseña actual es incorrecta.'}), 401

        # Validar fortaleza de la nueva contraseña
        resultado_password = utils.validar_password(nueva_password)
        if resultado_password is not True:
            return jsonify({'error': resultado_password}), 400

        if nueva_password != confirm:
            return jsonify({'error': 'Las contraseñas no coinciden.'}), 400

        cambios['password_hash'] = bcrypt.hashpw(
            nueva_password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    # ── Guardar cambios ──
    usuario = db.actualizar_usuario(user_id, cambios)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado.'}), 404

    # Mantener la sesión sincronizada con los nuevos datos
    session['user_nombre'] = usuario['nombre']
    session['user_email'] = usuario['email']

    return jsonify({
        'message': 'Perfil actualizado correctamente.',
        'usuario': {
            'id': usuario['id'],
            'nombre': usuario['nombre'],
            'email': usuario['email'],
            'rol': usuario['rol']
        }
    }), 200


# ── SOLICITAR RECUPERACIÓN DE CONTRASEÑA ─────────────────────────
@routes.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    """Genera un enlace de recuperación y lo envía por correo.

    Por seguridad SIEMPRE responde lo mismo, exista o no el email (evita que
    alguien descubra qué correos están registrados).
    """
    data = request.get_json() or {}
    email = data.get('email', '').strip()

    if not email:
        return jsonify({'error': 'El correo electrónico es obligatorio.'}), 400

    mensaje_generico = ('Si el correo está registrado, te enviamos un enlace '
                        'para restablecer tu contraseña.')
    respuesta = {'message': mensaje_generico}

    usuario = db.buscar_usuario_por_email(email)
    if usuario:
        # Invalidar enlaces anteriores y crear uno nuevo
        db.invalidar_tokens_de_usuario(usuario['id'])
        token = secrets.token_urlsafe(32)
        expira = datetime.now(timezone.utc) + timedelta(hours=TOKEN_VALIDEZ_HORAS)
        db.crear_token_recuperacion(usuario['id'], token, expira)

        enlace = request.host_url.rstrip('/') + '/restablecer?token=' + token
        cuerpo = (
            f"Hola {usuario['nombre']},\n\n"
            f"Recibimos una solicitud para restablecer tu contraseña en Talmocur.\n"
            f"Abre el siguiente enlace (válido por {TOKEN_VALIDEZ_HORAS} hora):\n\n"
            f"{enlace}\n\n"
            f"Si no fuiste tú, ignora este mensaje: tu contraseña no cambiará.\n"
        )
        enviado = email_utils.enviar_correo(
            usuario['email'], 'Recupera tu contraseña — Talmocur', cuerpo
        )

        # En modo desarrollo (sin SMTP) devolvemos el enlace para poder probar.
        from flask import current_app
        if current_app.debug and not enviado:
            respuesta['reset_url'] = enlace

    return jsonify(respuesta), 200


# ── RESTABLECER CONTRASEÑA CON TOKEN ─────────────────────────────
@routes.route('/api/reset-password', methods=['POST'])
def reset_password():
    """Cambia la contraseña usando un token válido recibido por correo."""
    data = request.get_json() or {}
    token = data.get('token', '').strip()
    password = data.get('password', '')
    confirm = data.get('confirmPassword', '')

    if not token:
        return jsonify({'error': 'Falta el token de recuperación.'}), 400

    usuario, vigente = db.buscar_token_recuperacion(token)
    if not usuario or not vigente:
        return jsonify({'error': 'El enlace no es válido o ya expiró. '
                                 'Solicita uno nuevo.'}), 400

    # Validar la nueva contraseña
    resultado_password = utils.validar_password(password)
    if resultado_password is not True:
        return jsonify({'error': resultado_password}), 400

    if password != confirm:
        return jsonify({'error': 'Las contraseñas no coinciden.'}), 400

    # Guardar la nueva contraseña y quemar el token
    password_hash = bcrypt.hashpw(
        password.encode('utf-8'), bcrypt.gensalt()
    ).decode('utf-8')
    db.actualizar_usuario(usuario['id'], {'password_hash': password_hash})
    db.marcar_token_usado(token)

    return jsonify({'message': 'Contraseña actualizada. Ya puedes iniciar sesión.'}), 200
