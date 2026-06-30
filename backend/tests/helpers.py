"""
helpers.py — Funciones y constantes reutilizables para los tests.

Contiene datos de prueba y funciones helper que simplifican la escritura
de tests de integración (registro, login, etc.).
"""

import bcrypt


# ── Datos de prueba reutilizables ────────────────────────────────

USUARIO_VALIDO = {
    'nombre': 'Juan Pérez',
    'email': 'juan@correo.com',
    'password': 'MiClave123!',
    'confirmPassword': 'MiClave123!'
}

ADMIN_VALIDO = {
    'nombre': 'Admin Talmocur',
    'email': 'admin@talmocur.cl',
    'password': 'AdminClave123!',
}


# ── Helpers de usuario ──────────────────────────────────────────

def registrar_usuario(client, datos=None):
    """Registra un usuario vía la API. Retorna la Response de Flask.

    Args:
        client: fixture client de Flask.
        datos: dict con los campos del formulario. Si es None, usa USUARIO_VALIDO.
    """
    payload = datos if datos is not None else USUARIO_VALIDO.copy()
    return client.post(
        '/api/register',
        json=payload,
        content_type='application/json',
    )


def login_usuario(client, email=None, password=None):
    """Hace login vía la API. Retorna la Response de Flask.

    Args:
        client: fixture client de Flask.
        email: correo del usuario (por defecto usa USUARIO_VALIDO).
        password: contraseña (por defecto usa USUARIO_VALIDO).
    """
    return client.post(
        '/api/login',
        json={
            'email': email or USUARIO_VALIDO['email'],
            'password': password or USUARIO_VALIDO['password'],
        },
        content_type='application/json',
    )


# ── Helpers de administrador ────────────────────────────────────

def registrar_y_login_admin(client):
    """Crea un usuario admin directamente en la BD y lo logea vía la API.

    Crea el usuario con rol 'admin' via db_sqlite (no pasa por la API de
    registro que siempre asigna rol 'pasajero') y luego hace login normal.
    Retorna la Response del login.
    """
    import db_sqlite as db

    password_hash = bcrypt.hashpw(
        ADMIN_VALIDO['password'].encode('utf-8'),
        bcrypt.gensalt(),
    ).decode('utf-8')

    usuario = db.crear_usuario(
        ADMIN_VALIDO['nombre'],
        ADMIN_VALIDO['email'],
        password_hash,
    )
    # Promover a admin (crear_usuario siempre asigna 'pasajero')
    db.actualizar_usuario(usuario['id'], {'rol': 'admin'})

    return login_usuario(
        client,
        email=ADMIN_VALIDO['email'],
        password=ADMIN_VALIDO['password'],
    )


# ── Helpers de datos de prueba (buses, recorridos) ──────────────

def crear_bus_test(client, patente='TEST-01', capacidad=10):
    """Crea un bus vía la API (requiere sesión de admin). Retorna la Response."""
    return client.post('/api/buses', json={
        'patente': patente,
        'capacidad': capacidad,
        'modelo': 'Bus de prueba',
        'chofer': 'Chofer Test',
        'estado': 'Activo',
    })


def crear_recorrido_test(db_session):
    """Crea un recorrido directamente en la BD. Retorna el objeto Recorrido."""
    from models import Recorrido

    recorrido = Recorrido(
        origen='Curicó', destino='Talca', tipo='ida', precio_base=3500.0,
    )
    db_session.add(recorrido)
    db_session.commit()
    db_session.refresh(recorrido)
    return recorrido


def crear_horario_test(client, patente, id_recorrido, hora='08:00', precio=3500):
    """Crea un horario vía la API (requiere sesión de admin). Retorna la Response."""
    return client.post('/api/horarios', json={
        'patente': patente,
        'id_recorrido': id_recorrido,
        'hora_salida': hora,
        'precio_base': precio,
        'activo': True,
    })
