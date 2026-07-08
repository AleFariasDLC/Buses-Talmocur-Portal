# Funcionamiento del Flujo de Compras y Emisión de Boletas

Este documento detalla el funcionamiento del flujo de compra de pasajes en la aplicación web, desde la selección interactiva de asientos en el frontend hasta las validaciones de negocio en el backend y la posterior emisión de la boleta de compra.

---

## 1. El Flujo de Compra de Pasajes

El proceso de compra consta de cuatro fases consecutivas:

1. **Búsqueda e Inicio**: El usuario busca un viaje en la página de inicio, selecciona un horario disponible y pulsa "Comprar". Es redirigido a `/compra-pasajes/asientos` con el identificador del horario de viaje y la fecha deseada como parámetros de la URL.
2. **Selección de Asientos**: Se despliega una interfaz con la distribución de asientos de la cabina del bus asignado a ese horario.
3. **Formulario de Pasajeros**: Para cada asiento seleccionado, se despliega un formulario interactivo que solicita:
   - Nombre completo
   - RUT
   - Correo electrónico de contacto
   - Teléfono
   - Tipo de pasaje (ej: `"adulto"`, `"estudiante"`)
   - Observaciones (ej: requerimientos de movilidad reducida)
4. **Confirmación y Pago**: El usuario pulsa "Confirmar Compra", se efectúa una validación final y un proceso de pago simulado en el backend, y el sistema redirige al usuario a la vista de la boleta.

---

## 2. Mapa de Asientos Interactivo (Frontend)

La cabina de asientos del bus se genera de manera dinámica en la página web mediante JavaScript ([asientos.js](file:///c:/Users/dipez/OneDrive/Documentos/Universidad/Metodoogias/Proyecto/static/js/asientos.js)) basándose en la capacidad del bus físico cargado en la base de datos:

- **Estructura de la Cabina**: Se dibuja una cuadrícula de 4 columnas que simula la distribución de un bus de larga distancia de un piso, con un pasillo central divisorio entre las columnas 2 y 3.
- **Estados Visuales de los Asientos**:
  - **Disponible**: Asiento clickable representado en color azul/verde.
  - **Seleccionado**: Asiento marcado en color amarillo que indica que el usuario lo ha añadido a su carrito actual.
  - **Ocupado (Vendido)**: Asiento inhabilitado representado en color gris oscuro con un icono de candado. El cursor se bloquea y no es posible hacer click ni interactuar con él.

---

## 3. Lógica de Control de Ocupación en Tiempo Real

El estado de ocupación de un asiento no se almacena como una propiedad booleana estática en la tabla `asiento`, ya que un mismo asiento físico está "disponible" para viajes en distintas fechas u horarios. 

### Consulta de Disponibilidad (`GET /api/asientos`)
Cuando un usuario ingresa a seleccionar asientos para un servicio horaria en una fecha específica, el frontend realiza una petición API para recuperar el estado:
1. El backend consulta la tabla `asiento_comprado` realizando un `JOIN` con la tabla `compra`.
2. Se filtran únicamente los registros asociados a ese `id_horario`, en la `fecha_viaje` consultada y cuyo estado de compra sea `"confirmada"`.
3. Todos los identificadores de asiento encontrados son devueltos como una lista de "asientos ocupados" al frontend.
4. El frontend deshabilita y marca con candado dichos números de asiento en el mapa de cabina.

---

## 4. Validaciones de Integridad y Reglas de Negocio en Backend

Cuando el usuario envía los datos para finalizar la compra, el endpoint `POST /api/confirmar-compra` de [routes.py](file:///c:/Users/dipez/OneDrive/Documentos/Universidad/Metodoogias/Proyecto/backend/routes.py) aplica validaciones de negocio e integridad de base de datos antes de guardar los registros:

- **Límites de Fecha**:
  - **Pasado**: No se permite comprar pasajes para fechas anteriores a la fecha actual local del servidor (`HTTP 400 Bad Request`).
  - **Futuro**: Para mantener un control ordenado de la planificación, el sistema restringe la compra con un máximo de **30 días de anticipación** (`HTTP 400 Bad Request`).
- **Prevención de Colisión Doble (Condición de Carrera)**:
  En sistemas de alta concurrencia, es posible que dos usuarios abran la misma pantalla y seleccionen el mismo asiento al mismo tiempo. Para evitar que se venda dos veces el mismo asiento físico para el mismo viaje:
  1. Justo antes de insertar la compra en la base de datos, el backend ejecuta una consulta de bloqueo en la tabla `asiento_comprado` para verificar que el asiento solicitado no haya sido comprado y confirmado en los últimos milisegundos.
  2. Si el asiento ya fue ocupado, el servidor cancela la transacción completa y retorna un código `HTTP 409 Conflict` informando al usuario que el asiento ya no está disponible.
  3. Si está libre, se procede a guardar los registros y se ejecuta el `commit()` de base de datos.
- **Invitados**: Si el usuario no ha iniciado sesión, el backend genera un perfil temporal asociado al email `'invitado@talmocur.local'` para que el flujo de compra no se vea interrumpido.

---

## 5. Emisión de la Boleta (Comprobante de Viaje)

Una vez confirmada e insertada la compra en la base de datos con éxito:

1. El backend retorna los datos del pasaje y un identificador único de compra.
2. El frontend redirige al usuario a `/boleta` almacenando temporalmente los datos de la transacción en la sesión o recuperándolos mediante su ID.
3. La página de la boleta ([boleta.html](file:///c:/Users/dipez/OneDrive/Documentos/Universidad/Metodoogias/Proyecto/templates/boleta.html)) renderiza un recibo de viaje de alta calidad visual:
   - **Código de Barras/QR Dinámico**: Generado estéticamente en la UI para representar la validez del pasaje digital.
   - **Información del Pasaje**: Muestra la fecha del viaje, la hora de salida del bus, la patente del bus asignado y el asiento reservado.
   - **Datos de Origen y Destino**: Despliega con claridad los puntos de partida y llegada del viaje.
   - **Monto y Pago**: Detalla el precio unitario del pasaje y el método de pago utilizado.
   - **Información del Pasajero**: Muestra el nombre y RUT del pasajero asociado a ese asiento para fines de control de abordaje en el bus.

---

## 6. Control del Historial de Navegación y Caché del Navegador

Para prevenir anomalías en la experiencia de usuario y fallos de lógica al usar los botones de "Atrás" y "Adelante" del navegador web (que podrían reenviar formularios de pago o cargar asientos desactualizados), el sistema implementa tres mecanismos de control:

### 6.1. Políticas de Caché en Endpoints Críticos (Evitación de Caché en HTTP)
En [app.py](file:///c:/Users/dipez/OneDrive/Documentos/Universidad/Metodoogias/Proyecto/backend/app.py), las rutas `/compra-pasajes`, `/boleta` y `/compra-pasajes/asientos` retornan la respuesta HTML adjuntando la cabecera HTTP de control de caché:
```http
Cache-Control: no-store, no-cache, must-revalidate, max-age=0
```
Esto fuerza al navegador a solicitar siempre una versión fresca del servidor, garantizando que el mapa de asientos disponibles se calcule con datos de compras actualizados en tiempo real en lugar de cargarse desde la caché local del disco.

### 6.2. Recarga en BFCache (Back-Forward Cache)
En el frontend de [asientos.js](file:///c:/Users/dipez/OneDrive/Documentos/Universidad/Metodoogias/Proyecto/static/js/asientos.js), se añade un oyente del evento `pageshow`:
```javascript
window.addEventListener('pageshow', function (event) {
  if (event.persisted) {
    window.location.reload();
  }
});
```
Si el navegador carga la página de selección de asientos recuperándola desde la memoria BFCache (historial de retroceso/avance rápido), se fuerza de forma automática la recarga del documento (`window.location.reload()`) para refrescar las ocupaciones de asientos y borrar cualquier selección previa huérfana.

### 6.3. Reemplazo del Historial y Redirección Limpia
Durante el proceso de confirmación de la compra en [compra_pasajes.js](file:///c:/Users/dipez/OneDrive/Documentos/Universidad/Metodoogias/Proyecto/static/js/compra_pasajes.js):
1. **Reemplazo de Estado**: Antes de redireccionar, se llama a `history.replaceState({ compraRealizada: true }, '', window.location.href)`. De esta forma, si el usuario intenta retroceder, el estado del historial marca que la compra ya fue procesada.
2. **Redirección No Retornable**: La redirección hacia la boleta de compra se realiza mediante `window.location.replace('/boleta')` en lugar de modificar `window.location.href`. Esto sustituye la entrada del formulario de compra por la boleta en el historial del navegador. De esta manera, si el usuario pulsa el botón "Atrás" desde la pantalla de la boleta, el navegador vuelve directamente a la pantalla de búsqueda de pasajes del home en vez de retornar al formulario de compra ya procesado.
