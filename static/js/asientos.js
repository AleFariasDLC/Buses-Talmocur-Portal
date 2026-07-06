/* ================================================================
   ASIENTOS.JS  –  Talmocur · Selección de asientos
   ================================================================ */


/* Lee los datos del viaje*/
const VIAJE = JSON.parse(document.getElementById('viaje-data').textContent);
const busId = VIAJE.patente;
const hora = VIAJE.hora;
const precio = VIAJE.precio;
const TOTAL_ASIENTOS = VIAJE.capacidad;
const ocupadosSet = new Set(VIAJE.asientosOcupados);

const PRECIO_FMT = `$${parseInt(precio).toLocaleString('es-CL')}`;


/* Rellena el topbar con los datos */
document.getElementById('top-hora').textContent = hora;
document.getElementById('top-bus').textContent = busId;
document.getElementById('top-precio').textContent = PRECIO_FMT;


/* Estado real de cada asiento */
const estadoAsientos = Array.from({ length: TOTAL_ASIENTOS }, (_, i) =>
  ocupadosSet.has(i + 1) ? 'ocupado' : 'libre'
);

const asientosSeleccionados = new Set();  // números de asientos seleccionados


/* ── 4. Renderizar grilla de asientos ────────────────────────── */
/**
 * Layout del bus: 10 filas, cada fila tiene 4 asientos (A, B | C, D).
 * Columnas en el grid: [num-fila] [A] [B] [pasillo] [C] [D]
 */
function renderizarAsientos() {
  const contenedor = document.getElementById('filasAsientos');
  contenedor.innerHTML = '';

  // Calcula cuántas filas necesita este bus según su capacidad
  const numFilas = Math.ceil(TOTAL_ASIENTOS / 4);

  for (let fila = 1; fila <= numFilas; fila++) {
    const divFila = document.createElement('div');
    divFila.className = 'sa-fila';
    divFila.setAttribute('role', 'row');

    // Número de fila
    const numFila = document.createElement('span');
    numFila.className = 'sa-fila__num';
    numFila.textContent = fila;
    numFila.setAttribute('aria-hidden', 'true');
    divFila.appendChild(numFila);

    // Columnas: A=0, B=1 | pasillo | C=2, D=3
    const colsIzq = [0, 1];   // A, B
    const colsDer = [2, 3];   // C, D

    // Asientos izquierda (A y B)
    colsIzq.forEach(col => {
      const numAsiento = (fila - 1) * 4 + col + 1;
      divFila.appendChild(crearAsiento(numAsiento, fila, col));
    });

    // Pasillo
    const pasillo = document.createElement('div');
    pasillo.className = 'sa-fila__pasillo';
    pasillo.setAttribute('aria-hidden', 'true');
    divFila.appendChild(pasillo);

    // Asientos derecha (C y D)
    colsDer.forEach(col => {
      const numAsiento = (fila - 1) * 4 + col + 1;
      divFila.appendChild(crearAsiento(numAsiento, fila, col));
    });

    contenedor.appendChild(divFila);
  }
}

/**
 * Crea un elemento botón que representa un asiento.
 * @param {number} num - Número del asiento (1–40)
 */
function crearAsiento(num) {
  const idx = num - 1;
  const estado = estadoAsientos[idx];

  const btn = document.createElement('button');
  btn.className = `sa-asiento sa-asiento--${estado}`;
  btn.dataset.num = num;
  btn.dataset.estado = estado;
  btn.setAttribute('role', 'option');
  btn.setAttribute('aria-label', `Asiento ${num} – ${estado}`);

  if (estado === 'ocupado') {
    btn.disabled = true;
    btn.setAttribute('aria-disabled', 'true');
  }

  // Número visible dentro del asiento
  const span = document.createElement('span');
  span.className = 'sa-asiento__num';
  span.textContent = num;
  btn.appendChild(span);

  // Evento click
  btn.addEventListener('click', () => seleccionarAsiento(btn, num));

  return btn;
}


/* ── 5. Lógica de selección múltiple de asientos ────────────────────────── */
function seleccionarAsiento(btn, num) {
  if (btn.dataset.estado === 'ocupado') return;

  if (asientosSeleccionados.has(num)) {
    // Deseleccionar asientos
    asientosSeleccionados.delete(num);
    btn.classList.remove('sa-asiento--seleccionado');
    btn.classList.add('sa-asiento--libre');
    btn.setAttribute('aria-label', `Asiento ${num} – libre`);
  } else {
    // Seleccionar asientos
    asientosSeleccionados.add(num);
    btn.classList.remove('sa-asiento--libre');
    btn.classList.add('sa-asiento--seleccionado');
    btn.setAttribute('aria-label', `Asiento ${num} – seleccionado`);
  }

  actualizarResumen();
}


/* ── 6. Actualizar panel de resumen ──────────────────────────── */
function actualizarResumen() {
  const btnConfirmar = document.getElementById('btnConfirmar');
  const resumenVacio = document.getElementById('resumenVacio');
  const resumenSel = document.getElementById('resumenSeleccion');
  const elLista = document.getElementById('resumenAsientoNum');
  const elContador = document.getElementById('resumenContador');
  const elPrecio = document.getElementById('resumenPrecio');
  const elHora = document.getElementById('resumenHora');

  if (asientosSeleccionados.size === 0) {
    resumenVacio.style.display = '';
    resumenSel.style.display = 'none';
    btnConfirmar.disabled = true;
    return;
  }

  resumenVacio.style.display = 'none';
  resumenSel.style.display = '';
  btnConfirmar.disabled = false;

  const sorted = Array.from(asientosSeleccionados).sort((a, b) => a - b);
  const precioNum = parseInt(precio);
  const total = precioNum * asientosSeleccionados.size;
  const totalFmt = `$${total.toLocaleString('es-CL')}`;

  // Chips de asientos seleccionados
  elLista.innerHTML = sorted
    .map(n => `<span class="sa-resumen__chip">${n}</span>`)
    .join('');

  elContador.textContent = `${asientosSeleccionados.size} asiento${asientosSeleccionados.size > 1 ? 's' : ''}`;
  elPrecio.textContent = totalFmt;
  elHora.textContent = hora;
}


/* ── 7. Botón confirmar compra ───────────────────────────────── */
document.getElementById('btnConfirmar').addEventListener('click', () => {
  if (asientosSeleccionados.size === 0) return;

  const sorted = Array.from(asientosSeleccionados).sort((a, b) => a - b);
  const total = parseInt(precio) * asientosSeleccionados.size;
  const totalFmt = `$${total.toLocaleString('es-CL')}`;

  sessionStorage.setItem('idHorarioSeleccionado', VIAJE.idHorario);
  sessionStorage.setItem('origenSeleccionado', VIAJE.origen);
  sessionStorage.setItem('destinoSeleccionado', VIAJE.destino);
  sessionStorage.setItem('fechaSeleccionada', VIAJE.fecha);
  sessionStorage.setItem('busSeleccionado', busId);
  sessionStorage.setItem('horaSeleccionada', hora);
  sessionStorage.setItem('precioSeleccionado', precio);
  sessionStorage.setItem('asientosSeleccionados', JSON.stringify(sorted));
  sessionStorage.setItem('asientoSeleccionado', sorted.join(', '));
  sessionStorage.setItem('totalSeleccionado', String(total));
  sessionStorage.setItem('totalSeleccionadoFmt', totalFmt);

  // Aquí en el futuro se conectará con la API de reserva
  //alert(`✅ Reserva registrada:\n\nBus: ${busId}\nAsientos: ${sorted.join(', ')}\nHora: ${hora}\nTotal: ${totalFmt}\n\n(Funcionalidad de pago próximamente)`);

  //Existe ruta de compra de pasajes, redirigir con nombre de ruta de flask
  window.location.assign('/compra-pasajes')
});


/* ── 8. Iniciar ──────────────────────────────────────────────── */
renderizarAsientos();
actualizarResumen();


/* ── 9. MAPA LEAFLET + OpenStreetMap ─────────────────────────── */
/**
 * Inicializa el mapa interactivo con Leaflet.js usando tiles de
 * OpenStreetMap (sin API key). La ruta sigue la Ruta 5 Sur real
 * entre Curicó y Talca con coordenadas GPS reales.
 */
function initMapaLeaflet() {
  const mapEl = document.getElementById('mapaLeaflet');
  if (!mapEl || typeof L === 'undefined') return;

  /* Corregir ruta de iconos de Leaflet (apuntar a archivos locales) */
  delete L.Icon.Default.prototype._getIconUrl;
  L.Icon.Default.mergeOptions({
    iconUrl: '/static/leaflet/marker-icon.png',
    shadowUrl: '/static/leaflet/marker-shadow.png',
    iconRetinaUrl: '/static/leaflet/marker-icon.png',
  });

  /* ── Coordenadas literales por ruta (Ingresadas manualmente) ── */
  const RUTAS_MAPA = {
    // Ruta: Curicó -> Talca
    "Curicó-Talca": [
      { latlng: [-34.984800474239314, -71.24580838453566], nombre: 'Terminal De Buses Curicó', detalle: 'Maipú 636, Curicó', tipo: 'origen' },
      { latlng: [-35.094148495408554, -71.31878667318661], nombre: 'Paradero Molina', detalle: 'Molina, Maule', tipo: 'parada' },
      { latlng: [-35.12952611574631, -71.35216713561492], nombre: 'Paradero Itahue', detalle: 'Puente Alto, Molina', tipo: 'parada' },
      { latlng: [-35.21930224041522, -71.42243265633414], nombre: 'Paradero Camarico', detalle: 'Camarico, Rio Claro', tipo: 'parada' },
      { latlng: [-35.30268971372136, -71.51769771925869], nombre: 'Paradero San Rafael', detalle: 'San Rafael', tipo: 'parada' },
      { latlng: [-35.36884174597917, -71.5906332560088], nombre: 'Paradero Panguilemo', detalle: 'Talca', tipo: 'parada' },
      { latlng: [-35.39938866192725, -71.62046454103272], nombre: 'Paradero Cruze Lircay', detalle: 'Talca', tipo: 'parada' },
      { latlng: [-35.418717276870936, -71.63192427631867], nombre: 'Paradero Parque Industrial Talca', detalle: 'Talca', tipo: 'parada' },
      { latlng: [-35.42829759595688, -71.63593351927078], nombre: 'Paradero 2 Norte', detalle: 'Talca', tipo: 'parada' },
      { latlng: [-35.43157875116553, -71.63719529177065], nombre: 'Paradero Varoli', detalle: 'Talca', tipo: 'parada' },
      { latlng: [-35.4319090, -71.6443620], nombre: 'Paradero 15 Oriente', detalle: 'Talca', tipo: 'parada' },
      { latlng: [-35.43177636340633, -71.64541360388556], nombre: 'Paradero Plaza Arturo Prat', detalle: 'Talca', tipo: 'parada' },
      { latlng: [-35.43016139127286, -71.64699132598537], nombre: 'Terminal De Buses Talca', detalle: 'Talca, Maule', tipo: 'destino' }
    ],

    // Ruta: Talca -> Curicó
    "Talca-Curicó": [
      { latlng: [-35.43016139127286, -71.64699132598537], nombre: 'Terminal De Buses Talca', detalle: 'Talca, Maule', tipo: 'origen' },
      { latlng: [-35.302637184296096, -71.5173192136632], nombre: 'Paradero San Rafael', detalle: 'San Rafael, Maule', tipo: 'parada' },
      { latlng: [-35.22001267169181, -71.42355664542728], nombre: 'Paradero Camarico', detalle: 'Camarico, Rio Claro', tipo: 'parada' },
      { latlng: [-35.1355718931921, -71.35766922078334], nombre: 'Paradero Itahue', detalle: 'Itahue, Molina', tipo: 'parada' },
      { latlng: [-35.09377167333507, -71.31836018809612], nombre: 'Paradero Molina', detalle: 'Molina, Maule', tipo: 'parada' },
      { latlng: [-35.050460276524845, -71.28213615677292], nombre: 'Paradero Lontué', detalle: 'Lontué, Molina', tipo: 'parada' },
      { latlng: [-35.0022361244218, -71.23882966018202], nombre: 'Paradero Los Niches', detalle: 'Los Niches, Curicó', tipo: 'parada' },
      { latlng: [-34.990404772669216, -71.23502633192253], nombre: 'Paradero Hospital Viejo, Curicó', detalle: 'Curicó, Maule', tipo: 'parada' },
      { latlng: [-34.990783357474804, -71.2396067209356], nombre: 'Paradero Calle Buen Pastor, Curicó', detalle: 'Curicó, Maule', tipo: 'parada' },
      { latlng: [-34.98962122106106, -71.24236787167128], nombre: 'Paradero Vuelta Calle Manuel Rodriguez, Curicó', detalle: 'Curicó, Maule', tipo: 'parada' },
      { latlng: [-34.98851934389254, -71.24245310310941], nombre: 'Paradero Esquina Calle Villota, Curicó', detalle: 'Curicó, Maule', tipo: 'parada' },
      { latlng: [-34.98627373840719, -71.2425522675447], nombre: 'Paradero Esquina Calle Estado, Curicó', detalle: 'Curicó, Maule', tipo: 'parada' },
      { latlng: [-34.984833609631, -71.24537368461873], nombre: 'Terminal De Buses Curicó', detalle: 'Curicó, Maule', tipo: 'destino' }
    ],

    // Ruta: Talca -> San Rafael
    "Talca-San Rafael": [
      { latlng: [-35.43016139127286, -71.64699132598537], nombre: 'Terminal De Buses Talca', detalle: 'Talca, Maule', tipo: 'origen' },
      { latlng: [-35.302637184296096, -71.5173192136632], nombre: 'Paradero San Rafael', detalle: 'San Rafael, Maule', tipo: 'destino' }
    ],

    // Ruta: Curicó -> Molina
    "Curicó-Molina": [
      { latlng: [-34.984800474239314, -71.24580838453566], nombre: 'Terminal de Buses Curicó', detalle: 'Maipú 636, Curicó', tipo: 'origen' },
      { latlng: [-35.094148495408554, -71.31878667318661], nombre: 'Paradero Molina', detalle: 'Molina, Maule', tipo: 'destino' }
    ],

    // Ruta: Curicó -> Itahue
    "Curicó-Itahue": [
      { latlng: [-34.984800474239314, -71.24580838453566], nombre: 'Terminal de Buses Curicó', detalle: 'Maipú 636, Curicó', tipo: 'origen' },
      { latlng: [-35.094148495408554, -71.31878667318661], nombre: 'Paradero Molina', detalle: 'Molina, Maule', tipo: 'parada' },
      { latlng: [-35.12952611574631, -71.35216713561492], nombre: 'Paradero Itahue', detalle: 'Puente Alto, Molina', tipo: 'destino' }
    ],

    // Ruta: Talca -> Molina
    "Talca-Molina": [
      { latlng: [-35.43016139127286, -71.64699132598537], nombre: 'Terminal De Buses Talca', detalle: 'Talca, Maule', tipo: 'origen' },
      { latlng: [-35.302637184296096, -71.5173192136632], nombre: 'Paradero San Rafael', detalle: 'San Rafael, Maule', tipo: 'parada' },
      { latlng: [-35.22001267169181, -71.42355664542728], nombre: 'Paradero Camarico', detalle: 'Camarico, Rio Claro', tipo: 'parada' },
      { latlng: [-35.1355718931921, -71.35766922078334], nombre: 'Paradero Itahue', detalle: 'Itahue, Molina', tipo: 'parada' },
      { latlng: [-35.09377167333507, -71.31836018809612], nombre: 'Paradero Molina', detalle: 'Molina, Maule', tipo: 'destino' }
    ]
  };

  // Obtenemos la clave exacta de la ruta seleccionada (Ej: "Curicó-Talca")
  const claveRuta = `${VIAJE.origen}-${VIAJE.destino}`;

  // Extraemos el array de paradas correspondiente. Si no existe aún o está vacío, evitamos que crashee
  let paradas = RUTAS_MAPA[claveRuta] || [];

  // Si no hay paradas cargadas aún para esa ruta, usamos Curicó-Talca como fallback para que el mapa no se rompa visualmente
  if (paradas.length === 0) {
    console.warn(`No se encontraron coordenadas para la ruta: ${claveRuta}. Usando fallback.`);
    paradas = RUTAS_MAPA["Curicó-Talca"];
  }

  /* ── Íconos con imágenes PNG descargadas ── */

  // Pin inicio (origen): pin_inicio.png
  const iconoInicio = L.icon({
    iconUrl: '/static/image/pin_inicio.png',
    iconSize: [50, 50],      // ancho x alto en píxeles — ajusta si queda muy grande/pequeño
    iconAnchor: [19, 50],      // punto del pin que toca el mapa (centro-abajo)
    popupAnchor: [0, -54]       // dónde aparece el popup respecto al pin
  });

  // Pin parada intermedia: pin_parada.png
  const iconoParada = L.icon({
    iconUrl: '/static/image/pin_parada.png',
    iconSize: [44, 44],
    iconAnchor: [17, 44],
    popupAnchor: [0, -48]
  });

  // Pin fin (destino): pin_fin.png
  const iconoFin = L.icon({
    iconUrl: '/static/image/pin_fin.png',
    iconSize: [50, 50],
    iconAnchor: [19, 50],
    popupAnchor: [0, -54]
  });

  /* ── Inicializar el mapa ── */
  const mapa = L.map('mapaLeaflet', {
    center: [-35.2060, -71.4500],
    zoom: 10,
    zoomControl: true,
    scrollWheelZoom: true,
    doubleClickZoom: true,
    dragging: true,
  });

  /* ── Tiles de OpenStreetMap ── */
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> | Ruta: <a href="https://project-osrm.org" target="_blank">OSRM</a>',
    maxZoom: 19,
    minZoom: 8,
  }).addTo(mapa);

  /* ─────────────────────────────────────────────────────────────────
     DIBUJAR RUTA REAL SIGUIENDO CARRETERAS (API OSRM gratuita)
     OSRM = OpenStreetMap Routing Machine. Devuelve la geometría exacta
     de la carretera (Ruta 5 Sur) sin necesitar API key.

     Nota: las coordenadas en OSRM van en orden  LONGITUD,LATITUD
     (al revés que Leaflet que usa LATITUD,LONGITUD).
  ───────────────────────────────────────────────────────────────── */

  // Convertir paradas de [lat,lng] a "lng,lat" que necesita OSRM
  const waypoints = paradas
    .map(p => `${p.latlng[1]},${p.latlng[0]}`)   // lng,lat
    .join(';');

  const osrmUrl =
    `https://router.project-osrm.org/route/v1/driving/${waypoints}` +
    `?overview=full&geometries=geojson`;

  /**
   * Dibuja la línea de ruta sobre el mapa usando las coordenadas dadas.
   * Se llama tanto con la ruta real de OSRM como con el fallback.
   * @param {Array} latlngs  - Array de [lat, lng] para Leaflet
   */
  function dibujarRuta(latlngs) {
    // Halo exterior (glow azul)
    L.polyline(latlngs, {
      color: '#1a73e8',
      weight: 16,
      opacity: 0.18,
      lineJoin: 'round',
      lineCap: 'round',
    }).addTo(mapa);

    // Línea principal
    const lineaPrincipal = L.polyline(latlngs, {
      color: '#1a73e8',
      weight: 7,
      opacity: 0.92,
      lineJoin: 'round',
      lineCap: 'round',
    }).addTo(mapa);

    // Hilo blanco interior (efecto Google Maps)
    L.polyline(latlngs, {
      color: '#ffffff',
      weight: 2.5,
      opacity: 0.55,
      lineJoin: 'round',
      lineCap: 'round',
    }).addTo(mapa);

    return lineaPrincipal;
  }

  /* ── Marcadores de paradas (se agregan siempre, independiente de OSRM) ── */
  function agregarMarcadores() {
    paradas.forEach(p => {
      let icono;
      if (p.tipo === 'origen') icono = iconoInicio;
      else if (p.tipo === 'destino') icono = iconoFin;
      else icono = iconoParada;

      const etiquetaTipo = {
        origen: '<span style="color:#1a1a1a;font-weight:700;font-size:10px;text-transform:uppercase;letter-spacing:.05em;">ORIGEN</span>',
        destino: '<span style="color:#1a1a1a;font-weight:700;font-size:10px;text-transform:uppercase;letter-spacing:.05em;">DESTINO</span>',
        parada: '<span style="color:#e53935;font-weight:700;font-size:10px;text-transform:uppercase;letter-spacing:.05em;">PARADA</span>',
      }[p.tipo];

      const popupHtml = `
        <div style="font-family:'DM Sans',sans-serif;min-width:150px;padding:2px 0;">
          <div style="margin-bottom:4px;">${etiquetaTipo}</div>
          <div style="font-size:14px;font-weight:700;color:#0f172a;margin-bottom:2px;">
            ${p.nombre}
          </div>
          <div style="font-size:11px;color:#64748b;">${p.detalle}</div>
        </div>`;

      L.marker(p.latlng, { icon: icono })
        .addTo(mapa)
        .bindPopup(popupHtml, { maxWidth: 220 });
    });
  }

  /* ── Pedir ruta real a OSRM ── */
  fetch(osrmUrl)
    .then(res => {
      if (!res.ok) throw new Error(`OSRM error: ${res.status}`);
      return res.json();
    })
    .then(data => {
      // OSRM devuelve GeoJSON con coordenadas en [lng, lat]
      // Leaflet necesita [lat, lng] → invertimos
      const coords = data.routes[0].geometry.coordinates
        .map(([lng, lat]) => [lat, lng]);

      const linea = dibujarRuta(coords);
      agregarMarcadores();
      mapa.fitBounds(linea.getBounds(), { padding: [40, 55] });
    })
    .catch(err => {
      // Si OSRM no está disponible (sin internet, etc.)
      // usa el fallback con las coordenadas aproximadas
      console.warn('OSRM no disponible, usando ruta aproximada:', err);

      const fallback = [
        [-34.9855, -71.2441],
        [-35.0360, -71.2720],
        [-35.1174, -71.2892],
        [-35.1830, -71.3210],
        [-35.2650, -71.4410],
        [-35.3065, -71.5205],
        [-35.3720, -71.6100],
        [-35.4270, -71.6554],
      ];
      const linea = dibujarRuta(fallback);
      agregarMarcadores();
      mapa.fitBounds(linea.getBounds(), { padding: [40, 55] });
    });
}

/* Iniciar el mapa cuando el DOM esté listo */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initMapaLeaflet);
} else {
  initMapaLeaflet();
}

