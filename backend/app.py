from flask import Flask, render_template, redirect, make_response, session, jsonify, request
import os
import secrets
from datetime import date, datetime, timezone, timedelta
from sqlalchemy import func
from dotenv import load_dotenv

# Cargar variables de entorno antes de crear la app
load_dotenv()

# Inicializar y poblar la base de datos con el seed automático (si está vacía).
# Centralizado en seed_db.py para mantener el código limpio y evitar ejecuciones redundantes.
from database import obtener_sesion
from models import Recorrido, Bus, Aviso, Asiento, HorarioViaje, Compra, AsientoComprado, Suspension
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
        origenes = sorted({r.origen for r in recorridos if r.precio_base > 0})

        origen_seleccionado = request.args.get('origen', '').strip()
        destino_seleccionado = request.args.get('destino', '').strip()

        hoy = date.today()
        max_fecha = hoy + timedelta(days=30)
        fecha_param = request.args.get('fecha', '').strip()
        try:
            fecha_consulta = date.fromisoformat(fecha_param) if fecha_param else hoy
        except ValueError:
            fecha_consulta = hoy

        if fecha_consulta > max_fecha:
            fecha_consulta = max_fecha

        # Hora actual local del servidor (sin zona horaria, para comparar con time())
        # En la fecha seleccionada hoy se aplica un margen de 10 minutos; para otras fechas
        # se muestran todos los horarios activos porque el viaje aún no ha ocurrido.
        ahora = datetime.now()
        hora_minima = ahora.time() if fecha_consulta == hoy else None

        # IDs de horarios suspendidos para la fecha consultada
        suspendidos = {
            s.id_horario
            for s in db.query(Suspension).filter(
                Suspension.fecha_inicio <= fecha_consulta,
                Suspension.fecha_fin   >= fecha_consulta
            ).all()
        }

        # Contar asientos ya comprados por bus físico y hora (corrida compartida) para la fecha consultada
        compras_raw = (
            db.query(
                HorarioViaje.patente,
                HorarioViaje.hora_salida,
                func.count(AsientoComprado.id).label('ocupados')
            )
            .join(Compra, Compra.id_horario == HorarioViaje.id_horario)
            .join(AsientoComprado, AsientoComprado.id_compra == Compra.id_compra)
            .filter(
                Compra.fecha_viaje == fecha_consulta,
                Compra.estado == 'confirmada'
            )
            .group_by(HorarioViaje.patente, HorarioViaje.hora_salida)
            .all()
        )
        ocupados_por_corrida = {
            (fila.patente, fila.hora_salida): fila.ocupados
            for fila in compras_raw
        }

        filtros_horarios = [HorarioViaje.activo == True]
        if hora_minima is not None:
            filtros_horarios.append(HorarioViaje.hora_salida >= hora_minima)

        query_horarios = (
            db.query(HorarioViaje)
            .join(Recorrido, HorarioViaje.id_recorrido == Recorrido.id_recorrido)
            .join(Bus, HorarioViaje.patente == Bus.patente)
            .filter(Bus.estado == 'Activo')
        )
        if origen_seleccionado:
            query_horarios = query_horarios.filter(Recorrido.origen == origen_seleccionado)
        if destino_seleccionado:
            query_horarios = query_horarios.filter(Recorrido.destino == destino_seleccionado)

        horarios_raw = (
            query_horarios
            .filter(*filtros_horarios)
            .order_by(HorarioViaje.hora_salida, HorarioViaje.patente)
            .all()
        )

        pasajes_hoy = []
        for h in horarios_raw:
            if h.id_horario in suspendidos:
                continue

            capacidad        = h.bus.capacidad
            ocupados         = ocupados_por_corrida.get((h.patente, h.hora_salida), 0)
            asientos_libres  = capacidad - ocupados

            pasajes_hoy.append({
                'id_horario':     h.id_horario,
                'hora_salida':    h.hora_salida.strftime('%H:%M'),
                'hora_llegada':   h.hora_llegada.strftime('%H:%M'),
                'origen':         h.recorrido.origen,
                'destino':        h.recorrido.destino,
                'patente':        h.bus.patente,
                'precio':         int(h.precio_base),
                'asientos_libres': asientos_libres,
                'capacidad':      capacidad,
                'agotado':        asientos_libres <= 0,
                'pocas_plazas':   0 < asientos_libres <= 5,
                'duracion_estimada': h.recorrido.duracion_estimada,
            })

    finally:
        db.close()
    return render_template(
        'home.html',
        origenes=origenes,
        pasajes_hoy=pasajes_hoy,
        hoy=hoy,
        fecha_hoy=fecha_consulta,
        fecha_seleccionada=fecha_consulta.strftime('%Y-%m-%d'),
        origen_seleccionado=origen_seleccionado,
        destino_seleccionado=destino_seleccionado
    )


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

@app.route('/ruta-visual')
def ruta_visual():
    origen = request.args.get('origen', '')
    destino = request.args.get('destino', '')
    return render_template('ruta_visual.html', origen=origen, destino=destino)


@app.route('/quienes-somos')
def quienes_somos():
    return render_template('quienes_somos.html')

@app.route('/compra-pasajes')
def compra_pasajes():
    # no-store: evita que el navegador cachee esta página
    response = make_response(render_template('compra_pasajes.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/boleta')
def boleta():
    # no-store: la boleta no debe quedar en el historial de caché.
    response = make_response(render_template('boleta.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response


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

@app.route('/compra-pasajes-asientos')
def compra_pasajes_asientos():
    id_horario = request.args.get('horario', type=int)

    # Si no viene el parámetro, redirigir al home
    if not id_horario:
        return redirect('/')

    db = obtener_sesion()
    try:
        horario = db.query(HorarioViaje).filter(
            HorarioViaje.id_horario == id_horario
        ).first()

        if not horario or horario.bus.estado == 'En mantención':
            return redirect('/')

        fecha_param = request.args.get('fecha', '').strip()
        hoy = date.today()
        try:
            fecha_consulta = date.fromisoformat(fecha_param) if fecha_param else hoy
        except ValueError:
            fecha_consulta = hoy

        # Obtener los números de asiento ya ocupados para este recorrido físico (mismo bus y hora) y fecha
        compras_confirmadas = db.query(Compra).join(
            HorarioViaje, Compra.id_horario == HorarioViaje.id_horario
        ).filter(
            HorarioViaje.patente == horario.patente,
            HorarioViaje.hora_salida == horario.hora_salida,
            Compra.fecha_viaje == fecha_consulta,
            Compra.estado == 'confirmada'
        ).all()

        asientos_ocupados = []
        for compra in compras_confirmadas:
            for ac in compra.asientos_compra:
                asientos_ocupados.append(ac.asiento.numero)

        datos_viaje = {
            'id_horario':        horario.id_horario,
            'origen':            horario.recorrido.origen,
            'destino':           horario.recorrido.destino,
            'hora_salida':       horario.hora_salida.strftime('%H:%M'),
            'hora_llegada':      horario.hora_llegada.strftime('%H:%M'),
            'patente':           horario.bus.patente,
            'precio':            int(horario.precio_base),
            'capacidad':         horario.bus.capacidad,
            'asientos_ocupados': asientos_ocupados,  # lista de números [3, 7, 12, ...]
            'duracion_estimada': horario.recorrido.duracion_estimada,
            'fecha':             fecha_consulta.isoformat(),
        }

    finally:
        db.close()

    # no-store: los asientos ocupados deben obtenerse frescos del servidor
    response = make_response(render_template('compra_pasajes_asientos.html', viaje=datos_viaje))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

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


# ── BUSES ────────────────────────────────────────────────────────


@app.route('/api/buses', methods=['GET'])
def listar_buses():
    """Lista todos los buses con sus horarios. Solo admin."""
    if session.get('user_rol') != 'admin':
        return jsonify({'error': 'Acceso denegado.'}), 403

    db = obtener_sesion()
    try:
        buses = db.query(Bus).order_by(Bus.patente).all()
        resultado = []
        for b in buses:
            horarios = []
            for h in sorted(b.horarios, key=lambda x: x.hora_salida):
                horarios.append({
                    'id_horario':  h.id_horario,
                    'recorrido':   f"{h.recorrido.origen} → {h.recorrido.destino}",
                    'hora_salida': h.hora_salida.strftime('%H:%M'),
                    'hora_llegada':h.hora_llegada.strftime('%H:%M'),
                    'precio_base': h.precio_base,
                    'activo':      h.activo,
                })
            resultado.append({
                'patente':        b.patente,
                'modelo':         b.modelo or '',
                'chofer':         b.chofer or '',
                'capacidad':      b.capacidad,
                'estado':         b.estado,
                'total_horarios': len(horarios),
                'horarios':       horarios,
            })
        return jsonify({'buses': resultado, 'total': len(resultado)}), 200
    finally:
        db.close()


@app.route('/api/buses', methods=['POST'])
def crear_bus():
    """Crea un bus nuevo con sus asientos físicos. Solo admin."""
    if session.get('user_rol') != 'admin':
        return jsonify({'error': 'Acceso denegado.'}), 403

    data      = request.get_json()
    patente   = (data.get('patente') or '').strip().upper()
    chofer    = (data.get('chofer')   or '').strip()
    modelo    = (data.get('modelo')   or '').strip()
    capacidad = int(data.get('capacidad', 44))
    estado    = data.get('estado', 'Activo')

    if not patente:
        return jsonify({'error': 'La patente es obligatoria.'}), 400
    if capacidad < 1 or capacidad > 200:
        return jsonify({'error': 'La capacidad debe estar entre 1 y 200.'}), 400

    db = obtener_sesion()
    try:
        if db.query(Bus).filter(Bus.patente == patente).first():
            return jsonify({'error': 'Ya existe un bus con esa patente.'}), 409

        bus = Bus(patente=patente, chofer=chofer, modelo=modelo,
                  capacidad=capacidad, estado=estado)
        db.add(bus)
        db.flush()

        for num in range(1, capacidad + 1):
            db.add(Asiento(numero=num, patente=patente))

        db.commit()
        return jsonify({'message': 'Bus creado correctamente.', 'patente': patente}), 201
    finally:
        db.close()


@app.route('/api/buses/<patente>', methods=['PUT'])
def editar_bus(patente):
    """Edita datos de un bus (excepto patente y capacidad). Solo admin."""
    if session.get('user_rol') != 'admin':
        return jsonify({'error': 'Acceso denegado.'}), 403

    db = obtener_sesion()
    try:
        bus = db.query(Bus).filter(Bus.patente == patente).first()
        if not bus:
            return jsonify({'error': 'Bus no encontrado.'}), 404

        data = request.get_json()
        if 'chofer' in data: bus.chofer = data['chofer'].strip()
        if 'modelo' in data: bus.modelo = data['modelo'].strip()
        if 'estado' in data: bus.estado = data['estado']

        db.commit()
        return jsonify({'message': 'Bus actualizado correctamente.'}), 200
    finally:
        db.close()


@app.route('/api/buses/<patente>', methods=['DELETE'])
def eliminar_bus(patente):
    """Elimina un bus, sus asientos y sus horarios. Solo admin."""
    if session.get('user_rol') != 'admin':
        return jsonify({'error': 'Acceso denegado.'}), 403

    db = obtener_sesion()
    try:
        bus = db.query(Bus).filter(Bus.patente == patente).first()
        if not bus:
            return jsonify({'error': 'Bus no encontrado.'}), 404

        # Eliminar horarios vinculados (y sus compras y suspensiones asociadas)
        for h in list(bus.horarios):
            for c in list(h.compras):
                db.delete(c)
            for s in list(h.suspensiones):
                db.delete(s)
            db.delete(h)

        # Eliminar asientos físicos
        db.query(Asiento).filter(Asiento.patente == patente).delete()

        db.delete(bus)
        db.commit()
        return jsonify({'message': 'Bus eliminado correctamente.'}), 200
    finally:
        db.close()


# ── RECORRIDOS (lectura pública para dropdowns) ───────────────────

@app.route('/api/recorridos', methods=['GET'])
def listar_recorridos():
    """Lista todos los recorridos. Público (para formularios de horario)."""
    db = obtener_sesion()
    try:
        recorridos = db.query(Recorrido).order_by(Recorrido.id_recorrido).all()
        return jsonify({'recorridos': [
            {'id': r.id_recorrido,
             'nombre': f"{r.origen} → {r.destino}",
             'origen': r.origen,
             'destino': r.destino,
             'precio_base': r.precio_base,
             'duracion_estimada': r.duracion_estimada}
            for r in recorridos
        ]}), 200
    finally:
        db.close()


@app.route('/api/recorridos/<int:id_recorrido>', methods=['PUT'])
def editar_tarifa_recorrido(id_recorrido):
    if session.get('user_rol') != 'admin':
        return jsonify({'error': 'Acceso denegado.'}), 403

    data = request.get_json() or {}
    precio_base = data.get('precio_base')

    if precio_base is None:
        return jsonify({'error': 'El precio base es obligatorio.'}), 400

    try:
        precio_base = float(precio_base)
        if precio_base <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({'error': 'El precio base debe ser un número positivo.'}), 400

    db = obtener_sesion()
    try:
        recorrido = db.query(Recorrido).filter(Recorrido.id_recorrido == id_recorrido).first()
        if not recorrido:
            return jsonify({'error': 'Recorrido no encontrado.'}), 404

        # Actualizar precio base del recorrido
        recorrido.precio_base = precio_base

        # Actualizar todos los horarios de viaje asociados a este recorrido
        horarios = db.query(HorarioViaje).filter(HorarioViaje.id_recorrido == id_recorrido).all()
        for h in horarios:
            h.precio_base = precio_base

        db.commit()
        return jsonify({
            'message': 'Tarifa general actualizada correctamente para todos los buses.',
            'recorrido': {
                'id': recorrido.id_recorrido,
                'origen': recorrido.origen,
                'destino': recorrido.destino,
                'precio_base': recorrido.precio_base
            }
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': f'Error al actualizar tarifa: {str(e)}'}), 500
    finally:
        db.close()


# ── HORARIOS ─────────────────────────────────────────────────────

def check_horario_conflict(db, patente, id_recorrido, hora_salida, ignore_id_horario=None):
    """
    Verifica si existe un conflicto de horario para un bus según las reglas:
    - Permitir exactamente la misma hora si comparten origen (tramos/sub-rutas).
    - 2 horas de diferencia si es el mismo recorrido.
    - 1 hora de diferencia si cambia de recorrido.
    Retorna (boolean_conflicto, mensaje_error)
    """
    prop_minutos = hora_salida.hour * 60 + hora_salida.minute

    query = db.query(HorarioViaje).filter(HorarioViaje.patente == patente)
    if ignore_id_horario is not None:
        query = query.filter(HorarioViaje.id_horario != ignore_id_horario)
    
    horarios_existentes = query.all()
    new_rec = db.query(Recorrido).filter(Recorrido.id_recorrido == id_recorrido).first()
    if not new_rec:
        return True, "Recorrido no encontrado."

    for h in horarios_existentes:
        exist_minutos = h.hora_salida.hour * 60 + h.hora_salida.minute
        diff_minutos = abs(prop_minutos - exist_minutos)
        
        # Permitir mismo bus en el mismo horario si son sub-recorridos compartidos
        if diff_minutos == 0:
            if h.id_recorrido == id_recorrido:
                return True, (
                    f"El bus ya tiene asignado este recorrido ({h.recorrido.origen} → {h.recorrido.destino}) "
                    f"a las {h.hora_salida.strftime('%H:%M')}."
                )
            if h.recorrido.origen == new_rec.origen:
                continue
            else:
                return True, (
                    f"Conflicto físico: El bus ya tiene una salida a las {h.hora_salida.strftime('%H:%M')} "
                    f"desde un origen diferente ({h.recorrido.origen})."
                )

        if h.id_recorrido == id_recorrido:
            # Mismo recorrido -> requiere 2 horas (120 minutos)
            if diff_minutos < 120:
                return True, (
                    f"No se puede registrar este recorrido. El bus ya tiene un viaje programado para el mismo recorrido "
                    f"a las {h.hora_salida.strftime('%H:%M')}. "
                    f"Debe haber al menos 2 horas de diferencia."
                )
        else:
            # Recorrido diferente -> requiere 1 hora (60 minutos)
            if diff_minutos < 60:
                return True, (
                    f"No se puede registrar este recorrido. El bus ya tiene un viaje programado para un recorrido diferente "
                    f"a las {h.hora_salida.strftime('%H:%M')}. "
                    f"Debe haber al menos 1 hora de diferencia."
                )
                
    return False, ""


@app.route('/api/horarios', methods=['POST'])
def crear_horario():
    """Agrega un horario a un bus con validación de conflictos. Solo admin."""
    if session.get('user_rol') != 'admin':
        return jsonify({'error': 'Acceso denegado.'}), 403

    data         = request.get_json()
    patente      = data.get('patente')
    id_recorrido = int(data.get('id_recorrido'))
    hora_str     = data.get('hora_salida', '')
    precio_base  = float(data.get('precio_base', 3500))
    activo       = bool(data.get('activo', True))

    if not patente or not id_recorrido or not hora_str:
        return jsonify({'error': 'Faltan campos obligatorios.'}), 400

    db = obtener_sesion()
    try:
        if not db.query(Bus).filter(Bus.patente == patente).first():
            return jsonify({'error': 'Bus no encontrado.'}), 404
        
        recorrido = db.query(Recorrido).filter(Recorrido.id_recorrido == id_recorrido).first()
        if not recorrido:
            return jsonify({'error': 'Recorrido no encontrado.'}), 404

        partes = hora_str.split(':')
        h, m = int(partes[0]), int(partes[1])
        base    = datetime(2000, 1, 1, h, m)
        llegada = (base + timedelta(minutes=recorrido.duracion_estimada)).time()

        # Validar conflicto de horarios
        conflicto, msg = check_horario_conflict(db, patente, id_recorrido, base.time())
        if conflicto:
            return jsonify({'error': msg}), 400

        horario = HorarioViaje(
            id_recorrido=id_recorrido,
            patente=patente,
            hora_salida=base.time(),
            hora_llegada=llegada,
            precio_base=precio_base,
            activo=activo,
        )
        db.add(horario)
        db.commit()
        db.refresh(horario)
        return jsonify({'message': 'Horario creado.', 'id_horario': horario.id_horario}), 201
    finally:
        db.close()


@app.route('/api/horarios/<int:id_horario>', methods=['PUT'])
def editar_horario(id_horario):
    """Edita precio, estado activo o la hora de salida de un horario con validación. Solo admin."""
    if session.get('user_rol') != 'admin':
        return jsonify({'error': 'Acceso denegado.'}), 403

    db = obtener_sesion()
    try:
        h = db.query(HorarioViaje).filter(HorarioViaje.id_horario == id_horario).first()
        if not h:
            return jsonify({'error': 'Horario no encontrado.'}), 404

        data = request.get_json()
        
        # Si se edita la hora de salida, debemos comprobar conflictos
        if 'hora_salida' in data:
            partes = data['hora_salida'].split(':')
            hh, mm = int(partes[0]), int(partes[1])
            base = datetime(2000, 1, 1, hh, mm)
            new_time = base.time()
            
            # Recorrido a evaluar: el actual o el nuevo si viniera
            rec_eval = int(data.get('id_recorrido', h.id_recorrido))
            recorrido = db.query(Recorrido).filter(Recorrido.id_recorrido == rec_eval).first()
            duracion = recorrido.duracion_estimada if recorrido else 45
            
            conflicto, msg = check_horario_conflict(db, h.patente, rec_eval, new_time, ignore_id_horario=id_horario)
            if conflicto:
                return jsonify({'error': msg}), 400
                
            h.hora_salida  = new_time
            h.hora_llegada = (base + timedelta(minutes=duracion)).time()

        if 'precio_base' in data:
            h.precio_base = float(data['precio_base'])
        if 'activo' in data:
            h.activo = bool(data['activo'])

        db.commit()
        return jsonify({'message': 'Horario actualizado.'}), 200
    finally:
        db.close()


@app.route('/api/horarios/<int:id_horario>', methods=['DELETE'])
def eliminar_horario(id_horario):
    """Elimina un horario de viaje. Solo admin."""
    if session.get('user_rol') != 'admin':
        return jsonify({'error': 'Acceso denegado.'}), 403

    db = obtener_sesion()
    try:
        h = db.query(HorarioViaje).filter(HorarioViaje.id_horario == id_horario).first()
        if not h:
            return jsonify({'error': 'Horario no encontrado.'}), 404
        # Eliminar compras y suspensiones asociadas
        for c in list(h.compras):
            db.delete(c)
        for s in list(h.suspensiones):
            db.delete(s)
        db.delete(h)
        db.commit()
        return jsonify({'message': 'Horario eliminado.'}), 200
    finally:
        db.close()


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
    if session.get('avisos_mostrados') is True:
        return jsonify({'avisos': []}), 200

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
        
        if 'user_id' in session:
            session['avisos_mostrados'] = True

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
