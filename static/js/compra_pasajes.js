/* ================================================================
   COMPRA_PASAJES.JS
   Maneja el envío del formulario de compra y redirección a boleta
   ================================================================ */

(function initCompraForm() {
  const form = document.getElementById('compraForm');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();

    // Obtener datos del formulario
    const datosCompra = {
      nombre: document.getElementById('nombre').value.trim(),
      rut: document.getElementById('rut').value.trim(),
      email: document.getElementById('email').value.trim(),
      telefono: document.getElementById('telefono').value.trim(),
      tipoPasaje: document.getElementById('tipo-pasaje').value,
      observaciones: document.getElementById('observaciones').value.trim(),
      // Datos del resumen (obtenidos del DOM)
      origen: document.querySelector('.cp-summary__item:nth-child(1) strong')?.textContent || 'Curicó',
      destino: document.querySelector('.cp-summary__item:nth-child(2) strong')?.textContent || 'Talca',
      bus: document.querySelector('.cp-summary__item:nth-child(2) strong')?.textContent || 'Bus A1',
      horaSalida: document.querySelector('.cp-summary__item:nth-child(3) strong')?.textContent || '07:00',
      horaLlegada: calcularHoraLlegada('07:00', 60),
      asiento: document.querySelector('.cp-summary__item:nth-child(4) strong')?.textContent || 'Por definir',
      precio: document.querySelector('.cp-summary__item:nth-child(5) strong')?.textContent?.replace(/\D/g, '') || '2800'
    };

    // Validar campos obligatorios
    if (!datosCompra.nombre || !datosCompra.rut || !datosCompra.email) {
      alert('Por favor, completa todos los campos obligatorios.');
      return;
    }

    // Guardar datos en localStorage
    localStorage.setItem('datosCompra', JSON.stringify(datosCompra));

    // Mostrar mensaje de éxito y redirigir
    mostrarMensajeExito();
    setTimeout(() => {
      window.location.href = '/boleta';
    }, 1500);
  });

  /**
   * Calcular hora de llegada
   */
  function calcularHoraLlegada(horaSalida, minutosViaje) {
    const [hh, mm] = horaSalida.split(':').map(Number);
    const totalMin = hh * 60 + mm + minutosViaje;
    const horaLlegada = String(Math.floor(totalMin / 60) % 24).padStart(2, '0');
    const minLlegada = String(totalMin % 60).padStart(2, '0');
    return `${horaLlegada}:${minLlegada}`;
  }

  /**
   * Mostrar mensaje de éxito
   */
  function mostrarMensajeExito() {
    const formContainer = form.parentElement;
    const mensaje = document.createElement('div');
    mensaje.className = 'compra-exito';
    mensaje.innerHTML = `
      <div class="compra-exito__content">
        <i class='bx bxs-check-circle'></i>
        <p>¡Compra confirmada! Generando boleta...</p>
      </div>
    `;
    formContainer.insertAdjacentElement('afterend', mensaje);

    // Agregar estilos
    const style = document.createElement('style');
    style.textContent = `
      .compra-exito {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        animation: fadeIn 0.3s ease;
      }

      @keyframes fadeIn {
        from {
          opacity: 0;
        }
        to {
          opacity: 1;
        }
      }

      .compra-exito__content {
        background: #fff;
        padding: 40px;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      }

      .compra-exito__content i {
        font-size: 3rem;
        color: #10b981;
        display: block;
        margin-bottom: 16px;
      }

      .compra-exito__content p {
        margin: 0;
        font-size: 1.1rem;
        color: #0f172a;
        font-weight: 500;
      }
    `;
    document.head.appendChild(style);
  }
})();
