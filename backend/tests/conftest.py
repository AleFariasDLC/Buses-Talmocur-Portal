"""
conftest.py — Configuración compartida para todos los tests.

Provee la fixture `client`: un cliente HTTP de Flask con base de datos
SQLite en memoria, completamente aislada para cada test.

Cada test recibe su propia base de datos vacía, así los tests son
completamente independientes entre sí.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from models import Base


@pytest.fixture()
def client(monkeypatch):
    """Cliente HTTP de Flask con base de datos aislada en memoria.

    Cada test que use esta fixture obtiene:
      - Una BD SQLite en memoria (vacía, con todas las tablas creadas).
      - Un cliente Flask listo para hacer peticiones HTTP.
      - Las operaciones de BD redirigidas a la BD de test.
    """
    # Crear motor SQLite en memoria con StaticPool para que todas
    # las sesiones compartan la misma conexión (y los mismos datos).
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSession = sessionmaker(bind=test_engine)

    # Crear todas las tablas del proyecto en la BD de test
    Base.metadata.create_all(test_engine)

    # Redirigir obtener_sesion() para que use la BD de test
    # en vez de la BD real (talmocur.db).
    # Hay que parchear en AMBOS módulos porque db_sqlite.py hace
    # `from database import obtener_sesion` (copia la referencia).
    import database
    import db_sqlite

    monkeypatch.setattr(database, 'obtener_sesion', lambda: TestSession())
    monkeypatch.setattr(db_sqlite, 'obtener_sesion', lambda: TestSession())

    from app import app
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'clave-secreta-de-test'

    with app.test_client() as c:
        yield c

    # Limpiar tablas al terminar el test
    Base.metadata.drop_all(test_engine)
