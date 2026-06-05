"""
db_json.py — Módulo CRUD para la "base de datos" temporal en JSON.

Maneja lectura/escritura del archivo data/usuarios.json.
Diseñado para ser reemplazado fácilmente por una BD real en el futuro.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

# Ruta al archivo JSON (relativa a la ubicación de este script)
_BASE_DIR = Path(__file__).resolve().parent.parent
_DATA_FILE = _BASE_DIR / "data" / "usuarios.json"


def _cargar_datos():
    """Lee el archivo JSON y retorna el diccionario completo."""
    if not _DATA_FILE.exists():
        # Si no existe, crear el archivo con estructura vacía
        _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        _guardar_datos({"usuarios": []})
        return {"usuarios": []}

    with open(_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _guardar_datos(datos):
    """Escribe el diccionario completo al archivo JSON."""
    _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)


def cargar_usuarios():
    """Retorna la lista de todos los usuarios."""
    datos = _cargar_datos()
    return datos.get("usuarios", [])


def buscar_usuario_por_email(email):
    """Busca un usuario por su correo electrónico.
    Retorna el diccionario del usuario o None si no existe.
    """
    usuarios = cargar_usuarios()
    for usuario in usuarios:
        if usuario["email"].lower() == email.lower():
            return usuario
    return None


def buscar_usuario_por_id(user_id):
    """Busca un usuario por su ID.
    Retorna el diccionario del usuario o None si no existe.
    """
    usuarios = cargar_usuarios()
    for usuario in usuarios:
        if usuario["id"] == user_id:
            return usuario
    return None


def crear_usuario(nombre, email, password_hash):
    """Crea un nuevo usuario y lo guarda en el JSON.

    Args:
        nombre: Nombre completo del usuario.
        email: Correo electrónico.
        password_hash: Contraseña ya hasheada con bcrypt.

    Returns:
        dict: El usuario creado (sin el hash de contraseña).
    """
    datos = _cargar_datos()

    nuevo_usuario = {
        "id": str(uuid.uuid4()),
        "nombre": nombre.strip(),
        "email": email.strip().lower(),
        "password_hash": password_hash,
        "fecha_registro": datetime.now().isoformat()
    }

    datos["usuarios"].append(nuevo_usuario)
    _guardar_datos(datos)

    # Retornar copia sin la contraseña
    usuario_seguro = {k: v for k, v in nuevo_usuario.items() if k != "password_hash"}
    return usuario_seguro


def actualizar_usuario(user_id, campos):
    """Actualiza campos de un usuario existente.

    Args:
        user_id: ID del usuario a actualizar.
        campos: Diccionario con los campos a actualizar.

    Returns:
        dict|None: El usuario actualizado o None si no se encontró.
    """
    datos = _cargar_datos()

    for usuario in datos["usuarios"]:
        if usuario["id"] == user_id:
            for clave, valor in campos.items():
                if clave != "id":  # No permitir cambiar el ID
                    usuario[clave] = valor
            _guardar_datos(datos)
            return {k: v for k, v in usuario.items() if k != "password_hash"}

    return None
