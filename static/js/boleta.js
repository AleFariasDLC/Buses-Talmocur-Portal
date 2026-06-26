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
    // Generar número de boleta simulado
    const numeroBoleta = `FACT-${new Date().getFullYear()}-${String(Math.floor(Math.random() * 1000000)).padStart(6, '0')}`;
    
    // Llenar elementos
    document.getElementById('boleta-numero').textContent = numeroBoleta;
    document.getElementById('boleta-fecha').textContent = new Date().toLocaleDateString('es-CL');
    
    // Información del viaje
    document.getElementById('boleta-origen').textContent = datos.origen || '—';
    document.getElementById('boleta-destino').textContent = datos.destino || '—';
    document.getElementById('boleta-salida').textContent = datos.horaSalida || '—';
    document.getElementById('boleta-llegada').textContent = datos.horaLlegada || '—';
    document.getElementById('boleta-bus').textContent = datos.bus || '—';
    document.getElementById('boleta-asiento').textContent = datos.asiento || '—';
    
    // Datos del pasajero
    document.getElementById('boleta-nombre').textContent = datos.nombre || '—';
    document.getElementById('boleta-rut').textContent = datos.rut || '—';
    document.getElementById('boleta-tipo-pasaje').textContent = datos.tipoPasaje || '—';
    document.getElementById('boleta-email').textContent = datos.email || '—';
    document.getElementById('boleta-telefono').textContent = datos.telefono || '—';
    
    // Observaciones (mostrar solo si existen)
    if (datos.observaciones && datos.observaciones.trim() !== '') {
      document.getElementById('boleta-observaciones').textContent = datos.observaciones;
      document.getElementById('seccion-observaciones').style.display = 'block';
    }
    
    // Precio
    const precioFormato = `$${parseInt(datos.precio || 0).toLocaleString('es-CL')}`;
    document.getElementById('boleta-precio').textContent = precioFormato;
    
    // Código para el QR
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
