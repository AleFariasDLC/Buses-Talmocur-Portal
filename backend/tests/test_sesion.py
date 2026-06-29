"""
test_sesion.py — Tests para el manejo de sesiones y rutas protegidas.

Endpoints cubiertos:
  - POST /api/logout
  - GET  /api/me
  - GET  /login   (redirección si ya hay sesión)
  - GET  /registro (redirección si ya hay sesión)
  - GET  /         (accesible siempre)

Requisito: REQ-F04 (control de acceso)
"""

from tests.helpers import registrar_usuario, login_usuario, USUARIO_VALIDO


# ═══════════════════════════════════════════════════════════════════
#  LOGOUT — POST /api/logout
# ═══════════════════════════════════════════════════════════════════

class TestLogout:
    """Tests para el endpoint de cierre de sesión."""

    def test_logout_con_sesion_activa(self, client):
        """Logout con sesión activa retorna 200."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.post('/api/logout')
        assert response.status_code == 200

    def test_logout_mensaje(self, client):
        """El mensaje confirma que la sesión se cerró."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.post('/api/logout')
        data = response.get_json()
        assert 'cerrada' in data['message'].lower()

    def test_logout_limpia_sesion(self, client):
        """Después de logout, /api/me retorna 401 (sin sesión)."""
        registrar_usuario(client)
        login_usuario(client)
        # Verificar que hay sesión
        assert client.get('/api/me').status_code == 200
        # Hacer logout
        client.post('/api/logout')
        # Verificar que ya no hay sesión
        assert client.get('/api/me').status_code == 401

    def test_logout_sin_sesion_es_idempotente(self, client):
        """Logout sin sesión activa retorna 200 (no da error)."""
        response = client.post('/api/logout')
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════
#  API ME — GET /api/me
# ═══════════════════════════════════════════════════════════════════

class TestApiMe:
    """Tests para obtener los datos del usuario logueado."""

    def test_me_con_sesion_activa(self, client):
        """Con sesión activa, retorna 200 y datos del usuario."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.get('/api/me')
        assert response.status_code == 200

    def test_me_retorna_nombre_y_email(self, client):
        """Los datos incluyen nombre, email y fecha de registro."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.get('/api/me')
        data = response.get_json()
        usuario = data['usuario']
        assert usuario['nombre'] == USUARIO_VALIDO['nombre']
        assert usuario['email'] == USUARIO_VALIDO['email']
        assert 'fecha_registro' in usuario

    def test_me_retorna_id(self, client):
        """Los datos incluyen el ID del usuario."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.get('/api/me')
        data = response.get_json()
        assert 'id' in data['usuario']

    def test_me_no_retorna_password(self, client):
        """GET /api/me nunca retorna la contraseña."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.get('/api/me')
        data = response.get_json()
        assert 'password' not in data['usuario']
        assert 'password_hash' not in data['usuario']

    def test_me_sin_sesion(self, client):
        """Sin sesión activa, retorna 401."""
        response = client.get('/api/me')
        assert response.status_code == 401

    def test_me_sin_sesion_mensaje(self, client):
        """El mensaje indica que no hay sesión activa."""
        response = client.get('/api/me')
        data = response.get_json()
        assert 'No hay sesión' in data['error']


# ═══════════════════════════════════════════════════════════════════
#  RUTAS PROTEGIDAS — Redirecciones según sesión
# ═══════════════════════════════════════════════════════════════════

class TestRutasProtegidas:
    """Tests de redirección según estado de sesión (REQ-F04)."""

    def test_login_redirige_si_hay_sesion(self, client):
        """GET /login redirige a / si el usuario ya está logueado."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.get('/login')
        assert response.status_code == 302

    def test_registro_redirige_si_hay_sesion(self, client):
        """GET /registro redirige a / si el usuario ya está logueado."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.get('/registro')
        assert response.status_code == 302

    def test_login_accesible_sin_sesion(self, client):
        """GET /login es accesible cuando no hay sesión."""
        response = client.get('/login')
        assert response.status_code == 200

    def test_registro_accesible_sin_sesion(self, client):
        """GET /registro es accesible cuando no hay sesión."""
        response = client.get('/registro')
        assert response.status_code == 200

    def test_home_accesible_sin_sesion(self, client):
        """GET / es accesible sin sesión (página pública)."""
        response = client.get('/')
        assert response.status_code == 200

    def test_home_accesible_con_sesion(self, client):
        """GET / es accesible con sesión activa."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.get('/')
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════
#  FLUJO COMPLETO — Tests end-to-end
# ═══════════════════════════════════════════════════════════════════

class TestFlujoCompleto:
    """Tests que verifican el flujo completo de usuario."""

    def test_registro_login_me_logout(self, client):
        """Flujo: registro → login → ver datos → logout → sin acceso."""
        # 1. Registro
        r1 = registrar_usuario(client)
        assert r1.status_code == 201

        # 2. Login
        r2 = login_usuario(client)
        assert r2.status_code == 200

        # 3. Ver datos del usuario
        r3 = client.get('/api/me')
        assert r3.status_code == 200
        assert r3.get_json()['usuario']['email'] == USUARIO_VALIDO['email']

        # 4. Logout
        r4 = client.post('/api/logout')
        assert r4.status_code == 200

        # 5. Verificar que ya no hay sesión
        r5 = client.get('/api/me')
        assert r5.status_code == 401

    def test_multiples_usuarios_independientes(self, client):
        """Dos usuarios distintos se registran y hacen login correctamente."""
        # Registrar usuario 1
        registrar_usuario(client)

        # Registrar usuario 2
        datos_2 = {
            'nombre': 'María López',
            'email': 'maria@correo.com',
            'password': 'OtraClave456!',
            'confirmPassword': 'OtraClave456!',
        }
        r2 = registrar_usuario(client, datos_2)
        assert r2.status_code == 201

        # Login con usuario 2
        r3 = login_usuario(client, email='maria@correo.com', password='OtraClave456!')
        assert r3.status_code == 200
        assert r3.get_json()['usuario']['nombre'] == 'María López'

    def test_login_cambia_sesion_a_nuevo_usuario(self, client):
        """Si un usuario hace login con otra cuenta, la sesión cambia."""
        # Registrar 2 usuarios
        registrar_usuario(client)
        datos_2 = {
            'nombre': 'Ana Torres',
            'email': 'ana@correo.com',
            'password': 'AnaPass789!',
            'confirmPassword': 'AnaPass789!',
        }
        registrar_usuario(client, datos_2)

        # Login con usuario 1
        login_usuario(client)
        r1 = client.get('/api/me')
        assert r1.get_json()['usuario']['nombre'] == USUARIO_VALIDO['nombre']

        # Login con usuario 2 (sin logout previo)
        login_usuario(client, email='ana@correo.com', password='AnaPass789!')
        r2 = client.get('/api/me')
        assert r2.get_json()['usuario']['nombre'] == 'Ana Torres'
