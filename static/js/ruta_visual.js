document.addEventListener('DOMContentLoaded', () => {
  const dataEl = document.getElementById('viaje-data-ruta');
  if (!dataEl) return;

  let VIAJE;
  try {
    VIAJE = JSON.parse(dataEl.textContent);
  } catch (err) {
    console.error("Error al parsear viaje-data-ruta:", err);
    return;
  }

  const mapEl = document.getElementById('mapaLeafletFull');
  if (!mapEl || typeof L === 'undefined') return;

  /* Corregir ruta de iconos de Leaflet */
  delete L.Icon.Default.prototype._getIconUrl;
  L.Icon.Default.mergeOptions({
    iconUrl: '/static/leaflet/marker-icon.png',
    shadowUrl: '/static/leaflet/marker-shadow.png',
    iconRetinaUrl: '/static/leaflet/marker-icon.png',
  });

  /* ── Coordenadas literales por ruta (Copia de asientos.js) ── */
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

  const claveRuta = `${VIAJE.origen}-${VIAJE.destino}`;
  let paradas = RUTAS_MAPA[claveRuta] || [];
  
  if (paradas.length === 0) {
    console.warn(`No se encontraron coordenadas para la ruta: ${claveRuta}. Usando fallback.`);
    paradas = RUTAS_MAPA["Curicó-Talca"]; 
  }

  /* ── Íconos ── */
  const iconoInicio = L.icon({
    iconUrl: '/static/image/pin_inicio.png',
    iconSize: [50, 50],
    iconAnchor: [19, 50],
    popupAnchor: [0, -54]
  });

  const iconoParada = L.icon({
    iconUrl: '/static/image/pin_parada.png',
    iconSize: [44, 44],
    iconAnchor: [17, 44],
    popupAnchor: [0, -48]
  });

  const iconoFin = L.icon({
    iconUrl: '/static/image/pin_fin.png',
    iconSize: [50, 50],
    iconAnchor: [19, 50],
    popupAnchor: [0, -54]
  });

  /* ── Inicializar Mapa ── */
  const mapa = L.map('mapaLeafletFull', {
    center: [-35.2060, -71.4500],
    zoom: 10,
    zoomControl: true,
    scrollWheelZoom: true,
    doubleClickZoom: true,
    dragging: true,
  });

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap | Ruta: OSRM',
    maxZoom: 19,
    minZoom: 8,
  }).addTo(mapa);

  const waypoints = paradas.map(p => `${p.latlng[1]},${p.latlng[0]}`).join(';');
  const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${waypoints}?overview=full&geometries=geojson`;

  function dibujarRuta(latlngs) {
    L.polyline(latlngs, { color: '#1a73e8', weight: 16, opacity: 0.18, lineJoin: 'round', lineCap: 'round' }).addTo(mapa);
    const lineaPrincipal = L.polyline(latlngs, { color: '#1a73e8', weight: 7, opacity: 0.92, lineJoin: 'round', lineCap: 'round' }).addTo(mapa);
    L.polyline(latlngs, { color: '#ffffff', weight: 2.5, opacity: 0.55, lineJoin: 'round', lineCap: 'round' }).addTo(mapa);
    return lineaPrincipal;
  }

  function agregarMarcadores() {
    paradas.forEach(p => {
      let icono = iconoParada;
      if (p.tipo === 'origen') icono = iconoInicio;
      else if (p.tipo === 'destino') icono = iconoFin;

      const etiquetaTipo = {
        origen: '<span style="color:#1a1a1a;font-weight:700;font-size:10px;text-transform:uppercase;">ORIGEN</span>',
        destino: '<span style="color:#1a1a1a;font-weight:700;font-size:10px;text-transform:uppercase;">DESTINO</span>',
        parada: '<span style="color:#e53935;font-weight:700;font-size:10px;text-transform:uppercase;">PARADA</span>',
      }[p.tipo] || '';

      const popupHtml = `
        <div style="font-family:'DM Sans',sans-serif;min-width:150px;padding:2px 0;">
          <div style="margin-bottom:4px;">${etiquetaTipo}</div>
          <div style="font-size:14px;font-weight:700;color:#0f172a;margin-bottom:2px;">${p.nombre}</div>
          <div style="font-size:11px;color:#64748b;">${p.detalle}</div>
        </div>`;

      L.marker(p.latlng, { icon: icono }).addTo(mapa).bindPopup(popupHtml, { maxWidth: 220 });
    });
  }

  fetch(osrmUrl)
    .then(res => res.json())
    .then(data => {
      if (!data.routes || !data.routes[0]) throw new Error("Sin rutas en OSRM");
      const coords = data.routes[0].geometry.coordinates.map(([lng, lat]) => [lat, lng]);
      const linea = dibujarRuta(coords);
      agregarMarcadores();
      mapa.fitBounds(linea.getBounds(), { padding: [40, 55] });
    })
    .catch(err => {
      console.warn('OSRM falló. Dibujando línea recta aproximada.', err);
      const coordsRectas = paradas.map(p => p.latlng);
      const linea = dibujarRuta(coordsRectas);
      agregarMarcadores();
      mapa.fitBounds(linea.getBounds(), { padding: [40, 55] });
    });
});
