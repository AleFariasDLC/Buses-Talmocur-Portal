"""
test_db_sqlite.py — Tests unitarios para las funciones CRUD de db_sqlite.py.

Módulo testeado: db_sqlite.py
Funciones cubiertas:
  - crear_usuario(): creación con datos válidos
  - buscar_usuario_por_email(): búsqueda y normalización
  - buscar_usuario_por_id(): búsqueda por UUID
  - actualizar_usuario(): actualización parcial de campos
  - _a_dict(): conversión de modelo a diccionario

Estos tests usan la fixture `client` para tener la BD aislada en memoria.
"""

import db_sqlite as db


# ═══════════════════════════════════════════════════════════════════
#  CREAR USUARIO
# ═══════════════════════════════════════════════════════════════════

class TestCrearUsuario:
    """Tests para la función crear_usuario()."""

    def test_crear_usuario_retorna_dict(self, client):
        """crear_usuario() retorna un diccionario con los datos."""
        resultado = db.crear_usuario('Test User', 'test@test.com', 'hash123')
        assert isinstance(resultado, dict)

    def test_crear_usuario_tiene_id(self, client):
        """El usuario creado tiene un ID UUID."""
        resultado = db.crear_usuario('Test User', 'test@test.com', 'hash123')
        assert 'id' in resultado
        assert len(resultado['id']) == 36  # formato UUID

    def test_crear_usuario_normaliza_email(self, client):
        """El email se normaliza a minúsculas."""
        resultado = db.crear_usuario('Test User', 'TEST@TEST.COM', 'hash123')
        assert resultado['email'] == 'test@test.com'

    def test_crear_usuario_strip_nombre(self, client):
        """El nombre se limpia de espacios en los extremos."""
        resultado = db.crear_usuario('  Test User  ', 'test@test.com', 'hash123')
        assert resultado['nombre'] == 'Test User'

    def test_crear_usuario_no_incluye_hash(self, client):
        """crear_usuario() no incluye el password_hash en el resultado."""
        resultado = db.crear_usuario('Test User', 'test@test.com', 'hash123')
        assert 'password_hash' not in resultado

    def test_crear_usuario_tiene_fecha_registro(self, client):
        """El usuario creado tiene fecha de registro."""
        resultado = db.crear_usuario('Test User', 'test@test.com', 'hash123')
        assert 'fecha_registro' in resultado
        assert resultado['fecha_registro'] is not None

    def test_crear_usuario_rol_por_defecto_es_pasajero(self, client):
        """El rol por defecto es 'pasajero'."""
        resultado = db.crear_usuario('Test User', 'test@test.com', 'hash123')
        assert resultado['rol'] == 'pasajero'


# ═══════════════════════════════════════════════════════════════════
#  BUSCAR USUARIO POR EMAIL
# ═══════════════════════════════════════════════════════════════════

class TestBuscarPorEmail:
    """Tests para buscar_usuario_por_email()."""

    def test_buscar_email_existente(self, client):
        """Buscar un email que existe retorna el usuario."""
        db.crear_usuario('Test User', 'test@test.com', 'hash123')
        resultado = db.buscar_usuario_por_email('test@test.com')
        assert resultado is not None
        assert resultado['email'] == 'test@test.com'

    def test_buscar_email_inexistente(self, client):
        """Buscar un email que no existe retorna None."""
        resultado = db.buscar_usuario_por_email('noexiste@test.com')
        assert resultado is None

    def test_buscar_email_insensible_a_mayusculas(self, client):
        """La búsqueda por email ignora mayúsculas/minúsculas."""
        db.crear_usuario('Test User', 'test@test.com', 'hash123')
        resultado = db.buscar_usuario_por_email('TEST@TEST.COM')
        assert resultado is not None

    def test_buscar_email_incluye_hash(self, client):
        """buscar_usuario_por_email() incluye el password_hash (para login)."""
        db.crear_usuario('Test User', 'test@test.com', 'hash123')
        resultado = db.buscar_usuario_por_email('test@test.com')
        assert 'password_hash' in resultado
        assert resultado['password_hash'] == 'hash123'

    def test_buscar_email_con_espacios(self, client):
        """La búsqueda con espacios alrededor del email funciona (strip)."""
        db.crear_usuario('Test User', 'test@test.com', 'hash123')
        resultado = db.buscar_usuario_por_email('  test@test.com  ')
        assert resultado is not None


# ═══════════════════════════════════════════════════════════════════
#  BUSCAR USUARIO POR ID
# ═══════════════════════════════════════════════════════════════════

class TestBuscarPorId:
    """Tests para buscar_usuario_por_id()."""

    def test_buscar_id_existente(self, client):
        """Buscar un ID que existe retorna el usuario."""
        creado = db.crear_usuario('Test User', 'test@test.com', 'hash123')
        resultado = db.buscar_usuario_por_id(creado['id'])
        assert resultado is not None
        assert resultado['id'] == creado['id']

    def test_buscar_id_inexistente(self, client):
        """Buscar un ID que no existe retorna None."""
        resultado = db.buscar_usuario_por_id('id-que-no-existe')
        assert resultado is None

    def test_buscar_id_retorna_datos_completos(self, client):
        """El usuario retornado tiene todos los campos esperados."""
        creado = db.crear_usuario('Test User', 'test@test.com', 'hash123')
        resultado = db.buscar_usuario_por_id(creado['id'])
        assert resultado['nombre'] == 'Test User'
        assert resultado['email'] == 'test@test.com'
        assert 'fecha_registro' in resultado
        assert 'rol' in resultado


# ═══════════════════════════════════════════════════════════════════
#  ACTUALIZAR USUARIO
# ═══════════════════════════════════════════════════════════════════

class TestActualizarUsuario:
    """Tests para actualizar_usuario()."""

    def test_actualizar_nombre(self, client):
        """Actualizar el nombre del usuario funciona correctamente."""
        creado = db.crear_usuario('Nombre Original', 'test@test.com', 'hash123')
        resultado = db.actualizar_usuario(creado['id'], {'nombre': 'Nombre Nuevo'})
        assert resultado is not None
        assert resultado['nombre'] == 'Nombre Nuevo'

    def test_actualizar_email(self, client):
        """Actualizar el email del usuario funciona correctamente."""
        creado = db.crear_usuario('Test User', 'test@test.com', 'hash123')
        resultado = db.actualizar_usuario(creado['id'], {'email': 'nuevo@test.com'})
        assert resultado is not None
        assert resultado['email'] == 'nuevo@test.com'

    def test_actualizar_rol(self, client):
        """Actualizar el rol del usuario funciona correctamente."""
        creado = db.crear_usuario('Test User', 'test@test.com', 'hash123')
        resultado = db.actualizar_usuario(creado['id'], {'rol': 'admin'})
        assert resultado is not None
        assert resultado['rol'] == 'admin'

    def test_actualizar_password_hash(self, client):
        """Actualizar el password_hash funciona correctamente."""
        creado = db.crear_usuario('Test User', 'test@test.com', 'hash123')
        resultado = db.actualizar_usuario(creado['id'], {'password_hash': 'nuevo_hash'})
        assert resultado is not None
        # Verificar que se actualizó buscando el usuario
        usuario = db.buscar_usuario_por_email('test@test.com')
        assert usuario['password_hash'] == 'nuevo_hash'

    def test_actualizar_no_incluye_hash_en_respuesta(self, client):
        """actualizar_usuario() no incluye password_hash en la respuesta."""
        creado = db.crear_usuario('Test User', 'test@test.com', 'hash123')
        resultado = db.actualizar_usuario(creado['id'], {'nombre': 'Otro'})
        assert 'password_hash' not in resultado

    def test_actualizar_multiples_campos(self, client):
        """Se pueden actualizar varios campos a la vez."""
        creado = db.crear_usuario('Test User', 'test@test.com', 'hash123')
        resultado = db.actualizar_usuario(creado['id'], {
            'nombre': 'Admin User',
            'rol': 'admin',
        })
        assert resultado['nombre'] == 'Admin User'
        assert resultado['rol'] == 'admin'

    def test_actualizar_usuario_inexistente(self, client):
        """Actualizar un usuario que no existe retorna None."""
        resultado = db.actualizar_usuario('id-falso', {'nombre': 'Test'})
        assert resultado is None

    def test_actualizar_campo_no_permitido_es_ignorado(self, client):
        """Campos fuera de la lista permitida se ignoran sin error."""
        creado = db.crear_usuario('Test User', 'test@test.com', 'hash123')
        # 'id' y 'fecha_registro' no están en campos_permitidos
        resultado = db.actualizar_usuario(creado['id'], {
            'id': 'id-falso',
            'fecha_registro': '2020-01-01',
            'campo_inventado': 'valor',
        })
        assert resultado is not None
        assert resultado['id'] == creado['id']  # no cambió el ID

    def test_actualizar_preserva_campos_no_modificados(self, client):
        """Los campos que no se actualizan conservan su valor original."""
        creado = db.crear_usuario('Test User', 'test@test.com', 'hash123')
        db.actualizar_usuario(creado['id'], {'nombre': 'Nuevo Nombre'})
        usuario = db.buscar_usuario_por_email('test@test.com')
        assert usuario['nombre'] == 'Nuevo Nombre'
        assert usuario['email'] == 'test@test.com'  # no cambió
        assert usuario['rol'] == 'pasajero'  # no cambió
