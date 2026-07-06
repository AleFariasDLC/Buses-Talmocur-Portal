/* ================================================================
   BOLETA.JS
   Lógica para generar y mostrar la boleta de compra
   ================================================================ */

(function initBoleta() {
  // Esperar a que el DOM esté completamente cargado
  document.addEventListener('DOMContentLoaded', () => {
    // Obtener datos de localStorage o de parámetros de URL
    const datosCompra = obtenerDatosCompra();
    
    if (datosCompra) {
      llenarBoleta(datosCompra);
      generarQR(datosCompra);
    }
  });

  /**
   * Obtener datos de la compra desde localStorage
   */
  function obtenerDatosCompra() {
    const datos = localStorage.getItem('datosCompra');
    if (datos) {
      localStorage.removeItem('datosCompra'); // Limpiar después de usar
      return JSON.parse(datos);
    }
    return null;
  }

  /**
   * Llenar la boleta con los datos de la compra
   */
  function llenarBoleta(datos) {
    const numeroBoleta = `FACT-${new Date().getFullYear()}-${String(Math.floor(Math.random() * 1000000)).padStart(6, '0')}`;

    document.getElementById('boleta-numero').textContent = numeroBoleta;
    document.getElementById('boleta-fecha').textContent = new Date().toLocaleDateString('es-CL');

    document.getElementById('boleta-origen').textContent = datos.origen || '—';
    document.getElementById('boleta-destino').textContent = datos.destino || '—';
    document.getElementById('boleta-salida').textContent = datos.horaSalida || '—';
    document.getElementById('boleta-llegada').textContent = datos.horaLlegada || '—';
    document.getElementById('boleta-bus').textContent = datos.bus || '—';
    document.getElementById('boleta-asiento').textContent = datos.asiento || '—';

    const pasajeros = Array.isArray(datos.pasajeros) && datos.pasajeros.length
      ? datos.pasajeros
      : [{
          asiento: datos.asiento,
          nombre: datos.nombre,
          rut: datos.rut,
          tipoPasaje: datos.tipoPasaje,
          email: datos.email,
          telefono: datos.telefono,
          observaciones: datos.observaciones,
        }];

    const contenedorPasajeros = document.getElementById('boleta-pasajeros');
    contenedorPasajeros.innerHTML = pasajeros.map((pasajero, index) => `
      <div class="boleta-pasajero-card">
        <div class="boleta-pasajero-card__header">
          <h4>Pasajero ${index + 1}</h4>
          <span>Asiento ${pasajero.asiento || '—'}</span>
        </div>
        <div class="boleta-grid">
          <div class="boleta-item boleta-item--full">
            <span class="boleta-item__label">Nombre completo</span>
            <span class="boleta-item__value">${pasajero.nombre || '—'}</span>
          </div>
          <div class="boleta-item">
            <span class="boleta-item__label">RUT</span>
            <span class="boleta-item__value">${pasajero.rut || '—'}</span>
          </div>
          <div class="boleta-item">
            <span class="boleta-item__label">Tipo de pasaje</span>
            <span class="boleta-item__value">${pasajero.tipoPasaje || '—'}</span>
          </div>
          <div class="boleta-item">
            <span class="boleta-item__label">Email</span>
            <span class="boleta-item__value">${pasajero.email || '—'}</span>
          </div>
          <div class="boleta-item">
            <span class="boleta-item__label">Teléfono</span>
            <span class="boleta-item__value">${pasajero.telefono || '—'}</span>
          </div>
        </div>
        ${pasajero.observaciones ? `<div class="boleta-observaciones">${pasajero.observaciones}</div>` : ''}
      </div>
    `).join('');

    if (pasajeros.some((p) => p.observaciones && p.observaciones.trim() !== '')) {
      document.getElementById('boleta-observaciones').textContent = pasajeros
        .filter((p) => p.observaciones && p.observaciones.trim() !== '')
        .map((p) => `Asiento ${p.asiento}: ${p.observaciones}`).join(' | ');
      document.getElementById('seccion-observaciones').style.display = 'block';
    }

    const precioFormato = `$${parseInt(datos.precio || 0).toLocaleString('es-CL')}`;
    document.getElementById('boleta-precio').textContent = precioFormato;
    document.getElementById('boleta-codigo').textContent = numeroBoleta;
  }

  /**
   * Generar QR con los datos de la boleta
   */
  function generarQR(datos) {
    const numeroBoleta = document.getElementById('boleta-numero').textContent;
    const datosQR = `TALMOCUR|${numeroBoleta}|${datos.nombre}|${datos.rut}|${datos.origen}|${datos.destino}|${datos.asiento}`;
    
    // Limpiar QR anterior si existe
    const qrContainer = document.getElementById('boleta-qr');
    qrContainer.innerHTML = '';
    
    // Generar nuevo QR
    new QRCode(qrContainer, {
      text: datosQR,
      width: 150,
      height: 150,
      correctLevel: QRCode.CorrectLevel.H,
      useSVG: false
    });
  }

  /**
   * Imprimir la boleta
   */
  document.getElementById('btn-imprimir')?.addEventListener('click', () => {
    window.print();
  });
})();
