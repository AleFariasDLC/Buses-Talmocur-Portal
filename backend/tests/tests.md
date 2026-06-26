# 🧪 Tests Automatizados — Buses Talmocur Portal

Suite de tests automatizados con **pytest** para verificar el correcto funcionamiento del backend del portal.

---

## Requisitos

- Python 3.12+
- Dependencias del proyecto instaladas (`pip install -r requirements.txt`)
- pytest instalado (`pip install pytest`)

---

## Cómo ejecutar los tests

Desde la carpeta `backend/`:

```bash
# Con el entorno virtual activado:
python -m pytest tests/ -v
```

O apuntando directamente al ejecutable del venv:

```bash
# Windows (PowerShell):
& ".venv\Scripts\python.exe" -m pytest tests/ -v
```

### Opciones útiles

```bash
# Ejecutar solo los tests de validaciones (rápido, no necesita BD):
python -m pytest tests/test_validaciones.py -v

# Ejecutar solo los tests de registro:
python -m pytest tests/test_registro.py -v

# Ejecutar un test específico:
python -m pytest tests/test_login.py::TestLoginExitoso::test_login_credenciales_correctas -v

# Ver un resumen corto:
python -m pytest tests/ --tb=line

# Modo silencioso (solo muestra fallos):
python -m pytest tests/ -q
```

---

## Estructura de archivos

```
backend/
├── pytest.ini              # Configuración de pytest
└── tests/
    ├── __init__.py          # Marca tests/ como paquete Python
    ├── conftest.py          # Fixture principal (cliente Flask con BD aislada)
    ├── helpers.py           # Constantes y funciones reutilizables
    ├── test_validaciones.py # Tests unitarios de validación
    ├── test_registro.py     # Tests de integración para registro
    ├── test_login.py        # Tests de integración para login
    ├── test_sesion.py       # Tests de sesión, logout y flujos completos
    ├── test_perfil.py       # Tests de perfil, context processor y cache
    ├── test_db_sqlite.py    # Tests unitarios para funciones CRUD
    └── test_robustez.py     # Tests de robustez y casos borde de la API
```

---

## Descripción de cada módulo de tests

### `test_validaciones.py` — 18 tests

Tests **unitarios** para las funciones de validación en `utils.py`. No requieren base de datos ni servidor Flask.

| Clase | Qué verifica |
|:------|:-------------|
| `TestValidarPasswordExitosa` | Contraseñas que cumplen todos los criterios |
| `TestValidarPasswordLongitud` | Rechazo por menos de 8 caracteres |
| `TestValidarPasswordMayusculas` | Rechazo por falta de mayúscula |
| `TestValidarPasswordMinusculas` | Rechazo por falta de minúscula |
| `TestValidarPasswordNumeros` | Rechazo por falta de número |
| `TestValidarPasswordEspeciales` | Rechazo por falta de carácter especial |
| `TestValidarPasswordCasosBorde` | Contraseñas vacías, solo espacios, solo números, etc. |
| `TestValidarEmailExitoso` | Emails con formato válido (puntos, subdominios, .cl, etc.) |
| `TestValidarEmailRechazado` | Emails sin @, sin dominio, vacíos, con espacios, etc. |

---

### `test_registro.py` — 20 tests

Tests de **integración** para el endpoint `POST /api/register`.

| Clase | Qué verifica |
|:------|:-------------|
| `TestRegistroExitoso` | Registro exitoso, datos retornados, email normalizado, ID generado |
| `TestRegistroNombreInvalido` | Nombre vacío o solo espacios |
| `TestRegistroEmailInvalido` | Email sin @, sin dominio, vacío |
| `TestRegistroEmailDuplicado` | Email ya registrado (409), insensible a mayúsculas |
| `TestRegistroPasswordInvalida` | Contraseña corta, sin mayúscula, sin minúscula, sin número, sin especial |
| `TestRegistroConfirmacionPassword` | Contraseñas que no coinciden |
| `TestRegistroSeguridad` | La contraseña nunca se retorna al cliente (REQ-NF01) |

---

### `test_login.py` — 13 tests

Tests de **integración** para el endpoint `POST /api/login`.

| Clase | Qué verifica |
|:------|:-------------|
| `TestLoginExitoso` | Login correcto, datos retornados, contraseña no expuesta |
| `TestLoginEmailInexistente` | Email no registrado retorna 401 con mensaje genérico |
| `TestLoginPasswordIncorrecta` | Contraseña incorrecta retorna 401 con mensaje genérico |
| `TestLoginMensajeSeguridad` | El mensaje de error es idéntico para email falso y password falsa |
| `TestLoginCamposVacios` | Campos vacíos retornan error |

---

### `test_sesion.py` — 19 tests

Tests de **integración** para el manejo de sesiones y rutas protegidas.

| Clase | Qué verifica |
|:------|:-------------|
| `TestLogout` | Cierre de sesión, limpieza de cookie, idempotencia |
| `TestApiMe` | Datos del usuario logueado, sin sesión retorna 401 |
| `TestRutasProtegidas` | `/login` y `/registro` redirigen si hay sesión, home siempre accesible |
| `TestFlujoCompleto` | Registro → login → ver datos → logout, múltiples usuarios |

---

### `test_perfil.py` — 12 tests

Tests de **integración** para la ruta `/perfil`, el context processor y los headers de cache.

| Clase | Qué verifica |
|:------|:-------------|
| `TestPerfilAcceso` | `/perfil` accesible con y sin sesión, retorna HTML |
| `TestContextProcessor` | `inject_usuario()` inyecta datos al navbar, menú de usuario aparece/desaparece según sesión |
| `TestCacheHeaders` | `/login` y `/registro` tienen `Cache-Control: no-store`, home no lo tiene |

---

### `test_db_sqlite.py` — 24 tests

Tests **unitarios** para las funciones CRUD en `db_sqlite.py`.

| Clase | Qué verifica |
|:------|:-------------|
| `TestCrearUsuario` | Creación con datos válidos, UUID, normalización de email, strip de nombre, rol por defecto |
| `TestBuscarPorEmail` | Búsqueda existente/inexistente, insensible a mayúsculas, incluye hash, strip de espacios |
| `TestBuscarPorId` | Búsqueda por UUID existente/inexistente, datos completos |
| `TestActualizarUsuario` | Actualización de nombre/email/rol/password, múltiples campos, campos no permitidos ignorados, preservación de campos no modificados |

---

### `test_robustez.py` — 22 tests

Tests de **robustez** para verificar que la API maneja correctamente peticiones malformadas.

| Clase | Qué verifica |
|:------|:-------------|
| `TestRegistroRobustez` | Sin body, JSON vacío, campos faltantes, campos extra, nombre largo, caracteres Unicode |
| `TestLoginRobustez` | Sin body, JSON vacío, campos faltantes, campos extra |
| `TestMetodosNoPermitidos` | GET en endpoints POST retorna 405, POST en endpoint GET retorna 405 |
| `TestRutasInexistentes` | Rutas inexistentes retornan 404 |
| `TestApiMeRobustez` | Sesión corrupta (user_id inválido) retorna 404 y limpia sesión, llamadas consecutivas |

---

## Cómo funciona el aislamiento de tests

Cada test recibe una **base de datos SQLite en memoria** completamente vacía e independiente. Esto se logra mediante la fixture `client` en `conftest.py`:

1. Se crea un motor SQLite en memoria (`sqlite:///:memory:`)
2. Se crean todas las tablas del proyecto en esa BD temporal
3. Se redirige la función `obtener_sesion()` para que use la BD temporal
4. Se entrega un cliente Flask listo para hacer peticiones
5. Al terminar el test, la BD se destruye

Esto garantiza que:
- Los tests **no modifican** la base de datos real del proyecto
- Cada test es **independiente** — no importa el orden de ejecución
- Los tests son **rápidos** — SQLite en memoria es casi instantáneo

---

## Cómo agregar nuevos tests

### 1. Test unitario (sin BD)

Si estás testeando una función pura (como validaciones), agrega tests en `test_validaciones.py` o crea un nuevo archivo `test_<nombre>.py`:

```python
from utils import mi_funcion

class TestMiFuncion:
    def test_caso_exitoso(self):
        assert mi_funcion('input') == 'output esperado'

    def test_caso_fallido(self):
        resultado = mi_funcion('input malo')
        assert resultado is not True
```

### 2. Test de integración (con BD y API)

Si necesitas hacer peticiones HTTP al backend, usa la fixture `client` y los helpers:

```python
from tests.helpers import registrar_usuario, login_usuario, USUARIO_VALIDO

class TestMiEndpoint:
    def test_ejemplo(self, client):
        # Registrar y logear un usuario
        registrar_usuario(client)
        login_usuario(client)

        # Hacer la petición que quieres testear
        response = client.get('/api/mi-endpoint')
        assert response.status_code == 200
```

### 3. Test unitario de BD (funciones CRUD)

Si necesitas testear funciones CRUD directamente, usa la fixture `client` para tener la BD aislada:

```python
import db_sqlite as db

class TestMiFuncionCRUD:
    def test_ejemplo(self, client):
        # La fixture `client` configura la BD en memoria
        resultado = db.crear_usuario('Test', 'test@test.com', 'hash')
        assert resultado['nombre'] == 'Test'
```

---

## Trazabilidad con requisitos

| Requisito | Tests que lo cubren |
|:----------|:-------------------|
| REQ-F04 — Login y control de acceso | `test_login.py`, `test_sesion.py`, `test_perfil.py` |
| REQ-NF01 — Contraseñas cifradas | `test_registro.py::TestRegistroSeguridad` |
| REQ-NF03 — Interfaz en español | Todos los tests verifican mensajes en español |
| Robustez y seguridad | `test_robustez.py` |

---

## Resultado actual

```
============================= 138 passed in ~18s ==============================
```
