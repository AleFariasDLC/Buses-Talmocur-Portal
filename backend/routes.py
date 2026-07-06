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
from datetime import datetime, timedelta, timezone
import bcrypt
import secrets

import db_sqlite as db
import utils
from database import obtener_sesion
from models import Asiento, AsientoComprado, Bus, Compra, HorarioViaje, Recorrido, Usuario
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

@routes.route('/api/asientos', methods=['GET'])
def obtener_asientos():
    patente = request.args.get('bus', '').strip()
    hora_salida = request.args.get('hora', '').strip()
    fecha_param = request.args.get('fecha', '').strip()

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

        hoy = date.today()
        try:
            fecha_consulta = date.fromisoformat(fecha_param) if fecha_param else hoy
        except ValueError:
            fecha_consulta = hoy

        sold_ids = set()
        if horario:
            sold_ids = {
                item.id_asiento
                for item in (
                    db_sess.query(AsientoComprado)
                    .join(Compra, AsientoComprado.id_compra == Compra.id_compra)
                    .join(HorarioViaje, Compra.id_horario == HorarioViaje.id_horario)
                    .filter(
                        HorarioViaje.patente == bus.patente,
                        HorarioViaje.hora_salida == horario.hora_salida,
                        Compra.fecha_viaje == fecha_consulta,
                        Compra.estado == 'confirmada'
                    )
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
    hora_salida = str(data.get('horaSalida', '')).strip()

    if not patente:
        return jsonify({'error': 'Faltan datos de la compra.'}), 400

    db_sess = obtener_sesion()
    try:
        bus = db_sess.query(Bus).filter(Bus.patente == patente).first()
        if not bus:
            bus = Bus(patente=patente, capacidad=40, estado='Activo')
            db_sess.add(bus)
            db_sess.commit()
            db_sess.refresh(bus)

        hora_obj = None
        if hora_salida:
            try:
                hora_obj = datetime.strptime(hora_salida, '%H:%M').time()
            except ValueError:
                hora_obj = None

        id_horario_req = data.get('idHorario')
        horario = None
        if id_horario_req:
            try:
                id_horario_req = int(id_horario_req)
                horario = db_sess.query(HorarioViaje).filter(HorarioViaje.id_horario == id_horario_req).first()
            except (TypeError, ValueError):
                horario = None

        if not horario and hora_obj:
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
        pasajeros = data.get('pasajeros')

        if pasajeros is None:
            asiento_numero = data.get('asiento')
            if asiento_numero is None:
                return jsonify({'error': 'Faltan datos de la compra.'}), 400
            try:
                asiento_numero = int(asiento_numero)
            except (TypeError, ValueError):
                return jsonify({'error': 'El asiento debe ser un número válido.'}), 400
            pasajeros = [{
                'asiento': asiento_numero,
                'nombre': data.get('nombre', 'Pasajero'),
                'rut': data.get('rut', ''),
                'email': data.get('email', ''),
                'telefono': data.get('telefono', ''),
                'tipoPasaje': data.get('tipoPasaje', 'adulto'),
                'observaciones': data.get('observaciones', ''),
            }]

        if not isinstance(pasajeros, list) or not pasajeros:
            return jsonify({'error': 'Debe enviar al menos un pasajero.'}), 400

        compras_creadas = []
        for pasajero in pasajeros:
            asiento_numero = pasajero.get('asiento')
            if asiento_numero is None:
                return jsonify({'error': 'Cada pasajero debe incluir un asiento.'}), 400
            try:
                asiento_numero = int(asiento_numero)
            except (TypeError, ValueError):
                return jsonify({'error': 'El asiento debe ser un número válido.'}), 400

            asiento = db_sess.query(Asiento).filter(
                Asiento.patente == bus.patente,
                Asiento.numero == asiento_numero,
            ).first()
            if not asiento:
                asiento = Asiento(numero=asiento_numero, patente=bus.patente)
                db_sess.add(asiento)
                db_sess.commit()
                db_sess.refresh(asiento)

            asiento_ya_vendido = (
                db_sess.query(AsientoComprado)
                .join(Compra, AsientoComprado.id_compra == Compra.id_compra)
                .join(HorarioViaje, Compra.id_horario == HorarioViaje.id_horario)
                .filter(
                    AsientoComprado.id_asiento == asiento.id_asiento,
                    HorarioViaje.patente == bus.patente,
                    HorarioViaje.hora_salida == horario.hora_salida,
                    Compra.fecha_viaje == fecha_viaje_obj,
                    Compra.estado == 'confirmada'
                )
                .first()
            )
            if asiento_ya_vendido:
                return jsonify({'error': f'El asiento {asiento_numero} ya está vendido.'}), 409

        for pasajero in pasajeros:
            asiento_numero = int(pasajero['asiento'])
            asiento = db_sess.query(Asiento).filter(
                Asiento.patente == bus.patente,
                Asiento.numero == asiento_numero,
            ).first()
            if not asiento:
                asiento = Asiento(numero=asiento_numero, patente=bus.patente)
                db_sess.add(asiento)
                db_sess.commit()
                db_sess.refresh(asiento)

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
                nombre_pasajero=str(pasajero.get('nombre', 'Pasajero') or 'Pasajero'),
                rut_pasajero=str(pasajero.get('rut', '') or ''),
                email_pasajero=str(pasajero.get('email', '') or ''),
                telefono_pasajero=str(pasajero.get('telefono', '') or ''),
                tipo_pasaje=str(pasajero.get('tipoPasaje', 'adulto') or 'adulto'),
                observaciones=str(pasajero.get('observaciones', '') or ''),
            )
            db_sess.add(asiento_comprado)
            db_sess.flush()
            compras_creadas.append({
                'id': compra.id_compra,
                'estado': compra.estado,
                'monto_total': compra.monto_total,
                'asiento': {
                    'numero': asiento.numero,
                    'estado': 'ocupado',
                },
                'pasajero': {
                    'nombre': asiento_comprado.nombre_pasajero,
                    'rut': asiento_comprado.rut_pasajero,
                    'email': asiento_comprado.email_pasajero,
                    'telefono': asiento_comprado.telefono_pasajero,
                    'tipoPasaje': asiento_comprado.tipo_pasaje,
                    'observaciones': asiento_comprado.observaciones,
                },
            })

        db_sess.commit()

        if len(compras_creadas) == 1:
            return jsonify({
                'success': True,
                'compra': compras_creadas[0],
                'compras': compras_creadas,
                'asiento': compras_creadas[0]['asiento'],
            })

        return jsonify({
            'success': True,
            'compras': compras_creadas,
            'asiento': {
                'numero': None,
                'estado': 'ocupado',
            },
        })
    except Exception:
        db_sess.rollback()
        raise
    finally:
        db_sess.close()

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
