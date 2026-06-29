"""
test_recuperar.py — Tests de integración para la recuperación de contraseña.

Endpoints: POST /api/forgot-password, POST /api/reset-password
Requisito: REQ-F04 / REQ-NF01

NOTA: forgot-password solo devuelve 'reset_url' cuando la app está en modo
debug y no hay SMTP configurado. Estos tests activan app.debug para poder
obtener el enlace y completar el flujo sin enviar correos reales.
"""

import re
from tests.helpers import registrar_usuario, login_usuario, USUARIO_VALIDO


def _pedir_token(client, email):
    """Solicita recuperación y devuelve el token del enlace (modo debug)."""
    client.application.debug = True  # fuerza que la API devuelva reset_url
    r = client.post('/api/forgot-password', json={'email': email})
    data = r.get_json()
    url = data.get('reset_url')
    if not url:
        return None
    return re.search(r'token=([^&]+)', url).group(1)


# ═══════════════════════════════════════════════════════════════════
#  SOLICITAR ENLACE
# ═══════════════════════════════════════════════════════════════════

class TestForgotPassword:
    """POST /api/forgot-password."""

    def test_email_existente_retorna_200(self, client):
        registrar_usuario(client)
        r = client.post('/api/forgot-password', json={'email': USUARIO_VALIDO['email']})
        assert r.status_code == 200

    def test_email_inexistente_mismo_mensaje(self, client):
        """No revela si el email existe (anti-enumeración): mismo mensaje."""
        registrar_usuario(client)
        r1 = client.post('/api/forgot-password', json={'email': USUARIO_VALIDO['email']})
        r2 = client.post('/api/forgot-password', json={'email': 'noexiste@correo.com'})
        assert r1.get_json()['message'] == r2.get_json()['message']

    def test_email_inexistente_no_entrega_enlace(self, client):
        """Para un email no registrado nunca se entrega reset_url."""
        client.application.debug = True
        r = client.post('/api/forgot-password', json={'email': 'noexiste@correo.com'})
        assert 'reset_url' not in r.get_json()

    def test_email_vacio_retorna_400(self, client):
        r = client.post('/api/forgot-password', json={'email': ''})
        assert r.status_code == 400


# ═══════════════════════════════════════════════════════════════════
#  RESTABLECER CON TOKEN
# ═══════════════════════════════════════════════════════════════════

class TestResetPassword:
    """POST /api/reset-password."""

    def test_reset_exitoso_y_login(self, client):
        registrar_usuario(client)
        token = _pedir_token(client, USUARIO_VALIDO['email'])
        assert token is not None
        r = client.post('/api/reset-password', json={
            'token': token,
            'password': 'ClaveNueva123!',
            'confirmPassword': 'ClaveNueva123!',
        })
        assert r.status_code == 200
        # La nueva contraseña debe funcionar
        r_login = login_usuario(client, password='ClaveNueva123!')
        assert r_login.status_code == 200

    def test_token_invalido(self, client):
        r = client.post('/api/reset-password', json={
            'token': 'token-falso',
            'password': 'ClaveNueva123!',
            'confirmPassword': 'ClaveNueva123!',
        })
        assert r.status_code == 400

    def test_token_de_un_solo_uso(self, client):
        """Un token ya usado no puede reutilizarse."""
        registrar_usuario(client)
        token = _pedir_token(client, USUARIO_VALIDO['email'])
        # Primer uso: OK
        client.post('/api/reset-password', json={
            'token': token, 'password': 'ClaveNueva123!', 'confirmPassword': 'ClaveNueva123!',
        })
        # Segundo uso: rechazado
        r = client.post('/api/reset-password', json={
            'token': token, 'password': 'OtraClave123!', 'confirmPassword': 'OtraClave123!',
        })
        assert r.status_code == 400

    def test_password_debil_rechazada(self, client):
        registrar_usuario(client)
        token = _pedir_token(client, USUARIO_VALIDO['email'])
        r = client.post('/api/reset-password', json={
            'token': token, 'password': 'abc', 'confirmPassword': 'abc',
        })
        assert r.status_code == 400

    def test_passwords_no_coinciden(self, client):
        registrar_usuario(client)
        token = _pedir_token(client, USUARIO_VALIDO['email'])
        r = client.post('/api/reset-password', json={
            'token': token, 'password': 'ClaveNueva123!', 'confirmPassword': 'Distinta123!',
        })
        assert r.status_code == 400
