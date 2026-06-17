"""
migrar_json_a_db.py — Script de migración one-shot.

Lee los usuarios existentes en data/usuarios.json, crea todas las
tablas en talmocur.db e inserta los usuarios preservando sus IDs,
contraseñas y fechas de registro.

Ejecutar UNA sola vez:
    python backend/migrar_json_a_db.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Asegurar que Python encuentre los módulos del backend
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import crear_tablas, obtener_sesion
from models import Usuario

# Ruta al JSON con los usuarios actuales
_BASE_DIR  = Path(__file__).resolve().parent.parent
_DATA_FILE = _BASE_DIR / "data" / "usuarios.json"


def migrar():
    print("\n[*] Iniciando migracion JSON -> SQLite\n")

    # 1. Crear todas las tablas
    crear_tablas()

    # 2. Leer usuarios del JSON
    if not _DATA_FILE.exists():
        print("[!] No se encontro data/usuarios.json -- se creara la BD vacia.")
        return

    with open(_DATA_FILE, "r", encoding="utf-8") as f:
        datos = json.load(f)

    usuarios_json = datos.get("usuarios", [])
    print(f"[*] Usuarios encontrados en JSON: {len(usuarios_json)}\n")

    db = obtener_sesion()
    insertados = 0
    omitidos   = 0

    try:
        for u in usuarios_json:
            # Evitar duplicados si el script se corre más de una vez
            ya_existe = db.query(Usuario).filter(
                (Usuario.id == u["id"]) | (Usuario.email == u["email"])
            ).first()

            if ya_existe:
                print(f"   [=] Omitido (ya existe): {u['email']}")
                omitidos += 1
                continue

            # Parsear fecha_registro (puede venir como string ISO)
            try:
                fecha_reg = datetime.fromisoformat(u.get("fecha_registro", ""))
            except (ValueError, TypeError):
                fecha_reg = datetime.utcnow()

            nuevo = Usuario(
                id=u["id"],
                nombre=u["nombre"],
                email=u["email"],
                password_hash=u["password_hash"],
                fecha_registro=fecha_reg,
                rol="pasajero",
            )
            db.add(nuevo)
            print(f"   [OK] Migrado: {u['email']}")
            insertados += 1

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Error durante la migracion: {e}")
        sys.exit(1)
    finally:
        db.close()

    print(f"\n[DONE] Migracion completada.")
    print(f"   Insertados : {insertados}")
    print(f"   Omitidos   : {omitidos}")
    print(f"   BD creada  : backend/talmocur.db\n")


if __name__ == "__main__":
    migrar()
