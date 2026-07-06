/* ================================================================
   HOME.JS  –  Talmocur página de inicio
   ================================================================ */


/* ── 1. FECHA DE HOY en la sección de pasajes ────────────────── */
(function setFechaHoy() {
  const el = document.getElementById('fechaHoy');
  if (!el) return;

  const params = new URLSearchParams(window.location.search);
  const fechaParam = params.get('fecha');
  const fechaBase = fechaParam ? new Date(`${fechaParam}T00:00:00`) : new Date();
  const opciones = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
  el.textContent = fechaBase.toLocaleDateString('es-CL', opciones);
})();


/* ── 2. FECHA MÍNIMA en el input de fecha (no permite fechas pasadas) */
(function setMinFecha() {
  const input = document.getElementById('fecha');
  if (!input) return;

  const hoy = new Date().toISOString().split('T')[0];
  const params = new URLSearchParams(window.location.search);
  const fechaParam = params.get('fecha');
  const valorInicial = fechaParam || input.value || hoy;

  input.setAttribute('min', hoy);
  input.value = valorInicial;
})();


/* ── 3. SWAP origen ↔ destino + filtrado inteligente ────────── */
(function initSwap() {
  const btn     = document.querySelector('.buscador__swap');
  const origen  = document.getElementById('origen');
  const destino = document.getElementById('destino');
  if (!btn || !origen || !destino) return;

  const mappingDestinos = {
    'Curicó': ['Talca', 'Molina', 'Itahue'],
    'Talca': ['Curicó', 'San Rafael', 'Molina']
  };

  /**
   * Sincroniza las opciones del select destino para que correspondan
   * con las ciudades destino permitidas según el origen seleccionado.
   */
  function sincronizarDestino() {
    const valorOrigen  = origen.value;
    const selectedDest = destino.getAttribute('data-selected') || destino.value;
    destino.removeAttribute('data-selected'); // Limpiar para futuros cambios

    // Limpiar opciones
    destino.innerHTML = '<option value="">Seleccionar destino</option>';

    if (valorOrigen && mappingDestinos[valorOrigen]) {
      mappingDestinos[valorOrigen].forEach(ciudad => {
        const opt = document.createElement('option');
        opt.value = ciudad;
        opt.textContent = ciudad;
        if (ciudad === selectedDest) {
          opt.selected = true;
        }
        destino.appendChild(opt);
      });
    }
  }

  // Sincronizar al cambiar origen
  origen.addEventListener('change', sincronizarDestino);

  // Botón intercambiar
  btn.addEventListener('click', () => {
    const tempOrigen = origen.value;
    const tempDestino = destino.value;

    origen.value = tempDestino;
    destino.setAttribute('data-selected', tempOrigen);
    sincronizarDestino();
  });

  // Ejecutar al cargar para estado inicial correcto
  sincronizarDestino();
})();


/* ── 4. NAVBAR: sombra al hacer scroll ───────────────────────── */
(function initNavbarScroll() {
  const navbar = document.getElementById('navbar');
  if (!navbar) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 10) {
      navbar.style.boxShadow = '0 4px 20px rgba(29, 78, 216, 0.35)';
    } else {
      navbar.style.boxShadow = '0 2px 12px rgba(29, 78, 216, 0.25)';
    }
  }, { passive: true });
})();


/* ── 5. MODAL DE LOGIN: abrir / cerrar ───────────────────────── */
(function initLoginModal() {
  const overlay  = document.getElementById('loginOverlay');
  const modal    = document.getElementById('loginModal');
  const openBtn  = document.getElementById('openLogin');

  if (!overlay || !modal || !openBtn) return;

  /* Bloquea el scroll del body mientras el modal está abierto */
  function lockScroll()   { document.body.style.overflow = 'hidden'; }
  function unlockScroll() { document.body.style.overflow = '';       }

  /* Abre el modal */
  function openModal() {
    overlay.classList.add('is-visible');
    modal.classList.add('is-visible');
    modal.setAttribute('aria-hidden', 'false');
    lockScroll();

    /* Foco accesible: mueve el foco al primer campo */
    const firstInput = modal.querySelector('input');
    if (firstInput) setTimeout(() => firstInput.focus(), 50);
  }

  /* Cierra el modal */
  function closeModal() {
    overlay.classList.remove('is-visible');
    modal.classList.remove('is-visible');
    modal.setAttribute('aria-hidden', 'true');
    unlockScroll();
    openBtn.focus();   /* devuelve el foco al botón que lo abrió */
  }

  /* Eventos de apertura */
  openBtn.addEventListener('click', (e) => {
    e.preventDefault();
    openModal();
  });

  /* Cerrar al hacer clic en el overlay */
  overlay.addEventListener('click', closeModal);

  /* Cerrar con tecla Escape */
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('is-visible')) {
      closeModal();
    }
  });
})();


/* ── 6. TOGGLE MOSTRAR / OCULTAR CONTRASEÑA ─────────────────── */
(function initTogglePassword() {
  const btn      = document.getElementById('togglePassword');
  const input    = document.getElementById('password');
  const icon     = document.getElementById('toggleIcon');

  if (!btn || !input || !icon) return;

  btn.addEventListener('click', () => {
    const isHidden = input.type === 'password';
    input.type     = isHidden ? 'text' : 'password';
    icon.className = isHidden ? 'bx bxs-hide' : 'bx bxs-show';
    btn.setAttribute('aria-label', isHidden ? 'Ocultar contraseña' : 'Mostrar contraseña');
  });
})();


/* ── 7. AVISOS: toast deslizante desde la derecha ────────────── */
(function initAvisosToast() {

  const contenedor = document.getElementById('avisoToastContenedor');
  if (!contenedor) return;  // Usuario no logueado: nada que hacer

  const TIPO_META = {
    alerta:     { icono: 'bx-error',             label: 'Alerta',           clase: 'aviso-toast--alerta' },
    info:       { icono: 'bx-info-circle',       label: 'Información',      clase: 'aviso-toast--info' },
    precio:     { icono: 'bx-dollar-circle',     label: 'Cambio de tarifa', clase: 'aviso-toast--precio' },
    emergencia: { icono: 'bx-alarm-exclamation', label: 'Emergencia',       clase: 'aviso-toast--emergencia' },
  };

  let cola       = [];
  let timerId    = null;
  let toastActual = null;

  /**
   * Muestra el siguiente aviso de la cola.
   * Si no hay más, no hace nada.
   */
  function mostrarSiguiente() {
    if (cola.length === 0) return;
    const aviso = cola.shift();
    mostrarToast(aviso);
  }

  /**
   * Crea y anima un toast para un aviso dado.
   * Se cierra solo a los 10 s o al pulsar ×.
   */
  function mostrarToast(aviso) {
    const meta = TIPO_META[aviso.tipo] || TIPO_META.info;

    const toast = document.createElement('div');
    toast.className = `aviso-toast ${meta.clase}`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
      <div class="aviso-toast__cabecera">
        <span class="aviso-toast__tipo">
          <i class='bx ${meta.icono}'></i>
          ${meta.label}
        </span>
        <button class="aviso-toast__cerrar" aria-label="Cerrar aviso">
          <i class='bx bx-x'></i>
        </button>
      </div>
      <p class="aviso-toast__titulo">${aviso.titulo}</p>
      <p class="aviso-toast__mensaje">${aviso.mensaje}</p>
      <div class="aviso-toast__barra-wrap">
        <div class="aviso-toast__barra"></div>
      </div>
    `;

    contenedor.appendChild(toast);
    toastActual = toast;

    // Forzar reflow para que la animación de entrada funcione
    toast.getBoundingClientRect();
    toast.classList.add('aviso-toast--visible');

    // Función para cerrar y mostrar el siguiente
    function cerrar() {
      clearTimeout(timerId);
      toast.classList.remove('aviso-toast--visible');
      toast.classList.add('aviso-toast--saliendo');
      toast.addEventListener('transitionend', () => {
        toast.remove();
        toastActual = null;
        // Pequeña pausa antes de mostrar el siguiente
        setTimeout(mostrarSiguiente, 400);
      }, { once: true });
    }

    // Botón × para cerrar
    toast.querySelector('.aviso-toast__cerrar').addEventListener('click', cerrar);

    // Auto-cierre a los 10 segundos
    timerId = setTimeout(cerrar, 10000);
  }

  // Obtener los avisos vigentes del servidor
  fetch('/api/avisos/activos')
    .then(r => r.json())
    .then(data => {
      if (!data.avisos || data.avisos.length === 0) return;
      cola = data.avisos;
      // Pequeño delay para que el usuario vea la página primero
      setTimeout(mostrarSiguiente, 800);
    })
    .catch(() => {
      // Si falla silenciosamente, simplemente no se muestran avisos
    });

})();

