"""
test_admin_buses.py — Tests de integración para el CRUD de buses (admin).

Endpoints:
    GET    /api/buses            — Listar todos los buses
    POST   /api/buses            — Crear un bus nuevo
    PUT    /api/buses/<patente>   — Editar un bus
    DELETE /api/buses/<patente>   — Eliminar un bus

Requisito: Solo accesible por administradores (rol 'admin').
"""

from tests.helpers import (
    registrar_usuario, login_usuario, registrar_y_login_admin,
    crear_bus_test, USUARIO_VALIDO,
)


# ═══════════════════════════════════════════════════════════════════
#  CONTROL DE ACCESO — Solo admin
# ═══════════════════════════════════════════════════════════════════

class TestBusesAcceso:
    """Verificar que solo los admin pueden acceder al CRUD de buses."""

    def test_listar_buses_sin_sesion_retorna_403(self, client):
        """GET /api/buses sin sesión retorna 403."""
        r = client.get('/api/buses')
        assert r.status_code == 403

    def test_listar_buses_como_pasajero_retorna_403(self, client):
        """Un usuario con rol 'pasajero' no puede listar buses."""
        registrar_usuario(client)
        login_usuario(client)
        r = client.get('/api/buses')
        assert r.status_code == 403

    def test_crear_bus_sin_sesion_retorna_403(self, client):
        """POST /api/buses sin sesión retorna 403."""
        r = client.post('/api/buses', json={'patente': 'XX-1234', 'capacidad': 40})
        assert r.status_code == 403

    def test_crear_bus_como_pasajero_retorna_403(self, client):
        """Un pasajero no puede crear buses."""
        registrar_usuario(client)
        login_usuario(client)
        r = client.post('/api/buses', json={'patente': 'XX-1234', 'capacidad': 40})
        assert r.status_code == 403

    def test_editar_bus_sin_sesion_retorna_403(self, client):
        """PUT /api/buses/<patente> sin sesión retorna 403."""
        r = client.put('/api/buses/XX-1234', json={'chofer': 'Nuevo'})
        assert r.status_code == 403

    def test_eliminar_bus_sin_sesion_retorna_403(self, client):
        """DELETE /api/buses/<patente> sin sesión retorna 403."""
        r = client.delete('/api/buses/XX-1234')
        assert r.status_code == 403


# ═══════════════════════════════════════════════════════════════════
#  LISTAR BUSES
# ═══════════════════════════════════════════════════════════════════

class TestListarBuses:
    """GET /api/buses — admin."""

    def test_listar_buses_vacio(self, client):
        """Con BD vacía retorna lista vacía y total 0."""
        registrar_y_login_admin(client)
        r = client.get('/api/buses')
        assert r.status_code == 200
        data = r.get_json()
        assert data['total'] == 0
        assert data['buses'] == []

    def test_listar_buses_con_datos(self, client):
        """Después de crear un bus, aparece en la lista."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='AB-1234')
        r = client.get('/api/buses')
        assert r.status_code == 200
        data = r.get_json()
        assert data['total'] == 1
        assert data['buses'][0]['patente'] == 'AB-1234'


# ═══════════════════════════════════════════════════════════════════
#  CREAR BUS
# ═══════════════════════════════════════════════════════════════════

class TestCrearBus:
    """POST /api/buses — admin."""

    def test_crear_bus_exitoso(self, client):
        """Crear un bus con datos válidos retorna 201."""
        registrar_y_login_admin(client)
        r = crear_bus_test(client, patente='CD-5678', capacidad=40)
        assert r.status_code == 201
        data = r.get_json()
        assert data['patente'] == 'CD-5678'

    def test_crear_bus_genera_asientos(self, client):
        """Al crear un bus se generan los asientos físicos."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='EF-9012', capacidad=5)
        # Verificar vía listado que el bus tiene capacidad 5
        r = client.get('/api/buses')
        bus = r.get_json()['buses'][0]
        assert bus['capacidad'] == 5

    def test_crear_bus_patente_duplicada(self, client):
        """Crear un bus con patente ya existente retorna 409."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='GH-3456')
        r = crear_bus_test(client, patente='GH-3456')
        assert r.status_code == 409

    def test_crear_bus_patente_vacia(self, client):
        """Patente vacía retorna 400."""
        registrar_y_login_admin(client)
        r = client.post('/api/buses', json={'patente': '', 'capacidad': 40})
        assert r.status_code == 400

    def test_crear_bus_patente_normalizada_mayusculas(self, client):
        """La patente se normaliza a mayúsculas."""
        registrar_y_login_admin(client)
        r = crear_bus_test(client, patente='ab-1234')
        assert r.status_code == 201
        assert r.get_json()['patente'] == 'AB-1234'

    def test_crear_bus_capacidad_cero(self, client):
        """Capacidad 0 retorna 400."""
        registrar_y_login_admin(client)
        r = client.post('/api/buses', json={'patente': 'IJ-7890', 'capacidad': 0})
        assert r.status_code == 400

    def test_crear_bus_capacidad_excesiva(self, client):
        """Capacidad > 200 retorna 400."""
        registrar_y_login_admin(client)
        r = client.post('/api/buses', json={'patente': 'KL-1111', 'capacidad': 201})
        assert r.status_code == 400


# ═══════════════════════════════════════════════════════════════════
#  EDITAR BUS
# ═══════════════════════════════════════════════════════════════════

class TestEditarBus:
    """PUT /api/buses/<patente> — admin."""

    def test_editar_chofer(self, client):
        """Cambiar el chofer retorna 200."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='MN-2222')
        r = client.put('/api/buses/MN-2222', json={'chofer': 'Pedro López'})
        assert r.status_code == 200

    def test_editar_modelo(self, client):
        """Cambiar el modelo retorna 200."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='OP-3333')
        r = client.put('/api/buses/OP-3333', json={'modelo': 'Mercedes-Benz O500'})
        assert r.status_code == 200

    def test_editar_estado(self, client):
        """Cambiar el estado a 'En mantención' retorna 200."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='QR-4444')
        r = client.put('/api/buses/QR-4444', json={'estado': 'En mantención'})
        assert r.status_code == 200

    def test_editar_bus_inexistente(self, client):
        """Editar un bus que no existe retorna 404."""
        registrar_y_login_admin(client)
        r = client.put('/api/buses/NOEXISTE', json={'chofer': 'Nadie'})
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════
#  ELIMINAR BUS
# ═══════════════════════════════════════════════════════════════════

class TestEliminarBus:
    """DELETE /api/buses/<patente> — admin."""

    def test_eliminar_bus_exitoso(self, client):
        """Eliminar un bus existente retorna 200 y lo saca de la lista."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='ST-5555')
        r = client.delete('/api/buses/ST-5555')
        assert r.status_code == 200
        # Verificar que ya no aparece
        r_lista = client.get('/api/buses')
        assert r_lista.get_json()['total'] == 0

    def test_eliminar_bus_inexistente(self, client):
        """Eliminar un bus que no existe retorna 404."""
        registrar_y_login_admin(client)
        r = client.delete('/api/buses/NOEXISTE')
        assert r.status_code == 404

    def test_eliminar_bus_como_pasajero(self, client):
        """Un pasajero no puede eliminar buses (403)."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='UV-6666')
        client.post('/api/logout')
        registrar_usuario(client)
        login_usuario(client)
        r = client.delete('/api/buses/UV-6666')
        assert r.status_code == 403
