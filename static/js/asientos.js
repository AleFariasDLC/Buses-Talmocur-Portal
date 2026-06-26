/* ================================================================
   ASIENTOS.JS  –  Talmocur · Selección de asientos
   ================================================================ */


/* ── 1. Leer parámetros de la URL ────────────────────────────── */
const params       = new URLSearchParams(window.location.search);
const busId        = params.get('bus')    || 'A1';
const hora         = params.get('hora')   || '07:00';
const precio       = params.get('precio') || '2800';
const asientosDisp = parseInt(params.get('asientos') || '20', 10);

const TOTAL_ASIENTOS = 40;   // capacidad total del bus (10 filas × 4 asientos)
const PRECIO_FMT     = `$${parseInt(precio).toLocaleString('es-CL')}`;


/* ── 2. Rellenar topbar e info del mapa ──────────────────────── */
document.getElementById('top-hora').textContent    = hora;
document.getElementById('top-bus').textContent     = `Bus ${busId}`;
document.getElementById('top-precio').textContent  = PRECIO_FMT;
document.getElementById('detalle-bus').textContent = `Bus ${busId}`;
document.getElementById('detalle-hora').textContent = hora;

/* Calcular hora de llegada (salida + 60 minutos) */
function calcularHoraLlegada(horaSalida, minutosViaje) {
  const [hh, mm] = horaSalida.split(':').map(Number);
  const totalMin = hh * 60 + mm + minutosViaje;
  const horaLlegada = String(Math.floor(totalMin / 60) % 24).padStart(2, '0');
  const minLlegada  = String(totalMin % 60).padStart(2, '0');
  return `${horaLlegada}:${minLlegada}`;
}
const horaLlegada = calcularHoraLlegada(hora, 60);   // ← cambia 60 por los minutos reales
document.getElementById('detalle-hora-llegada').textContent = horaLlegada;


/* ── 3. Generar estado de cada asiento ───────────────────────── */
/**
 * Construye un array de 40 asientos.
 * Los asientos "disponibles" (asientosDisp) se marcan como libres,
 * el resto como ocupados. Los ocupados se distribuyen aleatoriamente.
 */
function generarEstadoAsientos(total, disponibles) {
  const estados = Array(total).fill('ocupado');

  // Seleccionar índices aleatorios para los asientos libres
  const indices = [];
  while (indices.length < disponibles && indices.length < total) {
    const idx = Math.floor(Math.random() * total);
    if (!indices.includes(idx)) indices.push(idx);
  }
  indices.forEach(i => { estados[i] = 'libre'; });

  return estados;
}

const estadoAsientos = generarEstadoAsientos(TOTAL_ASIENTOS, asientosDisp);
let asientoSeleccionado = null;   // número del asiento actualmente seleccionado (1-based)


/* ── 4. Renderizar grilla de asientos ────────────────────────── */
/**
 * Layout del bus: 10 filas, cada fila tiene 4 asientos (A, B | C, D).
 * Columnas en el grid: [num-fila] [A] [B] [pasillo] [C] [D]
 */
function renderizarAsientos() {
  const contenedor = document.getElementById('filasAsientos');
  contenedor.innerHTML = '';

  for (let fila = 1; fila <= 10; fila++) {
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
  const idx    = num - 1;
  const estado = estadoAsientos[idx];

  const btn = document.createElement('button');
  btn.className    = `sa-asiento sa-asiento--${estado}`;
  btn.dataset.num  = num;
  btn.dataset.estado = estado;
  btn.setAttribute('role', 'option');
  btn.setAttribute('aria-label', `Asiento ${num} – ${estado}`);

  if (estado === 'ocupado') {
    btn.disabled = true;
    btn.setAttribute('aria-disabled', 'true');
  }

  // Número visible dentro del asiento
  const span = document.createElement('span');
  span.className   = 'sa-asiento__num';
  span.textContent = num;
  btn.appendChild(span);

  // Evento click
  btn.addEventListener('click', () => seleccionarAsiento(btn, num));

  return btn;
}


/* ── 5. Lógica de selección ──────────────────────────────────── */
function seleccionarAsiento(btn, num) {
  if (btn.dataset.estado === 'ocupado') return;

  // Deseleccionar el anterior
  if (asientoSeleccionado !== null) {
    const anterior = document.querySelector(`.sa-asiento[data-num="${asientoSeleccionado}"]`);
    if (anterior) {
      anterior.classList.remove('sa-asiento--seleccionado');
      anterior.classList.add('sa-asiento--libre');
      anterior.setAttribute('aria-label', `Asiento ${asientoSeleccionado} – libre`);
    }
  }

  // Si se hace clic en el mismo asiento → deseleccionar
  if (asientoSeleccionado === num) {
    asientoSeleccionado = null;
    actualizarResumen(null);
    return;
  }

  // Seleccionar el nuevo
  btn.classList.remove('sa-asiento--libre');
  btn.classList.add('sa-asiento--seleccionado');
  btn.setAttribute('aria-label', `Asiento ${num} – seleccionado`);
  asientoSeleccionado = num;

  actualizarResumen(num);
}


/* ── 6. Actualizar panel de resumen ──────────────────────────── */
function actualizarResumen(num) {
  const btnConfirmar    = document.getElementById('btnConfirmar');
  const resumenVacio    = document.getElementById('resumenVacio');
  const resumenSel      = document.getElementById('resumenSeleccion');
  const elNum           = document.getElementById('resumenAsientoNum');
  const elPrecio        = document.getElementById('resumenPrecio');
  const elHora          = document.getElementById('resumenHora');

  if (num === null) {
    resumenVacio.style.display = '';
    resumenSel.style.display   = 'none';
    btnConfirmar.disabled      = true;
    return;
  }

  resumenVacio.style.display = 'none';
  resumenSel.style.display   = '';
  btnConfirmar.disabled      = false;

  elNum.textContent    = `Asiento N.º ${num}`;
  elPrecio.textContent = PRECIO_FMT;
  elHora.textContent   = hora;
}


/* ── 7. Botón confirmar compra ───────────────────────────────── */
document.getElementById('btnConfirmar').addEventListener('click', () => {
  if (asientoSeleccionado === null) return;

  // Aquí en el futuro se conectará con la API de reserva
  alert(`✅ Reserva registrada:\n\nBus: ${busId}\nAsiento: ${asientoSeleccionado}\nHora: ${hora}\nPrecio: ${PRECIO_FMT}\n\n(Funcionalidad de pago próximamente)`);
});


/* ── 8. Iniciar ──────────────────────────────────────────────── */
renderizarAsientos();
actualizarResumen(null);


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
    iconUrl:       '/static/leaflet/marker-icon.png',
    shadowUrl:     '/static/leaflet/marker-shadow.png',
    iconRetinaUrl: '/static/leaflet/marker-icon.png',
  });

  /* ── Coordenadas reales de las paradas ── */
  const paradas = [
    {
      latlng: [-34.984800474239314, -71.24580838453566],
      nombre: 'Terminal de Buses Curicó',
      detalle: 'Maipú 636, Curicó',
      tipo: 'origen'
    },
    {
      latlng: [-35.094148495408554, -71.31878667318661],
      nombre: 'Paradero Molina',
      detalle: 'Molina, Maule',
      tipo: 'parada'
    },
    {
      latlng: [-35.12952611574631, -71.35216713561492],
      nombre: 'Paradero Itahue',
      detalle: 'Puente Alto, Molina',
      tipo: 'parada'
    },
    {
      latlng: [-35.21930224041522, -71.42243265633414],
      nombre: 'Paradero Camarico',
      detalle: 'Camarico, Rio Claro',
      tipo: 'parada'
    },
    {
      latlng: [-35.30268971372136, -71.51769771925869],
      nombre: 'Paradero San Rafael',
      detalle: 'San Rafael',
      tipo: 'parada'
    },
    {
      latlng: [-35.36884174597917, -71.5906332560088],
      nombre: 'Paradero Panguilemo',
      detalle: 'Talca',
      tipo: 'parada'
    },
    {
      latlng: [-35.39938866192725, -71.62046454103272],
      nombre: 'Paradero Cruze Lircay',
      detalle: 'Talca',
      tipo: 'parada'
    },
    {
      latlng: [-35.418717276870936, -71.63192427631867],
      nombre: 'Paradero Parque Industrial Talca',
      detalle: 'Talca',
      tipo: 'parada'
    },
    {
      latlng: [-35.42829759595688, -71.63593351927078],
      nombre: 'Paradero 2 Norte',
      detalle: 'Talca',
      tipo: 'parada'
    },
    {
      latlng: [-35.43157875116553, -71.63719529177065],
      nombre: 'Paradero Varoli',
      detalle: 'Talca',
      tipo: 'parada'
    },
    {
      latlng: [-35.4319090, -71.6443620],
      nombre: 'Paradero 15 Oriente',
      detalle: 'Talca',
      tipo: 'parada'
    },
    {
      latlng: [-35.43177636340633, -71.64541360388556],
      nombre: 'Paradero Plaza Arturo Prat',
      detalle: 'Talca',
      tipo: 'parada'
    },
    {
      latlng: [-35.43016139127286, -71.64699132598537],
      nombre: 'Terminal de Buses Talca',
      detalle: 'Talca, Maule',
      tipo: 'destino'
    }
  ];

  /* ── Íconos con imágenes PNG descargadas ── */

  // Pin inicio (origen): pin_inicio.png
  const iconoInicio = L.icon({
    iconUrl:    '/static/image/pin_inicio.png',
    iconSize:   [50, 50],      // ancho x alto en píxeles — ajusta si queda muy grande/pequeño
    iconAnchor: [19, 50],      // punto del pin que toca el mapa (centro-abajo)
    popupAnchor:[0, -54]       // dónde aparece el popup respecto al pin
  });

  // Pin parada intermedia: pin_parada.png
  const iconoParada = L.icon({
    iconUrl:    '/static/image/pin_parada.png',
    iconSize:   [44, 44],
    iconAnchor: [17, 44],
    popupAnchor:[0, -48]
  });

  // Pin fin (destino): pin_fin.png
  const iconoFin = L.icon({
    iconUrl:    '/static/image/pin_fin.png',
    iconSize:   [50, 50],
    iconAnchor: [19, 50],
    popupAnchor:[0, -54]
  });

  /* ── Inicializar el mapa ── */
  const mapa = L.map('mapaLeaflet', {
    center:          [-35.2060, -71.4500],
    zoom:            10,
    zoomControl:     true,
    scrollWheelZoom: true,
    doubleClickZoom: true,
    dragging:        true,
  });

  /* ── Tiles de OpenStreetMap ── */
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> | Ruta: <a href="https://project-osrm.org" target="_blank">OSRM</a>',
    maxZoom: 19,
    minZoom:  8,
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
      color:      '#1a73e8',
      weight:     16,
      opacity:    0.18,
      lineJoin:   'round',
      lineCap:    'round',
    }).addTo(mapa);

    // Línea principal
    const lineaPrincipal = L.polyline(latlngs, {
      color:    '#1a73e8',
      weight:   7,
      opacity:  0.92,
      lineJoin: 'round',
      lineCap:  'round',
    }).addTo(mapa);

    // Hilo blanco interior (efecto Google Maps)
    L.polyline(latlngs, {
      color:   '#ffffff',
      weight:  2.5,
      opacity: 0.55,
      lineJoin: 'round',
      lineCap:  'round',
    }).addTo(mapa);

    return lineaPrincipal;
  }

  /* ── Marcadores de paradas (se agregan siempre, independiente de OSRM) ── */
  function agregarMarcadores() {
    paradas.forEach(p => {
      let icono;
      if      (p.tipo === 'origen')  icono = iconoInicio;
      else if (p.tipo === 'destino') icono = iconoFin;
      else                           icono = iconoParada;

      const etiquetaTipo = {
        origen:  '<span style="color:#1a1a1a;font-weight:700;font-size:10px;text-transform:uppercase;letter-spacing:.05em;">ORIGEN</span>',
        destino: '<span style="color:#1a1a1a;font-weight:700;font-size:10px;text-transform:uppercase;letter-spacing:.05em;">DESTINO</span>',
        parada:  '<span style="color:#e53935;font-weight:700;font-size:10px;text-transform:uppercase;letter-spacing:.05em;">PARADA</span>',
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

