"""
test_admin_horarios.py — Tests de integración para el CRUD de horarios (admin).

Endpoints:
    POST   /api/horarios             — Crear horario
    PUT    /api/horarios/<id>         — Editar horario
    DELETE /api/horarios/<id>         — Eliminar horario

También testea la función check_horario_conflict() de app.py.
"""

from tests.helpers import (
    registrar_usuario, login_usuario, registrar_y_login_admin,
    crear_bus_test, crear_recorrido_test, crear_horario_test,
)


# ═══════════════════════════════════════════════════════════════════
#  CONTROL DE ACCESO
# ═══════════════════════════════════════════════════════════════════

class TestHorariosAcceso:
    """Solo admin puede gestionar horarios."""

    def test_crear_horario_sin_sesion_retorna_403(self, client):
        r = client.post('/api/horarios', json={
            'patente': 'XX-0000', 'id_recorrido': 1, 'hora_salida': '08:00',
        })
        assert r.status_code == 403

    def test_crear_horario_como_pasajero_retorna_403(self, client):
        registrar_usuario(client)
        login_usuario(client)
        r = client.post('/api/horarios', json={
            'patente': 'XX-0000', 'id_recorrido': 1, 'hora_salida': '08:00',
        })
        assert r.status_code == 403

    def test_editar_horario_sin_sesion_retorna_403(self, client):
        r = client.put('/api/horarios/1', json={'precio_base': 5000})
        assert r.status_code == 403

    def test_eliminar_horario_sin_sesion_retorna_403(self, client):
        r = client.delete('/api/horarios/1')
        assert r.status_code == 403


# ═══════════════════════════════════════════════════════════════════
#  CREAR HORARIO
# ═══════════════════════════════════════════════════════════════════

class TestCrearHorario:
    """POST /api/horarios — admin."""

    def test_crear_horario_exitoso(self, client, db_session):
        """Crear un horario con datos válidos retorna 201."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-01')
        recorrido = crear_recorrido_test(db_session)
        r = crear_horario_test(client, 'BUS-01', recorrido.id_recorrido, '10:00')
        assert r.status_code == 201
        assert 'id_horario' in r.get_json()

    def test_crear_horario_bus_inexistente(self, client, db_session):
        """Bus inexistente retorna 404."""
        registrar_y_login_admin(client)
        recorrido = crear_recorrido_test(db_session)
        r = crear_horario_test(client, 'NOEXISTE', recorrido.id_recorrido)
        assert r.status_code == 404

    def test_crear_horario_recorrido_inexistente(self, client):
        """Recorrido inexistente retorna 404."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-02')
        r = crear_horario_test(client, 'BUS-02', 9999)
        assert r.status_code == 404

    def test_crear_horario_campos_faltantes(self, client):
        """Campos obligatorios faltantes produce un error (bug: app.py no valida
        id_recorrido=None antes de hacer int(), lanza TypeError).
        Flask en modo TESTING propaga la excepción en vez de retornar 500."""
        import pytest
        registrar_y_login_admin(client)
        with pytest.raises(TypeError):
            client.post('/api/horarios', json={'patente': 'BUS-01'})


# ═══════════════════════════════════════════════════════════════════
#  VALIDACIÓN DE CONFLICTOS DE HORARIO
# ═══════════════════════════════════════════════════════════════════

class TestConflictoHorario:
    """check_horario_conflict: reglas de tiempo mínimo entre viajes."""

    def test_mismo_recorrido_menos_de_2h_rechazado(self, client, db_session):
        """Mismo recorrido con menos de 2 horas de diferencia: rechazado."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-C1')
        rec = crear_recorrido_test(db_session)
        crear_horario_test(client, 'BUS-C1', rec.id_recorrido, '10:00')
        # 11:00 → solo 1 hora de diferencia, mismo recorrido → rechazado
        r = crear_horario_test(client, 'BUS-C1', rec.id_recorrido, '11:00')
        assert r.status_code == 400
        assert 'diferencia' in r.get_json()['error'].lower() or '2 horas' in r.get_json()['error']

    def test_mismo_recorrido_2h_exactas_permitido(self, client, db_session):
        """Mismo recorrido con exactamente 2 horas de diferencia: permitido."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-C2')
        rec = crear_recorrido_test(db_session)
        crear_horario_test(client, 'BUS-C2', rec.id_recorrido, '08:00')
        r = crear_horario_test(client, 'BUS-C2', rec.id_recorrido, '10:00')
        assert r.status_code == 201

    def test_distinto_recorrido_menos_de_1h_rechazado(self, client, db_session):
        """Distinto recorrido con menos de 1 hora de diferencia: rechazado."""
        from models import Recorrido
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-C3')
        rec1 = crear_recorrido_test(db_session)
        # Crear segundo recorrido diferente
        rec2 = Recorrido(origen='Talca', destino='Santiago', tipo='ida', precio_base=5000)
        db_session.add(rec2)
        db_session.commit()
        db_session.refresh(rec2)

        crear_horario_test(client, 'BUS-C3', rec1.id_recorrido, '10:00')
        # 10:30 → solo 30 min de diferencia, distinto recorrido → rechazado
        r = crear_horario_test(client, 'BUS-C3', rec2.id_recorrido, '10:30')
        assert r.status_code == 400

    def test_distinto_recorrido_1h_exacta_permitido(self, client, db_session):
        """Distinto recorrido con exactamente 1 hora: permitido."""
        from models import Recorrido
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-C4')
        rec1 = crear_recorrido_test(db_session)
        rec2 = Recorrido(origen='Talca', destino='Santiago', tipo='ida', precio_base=5000)
        db_session.add(rec2)
        db_session.commit()
        db_session.refresh(rec2)

        crear_horario_test(client, 'BUS-C4', rec1.id_recorrido, '10:00')
        r = crear_horario_test(client, 'BUS-C4', rec2.id_recorrido, '11:00')
        assert r.status_code == 201

    def test_buses_diferentes_no_conflictan(self, client, db_session):
        """Buses diferentes pueden tener horarios a la misma hora."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-A')
        crear_bus_test(client, patente='BUS-B')
        rec = crear_recorrido_test(db_session)
        r1 = crear_horario_test(client, 'BUS-A', rec.id_recorrido, '10:00')
        r2 = crear_horario_test(client, 'BUS-B', rec.id_recorrido, '10:00')
        assert r1.status_code == 201
        assert r2.status_code == 201


# ═══════════════════════════════════════════════════════════════════
#  EDITAR HORARIO
# ═══════════════════════════════════════════════════════════════════

class TestEditarHorario:
    """PUT /api/horarios/<id> — admin."""

    def test_editar_precio(self, client, db_session):
        """Cambiar el precio retorna 200."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-E1')
        rec = crear_recorrido_test(db_session)
        r_crear = crear_horario_test(client, 'BUS-E1', rec.id_recorrido, '10:00', 3500)
        id_h = r_crear.get_json()['id_horario']
        r = client.put(f'/api/horarios/{id_h}', json={'precio_base': 5000})
        assert r.status_code == 200

    def test_editar_estado_activo(self, client, db_session):
        """Desactivar un horario retorna 200."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-E2')
        rec = crear_recorrido_test(db_session)
        r_crear = crear_horario_test(client, 'BUS-E2', rec.id_recorrido, '14:00')
        id_h = r_crear.get_json()['id_horario']
        r = client.put(f'/api/horarios/{id_h}', json={'activo': False})
        assert r.status_code == 200

    def test_editar_hora_salida(self, client, db_session):
        """Cambiar la hora de salida retorna 200."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-E3')
        rec = crear_recorrido_test(db_session)
        r_crear = crear_horario_test(client, 'BUS-E3', rec.id_recorrido, '10:00')
        id_h = r_crear.get_json()['id_horario']
        r = client.put(f'/api/horarios/{id_h}', json={'hora_salida': '15:00'})
        assert r.status_code == 200

    def test_editar_horario_inexistente(self, client):
        """Horario inexistente retorna 404."""
        registrar_y_login_admin(client)
        r = client.put('/api/horarios/99999', json={'precio_base': 5000})
        assert r.status_code == 404

    def test_editar_hora_con_conflicto(self, client, db_session):
        """Cambiar la hora generando un conflicto retorna 400."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-E4')
        rec = crear_recorrido_test(db_session)
        crear_horario_test(client, 'BUS-E4', rec.id_recorrido, '08:00')
        r_crear = crear_horario_test(client, 'BUS-E4', rec.id_recorrido, '12:00')
        id_h = r_crear.get_json()['id_horario']
        # Mover de 12:00 a 09:00 → conflicto con el de 08:00 (< 2h)
        r = client.put(f'/api/horarios/{id_h}', json={'hora_salida': '09:00'})
        assert r.status_code == 400


# ═══════════════════════════════════════════════════════════════════
#  ELIMINAR HORARIO
# ═══════════════════════════════════════════════════════════════════

class TestEliminarHorario:
    """DELETE /api/horarios/<id> — admin."""

    def test_eliminar_horario_exitoso(self, client, db_session):
        """Eliminar un horario existente retorna 200."""
        registrar_y_login_admin(client)
        crear_bus_test(client, patente='BUS-D1')
        rec = crear_recorrido_test(db_session)
        r_crear = crear_horario_test(client, 'BUS-D1', rec.id_recorrido, '10:00')
        id_h = r_crear.get_json()['id_horario']
        r = client.delete(f'/api/horarios/{id_h}')
        assert r.status_code == 200

    def test_eliminar_horario_inexistente(self, client):
        """Eliminar un horario que no existe retorna 404."""
        registrar_y_login_admin(client)
        r = client.delete('/api/horarios/99999')
        assert r.status_code == 404
