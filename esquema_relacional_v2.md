**Esquema relacional preliminar, basado en el diagrama E-R V2.**

***Conceptos:***
- PK se refiere a la llave primaria (primary key), que es un identificador único y no nulo de una tabla
- FK se refiere a la llave foránea (foreign key), que es un atributo que hace referencia a la PK de otra, tabla, permitiendo relacionarlas.

**Esquema relacional:**

Administrador(**Rut[PK]**, Correo, Nombre, Teléfono)

Pasajero (**Rut[PK]**, Correo, Nombre, Teléfono)

Ruta(**IDRuta[PK]**, Origen, Destino, RefAdmin)
*FK(Ruta, Administrador) = {RefAdmin}*

Parada(**IDParada[PK]**, Nombre, Dirección)

RutaParada(RefRuta, RefParada)
**PK(RutaParada) = {RefRuta, RefParada}**
*FK(RutaParada, Ruta) = {RefRuta}*
*FK(RutaParada, Parada) = {RefParada}*

Bus(**Patente[PK]**, Capacidad, Estado, Asientos)

Viaje(**IDViaje[PK]**, Fecha, Salida, Llegada, Cupos, Estado, RefBus)
*FK(Viaje, Bus) = {RefBus}*

Reserva(**IDReserva[PK]**, Fecha, Estado, Precio, RefPago)
*FK(Reserva, Pago) = {RefPago}*

Pago(**IDPago[PK]**, Monto, Fecha, MétodoPago, RefReserva, RefPasajero)
*FK(Pago, Reserva) = {RefReserva}*
*FK(Pago, Pasajero) = {RefPasajero}*