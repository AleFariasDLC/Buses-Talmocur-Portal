# database.py
# Este archivo crea la conexión a la base de datos y genera las tablas.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# ─────────────────────────────────────────────
# Configuración de la base de datos
# ─────────────────────────────────────────────
# Usamos SQLite porque no requiere instalar nada extra.
# El archivo "talmocur.db" se crea automáticamente en la misma carpeta.
#
# Si en el futuro quieres usar PostgreSQL o MySQL, solo cambia esta línea:
#   PostgreSQL: "postgresql://usuario:contraseña@localhost/talmocur"
#   MySQL:      "mysql+pymysql://usuario:contraseña@localhost/talmocur"

DATABASE_URL = "sqlite:///talmocur.db"

engine = create_engine(DATABASE_URL, echo=True)
# echo=True hace que SQLAlchemy imprima en consola el SQL que genera (útil para aprender)

# Session es lo que usamos para hacer consultas y guardar datos
SessionLocal = sessionmaker(bind=engine)


def crear_tablas():
    """Crea todas las tablas en la base de datos si no existen."""
    Base.metadata.create_all(engine)
    print("\n[OK] Tablas creadas exitosamente.\n")


def obtener_sesion():
    """Devuelve una sesión de base de datos lista para usar."""
    return SessionLocal()


if __name__ == "__main__":
    crear_tablas()
