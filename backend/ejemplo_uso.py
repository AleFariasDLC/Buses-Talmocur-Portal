# ejemplo_uso.py
# Muestra cómo insertar datos y hacer consultas básicas.
# Ejecuta este archivo DESPUÉS de haber corrido database.py

from datetime import date, time
from database import crear_tablas, obtener_sesion
from models import Administrador, Pasajero, Ruta, Parada, Bus, Viaje, Reserva, Pago


def poblar_datos_ejemplo():
    """Inserta datos de prueba en todas las tablas."""
    db = obtener_sesion()

    try:
        # ── 1. Crear Administrador ──────────────────────
        admin = Administrador(
            rut="12345678-9",
            nombre="Carlos Pérez",
            correo="carlos@talmocur.cl",
            telefono="+56912345678"
        )
        db.add(admin)

        # ── 2. Crear Pasajero ───────────────────────────
        pasajero = Pasajero(
            rut="98765432-1",
            nombre="Ana García",
            correo="ana@gmail.com",
            telefono="+56987654321"
        )
        db.add(pasajero)

        # ── 3. Crear Bus ────────────────────────────────
        bus = Bus(
            patente="ABCD12",
            capacidad=30,
            estado="Activo",
            asientos=30
        )
        db.add(bus)

        # ── 4. Crear Paradas ────────────────────────────
        parada1 = Parada(nombre="Terminal Santiago", direccion="Av. Alameda 3750, Santiago")
        parada2 = Parada(nombre="Parada Rancagua",   direccion="O'Higgins 123, Rancagua")
        parada3 = Parada(nombre="Terminal Talca",    direccion="2 Sur 1960, Talca")
        db.add_all([parada1, parada2, parada3])

        # Guardar todo lo anterior antes de crear relaciones
        db.commit()

        # ── 5. Crear Ruta (con paradas) ─────────────────
        ruta = Ruta(
            origen="Santiago",
            destino="Talca",
            rut_admin=admin.rut,
            paradas=[parada1, parada2, parada3]  # asigna paradas directamente
        )
        db.add(ruta)
        db.commit()

        # ── 6. Crear Viaje ──────────────────────────────
        viaje = Viaje(
            fecha=date(2026, 6, 15),
            hora_salida=time(8, 0),
            hora_llegada=time(11, 30),
            cupos=30,
            estado="Programado",
            id_ruta=ruta.id_ruta,
            patente=bus.patente
        )
        db.add(viaje)
        db.commit()

        # ── 7. Crear Reserva ────────────────────────────
        reserva = Reserva(
            fecha=date(2026, 6, 10),
            estado="Confirmada",
            precio=8500.0,
            id_viaje=viaje.id_viaje,
            rut_pasajero=pasajero.rut
        )
        db.add(reserva)
        db.commit()

        # ── 8. Crear Pago ───────────────────────────────
        pago = Pago(
            monto=8500.0,
            fecha=date(2026, 6, 10),
            metodo_pago="Tarjeta",
            id_reserva=reserva.id_reserva
        )
        db.add(pago)
        db.commit()

        print("✅ Datos de ejemplo insertados correctamente.\n")

    except Exception as e:
        db.rollback()  # Si algo falla, deshace todo
        print(f"❌ Error: {e}")
    finally:
        db.close()


def consultas_ejemplo():
    """Muestra cómo hacer consultas básicas."""
    db = obtener_sesion()

    print("=" * 50)
    print("📋 CONSULTAS DE EJEMPLO")
    print("=" * 50)

    # Listar todos los viajes
    viajes = db.query(Viaje).all()
    print(f"\n🚌 Viajes registrados: {len(viajes)}")
    for v in viajes:
        print(f"   - Viaje #{v.id_viaje} | {v.fecha} | {v.hora_salida} → {v.hora_llegada} | Estado: {v.estado}")

    # Listar reservas de un pasajero
    pasajero = db.query(Pasajero).filter(Pasajero.rut == "98765432-1").first()
    if pasajero:
        print(f"\n👤 Reservas de {pasajero.nombre}:")
        for r in pasajero.reservas:
            print(f"   - Reserva #{r.id_reserva} | Estado: {r.estado} | Precio: ${r.precio:,.0f}")

    # Ver ruta con sus paradas
    ruta = db.query(Ruta).first()
    if ruta:
        print(f"\n🗺️  Ruta #{ruta.id_ruta}: {ruta.origen} → {ruta.destino}")
        print(f"   Paradas:")
        for p in ruta.paradas:
            print(f"   - {p.nombre}: {p.direccion}")

    db.close()


if __name__ == "__main__":
    crear_tablas()
    poblar_datos_ejemplo()
    consultas_ejemplo()
