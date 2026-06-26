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
  window.location.assign('/compra-pasajes');
  //alert(`✅ Reserva registrada:\n\nBus: ${busId}\nAsiento: ${asientoSeleccionado}\nHora: ${hora}\nPrecio: ${PRECIO_FMT}\n\n(Funcionalidad de pago próximamente)`);
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
      latlng: [-34.9855, -71.2441],
      nombre: 'Terminal de Buses Curicó',
      detalle: 'Maipú 636, Curicó',
      tipo: 'origen'
    },
    {
      latlng: [-35.1174, -71.2892],
      nombre: 'Paradero Molina',
      detalle: 'Molina, Maule',
      tipo: 'parada'
    },
    {
      latlng: [-35.1830, -71.3210],
      nombre: 'Subestación Itahue EFE',
      detalle: 'Itahue, Molina',
      tipo: 'parada'
    },
    {
      latlng: [-35.3065, -71.5205],
      nombre: 'Vulcanización San Javier',
      detalle: 'Ruta 5 Sur, San Javier',
      tipo: 'parada'
    },
    {
      latlng: [-35.4270, -71.6554],
      nombre: 'Terminal de Buses Talca',
      detalle: '2 Sur 1936, Talca',
      tipo: 'destino'
    }
  ];

  /* ── Coordenadas de la ruta (Ruta 5 Sur) ── */
  const coordsRuta = [
    [-34.9855, -71.2441],   // Curicó
    [-34.9990, -71.2560],
    [-35.0145, -71.2640],
    [-35.0360, -71.2720],
    [-35.0560, -71.2780],
    [-35.0780, -71.2840],
    [-35.1000, -71.2870],
    [-35.1174, -71.2892],   // Molina
    [-35.1380, -71.3010],
    [-35.1580, -71.3130],
    [-35.1830, -71.3210],   // Itahue EFE
    [-35.2040, -71.3440],
    [-35.2240, -71.3750],
    [-35.2440, -71.4080],
    [-35.2650, -71.4410],
    [-35.2850, -71.4730],
    [-35.3065, -71.5205],   // San Javier
    [-35.3280, -71.5520],
    [-35.3500, -71.5840],
    [-35.3720, -71.6100],
    [-35.3970, -71.6330],
    [-35.4270, -71.6554]    // Talca
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
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>',
    maxZoom: 19,
    minZoom:  8,
  }).addTo(mapa);

  /* ── Halo exterior (glow azul) de la ruta ── */
  L.polyline(coordsRuta, {
    color:      '#1a73e8',
    weight:     16,
    opacity:    0.18,
    lineJoin:   'round',
    lineCap:    'round',
    smoothFactor: 1.5,
  }).addTo(mapa);

  /* ── Línea principal de la ruta ── */
  const lineaRuta = L.polyline(coordsRuta, {
    color:        '#1a73e8',
    weight:       7,
    opacity:      0.92,
    lineJoin:     'round',
    lineCap:      'round',
    smoothFactor: 1.5,
  }).addTo(mapa);

  /* ── Hilo blanco interior (efecto Google Maps) ── */
  L.polyline(coordsRuta, {
    color:   '#ffffff',
    weight:  2.5,
    opacity: 0.55,
    lineJoin:   'round',
    lineCap:    'round',
    smoothFactor: 1.5,
  }).addTo(mapa);

  /* ── Marcadores de paradas ── */
  paradas.forEach(p => {
    // Elegir el icono según el tipo de parada
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
      .bindPopup(popupHtml, { maxWidth: 220, offset: [0, 0] });
  });

  /* ── Ajustar vista para mostrar la ruta completa ── */
  mapa.fitBounds(lineaRuta.getBounds(), { padding: [40, 55] });
}

/* Iniciar el mapa cuando el DOM esté listo */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initMapaLeaflet);
} else {
  initMapaLeaflet();
}

