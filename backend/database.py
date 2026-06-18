# database.py
# Este archivo crea la conexión a la base de datos y genera las tablas.

import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from models import Base

# ─────────────────────────────────────────────
# Configuración de la base de datos
# ─────────────────────────────────────────────
# Usamos SQLite porque no requiere instalar nada extra.
# El archivo "talmocur.db" se crea automáticamente en la misma carpeta
# que este script (backend/) si no existe.
#
# Si en el futuro quieres usar PostgreSQL o MySQL, solo cambia esta línea:
#   PostgreSQL: "postgresql://usuario:contraseña@localhost/talmocur"
#   MySQL:      "mysql+pymysql://usuario:contraseña@localhost/talmocur"

DATABASE_URL = "sqlite:///talmocur.db"

engine = create_engine(DATABASE_URL, echo=False)
# echo=False: SQLAlchemy no imprime el SQL generado en consola.
# Cambia a echo=True si necesitas depurar las consultas SQL.

# Session es lo que usamos para hacer consultas y guardar datos
SessionLocal = sessionmaker(bind=engine)


def crear_tablas():
    """Crea todas las tablas en la base de datos si no existen.

    Se llama automáticamente al iniciar la app. Si las tablas ya existen,
    SQLAlchemy las deja intactas (no borra datos).
    """
    inspector = inspect(engine)
    tablas_existentes = inspector.get_table_names()

    Base.metadata.create_all(engine)

    if tablas_existentes:
        print("[BD] Base de datos ya existente — tablas verificadas correctamente.")
    else:
        print("[BD] Base de datos nueva creada con todas las tablas.")


def obtener_sesion():
    """Devuelve una sesión de base de datos lista para usar."""
    return SessionLocal()


if __name__ == "__main__":
    crear_tablas()
