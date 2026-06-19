"""
seed_db.py — Inicializa la base de datos con los datos mínimos necesarios.

Comportamiento:
  - Si data/talmocur.db NO existe → la crea con todas las tablas y la puebla.
  - Si data/talmocur.db YA existe → no hace nada (protege los datos actuales).

Uso manual (solo si necesitas reinicializar):
  1. Borra manualmente el archivo data/talmocur.db
  2. Ejecuta: python seed_db.py  (desde la carpeta backend/)

Este script también es invocado automáticamente por app.py al arrancar,
por lo que en condiciones normales NO hay que ejecutarlo a mano.
"""

import os
import sys

# Asegurar que Python encuentre los módulos del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import crear_tablas, obtener_sesion, _RUTA_DB
from models import Recorrido, Usuario
import uuid
from datetime import datetime


def seed(quiet=False):
    """Crea la BD y puebla los datos base si no existen."""

    # ── 1. Crear tablas (idempotente: no borra datos si ya existen) ──
    crear_tablas(quiet=quiet)

    # Evitar duplicados debido al reloader de Flask (Werkzeug) en modo debug
    is_reloader_parent = (os.environ.get('WERKZEUG_RUN_MAIN') is None and 
                          os.environ.get('FLASK_USE_RELOADER') == 'true')

    db = obtener_sesion()
    try:
        # ── 2. Recorridos iniciales ──────────────────────────────────
        if db.query(Recorrido).count() == 0:
            recorridos = [
                Recorrido(origen="Curicó", destino="Talca",  tipo="ida", precio_base=3500.0),
                Recorrido(origen="Talca",  destino="Curicó", tipo="ida", precio_base=3500.0),
            ]
            db.add_all(recorridos)
            db.commit()
            if not is_reloader_parent:
                print("[Seed] Recorridos iniciales insertados:")
                for r in db.query(Recorrido).all():
                    print(f"  · {r.origen} → {r.destino}  |  ${r.precio_base:,.0f}")
        elif not quiet and not is_reloader_parent:
            print(f"[Seed] Recorridos ya existentes ({db.query(Recorrido).count()}) — sin cambios.")

        # ── 3. Usuario Administrador Inicial ─────────────────────────
        admin_email = "admin@talmocur.cl"
        admin_exists = db.query(Usuario).filter(Usuario.email == admin_email).first() is not None
        if not admin_exists:
            # Hash de la contraseña "TalmocurAdmin2026!"
            admin_hash = "$2b$12$z.U/po8vbsNqsEHH65uaF.HrVMYkaZla1XzWl21PyTWOCKDEyhWUe"
            admin_user = Usuario(
                id=str(uuid.uuid4()),
                nombre="Administrador Talmocur",
                email=admin_email,
                password_hash=admin_hash,
                rol="admin",
                fecha_registro=datetime.utcnow()
            )
            db.add(admin_user)
            db.commit()
            if not is_reloader_parent:
                print(f"[Seed] Usuario Administrador creado: {admin_email}")
        else:
            if not quiet and not is_reloader_parent:
                print(f"[Seed] Usuario Administrador '{admin_email}' ya existente — sin cambios.")

        # ── Agregar aquí más seeds a futuro ─────────────────────────
        # Ejemplo: poblar tabla Bus, HorarioViaje, etc.

    finally:

        db.close()

    if not quiet and not is_reloader_parent:
        print(f"[Seed] BD lista en: {_RUTA_DB}")


if __name__ == "__main__":
    seed()
