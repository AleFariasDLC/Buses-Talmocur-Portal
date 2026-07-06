"""
test_rutas_paginas.py — Tests de integración para las rutas de páginas
y control de acceso del panel de administración.

Rutas testeadas:
    /admin           — Solo accesible por admin
    /recuperar       — Página de recuperación
    /restablecer     — Página de restablecimiento
    /tarifas         — Página de tarifas
    /quienes-somos   — Página informativa
    /compra-pasajes  — Página de compra
    /boleta          — Página de boleta
    /api/origenes    — Orígenes y destinos
    /api/recorridos  — Lista de recorridos
"""

from tests.helpers import (
    registrar_usuario, login_usuario, registrar_y_login_admin,
    crear_recorrido_test,
)


# ═══════════════════════════════════════════════════════════════════
#  PANEL DE ADMINISTRACIÓN
# ═══════════════════════════════════════════════════════════════════

class TestAdminDashboard:
    """/admin — solo accesible con rol 'admin'."""

    def test_admin_sin_sesion_redirige_a_login(self, client):
        """/admin sin sesión redirige a /login."""
        r = client.get('/admin')
        assert r.status_code == 302
        assert '/login' in r.headers['Location']

    def test_admin_como_pasajero_redirige_a_login(self, client):
        """Un pasajero no puede acceder a /admin."""
        registrar_usuario(client)
        login_usuario(client)
        r = client.get('/admin')
        assert r.status_code == 302
        assert '/login' in r.headers['Location']

    def test_admin_como_admin_retorna_html(self, client):
        """Un admin puede acceder a /admin y recibe HTML."""
        registrar_y_login_admin(client)
        r = client.get('/admin')
        assert r.status_code == 200
        assert b'text/html' in r.content_type.encode() or 'html' in r.content_type


# ═══════════════════════════════════════════════════════════════════
#  PÁGINAS DE RECUPERACIÓN
# ═══════════════════════════════════════════════════════════════════

class TestPaginasRecuperacion:
    """Páginas de recuperación y restablecimiento de contraseña."""

    def test_recuperar_retorna_html(self, client):
        """/recuperar retorna 200 con HTML."""
        r = client.get('/recuperar')
        assert r.status_code == 200

    def test_recuperar_tiene_no_store(self, client):
        """/recuperar tiene Cache-Control: no-store."""
        r = client.get('/recuperar')
        assert 'no-store' in r.headers.get('Cache-Control', '')

    def test_restablecer_retorna_html(self, client):
        """/restablecer retorna 200 con HTML."""
        r = client.get('/restablecer')
        assert r.status_code == 200

    def test_restablecer_tiene_no_store(self, client):
        """/restablecer tiene Cache-Control: no-store."""
        r = client.get('/restablecer')
        assert 'no-store' in r.headers.get('Cache-Control', '')


# ═══════════════════════════════════════════════════════════════════
#  PÁGINAS PÚBLICAS
# ═══════════════════════════════════════════════════════════════════

class TestPaginasPublicas:
    """Páginas accesibles sin autenticación."""

    def test_tarifas_retorna_html(self, client):
        """/tarifas retorna 200."""
        r = client.get('/tarifas')
        assert r.status_code == 200

    def test_quienes_somos_retorna_html(self, client):
        """/quienes-somos retorna 200."""
        r = client.get('/quienes-somos')
        assert r.status_code == 200

    def test_compra_pasajes_retorna_html(self, client):
        """/compra-pasajes retorna 200."""
        r = client.get('/compra-pasajes')
        assert r.status_code == 200

    def test_boleta_retorna_html(self, client):
        """/boleta retorna 200."""
        r = client.get('/boleta')
        assert r.status_code == 200

    def test_perfil_retorna_html(self, client):
        """/perfil retorna 200 (accesible con y sin sesión)."""
        r = client.get('/perfil')
        assert r.status_code == 200

    def test_compra_pasajes_asientos_retorna_html(self, client, db_session):
        """/compra-pasajes-asientos retorna 200."""
        from models import Recorrido, Bus, HorarioViaje
        from datetime import time

        rec = Recorrido(origen="Curicó", destino="Talca", tipo="ida", precio_base=3500, duracion_estimada=60)
        bus = Bus(patente="CGKR-15", capacidad=40, estado="Activo")
        db_session.add_all([rec, bus])
        db_session.commit()

        horario = HorarioViaje(
            id_recorrido=rec.id_recorrido,
            patente=bus.patente,
            hora_salida=time(8, 0),
            hora_llegada=time(9, 0),
            precio_base=3500,
            activo=True
        )
        db_session.add(horario)
        db_session.commit()

        r = client.get(f'/compra-pasajes-asientos?horario={horario.id_horario}')
        assert r.status_code == 200

    def test_compra_pasajes_asientos_bus_mantenimiento_redirige(self, client, db_session):
        """/compra-pasajes-asientos redirige a / si el bus está en mantención."""
        from models import Recorrido, Bus, HorarioViaje
        from datetime import time

        rec = Recorrido(origen="Curicó", destino="Talca", tipo="ida", precio_base=3500, duracion_estimada=60)
        bus = Bus(patente="CGKR-15", capacidad=40, estado="En mantención")
        db_session.add_all([rec, bus])
        db_session.commit()

        horario = HorarioViaje(
            id_recorrido=rec.id_recorrido,
            patente=bus.patente,
            hora_salida=time(8, 0),
            hora_llegada=time(9, 0),
            precio_base=3500,
            activo=True
        )
        db_session.add(horario)
        db_session.commit()

        r = client.get(f'/compra-pasajes-asientos?horario={horario.id_horario}')
        assert r.status_code == 302
        assert '/' in r.headers['Location']

    def test_bus_mantenimiento_excluido_de_home(self, client, db_session):
        """Los horarios de buses en mantención no se muestran en el listado del home."""
        from models import Recorrido, Bus, HorarioViaje
        from datetime import time

        rec = Recorrido(origen="Curicó", destino="Talca", tipo="ida", precio_base=3500, duracion_estimada=60)
        bus_mantenimiento = Bus(patente="CGKR-99", capacidad=40, estado="En mantención")
        bus_activo = Bus(patente="CGKR-15", capacidad=40, estado="Activo")
        db_session.add_all([rec, bus_mantenimiento, bus_activo])
        db_session.commit()

        h_mantenimiento = HorarioViaje(
            id_recorrido=rec.id_recorrido,
            patente=bus_mantenimiento.patente,
            hora_salida=time(8, 0),
            hora_llegada=time(9, 0),
            precio_base=3500,
            activo=True
        )
        h_activo = HorarioViaje(
            id_recorrido=rec.id_recorrido,
            patente=bus_activo.patente,
            hora_salida=time(10, 0),
            hora_llegada=time(11, 0),
            precio_base=3500,
            activo=True
        )
        db_session.add_all([h_mantenimiento, h_activo])
        db_session.commit()

        r = client.get('/?origen=Curicó&destino=Talca&fecha=2026-07-10')
        assert r.status_code == 200
        html = r.get_data(as_text=True)
        assert "CGKR-15" in html  # el bus activo debe aparecer
        assert "CGKR-99" not in html  # el bus en mantención no debe aparecer


# ═══════════════════════════════════════════════════════════════════
#  API DE ORÍGENES Y RECORRIDOS
# ═══════════════════════════════════════════════════════════════════

class TestHomeBusqueda:
    """GET / con parámetros de búsqueda desde la portada."""

    def test_home_con_fecha_seleccionada_muestra_la_fecha_en_la_respuesta(self, client):
        """La portada debe responder al parámetro fecha del buscador."""
        r = client.get('/?fecha=2026-07-10')
        assert r.status_code == 200
        html = r.get_data(as_text=True)
        assert 'name="fecha"' in html
        assert 'value="2026-07-10"' in html


class TestApiOrigenes:
    """GET /api/origenes — público."""

    def test_origenes_sin_datos(self, client):
        """Sin recorridos retorna listas vacías."""
        r = client.get('/api/origenes')
        assert r.status_code == 200
        data = r.get_json()
        assert data['origenes'] == []
        assert data['destinos'] == []

    def test_origenes_con_datos(self, client, db_session):
        """Con recorridos retorna orígenes y destinos."""
        crear_recorrido_test(db_session)
        r = client.get('/api/origenes')
        assert r.status_code == 200
        data = r.get_json()
        assert 'Curicó' in data['origenes']
        assert 'Talca' in data['destinos']


class TestApiRecorridos:
    """GET /api/recorridos — público."""

    def test_recorridos_sin_datos(self, client):
        """Sin recorridos retorna lista vacía."""
        r = client.get('/api/recorridos')
        assert r.status_code == 200
        assert r.get_json()['recorridos'] == []

    def test_recorridos_con_datos(self, client, db_session):
        """Con recorridos retorna nombre y precio."""
        crear_recorrido_test(db_session)
        r = client.get('/api/recorridos')
        assert r.status_code == 200
        recorridos = r.get_json()['recorridos']
        assert len(recorridos) == 1
        assert 'Curicó' in recorridos[0]['nombre']
        assert recorridos[0]['precio_base'] == 3500.0
