"""
helpers.py — Funciones y constantes reutilizables para los tests.

Contiene datos de prueba y funciones helper que simplifican la escritura
de tests de integración (registro, login, etc.).
"""


# ── Datos de prueba reutilizables ────────────────────────────────

USUARIO_VALIDO = {
    'nombre': 'Juan Pérez',
    'email': 'juan@correo.com',
    'password': 'MiClave123!',
    'confirmPassword': 'MiClave123!'
}


# ── Helpers ──────────────────────────────────────────────────────

def registrar_usuario(client, datos=None):
    """Registra un usuario vía la API. Retorna la Response de Flask.

    Args:
        client: fixture client de Flask.
        datos: dict con los campos del formulario. Si es None, usa USUARIO_VALIDO.
    """
    payload = datos if datos is not None else USUARIO_VALIDO.copy()
    return client.post(
        '/api/register',
        json=payload,
        content_type='application/json',
    )


def login_usuario(client, email=None, password=None):
    """Hace login vía la API. Retorna la Response de Flask.

    Args:
        client: fixture client de Flask.
        email: correo del usuario (por defecto usa USUARIO_VALIDO).
        password: contraseña (por defecto usa USUARIO_VALIDO).
    """
    return client.post(
        '/api/login',
        json={
            'email': email or USUARIO_VALIDO['email'],
            'password': password or USUARIO_VALIDO['password'],
        },
        content_type='application/json',
    )
