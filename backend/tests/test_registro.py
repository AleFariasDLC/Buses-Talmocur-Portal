"""
test_registro.py — Tests de integración para el endpoint de registro.

Endpoint: POST /api/register
Requisito: REQ-F04 (parcial — registro de usuarios)
Requisito: REQ-NF01 (contraseñas cifradas)
"""

from tests.helpers import registrar_usuario, USUARIO_VALIDO


# ═══════════════════════════════════════════════════════════════════
#  REGISTRO EXITOSO
# ═══════════════════════════════════════════════════════════════════

class TestRegistroExitoso:
    """Casos donde el registro debe retornar 201 Created."""

    def test_registro_con_datos_validos(self, client):
        """Registro con todos los campos válidos retorna 201."""
        response = registrar_usuario(client)
        assert response.status_code == 201

    def test_registro_mensaje_exitoso(self, client):
        """La respuesta contiene mensaje de éxito."""
        response = registrar_usuario(client)
        data = response.get_json()
        assert 'Cuenta creada exitosamente' in data['message']

    def test_registro_retorna_datos_usuario(self, client):
        """La respuesta incluye los datos del usuario creado."""
        response = registrar_usuario(client)
        data = response.get_json()
        assert 'usuario' in data
        usuario = data['usuario']
        assert usuario['nombre'] == USUARIO_VALIDO['nombre']

    def test_registro_email_normalizado_a_minusculas(self, client):
        """El email se guarda en minúsculas sin importar el input."""
        datos = USUARIO_VALIDO.copy()
        datos['email'] = 'JUAN@CORREO.COM'
        response = registrar_usuario(client, datos)
        assert response.status_code == 201
        assert response.get_json()['usuario']['email'] == 'juan@correo.com'

    def test_registro_no_retorna_password_hash(self, client):
        """La respuesta NO incluye el hash de la contraseña (seguridad)."""
        response = registrar_usuario(client)
        data = response.get_json()
        usuario = data['usuario']
        assert 'password_hash' not in usuario
        assert 'password' not in usuario

    def test_registro_genera_id(self, client):
        """El usuario creado recibe un ID único."""
        response = registrar_usuario(client)
        data = response.get_json()
        assert 'id' in data['usuario']
        assert len(data['usuario']['id']) > 0

    def test_registro_guarda_fecha_nacimiento(self, client):
        """La fecha de nacimiento se persiste en el usuario creado."""
        response = registrar_usuario(client)
        data = response.get_json()
        assert data['usuario']['fecha_nacimiento'] == '1995-06-20'


# ═══════════════════════════════════════════════════════════════════
#  NOMBRE INVÁLIDO
# ═══════════════════════════════════════════════════════════════════

class TestRegistroNombreInvalido:
    """Casos donde el nombre no es válido."""

    def test_nombre_vacio(self, client):
        """Nombre vacío retorna 400."""
        datos = USUARIO_VALIDO.copy()
        datos['nombre'] = ''
        response = registrar_usuario(client, datos)
        assert response.status_code == 400
        assert 'obligatorio' in response.get_json()['error'].lower()

    def test_nombre_solo_espacios(self, client):
        """Nombre con solo espacios retorna 400 (se hace strip)."""
        datos = USUARIO_VALIDO.copy()
        datos['nombre'] = '   '
        response = registrar_usuario(client, datos)
        assert response.status_code == 400


# ═══════════════════════════════════════════════════════════════════
#  EMAIL INVÁLIDO O DUPLICADO
# ═══════════════════════════════════════════════════════════════════

class TestRegistroEmailInvalido:
    """Casos donde el email es inválido."""

    def test_email_sin_arroba(self, client):
        """Email sin @ retorna 400."""
        datos = USUARIO_VALIDO.copy()
        datos['email'] = 'no-es-email'
        response = registrar_usuario(client, datos)
        assert response.status_code == 400
        assert 'correo' in response.get_json()['error'].lower()

    def test_email_sin_dominio(self, client):
        """Email sin dominio retorna 400."""
        datos = USUARIO_VALIDO.copy()
        datos['email'] = 'usuario@'
        response = registrar_usuario(client, datos)
        assert response.status_code == 400

    def test_email_vacio(self, client):
        """Email vacío retorna 400."""
        datos = USUARIO_VALIDO.copy()
        datos['email'] = ''
        response = registrar_usuario(client, datos)
        assert response.status_code == 400


class TestRegistroEmailDuplicado:
    """Casos de email ya registrado."""

    def test_email_duplicado_retorna_409(self, client):
        """Registrar con email ya existente retorna 409 Conflict."""
        # Primer registro: exitoso
        registrar_usuario(client)
        # Segundo registro: email duplicado
        response = registrar_usuario(client)
        assert response.status_code == 409
        assert 'ya existe' in response.get_json()['error'].lower()

    def test_email_duplicado_insensible_a_mayusculas(self, client):
        """La detección de duplicados ignora mayúsculas/minúsculas."""
        registrar_usuario(client)
        datos = USUARIO_VALIDO.copy()
        datos['email'] = 'JUAN@CORREO.COM'  # mismo email en mayúsculas
        response = registrar_usuario(client, datos)
        assert response.status_code == 409


# ═══════════════════════════════════════════════════════════════════
#  CONTRASEÑA INVÁLIDA
# ═══════════════════════════════════════════════════════════════════

class TestRegistroPasswordInvalida:
    """Casos donde la contraseña no cumple los requisitos de seguridad."""

    def test_password_menor_8_caracteres(self, client):
        """Contraseña menor a 8 caracteres retorna 400."""
        datos = USUARIO_VALIDO.copy()
        datos['password'] = 'Ab1!'
        datos['confirmPassword'] = 'Ab1!'
        response = registrar_usuario(client, datos)
        assert response.status_code == 400
        assert '8 caracteres' in response.get_json()['error']

    def test_password_sin_mayuscula(self, client):
        """Contraseña sin mayúsculas retorna 400."""
        datos = USUARIO_VALIDO.copy()
        datos['password'] = 'miclave123!'
        datos['confirmPassword'] = 'miclave123!'
        response = registrar_usuario(client, datos)
        assert response.status_code == 400
        assert 'mayúscula' in response.get_json()['error']

    def test_password_sin_minuscula(self, client):
        """Contraseña sin minúsculas retorna 400."""
        datos = USUARIO_VALIDO.copy()
        datos['password'] = 'MICLAVE123!'
        datos['confirmPassword'] = 'MICLAVE123!'
        response = registrar_usuario(client, datos)
        assert response.status_code == 400
        assert 'minúscula' in response.get_json()['error']

    def test_password_sin_numero(self, client):
        """Contraseña sin números retorna 400."""
        datos = USUARIO_VALIDO.copy()
        datos['password'] = 'MiClaveSegura!'
        datos['confirmPassword'] = 'MiClaveSegura!'
        response = registrar_usuario(client, datos)
        assert response.status_code == 400
        assert 'número' in response.get_json()['error']

    def test_password_sin_caracter_especial(self, client):
        """Contraseña sin caracteres especiales retorna 400."""
        datos = USUARIO_VALIDO.copy()
        datos['password'] = 'MiClave123'
        datos['confirmPassword'] = 'MiClave123'
        response = registrar_usuario(client, datos)
        assert response.status_code == 400
        assert 'especial' in response.get_json()['error']


class TestRegistroConfirmacionPassword:
    """Casos donde las contraseñas no coinciden."""

    def test_passwords_no_coinciden(self, client):
        """Contraseña y confirmación diferentes retorna 400."""
        datos = USUARIO_VALIDO.copy()
        datos['confirmPassword'] = 'OtraClave456!'
        response = registrar_usuario(client, datos)
        assert response.status_code == 400
        assert 'no coinciden' in response.get_json()['error'].lower()


# ═══════════════════════════════════════════════════════════════════
#  SEGURIDAD — REQ-NF01
# ═══════════════════════════════════════════════════════════════════

class TestRegistroSeguridad:
    """Tests de seguridad relacionados al registro."""

    def test_password_no_se_almacena_en_texto_plano(self, client):
        """REQ-NF01: la contraseña nunca se retorna al cliente."""
        response = registrar_usuario(client)
        data = response.get_json()
        # El campo password_hash no debe estar en la respuesta
        assert 'password_hash' not in data.get('usuario', {})
        # Tampoco la contraseña original
        assert USUARIO_VALIDO['password'] not in str(data)
