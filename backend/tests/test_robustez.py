"""
test_robustez.py — Tests de robustez y casos borde de la API.

Verifica que la API maneja correctamente peticiones malformadas,
tipos de contenido incorrectos y payloads inesperados.

Estos tests son importantes para la seguridad y estabilidad
del servidor en producción.
"""

from tests.helpers import registrar_usuario, login_usuario


# ═══════════════════════════════════════════════════════════════════
#  REGISTRO — Peticiones malformadas
# ═══════════════════════════════════════════════════════════════════

class TestRegistroRobustez:
    """Tests de robustez para POST /api/register."""

    def test_registro_sin_body(self, client):
        """POST /api/register sin body retorna error (no 500)."""
        response = client.post('/api/register')
        assert response.status_code in (400, 415)

    def test_registro_body_vacio_json(self, client):
        """POST /api/register con JSON vacío {} retorna 400."""
        response = client.post('/api/register', json={})
        assert response.status_code == 400

    def test_registro_campo_nombre_faltante(self, client):
        """POST /api/register sin el campo 'nombre' retorna 400."""
        response = client.post('/api/register', json={
            'email': 'test@test.com',
            'password': 'MiClave123!',
            'confirmPassword': 'MiClave123!',
        })
        assert response.status_code == 400

    def test_registro_campo_email_faltante(self, client):
        """POST /api/register sin el campo 'email' retorna 400."""
        response = client.post('/api/register', json={
            'nombre': 'Test User',
            'password': 'MiClave123!',
            'confirmPassword': 'MiClave123!',
        })
        assert response.status_code == 400

    def test_registro_campo_password_faltante(self, client):
        """POST /api/register sin el campo 'password' retorna 400."""
        response = client.post('/api/register', json={
            'nombre': 'Test User',
            'email': 'test@test.com',
            'confirmPassword': 'MiClave123!',
        })
        assert response.status_code == 400

    def test_registro_campo_confirm_faltante(self, client):
        """POST /api/register sin 'confirmPassword' retorna 400."""
        response = client.post('/api/register', json={
            'nombre': 'Test User',
            'email': 'test@test.com',
            'password': 'MiClave123!',
        })
        assert response.status_code == 400

    def test_registro_con_campos_extra_no_causa_error(self, client):
        """Campos extra en el payload se ignoran sin causar error."""
        response = client.post('/api/register', json={
            'nombre': 'Test User',
            'email': 'test@test.com',
            'password': 'MiClave123!',
            'confirmPassword': 'MiClave123!',
            'campo_extra': 'valor',
            'otro_campo': 12345,
        })
        assert response.status_code == 201

    def test_registro_nombre_muy_largo(self, client):
        """Registro con nombre extremadamente largo no causa 500."""
        response = client.post('/api/register', json={
            'nombre': 'A' * 500,
            'email': 'test@test.com',
            'password': 'MiClave123!',
            'confirmPassword': 'MiClave123!',
        })
        # Puede ser 201 (acepta) o 400 (rechaza), pero no 500
        assert response.status_code != 500

    def test_registro_con_caracteres_unicode(self, client):
        """Registro con caracteres especiales (acentos, ñ, emojis) funciona."""
        response = client.post('/api/register', json={
            'nombre': 'José María Ñoño',
            'email': 'jose@correo.com',
            'password': 'MiClave123!',
            'confirmPassword': 'MiClave123!',
        })
        assert response.status_code == 201
        assert response.get_json()['usuario']['nombre'] == 'José María Ñoño'


# ═══════════════════════════════════════════════════════════════════
#  LOGIN — Peticiones malformadas
# ═══════════════════════════════════════════════════════════════════

class TestLoginRobustez:
    """Tests de robustez para POST /api/login."""

    def test_login_sin_body(self, client):
        """POST /api/login sin body retorna error (no 500)."""
        response = client.post('/api/login')
        assert response.status_code in (400, 415)

    def test_login_body_vacio_json(self, client):
        """POST /api/login con JSON vacío {} retorna 400."""
        response = client.post('/api/login', json={})
        assert response.status_code == 400

    def test_login_sin_campo_email(self, client):
        """POST /api/login sin el campo 'email' retorna 400."""
        response = client.post('/api/login', json={
            'password': 'MiClave123!',
        })
        assert response.status_code == 400

    def test_login_sin_campo_password(self, client):
        """POST /api/login sin el campo 'password' retorna 400."""
        response = client.post('/api/login', json={
            'email': 'test@test.com',
        })
        assert response.status_code == 400

    def test_login_con_campos_extra(self, client):
        """Campos extra en el payload de login se ignoran sin causar error."""
        registrar_usuario(client)
        response = client.post('/api/login', json={
            'email': 'juan@correo.com',
            'password': 'MiClave123!',
            'campo_extra': 'valor',
        })
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════
#  MÉTODOS HTTP NO PERMITIDOS
# ═══════════════════════════════════════════════════════════════════

class TestMetodosNoPermitidos:
    """Tests para verificar que métodos HTTP incorrectos retornan 405."""

    def test_register_get_no_permitido(self, client):
        """GET /api/register retorna 405 Method Not Allowed."""
        response = client.get('/api/register')
        assert response.status_code == 405

    def test_login_get_no_permitido(self, client):
        """GET /api/login retorna 405 Method Not Allowed."""
        response = client.get('/api/login')
        assert response.status_code == 405

    def test_logout_get_no_permitido(self, client):
        """GET /api/logout retorna 405 Method Not Allowed."""
        response = client.get('/api/logout')
        assert response.status_code == 405

    def test_me_post_no_permitido(self, client):
        """POST /api/me retorna 405 Method Not Allowed."""
        response = client.post('/api/me')
        assert response.status_code == 405


# ═══════════════════════════════════════════════════════════════════
#  RUTAS INEXISTENTES
# ═══════════════════════════════════════════════════════════════════

class TestRutasInexistentes:
    """Tests para verificar que rutas inexistentes retornan 404."""

    def test_ruta_api_inexistente(self, client):
        """GET /api/ruta-falsa retorna 404."""
        response = client.get('/api/ruta-falsa')
        assert response.status_code == 404

    def test_ruta_pagina_inexistente(self, client):
        """GET /pagina-falsa retorna 404."""
        response = client.get('/pagina-falsa')
        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════════
#  API /me — Robustez
# ═══════════════════════════════════════════════════════════════════

class TestApiMeRobustez:
    """Tests de robustez para GET /api/me."""

    def test_me_con_sesion_corrupta(self, client):
        """Si la sesión tiene un user_id inválido, retorna 404 y limpia la sesión."""
        # Simular una sesión con un user_id que no existe en la BD
        with client.session_transaction() as sess:
            sess['user_id'] = 'id-que-no-existe-en-bd'
            sess['user_nombre'] = 'Fantasma'
            sess['user_email'] = 'fantasma@test.com'

        response = client.get('/api/me')
        assert response.status_code == 404
        assert 'no encontrado' in response.get_json()['error'].lower()

        # Verificar que la sesión se limpió
        response2 = client.get('/api/me')
        assert response2.status_code == 401

    def test_me_multiples_llamadas_consecutivas(self, client):
        """Múltiples llamadas a /api/me retornan los mismos datos."""
        registrar_usuario(client)
        login_usuario(client)

        r1 = client.get('/api/me')
        r2 = client.get('/api/me')
        r3 = client.get('/api/me')

        assert r1.get_json() == r2.get_json() == r3.get_json()
