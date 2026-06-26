from datetime import date, time

import database
from models import Asiento, Bus, HorarioViaje, Recorrido


def test_asientos_reales_y_compra_cambia_estado(client):
    db = database.obtener_sesion()
    try:
        bus = Bus(patente="TESTBUS", capacidad=40, estado="Activo")
        recorrido = Recorrido(origen="Curicó", destino="Talca", tipo="ida", precio_base=3500.0)
        db.add_all([bus, recorrido])
        db.commit()
        db.refresh(bus)
        db.refresh(recorrido)

        asiento = Asiento(numero=1, patente=bus.patente)
        horario = HorarioViaje(
            id_recorrido=recorrido.id_recorrido,
            patente=bus.patente,
            hora_salida=time(7, 0),
            hora_llegada=time(8, 0),
            precio_base=2800.0,
            activo=True,
        )
        db.add_all([asiento, horario])
        db.commit()
    finally:
        db.close()

    response = client.get('/api/asientos?bus=TESTBUS&hora=07:00')
    assert response.status_code == 200
    data = response.get_json()
    assert data['bus']['patente'] == 'TESTBUS'
    assert data['asientos'][0]['estado'] == 'libre'

    compra_response = client.post('/api/confirmar-compra', json={
        'patente': 'TESTBUS',
        'horaSalida': '07:00',
        'asiento': 1,
        'nombre': 'Juan Pérez',
        'rut': '12.345.678-9',
        'email': 'juan@example.cl',
        'telefono': '+56 9 1111 2222',
        'tipoPasaje': 'adulto',
        'observaciones': 'Sin observaciones',
        'precio': '2800',
        'fechaViaje': date.today().isoformat(),
    })
    assert compra_response.status_code == 200

    response = client.get('/api/asientos?bus=TESTBUS&hora=07:00')
    assert response.status_code == 200
    data = response.get_json()
    asiento_actualizado = next(item for item in data['asientos'] if item['numero'] == 1)
    assert asiento_actualizado['estado'] == 'ocupado'
