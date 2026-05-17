![](/base_datos_talmocur.png)

*Diagrama ER inspirado en el diagrama de clases sugerido por el profesor. Versión 1, sujeto a cambios.*

### Conceptos de diseño de bases de datos:

-	El uso de la palabra puede implica que una entidad podría o no relacionarse con otra, por ejemplo, una persona podría o no comprar productos en un sitio de supermercados, y aun así se considera un usuario. Se representa con una línea simple como las de Ruta y Parada.
-	El uso de la palabra debe implica que una entidad tiene que relacionarse con otra. Por ejemplo, una boleta debe estar asociada a un solo comprador. Se representa como una línea doble, como la de Viaje hacia Bus.

**Explicación de las relaciones:**
<p>Administrador y Ruta: Un administrador puede gestionar varias rutas, una ruta debe ser gestionada por un administrador.</p>
<p>Ruta y Parada: Una ruta tiene varias paradas, y una parada puede estar en varias rutas.</p>
<p>Ruta y Viaje: Una ruta puede estar asociada a varios viajes, un viaje debe tener asociada una sola ruta.</p>
<p>Viaje y Bus: Un viaje debe ser realizado por un solo bus, un bus puede realizar varios viajes.</p>
<p>Viaje y Reserva: Un viaje puede estar asociado a (existir en) varias reservas, una reserva debe tener asociada un solo viaje.</p>
<p>Pasajero y Reserva: Un pasajero puede hacer varias reservas, una reserva debe ser hecha por solo un pasajero.</p>
<p>Reserva y Pago: Una reserva debe estar asociada a un solo pago, un pago debe estar asociado a una reserva. (Esto puede cambiar si se piensa en tarjetas de crédito).</p>
