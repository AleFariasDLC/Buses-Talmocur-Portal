# test/db_test.py
import sqlite3
import pytest
from backend import db_utils


@pytest.fixture
def conn(tmp_path):
    db_path = tmp_path / "test.db"
    connection = db_utils.crear_conexion(str(db_path))
    db_utils.inicializar_bd(connection)
    yield connection
    connection.close()


def test_mostrar_usuarios_vacio(conn):
    usuarios = db_utils.listar_usuarios(conn)
    assert usuarios == []


def test_agregar_usuario(conn):
    usuario_id = db_utils.crear_usuario(
        conn,
        nombre="Paul",
        email="paul@example.com",
        password_hash="hash123"
    )

    usuarios = db_utils.listar_usuarios(conn)
    assert len(usuarios) == 1
    assert usuarios[0]["id"] == usuario_id
    assert usuarios[0]["nombre"] == "Paul"
    assert usuarios[0]["email"] == "paul@example.com"


def test_modificar_usuario(conn):
    usuario_id = db_utils.crear_usuario(
        conn,
        nombre="Paul",
        email="paul@example.com",
        password_hash="hash123"
    )

    actualizado = db_utils.actualizar_usuario(
        conn,
        usuario_id,
        {"nombre": "Paul Actualizado"}
    )

    assert actualizado is True
    usuario = db_utils.obtener_usuario_por_id(conn, usuario_id)
    assert usuario["nombre"] == "Paul Actualizado"


def test_eliminar_usuario(conn):
    usuario_id = db_utils.crear_usuario(
        conn,
        nombre="Paul",
        email="paul@example.com",
        password_hash="hash123"
    )

    eliminado = db_utils.eliminar_usuario(conn, usuario_id)

    assert eliminado is True
    usuario = db_utils.obtener_usuario_por_id(conn, usuario_id)
    assert usuario is None