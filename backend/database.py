# database.py
# Este archivo crea la conexión a la base de datos y genera las tablas.

import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from models import Base

# ─────────────────────────────────────────────
# Ruta absoluta a la BD — siempre apunta a /data/talmocur.db
# sin importar desde qué directorio se ejecute el script.
# ─────────────────────────────────────────────
#   Estructura esperada:
#       Proyecto/
#           backend/      ← este archivo vive aquí
#           data/
#               talmocur.db   ← la BD vive aquí

_DIR_BACKEND = os.path.dirname(os.path.abspath(__file__))   # .../Proyecto/backend
_DIR_DATA    = os.path.join(_DIR_BACKEND, '..', 'data')     # .../Proyecto/data

# Crear la carpeta /data si todavía no existe
os.makedirs(_DIR_DATA, exist_ok=True)

_RUTA_DB     = os.path.join(_DIR_DATA, 'talmocur.db')       # ruta absoluta al archivo

# SQLite con 4 barras = ruta absoluta (la 3.ª barra pertenece a la ruta)
DATABASE_URL = f"sqlite:///{_RUTA_DB}"

# ─────────────────────────────────────────────
# Si en el futuro quieres usar PostgreSQL o MySQL, solo cambia DATABASE_URL:
#   PostgreSQL: "postgresql://usuario:contraseña@localhost/talmocur"
#   MySQL:      "mysql+pymysql://usuario:contraseña@localhost/talmocur"
# ─────────────────────────────────────────────

engine = create_engine(DATABASE_URL, echo=False)
# echo=False: SQLAlchemy no imprime el SQL generado en consola.
# Cambia a echo=True si necesitas depurar las consultas SQL.

# Session es lo que usamos para hacer consultas y guardar datos
SessionLocal = sessionmaker(bind=engine)


def crear_tablas(quiet=False):
    """Crea todas las tablas en la base de datos si no existen.

    Se llama automáticamente al iniciar la app. Si las tablas ya existen,
    SQLAlchemy las deja intactas (no borra datos).
    La carpeta /data se crea sola si no existe.
    """
    inspector = inspect(engine)
    tablas_existentes = inspector.get_table_names()

    Base.metadata.create_all(engine)
    _asegurar_columna_fecha_nacimiento()

    # Evitar duplicados debido al reloader de Flask (Werkzeug) en modo debug
    is_reloader_parent = (os.environ.get('WERKZEUG_RUN_MAIN') is None and 
                          os.environ.get('FLASK_USE_RELOADER') == 'true')

    if not is_reloader_parent:
        if not tablas_existentes:
            print(f"[BD] Base de datos nueva creada en: {_RUTA_DB}")
        elif not quiet:
            print("[BD] Base de datos ya existente — tablas verificadas correctamente.")


def _asegurar_columna_fecha_nacimiento():
    """Añade la columna fecha_nacimiento a usuarios existentes si hace falta."""
    inspector = inspect(engine)
    if 'usuario' not in inspector.get_table_names():
        return

    columnas = {columna['name'] for columna in inspector.get_columns('usuario')}
    if 'fecha_nacimiento' not in columnas:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE usuario ADD COLUMN fecha_nacimiento DATE"))


def obtener_sesion():
    """Devuelve una sesión de base de datos lista para usar."""
    return SessionLocal()


if __name__ == "__main__":
    crear_tablas()
