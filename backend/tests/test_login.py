"""
test_login.py — Tests de integración para el endpoint de login.

Endpoint: POST /api/login
Requisito: REQ-F04 (inicio de sesión y control de acceso)
"""

from tests.helpers import registrar_usuario, login_usuario, USUARIO_VALIDO


# ═══════════════════════════════════════════════════════════════════
#  LOGIN EXITOSO
# ═══════════════════════════════════════════════════════════════════

class TestLoginExitoso:
    """Casos donde el login debe retornar 200 OK."""

    def test_login_credenciales_correctas(self, client):
        """Login con email y contraseña correctos retorna 200."""
        registrar_usuario(client)
        response = login_usuario(client)
        assert response.status_code == 200

    def test_login_mensaje_exitoso(self, client):
        """La respuesta contiene mensaje de sesión iniciada."""
        registrar_usuario(client)
        response = login_usuario(client)
        data = response.get_json()
        assert 'Sesión iniciada' in data['message']

    def test_login_retorna_datos_usuario(self, client):
        """La respuesta incluye id, nombre y email del usuario."""
        registrar_usuario(client)
        response = login_usuario(client)
        data = response.get_json()
        usuario = data['usuario']
        assert 'id' in usuario
        assert usuario['nombre'] == USUARIO_VALIDO['nombre']
        assert usuario['email'] == USUARIO_VALIDO['email']

    def test_login_no_retorna_password(self, client):
        """La respuesta del login NO incluye la contraseña."""
        registrar_usuario(client)
        response = login_usuario(client)
        data = response.get_json()
        usuario = data['usuario']
        assert 'password' not in usuario
        assert 'password_hash' not in usuario


# ═══════════════════════════════════════════════════════════════════
#  LOGIN FALLIDO
# ═══════════════════════════════════════════════════════════════════

class TestLoginEmailInexistente:
    """Casos donde el email no está registrado."""

    def test_email_no_registrado(self, client):
        """Login con email inexistente retorna 401."""
        response = login_usuario(client, email='noexiste@correo.com', password='Pass123!')
        assert response.status_code == 401

    def test_email_no_registrado_mensaje_generico(self, client):
        """El mensaje de error no revela que el email no existe."""
        response = login_usuario(client, email='noexiste@correo.com', password='Pass123!')
        data = response.get_json()
        assert 'incorrectos' in data['error'].lower()


class TestLoginPasswordIncorrecta:
    """Casos donde la contraseña es incorrecta."""

    def test_password_incorrecta(self, client):
        """Login con contraseña incorrecta retorna 401."""
        registrar_usuario(client)
        response = login_usuario(client, password='ClaveIncorrecta1!')
        assert response.status_code == 401

    def test_password_incorrecta_mensaje_generico(self, client):
        """El mensaje de error es genérico (seguridad — no revela si el email existe)."""
        registrar_usuario(client)
        response = login_usuario(client, password='ClaveIncorrecta1!')
        data = response.get_json()
        assert 'incorrectos' in data['error'].lower()


class TestLoginMensajeSeguridad:
    """El mensaje de error debe ser el mismo para email inexistente y password incorrecta."""

    def test_mismo_mensaje_email_inexistente_y_password_incorrecta(self, client):
        """El error es idéntico para ambos casos (evita enumeración de usuarios)."""
        registrar_usuario(client)

        # Caso 1: email no existe
        r1 = login_usuario(client, email='falso@correo.com', password='Pass123!')
        # Caso 2: email existe pero password incorrecta
        r2 = login_usuario(client, password='ClaveIncorrecta1!')

        assert r1.get_json()['error'] == r2.get_json()['error']


class TestLoginCamposVacios:
    """Casos donde faltan campos obligatorios.

    NOTA: Actualmente la API retorna 401 (no 400) cuando los campos están
    vacíos, porque el string vacío pasa la validación `if not email or not password`
    solo cuando es realmente vacío "". Cuando se envía email="" via JSON,
    la ruta sigue el flujo normal y no encuentra al usuario → 401.
    Esto podría mejorarse retornando 400 con un mensaje más específico.
    """

    def test_email_vacio(self, client):
        """Login con email vacío retorna error."""
        response = login_usuario(client, email='', password='Pass123!')
        # La API retorna 401 (trata el campo vacío como credencial inválida)
        assert response.status_code in (400, 401)

    def test_password_vacia(self, client):
        """Login con contraseña vacía retorna error."""
        response = login_usuario(client, email='test@test.com', password='')
        assert response.status_code in (400, 401)

    def test_ambos_campos_vacios(self, client):
        """Login con ambos campos vacíos retorna error."""
        response = login_usuario(client, email='', password='')
        assert response.status_code in (400, 401)

    def test_campos_vacios_retorna_mensaje_de_error(self, client):
        """El servidor retorna un mensaje de error cuando los campos están vacíos."""
        response = login_usuario(client, email='', password='')
        data = response.get_json()
        assert 'error' in data
        assert len(data['error']) > 0
