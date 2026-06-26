"""
test_perfil.py — Tests de integración para la ruta /perfil.

Endpoint: GET /perfil
Requisito: REQ-F04 (control de acceso — página de perfil)
"""

from tests.helpers import registrar_usuario, login_usuario, USUARIO_VALIDO


# ═══════════════════════════════════════════════════════════════════
#  ACCESO A /perfil
# ═══════════════════════════════════════════════════════════════════

class TestPerfilAcceso:
    """Tests de acceso a la página de perfil."""

    def test_perfil_accesible_sin_sesion(self, client):
        """GET /perfil retorna 200 incluso sin sesión (renderiza el template)."""
        response = client.get('/perfil')
        assert response.status_code == 200

    def test_perfil_accesible_con_sesion(self, client):
        """GET /perfil retorna 200 con sesión activa."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.get('/perfil')
        assert response.status_code == 200

    def test_perfil_retorna_html(self, client):
        """La respuesta de /perfil es HTML."""
        response = client.get('/perfil')
        assert 'text/html' in response.content_type


# ═══════════════════════════════════════════════════════════════════
#  CONTEXT PROCESSOR — inject_usuario()
# ═══════════════════════════════════════════════════════════════════

class TestContextProcessor:
    """Tests para verificar que inject_usuario() inyecta datos al template.

    NOTA: El navbar muestra solo el primer nombre del usuario (ej. "Juan"),
    no el nombre completo. La página de perfil carga los datos del usuario
    vía JavaScript (/api/me), no los renderiza en el HTML del servidor.
    """

    def test_home_sin_sesion_no_muestra_menu_usuario(self, client):
        """Sin sesión, el HTML del home no contiene el menú de usuario."""
        response = client.get('/')
        html = response.data.decode('utf-8')
        assert 'usuario-menu__nombre' not in html

    def test_home_con_sesion_muestra_nombre_en_navbar(self, client):
        """Con sesión, el navbar muestra el primer nombre del usuario."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.get('/')
        html = response.data.decode('utf-8')
        # El template muestra el primer nombre (split del nombre completo)
        primer_nombre = USUARIO_VALIDO['nombre'].split()[0]
        assert primer_nombre in html

    def test_home_con_sesion_tiene_menu_usuario(self, client):
        """Con sesión, el HTML contiene el menú desplegable del usuario."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.get('/')
        html = response.data.decode('utf-8')
        assert 'usuario-menu__nombre' in html
        assert 'btnCerrarSesion' in html

    def test_perfil_con_sesion_muestra_menu_usuario(self, client):
        """Con sesión, el navbar del perfil muestra el menú de usuario."""
        registrar_usuario(client)
        login_usuario(client)
        response = client.get('/perfil')
        html = response.data.decode('utf-8')
        assert 'usuario-menu' in html

    def test_logout_limpia_datos_del_template(self, client):
        """Después de logout, el menú de usuario desaparece del navbar."""
        registrar_usuario(client)
        login_usuario(client)
        # Verificar que aparece con sesión
        r1 = client.get('/')
        assert 'usuario-menu__nombre' in r1.data.decode('utf-8')
        # Hacer logout
        client.post('/api/logout')
        # Verificar que ya no aparece
        r2 = client.get('/')
        assert 'usuario-menu__nombre' not in r2.data.decode('utf-8')


# ═══════════════════════════════════════════════════════════════════
#  HEADERS DE CACHE — Login y Registro
# ═══════════════════════════════════════════════════════════════════

class TestCacheHeaders:
    """Tests para verificar que las páginas sensibles tienen Cache-Control: no-store."""

    def test_login_tiene_cache_control_no_store(self, client):
        """GET /login incluye header Cache-Control: no-store."""
        response = client.get('/login')
        assert response.headers.get('Cache-Control') == 'no-store'

    def test_registro_tiene_cache_control_no_store(self, client):
        """GET /registro incluye header Cache-Control: no-store."""
        response = client.get('/registro')
        assert response.headers.get('Cache-Control') == 'no-store'

    def test_home_no_tiene_no_store(self, client):
        """GET / (home) no necesita Cache-Control: no-store."""
        response = client.get('/')
        cache_control = response.headers.get('Cache-Control', '')
        assert 'no-store' not in cache_control
