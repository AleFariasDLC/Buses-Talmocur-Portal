/* ================================================================
   COMPRA_PASAJES.JS
   Maneja el envío del formulario de compra y redirección a boleta
   ================================================================ */

(function initCompraForm() {
  const form = document.getElementById('compraForm');
  if (!form) return;

  const busSeleccionado = sessionStorage.getItem('busSeleccionado') || 'A1';
  const horaSeleccionada = sessionStorage.getItem('horaSeleccionada') || '07:00';
  const precioSeleccionado = sessionStorage.getItem('precioSeleccionado') || '2800';
  const asientoSeleccionado = sessionStorage.getItem('asientoSeleccionado') || 'Por definir';

  const resumenItems = document.querySelectorAll('.cp-summary__item strong');
  if (resumenItems.length >= 5) {
    resumenItems[0].textContent = 'Curicó → Talca';
    resumenItems[1].textContent = `Bus ${busSeleccionado}`;
    resumenItems[2].textContent = horaSeleccionada;
    resumenItems[3].textContent = asientoSeleccionado === 'Por definir' ? 'Por definir' : `N.º ${asientoSeleccionado}`;
    resumenItems[4].textContent = `$${parseInt(precioSeleccionado).toLocaleString('es-CL')}`;
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const datosCompra = {
      nombre: document.getElementById('nombre').value.trim(),
      rut: document.getElementById('rut').value.trim(),
      email: document.getElementById('email').value.trim(),
      telefono: document.getElementById('telefono').value.trim(),
      tipoPasaje: document.getElementById('tipo-pasaje').value,
      observaciones: document.getElementById('observaciones').value.trim(),
      origen: 'Curicó',
      destino: 'Talca',
      bus: `Bus ${busSeleccionado}`,
      horaSalida: horaSeleccionada,
      horaLlegada: calcularHoraLlegada(horaSeleccionada, 60),
      asiento: asientoSeleccionado === 'Por definir' ? 'Por definir' : `N.º ${asientoSeleccionado}`,
      precio: precioSeleccionado
    };

    if (!datosCompra.nombre || !datosCompra.rut || !datosCompra.email) {
      alert('Por favor, completa todos los campos obligatorios.');
      return;
    }

    try {
      const response = await fetch('/api/confirmar-compra', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patente: busSeleccionado,
          horaSalida: horaSeleccionada,
          asiento: asientoSeleccionado,
          nombre: datosCompra.nombre,
          rut: datosCompra.rut,
          email: datosCompra.email,
          telefono: datosCompra.telefono,
          tipoPasaje: datosCompra.tipoPasaje,
          observaciones: datosCompra.observaciones,
          precio: precioSeleccionado,
          fechaViaje: new Date().toISOString().slice(0, 10),
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || 'No se pudo confirmar la compra');
      }

      localStorage.setItem('datosCompra', JSON.stringify(datosCompra));
      localStorage.setItem('compraConfirmada', JSON.stringify(payload));
      mostrarMensajeExito();
      setTimeout(() => {
        window.location.href = '/boleta';
      }, 1500);
    } catch (error) {
      alert(error.message);
    }
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
