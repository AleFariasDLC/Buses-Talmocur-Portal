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
  const totalSeleccionado = sessionStorage.getItem('totalSeleccionado');
  const asientosSeleccionados = JSON.parse(sessionStorage.getItem('asientosSeleccionados') || '[]');
  const resumenAsientos = document.getElementById('cp-asientos-resumen');
  const pasajerosContainer = document.getElementById('pasajerosContainer');
  const cantidadPasajes = Array.isArray(asientosSeleccionados) && asientosSeleccionados.length ? asientosSeleccionados.length : 1;
  const precioUnitario = parseInt(precioSeleccionado, 10) || 0;
  const precioTotal = totalSeleccionado ? parseInt(totalSeleccionado, 10) : (precioUnitario * cantidadPasajes);

  const idHorarioSeleccionado = sessionStorage.getItem('idHorarioSeleccionado');
  const origenSeleccionado = sessionStorage.getItem('origenSeleccionado') || 'Curicó';
  const destinoSeleccionado = sessionStorage.getItem('destinoSeleccionado') || 'Talca';
  const fechaSeleccionada = sessionStorage.getItem('fechaSeleccionada') || new Date().toISOString().slice(0, 10);

  const resumenItems = document.querySelectorAll('.cp-summary__item strong');
  if (resumenItems.length >= 5) {
    resumenItems[0].textContent = `${origenSeleccionado} → ${destinoSeleccionado}`;
    resumenItems[1].textContent = `Bus ${busSeleccionado}`;
    resumenItems[2].textContent = horaSeleccionada;
    if (resumenAsientos) {
      resumenAsientos.textContent = asientosSeleccionados.length ? asientosSeleccionados.join(', ') : 'Por definir';
    }
    resumenItems[4].textContent = `$${precioTotal.toLocaleString('es-CL')}`;
  }

  const numerosAsientos = Array.isArray(asientosSeleccionados) && asientosSeleccionados.length
    ? asientosSeleccionados
    : [1];

  renderizarPasajeros(numerosAsientos);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const pasajeros = Array.from(pasajerosContainer.querySelectorAll('.cp-pasajero-card')).map((card, index) => {
      const asiento = card.querySelector('[name="asiento[]"]').value;
      return {
        asiento: Number(asiento),
        nombre: card.querySelector('[name="nombre[]"]').value.trim(),
        rut: card.querySelector('[name="rut[]"]').value.trim(),
        email: card.querySelector('[name="email[]"]').value.trim(),
        telefono: card.querySelector('[name="telefono[]"]').value.trim(),
        tipoPasaje: card.querySelector('[name="tipo_pasaje[]"]').value,
        observaciones: card.querySelector('[name="observaciones[]"]').value.trim(),
      };
    });

    const datosCompra = {
      origen: origenSeleccionado,
      destino: destinoSeleccionado,
      bus: `Bus ${busSeleccionado}`,
      horaSalida: horaSeleccionada,
      horaLlegada: calcularHoraLlegada(horaSeleccionada, 60),
      asiento: pasajeros.map((p) => `N.º ${p.asiento}`).join(', '),
      precio: String(precioTotal),
      pasajeros,
    };

    const invalidos = pasajeros.some((p) => !p.nombre || !p.rut || !p.email);
    if (invalidos) {
      alert('Por favor, completa todos los campos obligatorios de cada pasajero.');
      return;
    }

    try {
      const response = await fetch('/api/confirmar-compra', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          idHorario: idHorarioSeleccionado,
          patente: busSeleccionado,
          horaSalida: horaSeleccionada,
          precio: String(precioTotal),
          fechaViaje: fechaSeleccionada,
          pasajeros,
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || 'No se pudo confirmar la compra');
      }

      localStorage.setItem('datosCompra', JSON.stringify(datosCompra));
      localStorage.setItem('compraConfirmada', JSON.stringify(payload));

      // Reemplazar la entrada actual del historial con la URL actual marcada como "procesada".
      // De este modo, si el usuario presiona Atrás desde la boleta, el navegador
      // no puede volver a este formulario con el modal de compra bloqueando.
      history.replaceState({ compraRealizada: true }, '', window.location.href);

      mostrarMensajeExito();
      setTimeout(() => {
        // Usar replace para que /boleta sustituya /compra-pasajes en el historial;
        // así el botón Atrás desde la boleta va directo al home.
        window.location.replace('/boleta');
      }, 1500);
    } catch (error) {
      alert(error.message);
    }
  });

  function renderizarPasajeros(asientos) {
    pasajerosContainer.innerHTML = '';
    asientos.forEach((asiento, index) => {
      const card = document.createElement('div');
      card.className = 'cp-pasajero-card';
      card.innerHTML = `
        <div class="cp-pasajero-card__header">
          <h3>Pasajero ${index + 1}</h3>
          <span class="cp-pasajero-card__asiento">Asiento ${asiento}</span>
        </div>
        <input type="hidden" name="asiento[]" value="${asiento}" />
        <div class="cp-form__grid">
          <div class="cp-field cp-field--full">
            <label>Nombre completo</label>
            <input type="text" name="nombre[]" placeholder="Ej. María Pérez" required />
          </div>
          <div class="cp-field">
            <label>RUT</label>
            <input type="text" name="rut[]" placeholder="12.345.678-9" required />
          </div>
          <div class="cp-field">
            <label>Correo electrónico</label>
            <input type="email" name="email[]" placeholder="correo@ejemplo.cl" required />
          </div>
          <div class="cp-field">
            <label>Teléfono</label>
            <input type="tel" name="telefono[]" placeholder="+56 9 1234 5678" />
          </div>
          <div class="cp-field">
            <label>Tipo de pasaje</label>
            <select name="tipo_pasaje[]">
              <option value="adulto">Adulto</option>
              <option value="estudiante">Estudiante</option>
              <option value="tercera-edad">Tercera edad</option>
              <option value="nino">Niño</option>
            </select>
          </div>
          <div class="cp-field cp-field--full">
            <label>Observaciones</label>
            <textarea name="observaciones[]" placeholder="Necesidades especiales, equipaje, etc."></textarea>
          </div>
        </div>
      `;
      pasajerosContainer.appendChild(card);
    });
  }

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
