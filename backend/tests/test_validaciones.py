"""
test_validaciones.py — Tests unitarios para las funciones de validación.

Módulo testeado: utils.py
Funciones cubiertas:
  - validar_password(): longitud, mayúsculas, minúsculas, números, especiales
  - validar_email(): formato de correo electrónico

Estos tests NO necesitan la BD ni el servidor Flask (son unitarios puros).
"""

from utils import validar_password, validar_email


# ═══════════════════════════════════════════════════════════════════
#  VALIDACIÓN DE CONTRASEÑA
# ═══════════════════════════════════════════════════════════════════

class TestValidarPasswordExitosa:
    """Casos donde la contraseña cumple todos los requisitos."""

    def test_password_valida_basica(self):
        """Contraseña que cumple todos los criterios retorna True."""
        assert validar_password('MiClave123!') is True

    def test_password_exactamente_8_caracteres(self):
        """Contraseña con exactamente 8 caracteres (el mínimo) es aceptada."""
        assert validar_password('Abcde1!x') is True

    def test_password_larga(self):
        """Contraseña muy larga es aceptada."""
        assert validar_password('EstaEsUnaContraseñaMuyLarga123!') is True

    def test_password_con_multiples_especiales(self):
        """Contraseña con varios caracteres especiales es aceptada."""
        assert validar_password('Cl@ve#2024!') is True


class TestValidarPasswordLongitud:
    """Casos de longitud de contraseña."""

    def test_password_menor_a_8_caracteres(self):
        """Contraseña con menos de 8 caracteres es rechazada."""
        resultado = validar_password('Ab1!')
        assert resultado is not True
        assert '8 caracteres' in resultado

    def test_password_con_7_caracteres(self):
        """Contraseña con exactamente 7 caracteres es rechazada."""
        resultado = validar_password('Abcde1!')
        assert resultado is not True

    def test_password_vacia(self):
        """Contraseña vacía es rechazada."""
        resultado = validar_password('')
        assert resultado is not True


class TestValidarPasswordMayusculas:
    """Casos de requisito de mayúsculas."""

    def test_sin_mayuscula(self):
        """Contraseña sin ninguna mayúscula es rechazada."""
        resultado = validar_password('miclave123!')
        assert resultado is not True
        assert 'mayúscula' in resultado


class TestValidarPasswordMinusculas:
    """Casos de requisito de minúsculas."""

    def test_sin_minuscula(self):
        """Contraseña sin ninguna minúscula es rechazada."""
        resultado = validar_password('MICLAVE123!')
        assert resultado is not True
        assert 'minúscula' in resultado


class TestValidarPasswordNumeros:
    """Casos de requisito de números."""

    def test_sin_numero(self):
        """Contraseña sin números es rechazada."""
        resultado = validar_password('MiClave!!!')
        assert resultado is not True
        assert 'número' in resultado


class TestValidarPasswordEspeciales:
    """Casos de requisito de caracteres especiales."""

    def test_sin_caracter_especial(self):
        """Contraseña sin caracteres especiales es rechazada."""
        resultado = validar_password('MiClave123')
        assert resultado is not True
        assert 'especial' in resultado


class TestValidarPasswordCasosBorde:
    """Casos borde y combinaciones inusuales."""

    def test_solo_espacios(self):
        """Contraseña de solo espacios es rechazada."""
        resultado = validar_password('        ')
        assert resultado is not True

    def test_solo_numeros(self):
        """Contraseña de solo números es rechazada (falta mayúscula, minúscula, especial)."""
        resultado = validar_password('12345678')
        assert resultado is not True

    def test_solo_letras_minusculas(self):
        """Contraseña de solo minúsculas es rechazada (falta mayúscula, número, especial)."""
        resultado = validar_password('abcdefgh')
        assert resultado is not True

    def test_solo_letras_mayusculas(self):
        """Contraseña de solo mayúsculas es rechazada (falta minúscula, número, especial)."""
        resultado = validar_password('ABCDEFGH')
        assert resultado is not True


# ═══════════════════════════════════════════════════════════════════
#  VALIDACIÓN DE EMAIL
# ═══════════════════════════════════════════════════════════════════

class TestValidarEmailExitoso:
    """Casos donde el email tiene formato válido."""

    def test_email_simple(self):
        """Email con formato estándar es aceptado."""
        assert validar_email('usuario@correo.com') is True

    def test_email_con_puntos_en_nombre(self):
        """Email con puntos en el nombre es aceptado."""
        assert validar_email('nombre.apellido@correo.com') is True

    def test_email_con_subdominio(self):
        """Email con subdominio es aceptado."""
        assert validar_email('usuario@mail.empresa.com') is True

    def test_email_con_numeros(self):
        """Email con números es aceptado."""
        assert validar_email('usuario123@correo.com') is True

    def test_email_con_guion_bajo(self):
        """Email con guion bajo es aceptado."""
        assert validar_email('nombre_apellido@correo.com') is True

    def test_email_con_guion(self):
        """Email con guion en el nombre es aceptado."""
        assert validar_email('nombre-apellido@correo.com') is True

    def test_email_dominio_cl(self):
        """Email con dominio .cl (chileno) es aceptado."""
        assert validar_email('usuario@empresa.cl') is True


class TestValidarEmailRechazado:
    """Casos donde el email tiene formato inválido."""

    def test_sin_arroba(self):
        """Email sin @ es rechazado."""
        resultado = validar_email('usuariocorreo.com')
        assert resultado is not True

    def test_sin_dominio(self):
        """Email sin dominio después del @ es rechazado."""
        resultado = validar_email('usuario@')
        assert resultado is not True

    def test_sin_extension(self):
        """Email sin extensión (.com, .cl, etc.) es rechazado."""
        resultado = validar_email('usuario@correo')
        assert resultado is not True

    def test_vacio(self):
        """Email vacío es rechazado."""
        resultado = validar_email('')
        assert resultado is not True

    def test_con_espacios(self):
        """Email con espacios es rechazado."""
        resultado = validar_email('usuario @correo.com')
        assert resultado is not True

    def test_solo_arroba(self):
        """Solo @ no es un email válido."""
        resultado = validar_email('@')
        assert resultado is not True

    def test_multiples_arrobas(self):
        """Email con múltiples @ es rechazado."""
        resultado = validar_email('user@@correo.com')
        assert resultado is not True
