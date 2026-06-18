/* ================================================================
   NAVBAR.JS — Lógica global del menú de usuario
   ================================================================ */

(function initUsuarioMenu() {
  const btn      = document.getElementById('btnUsuarioMenu');
  const dropdown = document.getElementById('usuarioDropdown');
  const btnLogout = document.getElementById('btnCerrarSesion');

  // Si no hay menú de usuario (no logueado), salir
  if (!btn || !dropdown) return;

  /* ── Toggle dropdown ─────────────────────────────────────────── */
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = dropdown.classList.contains('usuario-menu__dropdown--abierto');

    if (isOpen) {
      dropdown.classList.remove('usuario-menu__dropdown--abierto');
      btn.setAttribute('aria-expanded', 'false');
    } else {
      dropdown.classList.add('usuario-menu__dropdown--abierto');
      btn.setAttribute('aria-expanded', 'true');
    }
  });

  /* ── Cerrar al hacer click fuera ─────────────────────────────── */
  document.addEventListener('click', (e) => {
    if (!btn.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.remove('usuario-menu__dropdown--abierto');
      btn.setAttribute('aria-expanded', 'false');
    }
  });

  /* ── Cerrar sesión ───────────────────────────────────────────── */
  if (btnLogout) {
    btnLogout.addEventListener('click', async () => {
      try {
        const response = await fetch('/api/logout', { method: 'POST' });
        if (response.ok) {
          window.location.href = '/';
        }
      } catch (err) {
        console.error('Error al cerrar sesión:', err);
        window.location.href = '/';
      }
    });
  }
})();
