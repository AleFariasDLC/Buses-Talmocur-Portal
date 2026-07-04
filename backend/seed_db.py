"""
seed_db.py — Inicializa la base de datos con los datos mínimos necesarios.

Comportamiento:
  - Si data/talmocur.db NO existe → la crea con todas las tablas y la puebla.
  - Si data/talmocur.db YA existe → aplica solo las partes que faltan
    (p.ej. buses si aún no hay ninguno).

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
from models import Recorrido, Usuario, Bus, Asiento, HorarioViaje
import uuid
from datetime import datetime, timedelta, timezone


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def _hacer_hora(h, m, duracion_min=45):
    """Devuelve (hora_salida: time, hora_llegada: time) para un slot."""
    base   = datetime(2000, 1, 1, h, m)
    llegada = base + timedelta(minutes=duracion_min)
    return base.time(), llegada.time()


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
                    print(f"  * {r.origen} -> {r.destino}  |  ${r.precio_base:,.0f}")
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
                fecha_registro=datetime.now(timezone.utc)
            )
            db.add(admin_user)
            db.commit()
            if not is_reloader_parent:
                print(f"[Seed] Usuario Administrador creado: {admin_email}")
        else:
            if not quiet and not is_reloader_parent:
                print(f"[Seed] Usuario Administrador '{admin_email}' ya existente — sin cambios.")

        # ── 4. Flota de buses y horarios ─────────────────────────────
        # Solo se ejecuta si no hay ningún bus en la BD.
        # Garantiza que todos los integrantes del equipo tengan los mismos
        # datos al arrancar la app por primera vez (o con BD vacía).
        if db.query(Bus).count() == 0:

            PRECIO_BASE = 3500.0

            buses_data = [
                {"patente": "CGKR-15", "modelo": "Mercedes O500", "chofer": "Carlos Muñoz",    "capacidad": 40},
                {"patente": "BHPT-28", "modelo": "Volvo B420R",   "chofer": "Roberto Herrera", "capacidad": 40},
                {"patente": "DLWS-33", "modelo": "Mercedes O500", "chofer": "Andrés Soto",     "capacidad": 40},
                {"patente": "FMJV-41", "modelo": "Volvo B420R",   "chofer": "Felipe Reyes",    "capacidad": 40},
                {"patente": "KNRB-52", "modelo": "Mercedes O500", "chofer": "Ignacio Vera",    "capacidad": 40},
            ]

            # Crear buses y sus asientos físicos
            for bd in buses_data:
                bus = Bus(
                    patente=bd["patente"],
                    modelo=bd["modelo"],
                    chofer=bd["chofer"],
                    capacidad=bd["capacidad"],
                    estado="Activo",
                )
                db.add(bus)
                for num in range(1, bd["capacidad"] + 1):
                    db.add(Asiento(numero=num, patente=bd["patente"]))

            db.commit()

            # ── Horarios de viaje ──────────────────────────────────
            # Obtener recorridos (ya insertados arriba o en ejecuciones previas)
            rec_ct = db.query(Recorrido).filter_by(origen="Curicó", destino="Talca").first()
            rec_tc = db.query(Recorrido).filter_by(origen="Talca",  destino="Curicó").first()

            # Rotación regular:
            # - Bus 1 alternando C->T y T->C cada 1h.
            # - Bus 3 alternando T->C y C->T cada 1h.
            # - Bus 2 alternando C->T y T->C en las medias horas cada 1h.
            # - Bus 4 alternando T->C y C->T en las medias horas cada 1h.
            # - Bus 5 (KNRB-52) de refuerzo para horas punta C->T y T->C.

            horarios_por_bus = [
                # Bus 1: CGKR-15 (Horas en punto: sale de Curicó, regresa de Talca)
                ("CGKR-15", rec_ct, [(8,0), (10,0), (12,0), (14,0), (16,0), (18,0), (20,0)]),
                ("CGKR-15", rec_tc, [(9,0), (11,0), (13,0), (15,0), (17,0), (19,0), (21,0)]),

                # Bus 3: DLWS-33 (Horas en punto: sale de Talca, regresa de Curicó)
                ("DLWS-33", rec_tc, [(8,0), (10,0), (12,0), (14,0), (16,0), (18,0), (20,0)]),
                ("DLWS-33", rec_ct, [(9,0), (11,0), (13,0), (15,0), (17,0), (19,0), (21,0)]),

                # Bus 2: BHPT-28 (Medias horas: sale de Curicó, regresa de Talca)
                ("BHPT-28", rec_ct, [(8,30), (10,30), (12,30), (14,30), (16,30), (18,30), (20,30)]),
                ("BHPT-28", rec_tc, [(9,30), (11,30), (13,30), (15,30), (17,30), (19,30)]),

                # Bus 4: FMJV-41 (Medias horas: sale de Talca, regresa de Curicó)
                ("FMJV-41", rec_tc, [(8,30), (10,30), (12,30), (14,30), (16,30), (18,30), (20,30)]),
                ("FMJV-41", rec_ct, [(9,30), (11,30), (13,30), (15,30), (17,30), (19,30)]),

                # Bus 5: KNRB-52 (Refuerzo punta)
                ("KNRB-52", rec_ct, [(8,0), (12,0), (17,0)]),
                ("KNRB-52", rec_tc, [(9,0), (13,0), (18,0)]),
            ]

            nuevos_horarios = []
            for patente, rec, slots in horarios_por_bus:
                if not rec:
                    continue
                for h, m in slots:
                    salida, llegada = _hacer_hora(h, m, duracion_min=45)
                    nuevos_horarios.append(HorarioViaje(
                        id_recorrido=rec.id_recorrido,
                        patente=patente,
                        hora_salida=salida,
                        hora_llegada=llegada,
                        precio_base=PRECIO_BASE,
                        activo=True,
                    ))

            db.add_all(nuevos_horarios)
            db.commit()

            total_asientos = sum(b["capacidad"] for b in buses_data)
            if not is_reloader_parent:
                print(f"[Seed] {len(buses_data)} buses creados ({total_asientos} asientos en total).")
                print(f"[Seed] {len(nuevos_horarios)} horarios de viaje insertados "
                      f"(Curico <-> Talca alternados, 8:00-21:00 cada 30 min sin conflictos).")

        elif not quiet and not is_reloader_parent:
            print(f"[Seed] Buses ya existentes ({db.query(Bus).count()}) — sin cambios.")

    finally:
        db.close()

    if not quiet and not is_reloader_parent:
        print(f"[Seed] BD lista en: {_RUTA_DB}")


if __name__ == "__main__":
    seed()
