"""
test_admin_avisos.py — Tests de integración para el CRUD de avisos (admin).

Endpoints:
    POST   /api/avisos            — Crear aviso
    GET    /api/avisos            — Listar todos (admin)
    GET    /api/avisos/activos    — Avisos vigentes (público)
    PUT    /api/avisos/<id>       — Editar aviso
    DELETE /api/avisos/<id>       — Eliminar aviso
"""

from tests.helpers import (
    registrar_usuario, login_usuario, registrar_y_login_admin,
)


# ═══════════════════════════════════════════════════════════════════
#  CONTROL DE ACCESO
# ═══════════════════════════════════════════════════════════════════

class TestAvisosAcceso:
    """Solo admin puede crear, listar (todos), editar y eliminar avisos."""

    def test_crear_aviso_sin_sesion_retorna_403(self, client):
        r = client.post('/api/avisos', json={
            'titulo': 'Test', 'mensaje': 'Test', 'tipo': 'info',
        })
        assert r.status_code == 403

    def test_crear_aviso_como_pasajero_retorna_403(self, client):
        registrar_usuario(client)
        login_usuario(client)
        r = client.post('/api/avisos', json={
            'titulo': 'Test', 'mensaje': 'Test', 'tipo': 'info',
        })
        assert r.status_code == 403

    def test_listar_avisos_sin_sesion_retorna_403(self, client):
        r = client.get('/api/avisos')
        assert r.status_code == 403

    def test_editar_aviso_sin_sesion_retorna_403(self, client):
        r = client.put('/api/avisos/1', json={'titulo': 'Nuevo'})
        assert r.status_code == 403

    def test_eliminar_aviso_sin_sesion_retorna_403(self, client):
        r = client.delete('/api/avisos/1')
        assert r.status_code == 403


# ═══════════════════════════════════════════════════════════════════
#  CREAR AVISO
# ═══════════════════════════════════════════════════════════════════

class TestCrearAviso:
    """POST /api/avisos — admin."""

    def test_crear_aviso_exitoso(self, client):
        """Crear un aviso con datos válidos retorna 201."""
        registrar_y_login_admin(client)
        r = client.post('/api/avisos', json={
            'titulo': 'Mantención programada',
            'mensaje': 'El servicio estará suspendido el martes.',
            'tipo': 'alerta',
            'duracion_dias': 3,
        })
        assert r.status_code == 201
        data = r.get_json()
        assert data['aviso']['titulo'] == 'Mantención programada'
        assert data['aviso']['tipo'] == 'alerta'
        assert data['aviso']['activo'] is True

    def test_crear_aviso_titulo_vacio_retorna_400(self, client):
        """Título vacío retorna 400."""
        registrar_y_login_admin(client)
        r = client.post('/api/avisos', json={
            'titulo': '', 'mensaje': 'Contenido', 'tipo': 'info',
        })
        assert r.status_code == 400

    def test_crear_aviso_mensaje_vacio_retorna_400(self, client):
        """Mensaje vacío retorna 400."""
        registrar_y_login_admin(client)
        r = client.post('/api/avisos', json={
            'titulo': 'Título', 'mensaje': '', 'tipo': 'info',
        })
        assert r.status_code == 400

    def test_crear_aviso_tipo_invalido_retorna_400(self, client):
        """Tipo no reconocido retorna 400."""
        registrar_y_login_admin(client)
        r = client.post('/api/avisos', json={
            'titulo': 'Test', 'mensaje': 'Test', 'tipo': 'invalido',
        })
        assert r.status_code == 400

    def test_crear_aviso_tipos_validos(self, client):
        """Los 4 tipos válidos se aceptan."""
        registrar_y_login_admin(client)
        for tipo in ('alerta', 'info', 'precio', 'emergencia'):
            r = client.post('/api/avisos', json={
                'titulo': f'Aviso {tipo}', 'mensaje': 'Contenido', 'tipo': tipo,
            })
            assert r.status_code == 201, f"Tipo '{tipo}' fue rechazado"


# ═══════════════════════════════════════════════════════════════════
#  LISTAR AVISOS (admin)
# ═══════════════════════════════════════════════════════════════════

class TestListarAvisos:
    """GET /api/avisos — admin."""

    def test_listar_avisos_vacio(self, client):
        """BD vacía retorna lista vacía."""
        registrar_y_login_admin(client)
        r = client.get('/api/avisos')
        assert r.status_code == 200
        assert r.get_json()['avisos'] == []

    def test_listar_avisos_con_datos(self, client):
        """Después de crear avisos, aparecen en la lista."""
        registrar_y_login_admin(client)
        client.post('/api/avisos', json={
            'titulo': 'Aviso 1', 'mensaje': 'Msg 1', 'tipo': 'info',
        })
        client.post('/api/avisos', json={
            'titulo': 'Aviso 2', 'mensaje': 'Msg 2', 'tipo': 'alerta',
        })
        r = client.get('/api/avisos')
        assert r.status_code == 200
        assert len(r.get_json()['avisos']) == 2


# ═══════════════════════════════════════════════════════════════════
#  AVISOS ACTIVOS (público)
# ═══════════════════════════════════════════════════════════════════

class TestAvisosActivos:
    """GET /api/avisos/activos — público."""

    def test_avisos_activos_sin_datos(self, client):
        """Sin avisos retorna lista vacía."""
        r = client.get('/api/avisos/activos')
        assert r.status_code == 200
        assert r.get_json()['avisos'] == []

    def test_avisos_activos_muestra_vigentes(self, client):
        """Un aviso activo con duración futura aparece en la lista."""
        registrar_y_login_admin(client)
        client.post('/api/avisos', json={
            'titulo': 'Vigente', 'mensaje': 'Msg', 'tipo': 'info',
            'duracion_dias': 30,
        })
        # Ahora cualquier usuario puede ver los activos
        client.post('/api/logout')
        r = client.get('/api/avisos/activos')
        assert r.status_code == 200
        avisos = r.get_json()['avisos']
        assert len(avisos) == 1
        assert avisos[0]['titulo'] == 'Vigente'

    def test_aviso_inactivo_no_aparece(self, client):
        """Un aviso desactivado manualmente no aparece en activos."""
        registrar_y_login_admin(client)
        r_crear = client.post('/api/avisos', json={
            'titulo': 'Desactivado', 'mensaje': 'Msg', 'tipo': 'info',
            'duracion_dias': 30,
        })
        id_aviso = r_crear.get_json()['aviso']['id_aviso']
        # Desactivar el aviso
        client.put(f'/api/avisos/{id_aviso}', json={'activo': False})
        r = client.get('/api/avisos/activos')
        assert r.get_json()['avisos'] == []


# ═══════════════════════════════════════════════════════════════════
#  EDITAR AVISO
# ═══════════════════════════════════════════════════════════════════

class TestEditarAviso:
    """PUT /api/avisos/<id> — admin."""

    def test_editar_titulo(self, client):
        """Cambiar el título retorna 200."""
        registrar_y_login_admin(client)
        r_crear = client.post('/api/avisos', json={
            'titulo': 'Original', 'mensaje': 'Msg', 'tipo': 'info',
        })
        id_aviso = r_crear.get_json()['aviso']['id_aviso']
        r = client.put(f'/api/avisos/{id_aviso}', json={'titulo': 'Editado'})
        assert r.status_code == 200

    def test_editar_tipo_invalido_retorna_400(self, client):
        """Cambiar a un tipo inválido retorna 400."""
        registrar_y_login_admin(client)
        r_crear = client.post('/api/avisos', json={
            'titulo': 'Test', 'mensaje': 'Msg', 'tipo': 'info',
        })
        id_aviso = r_crear.get_json()['aviso']['id_aviso']
        r = client.put(f'/api/avisos/{id_aviso}', json={'tipo': 'falso'})
        assert r.status_code == 400

    def test_editar_aviso_inexistente(self, client):
        """Aviso inexistente retorna 404."""
        registrar_y_login_admin(client)
        r = client.put('/api/avisos/99999', json={'titulo': 'Nada'})
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════
#  ELIMINAR AVISO
# ═══════════════════════════════════════════════════════════════════

class TestEliminarAviso:
    """DELETE /api/avisos/<id> — admin."""

    def test_eliminar_aviso_exitoso(self, client):
        """Eliminar un aviso existente retorna 200."""
        registrar_y_login_admin(client)
        r_crear = client.post('/api/avisos', json={
            'titulo': 'Borrable', 'mensaje': 'Msg', 'tipo': 'info',
        })
        id_aviso = r_crear.get_json()['aviso']['id_aviso']
        r = client.delete(f'/api/avisos/{id_aviso}')
        assert r.status_code == 200
        # Verificar que desapareció
        r_lista = client.get('/api/avisos')
        assert len(r_lista.get_json()['avisos']) == 0

    def test_eliminar_aviso_inexistente(self, client):
        """Aviso inexistente retorna 404."""
        registrar_y_login_admin(client)
        r = client.delete('/api/avisos/99999')
        assert r.status_code == 404
