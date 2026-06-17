"""
db_sqlite.py — Módulo CRUD para usuarios usando SQLAlchemy + SQLite.

Expone exactamente las mismas funciones que db_json.py para que
routes.py no necesite cambios importantes.
"""

from database import obtener_sesion
from models import Usuario


def buscar_usuario_por_email(email: str) -> dict | None:
    """Busca un usuario por su correo electrónico.
    Retorna un diccionario con los datos del usuario o None si no existe.
    """
    db = obtener_sesion()
    try:
        usuario = db.query(Usuario).filter(
            Usuario.email == email.strip().lower()
        ).first()
        return _a_dict(usuario) if usuario else None
    finally:
        db.close()


def buscar_usuario_por_id(user_id: str) -> dict | None:
    """Busca un usuario por su ID (UUID).
    Retorna un diccionario con los datos del usuario o None si no existe.
    """
    db = obtener_sesion()
    try:
        usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
        return _a_dict(usuario) if usuario else None
    finally:
        db.close()


def crear_usuario(nombre: str, email: str, password_hash: str) -> dict:
    """Crea un nuevo usuario y lo guarda en la BD.

    Args:
        nombre: Nombre completo del usuario.
        email: Correo electrónico (se normaliza a minúsculas).
        password_hash: Contraseña ya hasheada con bcrypt.

    Returns:
        dict: El usuario creado (sin el hash de contraseña).
    """
    import uuid
    from datetime import datetime

    db = obtener_sesion()
    try:
        nuevo = Usuario(
            id=str(uuid.uuid4()),
            nombre=nombre.strip(),
            email=email.strip().lower(),
            password_hash=password_hash,
            fecha_registro=datetime.utcnow(),
            rol="pasajero",
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return _a_dict(nuevo, incluir_hash=False)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def actualizar_usuario(user_id: str, campos: dict) -> dict | None:
    """Actualiza campos de un usuario existente.

    Args:
        user_id: ID del usuario a actualizar.
        campos: Diccionario con los campos a cambiar.

    Returns:
        dict | None: El usuario actualizado o None si no se encontró.
    """
    db = obtener_sesion()
    try:
        usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
        if not usuario:
            return None

        campos_permitidos = {"nombre", "email", "password_hash", "rol"}
        for clave, valor in campos.items():
            if clave in campos_permitidos:
                setattr(usuario, clave, valor)

        db.commit()
        db.refresh(usuario)
        return _a_dict(usuario, incluir_hash=False)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Helpers privados ──────────────────────────────────────────────

def _a_dict(usuario: Usuario, incluir_hash: bool = True) -> dict:
    """Convierte un objeto Usuario a diccionario.
    Por defecto incluye el password_hash (necesario para verificar login).
    Pasar incluir_hash=False para respuestas al cliente.
    """
    datos = {
        "id":             usuario.id,
        "nombre":         usuario.nombre,
        "email":          usuario.email,
        "fecha_registro": usuario.fecha_registro.isoformat()
                          if usuario.fecha_registro else None,
        "rol":            usuario.rol,
    }
    if incluir_hash:
        datos["password_hash"] = usuario.password_hash
    return datos
