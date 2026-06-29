"""
test_perfil_editar.py — Tests de integración para la edición de perfil.

Endpoint: PUT /api/me
Requisito: REQ-F04 (gestión de la cuenta de usuario)
"""

from tests.helpers import registrar_usuario, login_usuario, USUARIO_VALIDO


# ═══════════════════════════════════════════════════════════════════
#  EDICIÓN EXITOSA
# ═══════════════════════════════════════════════════════════════════

class TestEditarPerfilExitoso:
    """Casos donde la edición debe retornar 200 OK."""

    def test_editar_nombre(self, client):
        """Con sesión, cambiar el nombre retorna 200 y el nombre nuevo."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.put('/api/me', json={
            'nombre': 'Nombre Editado',
            'email': USUARIO_VALIDO['email'],
        })
        assert response.status_code == 200
        assert response.get_json()['usuario']['nombre'] == 'Nombre Editado'

    def test_editar_email(self, client):
        """Cambiar el email a uno libre retorna 200."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.put('/api/me', json={
            'nombre': USUARIO_VALIDO['nombre'],
            'email': 'nuevo@correo.com',
        })
        assert response.status_code == 200
        assert response.get_json()['usuario']['email'] == 'nuevo@correo.com'

    def test_editar_no_retorna_password(self, client):
        """La respuesta nunca incluye el hash de la contraseña."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.put('/api/me', json={
            'nombre': 'Otro Nombre',
            'email': USUARIO_VALIDO['email'],
        })
        usuario = response.get_json()['usuario']
        assert 'password_hash' not in usuario
        assert 'password' not in usuario


# ═══════════════════════════════════════════════════════════════════
#  CONTROL DE ACCESO
# ═══════════════════════════════════════════════════════════════════

class TestEditarPerfilSinSesion:
    """Sin sesión activa no se puede editar."""

    def test_editar_sin_sesion_retorna_401(self, client):
        """PUT /api/me sin sesión retorna 401."""
        response = client.put('/api/me', json={
            'nombre': 'Hacker', 'email': 'hacker@correo.com'
        })
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════════════
#  VALIDACIONES
# ═══════════════════════════════════════════════════════════════════

class TestEditarPerfilValidaciones:
    """Validaciones de los campos al editar."""

    def test_nombre_vacio(self, client):
        """Nombre vacío retorna 400."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.put('/api/me', json={
            'nombre': '', 'email': USUARIO_VALIDO['email']
        })
        assert response.status_code == 400

    def test_email_invalido(self, client):
        """Email inválido retorna 400."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.put('/api/me', json={
            'nombre': USUARIO_VALIDO['nombre'], 'email': 'no-es-email'
        })
        assert response.status_code == 400

    def test_email_de_otro_usuario(self, client):
        """No se puede tomar el email de otro usuario (409)."""
        # Usuario 1
        registrar_usuario(client)
        # Usuario 2
        otro = USUARIO_VALIDO.copy()
        otro['email'] = 'otro@correo.com'
        registrar_usuario(client, otro)
        # Login como usuario 2 e intentar usar el email del usuario 1
        login_usuario(client, email='otro@correo.com')
        response = client.put('/api/me', json={
            'nombre': otro['nombre'], 'email': USUARIO_VALIDO['email']
        })
        assert response.status_code == 409


# ═══════════════════════════════════════════════════════════════════
#  CAMBIO DE CONTRASEÑA DESDE EL PERFIL
# ═══════════════════════════════════════════════════════════════════

class TestEditarPerfilPassword:
    """Cambio de contraseña con verificación de la contraseña actual."""

    def test_password_actual_incorrecta(self, client):
        """Si la contraseña actual no coincide, retorna 401."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.put('/api/me', json={
            'nombre': USUARIO_VALIDO['nombre'],
            'email': USUARIO_VALIDO['email'],
            'currentPassword': 'ClaveQueNoEs1!',
            'password': 'NuevaClave123!',
            'confirmPassword': 'NuevaClave123!',
        })
        assert response.status_code == 401

    def test_password_nueva_debil(self, client):
        """Una nueva contraseña débil retorna 400."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.put('/api/me', json={
            'nombre': USUARIO_VALIDO['nombre'],
            'email': USUARIO_VALIDO['email'],
            'currentPassword': USUARIO_VALIDO['password'],
            'password': 'abc',
            'confirmPassword': 'abc',
        })
        assert response.status_code == 400

    def test_password_cambia_y_permite_login(self, client):
        """Con la contraseña actual correcta, el cambio funciona y permite login."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.put('/api/me', json={
            'nombre': USUARIO_VALIDO['nombre'],
            'email': USUARIO_VALIDO['email'],
            'currentPassword': USUARIO_VALIDO['password'],
            'password': 'NuevaClave123!',
            'confirmPassword': 'NuevaClave123!',
        })
        assert response.status_code == 200
        # Cerrar sesión y entrar con la nueva contraseña
        client.post('/api/logout')
        r_login = login_usuario(client, password='NuevaClave123!')
        assert r_login.status_code == 200
