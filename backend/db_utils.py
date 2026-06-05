import sqlite3
from datetime import datetime


def crear_conexion(ruta_db):
    return sqlite3.connect(ruta_db)


def inicializar_bd(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            fecha_registro TEXT NOT NULL
        )
    """)
    conn.commit()


def listar_usuarios(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre, email, password_hash, fecha_registro
        FROM usuarios
        ORDER BY id
    """)
    filas = cursor.fetchall()

    return [
        {
            "id": fila[0],
            "nombre": fila[1],
            "email": fila[2],
            "password_hash": fila[3],
            "fecha_registro": fila[4],
        }
        for fila in filas
    ]


def obtener_usuario_por_id(conn, usuario_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre, email, password_hash, fecha_registro
        FROM usuarios
        WHERE id = ?
    """, (usuario_id,))
    fila = cursor.fetchone()

    if fila is None:
        return None

    return {
        "id": fila[0],
        "nombre": fila[1],
        "email": fila[2],
        "password_hash": fila[3],
        "fecha_registro": fila[4],
    }


def crear_usuario(conn, nombre, email, password_hash):
    cursor = conn.cursor()
    fecha_registro = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO usuarios (nombre, email, password_hash, fecha_registro)
        VALUES (?, ?, ?, ?)
    """, (nombre, email, password_hash, fecha_registro))

    conn.commit()
    return cursor.lastrowid


def actualizar_usuario(conn, usuario_id, campos):
    columnas = []
    valores = []

    if "nombre" in campos:
        columnas.append("nombre = ?")
        valores.append(campos["nombre"])

    if "email" in campos:
        columnas.append("email = ?")
        valores.append(campos["email"])

    if "password_hash" in campos:
        columnas.append("password_hash = ?")
        valores.append(campos["password_hash"])

    if not columnas:
        return False

    valores.append(usuario_id)

    cursor = conn.cursor()
    cursor.execute(f"""
        UPDATE usuarios
        SET {", ".join(columnas)}
        WHERE id = ?
    """, valores)

    conn.commit()
    return cursor.rowcount > 0


def eliminar_usuario(conn, usuario_id):
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM usuarios
        WHERE id = ?
    """, (usuario_id,))

    conn.commit()
    return cursor.rowcount > 0