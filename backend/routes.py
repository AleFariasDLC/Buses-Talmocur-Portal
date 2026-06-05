"""
routes.py — Rutas API para autenticación de usuarios.

Endpoints:
    POST /api/register  — Crear una nueva cuenta
    POST /api/login     — Iniciar sesión
    POST /api/logout    — Cerrar sesión
    GET  /api/me        — Obtener datos del usuario logueado
"""

from flask import Blueprint, request, jsonify, session
import bcrypt

import db_json
import utils

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
    if db_json.buscar_usuario_por_email(email):
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

    usuario = db_json.crear_usuario(nombre, email, password_hash)

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
    usuario = db_json.buscar_usuario_por_email(email)
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

    return jsonify({
        'message': 'Sesión iniciada correctamente.',
        'usuario': {
            'id': usuario['id'],
            'nombre': usuario['nombre'],
            'email': usuario['email']
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

    usuario = db_json.buscar_usuario_por_id(user_id)
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