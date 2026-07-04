"""
test_db_tokens.py — Tests unitarios para las funciones CRUD de tokens
de recuperación en db_sqlite.py.

Funciones testeadas:
    crear_token_recuperacion()
    buscar_token_recuperacion()
    marcar_token_usado()
    invalidar_tokens_de_usuario()
"""

from datetime import datetime, timedelta, timezone
import db_sqlite as db


# ═══════════════════════════════════════════════════════════════════
#  CREAR TOKEN
# ═══════════════════════════════════════════════════════════════════

class TestCrearToken:
    """crear_token_recuperacion()."""

    def test_crear_token_exitoso(self, client):
        """Crear un token no lanza excepción y se puede buscar después."""
        usuario = db.crear_usuario('Token User', 'token@test.com', 'hash')
        expira = datetime.now(timezone.utc) + timedelta(hours=1)
        db.crear_token_recuperacion(usuario['id'], 'mi-token-secreto', expira)
        # Verificar que se puede buscar
        user_data, vigente = db.buscar_token_recuperacion('mi-token-secreto')
        assert user_data is not None
        assert user_data['email'] == 'token@test.com'
        assert vigente is True


# ═══════════════════════════════════════════════════════════════════
#  BUSCAR TOKEN
# ═══════════════════════════════════════════════════════════════════

class TestBuscarToken:
    """buscar_token_recuperacion()."""

    def test_token_inexistente(self, client):
        """Un token que no existe retorna (None, False)."""
        user_data, vigente = db.buscar_token_recuperacion('noexiste')
        assert user_data is None
        assert vigente is False

    def test_token_vigente(self, client):
        """Token no expirado y no usado retorna vigente=True."""
        usuario = db.crear_usuario('Vigente User', 'vigente@test.com', 'hash')
        expira = datetime.now(timezone.utc) + timedelta(hours=1)
        db.crear_token_recuperacion(usuario['id'], 'token-vigente', expira)
        user_data, vigente = db.buscar_token_recuperacion('token-vigente')
        assert vigente is True
        assert user_data['id'] == usuario['id']

    def test_token_expirado(self, client):
        """Token con fecha expirada retorna vigente=False."""
        usuario = db.crear_usuario('Expirado User', 'expirado@test.com', 'hash')
        expira = datetime.now(timezone.utc) - timedelta(hours=1)  # ya pasó
        db.crear_token_recuperacion(usuario['id'], 'token-expirado', expira)
        user_data, vigente = db.buscar_token_recuperacion('token-expirado')
        assert user_data is not None
        assert vigente is False

    def test_token_usado(self, client):
        """Token marcado como usado retorna vigente=False."""
        usuario = db.crear_usuario('Usado User', 'usado@test.com', 'hash')
        expira = datetime.now(timezone.utc) + timedelta(hours=1)
        db.crear_token_recuperacion(usuario['id'], 'token-usado', expira)
        db.marcar_token_usado('token-usado')
        user_data, vigente = db.buscar_token_recuperacion('token-usado')
        assert user_data is not None
        assert vigente is False

    def test_token_retorna_datos_usuario(self, client):
        """El dict retornado tiene id, nombre y email del usuario."""
        usuario = db.crear_usuario('Datos User', 'datos@test.com', 'hash')
        expira = datetime.now(timezone.utc) + timedelta(hours=1)
        db.crear_token_recuperacion(usuario['id'], 'token-datos', expira)
        user_data, _ = db.buscar_token_recuperacion('token-datos')
        assert 'id' in user_data
        assert 'nombre' in user_data
        assert 'email' in user_data
        assert user_data['nombre'] == 'Datos User'


# ═══════════════════════════════════════════════════════════════════
#  MARCAR TOKEN COMO USADO
# ═══════════════════════════════════════════════════════════════════

class TestMarcarTokenUsado:
    """marcar_token_usado()."""

    def test_marcar_token(self, client):
        """Después de marcar, el token ya no está vigente."""
        usuario = db.crear_usuario('Marcar User', 'marcar@test.com', 'hash')
        expira = datetime.now(timezone.utc) + timedelta(hours=1)
        db.crear_token_recuperacion(usuario['id'], 'token-marcar', expira)
        # Antes: vigente
        _, antes = db.buscar_token_recuperacion('token-marcar')
        assert antes is True
        # Marcar como usado
        db.marcar_token_usado('token-marcar')
        # Después: no vigente
        _, despues = db.buscar_token_recuperacion('token-marcar')
        assert despues is False

    def test_marcar_token_inexistente_no_falla(self, client):
        """Marcar un token que no existe no lanza excepción."""
        db.marcar_token_usado('token-fantasma')  # no debería fallar


# ═══════════════════════════════════════════════════════════════════
#  INVALIDAR TOKENS DE USUARIO
# ═══════════════════════════════════════════════════════════════════

class TestInvalidarTokensDeUsuario:
    """invalidar_tokens_de_usuario()."""

    def test_invalida_todos_los_tokens(self, client):
        """Marca todos los tokens no usados del usuario como usados."""
        usuario = db.crear_usuario('Multi User', 'multi@test.com', 'hash')
        expira = datetime.now(timezone.utc) + timedelta(hours=1)
        db.crear_token_recuperacion(usuario['id'], 'token-1', expira)
        db.crear_token_recuperacion(usuario['id'], 'token-2', expira)
        db.crear_token_recuperacion(usuario['id'], 'token-3', expira)
        # Todos vigentes antes
        for t in ('token-1', 'token-2', 'token-3'):
            _, v = db.buscar_token_recuperacion(t)
            assert v is True
        # Invalidar todos
        db.invalidar_tokens_de_usuario(usuario['id'])
        # Ninguno vigente después
        for t in ('token-1', 'token-2', 'token-3'):
            _, v = db.buscar_token_recuperacion(t)
            assert v is False

    def test_no_afecta_otros_usuarios(self, client):
        """Invalidar los tokens de un usuario no afecta a otro."""
        user_a = db.crear_usuario('User A', 'a@test.com', 'hash')
        user_b = db.crear_usuario('User B', 'b@test.com', 'hash')
        expira = datetime.now(timezone.utc) + timedelta(hours=1)
        db.crear_token_recuperacion(user_a['id'], 'token-a', expira)
        db.crear_token_recuperacion(user_b['id'], 'token-b', expira)
        # Invalidar solo los de user_a
        db.invalidar_tokens_de_usuario(user_a['id'])
        _, vigente_a = db.buscar_token_recuperacion('token-a')
        _, vigente_b = db.buscar_token_recuperacion('token-b')
        assert vigente_a is False
        assert vigente_b is True
