# Funcionamiento del Mapa de Recorridos

Este documento detalla la implementación, tecnología y lógica de funcionamiento del mapa interactivo utilizado en el portal de Buses Talmocur para representar de manera gráfica los recorridos y sus paradas intermedias.

---

## 1. Tecnologías Utilizadas

El sistema cartográfico del portal está compuesto por las siguientes herramientas integradas en el frontend:

1. **Leaflet.js**: Biblioteca JavaScript de código abierto para mapas interactivos móviles y responsivos. Se utiliza para la inicialización y manipulación de capas, marcadores y polilíneas.
2. **OpenStreetMap**: Proveedor de capas de teselas (map tiles) geográficas estándar e independientes que sirven como fondo cartográfico. No requiere clave de API.
3. **OSRM (Open Source Routing Machine)**: Servicio de enrutamiento terrestre de alto rendimiento basado en datos de OpenStreetMap. Se consume el endpoint de conducción (`/route/v1/driving/`) para calcular la ruta real a través de las autopistas y carreteras en lugar de dibujar líneas rectas directas.

---

## 2. Puntos Geográficos Predefinidos (`RUTAS_MAPA`)

Dado que las coordenadas de los paraderos y terminales de buses son fijas en la vida real, el sistema cuenta con un diccionario estático de coordenadas GPS en los archivos de frontend ([asientos.js](file:///c:/Users/dipez/OneDrive/Documentos/Universidad/Metodoogias/Proyecto/static/js/asientos.js) y [ruta_visual.js](file:///c:/Users/dipez/OneDrive/Documentos/Universidad/Metodoogias/Proyecto/static/js/ruta_visual.js)).

### Ejemplo de Rutas Cargadas (Ruta 5 Sur):
- **Curicó ↔ Talca**:
  - *Terminal de Buses Curicó*: `[-34.984800, -71.245808]` (Origen/Destino)
  - *Paradero Molina*: `[-35.094148, -71.318786]` (Parada intermedia)
  - *Paradero Itahue*: `[-35.129526, -71.352167]` (Parada intermedia)
  - *Paradero Camarico*: `[-35.219302, -71.422432]` (Parada intermedia)
  - *Paradero San Rafael*: `[-35.302689, -71.517697]` (Parada intermedia)
  - *Terminal de Buses Talca*: `[-35.430161, -71.646991]` (Origen/Destino)

---

## 3. Flujo de Funcionamiento del Mapa

El renderizado y trazado de un viaje sigue un flujo secuencial:

### Paso 1: Inyección de Datos desde el Servidor
El backend de Flask inyecta el origen y destino del viaje consultado directamente dentro del HTML mediante un bloque JSON invisible en el DOM:
```html
<script id="viaje-data-ruta" type="application/json">
  {"origen": "Curicó", "destino": "Talca"}
</script>
```

### Paso 2: Lectura y Validación en Frontend
El script parsea la información. Se genera una clave de búsqueda combinando origen y destino (ej: `"Curicó-Talca"`). 
- **Resiliencia (Fallback)**: Si no se encuentran coordenadas predefinidas en el diccionario para la combinación específica, se selecciona por defecto la ruta `"Curicó-Talca"` para prevenir que el mapa se rompa visualmente.

### Paso 3: Consulta al Enrutador OSRM
Se realiza una solicitud `GET` asíncrona hacia la API pública de OSRM concatenando las coordenadas geográficas de origen, paradas intermedias y destino en formato `longitud,latitud`:
```
https://router.project-osrm.org/route/v1/driving/lng1,lat1;lng2,lat2;lng3,lat3?overview=full&geometries=geojson
```

### Paso 4: Trazado de la Ruta Terrestre
- **Éxito en OSRM**: Se recupera la geometría en formato GeoJSON, se invierten los pares de coordenadas a `[latitud, longitud]` (formato requerido por Leaflet) y se dibuja una polilínea multicapa en color azul con bordes definidos.
- **Fallo en OSRM (Mecanismo de Recuperación)**: Si la API de OSRM no responde o falla, el código captura el error y traza de forma automática líneas rectas directas uniendo las coordenadas secuenciales de la ruta en el mapa.

### Paso 5: Ajuste de Zoom y Encuadre
Se llama a la función `mapa.fitBounds(linea.getBounds(), { padding: [...] })` para calcular automáticamente el nivel de zoom y centrado necesarios para que toda la ruta quede completamente visible en pantalla, independientemente de la resolución del dispositivo.

---

## 4. Elementos Visuales Personalizados

Para mejorar la estética e interactividad de la interfaz, el mapa implementa:

- **Pines y Marcadores de Colores**:
  - `pin_inicio.png`: Marcador para el terminal de origen.
  - `pin_parada.png`: Marcador redondo más pequeño para paraderos intermedios en carretera.
  - `pin_fin.png`: Marcador para el terminal de destino final.
- **Popups de Información**:
  Al hacer clic sobre cualquier pin del mapa, se despliega un globo popup con tipografía *DM Sans* que muestra el rol del punto (ORIGEN / DESTINO / PARADA), el nombre del paradero y detalles de su dirección exacta (ej: *Maipú 636, Curicó*).
