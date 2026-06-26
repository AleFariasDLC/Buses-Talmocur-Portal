"""
routes.py — Rutas API para autenticación de usuarios.

Endpoints:
    POST /api/register  — Crear una nueva cuenta
    POST /api/login     — Iniciar sesión
    POST /api/logout    — Cerrar sesión
    GET  /api/me        — Obtener datos del usuario logueado
"""

from datetime import date, datetime, time, timedelta, timezone

from flask import Blueprint, request, jsonify, session
import bcrypt

import db_sqlite as db
import utils
from database import obtener_sesion
from models import Asiento, AsientoComprado, Bus, Compra, HorarioViaje, Recorrido, Usuario

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


@routes.route('/api/asientos', methods=['GET'])
def obtener_asientos():
    patente = request.args.get('bus', '').strip()
    hora_salida = request.args.get('hora', '').strip()

    if not patente:
        return jsonify({'error': 'Falta el parámetro bus.'}), 400

    db_sess = obtener_sesion()
    try:
        bus = db_sess.query(Bus).filter(Bus.patente == patente).first()
        if not bus:
            bus = Bus(patente=patente, capacidad=40, estado='Activo')
            db_sess.add(bus)
            db_sess.commit()
            db_sess.refresh(bus)

        if db_sess.query(Asiento).filter(Asiento.patente == bus.patente).count() == 0:
            for numero in range(1, bus.capacidad + 1):
                db_sess.add(Asiento(numero=numero, patente=bus.patente))
            db_sess.commit()

        hora_obj = None
        if hora_salida:
            try:
                hora_obj = datetime.strptime(hora_salida, '%H:%M').time()
            except ValueError:
                hora_obj = None

        horario = None
        if hora_obj:
            horario = (
                db_sess.query(HorarioViaje)
                .filter(HorarioViaje.patente == bus.patente, HorarioViaje.hora_salida == hora_obj)
                .first()
            )
        if not horario:
            horario = db_sess.query(HorarioViaje).filter(HorarioViaje.patente == bus.patente).first()

        sold_ids = set()
        if horario:
            sold_ids = {
                item.id_asiento
                for item in (
                    db_sess.query(AsientoComprado)
                    .join(Compra, AsientoComprado.id_compra == Compra.id_compra)
                    .filter(Compra.id_horario == horario.id_horario)
                    .all()
                )
            }

        asientos = (
            db_sess.query(Asiento)
            .filter(Asiento.patente == bus.patente)
            .order_by(Asiento.numero)
            .all()
        )

        payload = []
        for asiento in asientos:
            payload.append({
                'id': asiento.id_asiento,
                'numero': asiento.numero,
                'estado': 'ocupado' if asiento.id_asiento in sold_ids else 'libre'
            })

        return jsonify({
            'bus': {
                'patente': bus.patente,
                'capacidad': bus.capacidad,
                'estado': bus.estado,
            },
            'asientos': payload,
            'hora': hora_salida,
        })
    finally:
        db_sess.close()


@routes.route('/api/confirmar-compra', methods=['POST'])
def confirmar_compra():
    data = request.get_json(silent=True) or {}
    patente = str(data.get('patente', '')).strip()
    asiento_numero = data.get('asiento')
    hora_salida = str(data.get('horaSalida', '')).strip()

    if not patente or asiento_numero is None:
        return jsonify({'error': 'Faltan datos de la compra.'}), 400

    try:
        asiento_numero = int(asiento_numero)
    except (TypeError, ValueError):
        return jsonify({'error': 'El asiento debe ser un número válido.'}), 400

    db_sess = obtener_sesion()
    try:
        bus = db_sess.query(Bus).filter(Bus.patente == patente).first()
        if not bus:
            bus = Bus(patente=patente, capacidad=40, estado='Activo')
            db_sess.add(bus)
            db_sess.commit()
            db_sess.refresh(bus)

        asiento = db_sess.query(Asiento).filter(
            Asiento.patente == bus.patente,
            Asiento.numero == asiento_numero,
        ).first()
        if not asiento:
            asiento = Asiento(numero=asiento_numero, patente=bus.patente)
            db_sess.add(asiento)
            db_sess.commit()
            db_sess.refresh(asiento)

        hora_obj = None
        if hora_salida:
            try:
                hora_obj = datetime.strptime(hora_salida, '%H:%M').time()
            except ValueError:
                hora_obj = None

        horario = None
        if hora_obj:
            horario = (
                db_sess.query(HorarioViaje)
                .filter(HorarioViaje.patente == bus.patente, HorarioViaje.hora_salida == hora_obj)
                .first()
            )

        if not horario:
            recorrido = db_sess.query(Recorrido).first()
            if not recorrido:
                recorrido = Recorrido(origen='Curicó', destino='Talca', tipo='ida', precio_base=3500.0)
                db_sess.add(recorrido)
                db_sess.commit()
                db_sess.refresh(recorrido)

            horario = HorarioViaje(
                id_recorrido=recorrido.id_recorrido,
                patente=bus.patente,
                hora_salida=hora_obj or time(7, 0),
                hora_llegada=(datetime.combine(date.today(), hora_obj or time(7, 0)) + timedelta(hours=1)).time(),
                precio_base=float(data.get('precio', 2800) or 2800),
                activo=True,
            )
            db_sess.add(horario)
            db_sess.commit()
            db_sess.refresh(horario)

        asiento_ya_vendido = (
            db_sess.query(AsientoComprado)
            .join(Compra, AsientoComprado.id_compra == Compra.id_compra)
            .filter(AsientoComprado.id_asiento == asiento.id_asiento, Compra.id_horario == horario.id_horario)
            .first()
        )
        if asiento_ya_vendido:
            return jsonify({'error': 'Ese asiento ya está vendido.'}), 409

        usuario_id = session.get('user_id')
        if not usuario_id:
            usuario = db_sess.query(Usuario).filter(Usuario.email == 'invitado@talmocur.local').first()
            if not usuario:
                import uuid
                usuario = Usuario(
                    id=str(uuid.uuid4()),
                    nombre='Pasajero invitado',
                    email='invitado@talmocur.local',
                    password_hash='guest',
                    rol='pasajero',
                )
                db_sess.add(usuario)
                db_sess.commit()
                db_sess.refresh(usuario)
            usuario_id = usuario.id

        fecha_viaje = data.get('fechaViaje') or date.today().isoformat()
        try:
            fecha_viaje_obj = date.fromisoformat(str(fecha_viaje))
        except ValueError:
            fecha_viaje_obj = date.today()

        monto_total = float(data.get('precio', 2800) or 2800)
        compra = Compra(
            id_usuario=usuario_id,
            id_horario=horario.id_horario,
            fecha_viaje=fecha_viaje_obj,
            monto_total=monto_total,
            metodo_pago='simulado',
            estado='confirmada',
        )
        db_sess.add(compra)
        db_sess.flush()

        asiento_comprado = AsientoComprado(
            id_compra=compra.id_compra,
            id_asiento=asiento.id_asiento,
            precio_unitario=monto_total,
        )
        db_sess.add(asiento_comprado)
        db_sess.commit()
        db_sess.refresh(compra)

        return jsonify({
            'success': True,
            'compra': {
                'id': compra.id_compra,
                'estado': compra.estado,
                'monto_total': compra.monto_total,
                'asiento': asiento.numero,
            },
            'asiento': {
                'numero': asiento.numero,
                'estado': 'ocupado',
            },
        })
    except Exception:
        db_sess.rollback()
        raise
    finally:
        db_sess.close()