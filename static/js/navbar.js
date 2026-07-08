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

/* ================================================================
   Menú móvil
   ================================================================ */
(function initMenuMovil() {
  const btnMenuMovil = document.getElementById('btnMenuMovil');
  const menuMovil      = document.getElementById('menuMovil');
  const btnLogoutMovil = document.getElementById('btnCerrarSesionMovil');

  if (!btnMenuMovil || !menuMovil) return;

  /* ── Toggle menú ─────────────────────────────────────────────── */
  btnMenuMovil.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = menuMovil.classList.contains('abierto');

    if (isOpen) {
      cerrarMenuMovil();
    } else {
      abrirMenuMovil();
    }
  });

  function abrirMenuMovil() {
    menuMovil.classList.add('abierto');
    menuMovil.setAttribute('aria-hidden', 'false');
    btnMenuMovil.setAttribute('aria-expanded', 'true');
    btnMenuMovil.setAttribute('aria-label', 'Cerrar menú');
  }

  function cerrarMenuMovil() {
    menuMovil.classList.remove('abierto');
    menuMovil.setAttribute('aria-hidden', 'true');
    btnMenuMovil.setAttribute('aria-expanded', 'false');
    btnMenuMovil.setAttribute('aria-label', 'Abrir menú');
  }

  /* ── Cerrar al hacer click fuera ─────────────────────────────── */
  document.addEventListener('click', (e) => {
    const navbar = document.getElementById('navbar');
    if (navbar && !navbar.contains(e.target)) {
      cerrarMenuMovil();
    }
  });

  /* ── Cerrar al hacer click en un enlace del menú ─────────────── */
  menuMovil.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => cerrarMenuMovil());
  });

  /* ── Cerrar sesión desde menú móvil ──────────────────────────── */
  if (btnLogoutMovil) {
    btnLogoutMovil.addEventListener('click', async () => {
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
