"""
test_asientos_compra.py — Tests de integración para asientos y compra de pasajes.

Endpoints:
    GET  /api/asientos          — Consultar estado de asientos de un bus
    POST /api/confirmar-compra  — Comprar un asiento
"""

from tests.helpers import (
    registrar_usuario, login_usuario, registrar_y_login_admin,
    crear_bus_test, crear_recorrido_test, crear_horario_test,
)


# ═══════════════════════════════════════════════════════════════════
#  CONSULTAR ASIENTOS
# ═══════════════════════════════════════════════════════════════════

class TestObtenerAsientos:
    """GET /api/asientos."""

    def test_sin_parametro_bus_retorna_400(self, client):
        """Falta el parámetro 'bus' → 400."""
        r = client.get('/api/asientos')
        assert r.status_code == 400
        assert 'bus' in r.get_json()['error'].lower()

    def test_bus_existente_retorna_asientos(self, client, db_session):
        """Un bus existente retorna sus asientos con estado 'libre'."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-A1', capacidad=5)
        client.post('/api/logout')  # endpoint público
        r = client.get('/api/asientos?bus=BUS-A1')
        assert r.status_code == 200
        data = r.get_json()
        assert data['bus']['patente'] == 'BUS-A1'
        assert len(data['asientos']) == 5
        # Todos deben estar libres
        assert all(a['estado'] == 'libre' for a in data['asientos'])

    def test_bus_auto_creado_si_no_existe(self, client):
        """Si el bus no existe, se crea automáticamente con 40 asientos."""
        r = client.get('/api/asientos?bus=NUEVO-01')
        assert r.status_code == 200
        data = r.get_json()
        assert data['bus']['patente'] == 'NUEVO-01'
        assert data['bus']['capacidad'] == 40
        assert len(data['asientos']) == 40

    def test_asientos_con_hora(self, client, db_session):
        """Pasar el parámetro 'hora' filtra por horario."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-A2', capacidad=5)
        rec = crear_recorrido_test(db_session)
        crear_horario_test(client, 'BUS-A2', rec.id_recorrido, '10:00')
        client.post('/api/logout')
        r = client.get('/api/asientos?bus=BUS-A2&hora=10:00')
        assert r.status_code == 200
        assert r.get_json()['hora'] == '10:00'

    def test_asiento_ocupado_despues_de_compra(self, client, db_session):
        """Después de una compra, el asiento aparece como 'ocupado'."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-A3', capacidad=5)
        rec = crear_recorrido_test(db_session)
        crear_horario_test(client, 'BUS-A3', rec.id_recorrido, '09:00')
        client.post('/api/logout')

        # Comprar asiento 1
        client.post('/api/confirmar-compra', json={
            'patente': 'BUS-A3', 'asiento': 1,
            'horaSalida': '09:00', 'precio': 3500,
        })
        # Verificar que asiento 1 está ocupado
        r = client.get('/api/asientos?bus=BUS-A3&hora=09:00')
        asientos = r.get_json()['asientos']
        asiento_1 = next(a for a in asientos if a['numero'] == 1)
        assert asiento_1['estado'] == 'ocupado'
        # Los demás siguen libres
        otros = [a for a in asientos if a['numero'] != 1]
        assert all(a['estado'] == 'libre' for a in otros)


# ═══════════════════════════════════════════════════════════════════
#  CONFIRMAR COMPRA
# ═══════════════════════════════════════════════════════════════════

class TestConfirmarCompra:
    """POST /api/confirmar-compra."""

    def test_compra_exitosa(self, client, db_session):
        """Compra con datos válidos retorna success: true."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-V1', capacidad=10)
        rec = crear_recorrido_test(db_session)
        crear_horario_test(client, 'BUS-V1', rec.id_recorrido, '08:00')
        client.post('/api/logout')

        registrar_usuario(client)
        login_usuario(client)
        r = client.post('/api/confirmar-compra', json={
            'patente': 'BUS-V1', 'asiento': 1,
            'horaSalida': '08:00', 'precio': 3500,
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        assert data['compra']['estado'] == 'confirmada'
        assert data['asiento']['numero'] == 1
        assert data['asiento']['estado'] == 'ocupado'

    def test_compra_sin_datos_retorna_400(self, client):
        """Sin body retorna 400."""
        r = client.post('/api/confirmar-compra', json={})
        assert r.status_code == 400

    def test_compra_sin_patente_retorna_400(self, client):
        """Sin patente retorna 400."""
        r = client.post('/api/confirmar-compra', json={'asiento': 1})
        assert r.status_code == 400

    def test_compra_asiento_invalido_retorna_400(self, client):
        """Asiento no numérico retorna 400."""
        r = client.post('/api/confirmar-compra', json={
            'patente': 'BUS-01', 'asiento': 'abc',
        })
        assert r.status_code == 400

    def test_compra_asiento_ya_vendido_retorna_409(self, client, db_session):
        """Comprar un asiento ya vendido retorna 409."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-V2', capacidad=10)
        rec = crear_recorrido_test(db_session)
        crear_horario_test(client, 'BUS-V2', rec.id_recorrido, '10:00')
        client.post('/api/logout')

        # Primera compra: OK
        r1 = client.post('/api/confirmar-compra', json={
            'patente': 'BUS-V2', 'asiento': 3,
            'horaSalida': '10:00', 'precio': 3500,
        })
        assert r1.status_code == 200
        # Segunda compra del mismo asiento: conflicto
        r2 = client.post('/api/confirmar-compra', json={
            'patente': 'BUS-V2', 'asiento': 3,
            'horaSalida': '10:00', 'precio': 3500,
        })
        assert r2.status_code == 409

    def test_compra_como_invitado(self, client, db_session):
        """Sin sesión, se asigna un usuario invitado automáticamente."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-V3', capacidad=10)
        rec = crear_recorrido_test(db_session)
        crear_horario_test(client, 'BUS-V3', rec.id_recorrido, '07:00')
        client.post('/api/logout')

        r = client.post('/api/confirmar-compra', json={
            'patente': 'BUS-V3', 'asiento': 1,
            'horaSalida': '07:00', 'precio': 2800,
        })
        assert r.status_code == 200
        assert r.get_json()['success'] is True

    def test_compra_con_fecha_viaje(self, client, db_session):
        """Se puede especificar una fecha de viaje."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-V4', capacidad=10)
        rec = crear_recorrido_test(db_session)
        crear_horario_test(client, 'BUS-V4', rec.id_recorrido, '06:00')
        client.post('/api/logout')

        r = client.post('/api/confirmar-compra', json={
            'patente': 'BUS-V4', 'asiento': 2,
            'horaSalida': '06:00', 'precio': 3500,
            'fechaViaje': '2026-07-15',
        })
        assert r.status_code == 200

    def test_compra_monto_correcto(self, client, db_session):
        """El monto total refleja el precio enviado."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-V5', capacidad=10)
        rec = crear_recorrido_test(db_session)
        crear_horario_test(client, 'BUS-V5', rec.id_recorrido, '11:00')
        client.post('/api/logout')

        r = client.post('/api/confirmar-compra', json={
            'patente': 'BUS-V5', 'asiento': 5,
            'horaSalida': '11:00', 'precio': 4200,
        })
        assert r.status_code == 200
        assert r.get_json()['compra']['monto_total'] == 4200

    def test_compra_multiple_de_asientos_con_pasajeros(self, client, db_session):
        """Una compra puede reservar varios asientos y guardar datos del pasajero por asiento."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-M1', capacidad=10)
        rec = crear_recorrido_test(db_session)
        crear_horario_test(client, 'BUS-M1', rec.id_recorrido, '12:00')
        client.post('/api/logout')

        registrar_usuario(client)
        login_usuario(client)
        r = client.post('/api/confirmar-compra', json={
            'patente': 'BUS-M1',
            'horaSalida': '12:00',
            'precio': 3500,
            'pasajeros': [
                {
                    'asiento': 1,
                    'nombre': 'Ana Pérez',
                    'rut': '11111111-1',
                    'email': 'ana@example.com',
                    'telefono': '+56 9 1111 1111',
                    'tipoPasaje': 'adulto',
                    'observaciones': 'Asiento ventana',
                },
                {
                    'asiento': 2,
                    'nombre': 'Luis Gómez',
                    'rut': '22222222-2',
                    'email': 'luis@example.com',
                    'telefono': '+56 9 2222 2222',
                    'tipoPasaje': 'estudiante',
                    'observaciones': 'Asiento pasillo',
                },
            ],
        })

        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        assert len(data['compras']) == 2
        assert [item['asiento']['numero'] for item in data['compras']] == [1, 2]
        assert data['compras'][0]['pasajero']['nombre'] == 'Ana Pérez'
        assert data['compras'][1]['pasajero']['rut'] == '22222222-2'
