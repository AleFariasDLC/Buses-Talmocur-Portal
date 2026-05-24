/* ================================================================
   HOME.JS  –  Talmocur página de inicio
   ================================================================ */


/* ── 1. FECHA DE HOY en la sección de pasajes ────────────────── */
(function setFechaHoy() {
  const el = document.getElementById('fechaHoy');
  if (!el) return;

  const hoy = new Date();
  const opciones = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
  el.textContent = hoy.toLocaleDateString('es-CL', opciones);
})();


/* ── 2. FECHA MÍNIMA en el input de fecha (no permite fechas pasadas) */
(function setMinFecha() {
  const input = document.getElementById('fecha');
  if (!input) return;

  const hoy = new Date().toISOString().split('T')[0];
  input.setAttribute('min', hoy);
  input.value = hoy;
})();


/* ── 3. SWAP origen ↔ destino ────────────────────────────────── */
(function initSwap() {
  const btn     = document.querySelector('.buscador__swap');
  const origen  = document.getElementById('origen');
  const destino = document.getElementById('destino');
  if (!btn || !origen || !destino) return;

  btn.addEventListener('click', () => {
    const temp    = origen.value;
    origen.value  = destino.value;
    destino.value = temp;
  });
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
