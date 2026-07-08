# Funcionamiento de la Página de Inicio (Home)

Este documento describe la página de inicio del portal de Buses Talmocur, detallando la interacción de la barra de búsqueda de pasajes, la lógica en el backend para la visualización de los "Pasajes de Hoy" (viajes del día) y el sistema dinámico de avisos al usuario (avisos flotantes tipo Toast).

---

## 1. La Barra de Búsqueda de Pasajes

Ubicada en la parte superior del home, permite a los usuarios buscar y filtrar los horarios de salida disponibles. 

### Sincronización Dinámica de Destinos
Para evitar búsquedas erróneas de trayectos que no opera la empresa, el formulario realiza un filtrado inteligente en el frontend ([home.js](file:///c:/Users/dipez/OneDrive/Documentos/Universidad/Metodoogias/Proyecto/static/js/home.js)):
- Si el usuario selecciona **Curicó** como origen, las opciones del destino se limitan dinámicamente a: *Talca*, *Molina* e *Itahue*.
- Si selecciona **Talca** como origen, el destino se limita a: *Curicó*, *San Rafael* y *Molina*.

### Botón de Intercambio (Swap)
El botón de swap permite permutar rápidamente las ciudades elegidas. Al presionarlo:
1. Copia temporalmente los valores de origen y destino.
2. Invierte el valor del origen.
3. Sincroniza el listado del destino según el nuevo origen y selecciona automáticamente la ciudad inversa.

### Validación y Límites de Fechas
- El selector de fecha tiene restricciones físicas mediante los atributos `min` y `max` de HTML5.
- **Límite Mínimo**: La fecha de hoy.
- **Límite Máximo**: 30 días de anticipación.
- Si un usuario ingresa manualmente una fecha inválida (por ejemplo, modificando la URL o usando la consola de desarrollo), el script frontend detecta la anomalía, muestra una alerta al usuario y reajusta la fecha al límite permitido (hoy o el día 30).

### Desplazamiento Automático (Auto-Scroll)
Si el usuario llega a la página principal con parámetros de búsqueda en la URL (ej: `?origen=Curico&destino=Talca&fecha=2026-07-20`), el frontend ejecuta un scroll suave (`scrollIntoView({ behavior: 'smooth' })`) después de 400 milisegundos directamente hacia la sección de resultados ("Pasajes de Hoy") para ahorrarle scroll manual.

---

## 2. Sección "Pasajes de Hoy" y Resultados de Búsqueda

Los pasajes disponibles se renderizan dinámicamente a partir de la consulta del endpoint `/` en [app.py](file:///c:/Users/dipez/OneDrive/Documentos/Universidad/Metodoogias/Proyecto/backend/app.py).

### Lógica de Filtrado y Exclusión en el Backend:
Para determinar qué horarios de viaje mostrar, el servidor ejecuta las siguientes reglas sobre la base de datos SQLite:
1. **Buses Activos**: Solo se listan horarios asignados a buses cuyo estado sea `"Activo"`. Si el bus está `"En mantención"`, sus viajes programados se ocultan.
2. **Control de Suspenso**: Se cruzan los horarios con la tabla `suspension`. Si el viaje coincide con un rango de fechas suspendido (`fecha_inicio <= fecha_consulta <= fecha_fin`), queda excluido de la vista.
3. **Margen de Viaje Iniciado**: Si la fecha consultada es **hoy**, se calcula la hora local del servidor. Solo se muestran los buses cuya hora de salida sea igual o mayor a la hora actual. Esto evita que los usuarios compren pasajes para buses que ya partieron.
4. **Cálculo de Plazas Disponibles**: Se realiza un conteo agrupado de pasajes vendidos (`asiento_comprado`) para esa fecha y horario. Los asientos libres se calculan restando los ocupados a la capacidad del bus (`capacidad - ocupados`).

### Flags Visuales en la UI:
- **Agotado**: Si los asientos libres son $\le 0$, la tarjeta se bloquea y se muestra el indicador "Agotado".
- **Pocas Plazas**: Si los asientos libres están entre $1$ y $5$, se resalta en color naranja el mensaje "¡Solo quedan N asientos!".
- **Normal**: Si quedan más de 5 asientos, se muestra el contador normal en color verde.
- **Duración**: Cada tarjeta muestra la duración estimada del trayecto (ej: *45 minutos*).

---

## 3. Sistema de Avisos Flotantes (Toasts)

Los comunicados de emergencia, tarifas u operatividad creados por el administrador se muestran a los usuarios autenticados al entrar al home mediante una interfaz interactiva de Toasts deslizantes:

- **Origen de Datos**: Se consumen desde el endpoint `/api/avisos/activos`, el cual recupera únicamente avisos vigentes donde `activo = True` y la fecha de creación sumada a la duración en días sea mayor a la fecha actual.
- **Cola de Mensajes (FIFO)**: Para no abrumar al usuario con múltiples ventanas emergentes simultáneas, los avisos se encolan. Se muestra uno a la vez.
- **Tipos de Avisos y Categorización Visual**:
  - `alerta` (⚠️ Alerta): Estilo en color naranja/amarillo para fallas o retrasos menores.
  - `info` (ℹ️ Información): Estilo azul para noticias generales o convenios.
  - `precio` (💵 Tarifa): Estilo verde para cambios en el costo de pasajes.
  - `emergencia` (🚨 Emergencia): Estilo rojo brillante para suspensiones totales de recorridos o condiciones climáticas extremas.
- **Temporizador e Indicador de Autocierre**:
  Cada aviso permanece visible en pantalla durante **10 segundos**. En la parte inferior del toast, una barra de progreso animada mediante CSS decrece visualmente indicando el tiempo restante.
- **Interacción**: El usuario puede cerrar el aviso manualmente presionando el botón "×". Al cerrarse (de manera manual o automática), el script espera 400 milisegundos antes de deslizar el siguiente aviso de la cola.
