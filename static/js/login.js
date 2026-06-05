/* ================================================================
   LOGIN.JS –  Talmocur página de login
   ================================================================ */

<<<<<<< HEAD
 /* ── 1. VALIDACIÓN DE USUARIO ───────────── */
(function initLoginValidation() {
    const form = document.getElementById('loginForm');
    if (!form) return;
    form.addEventListener('submit', (e) => {
        const username = form.username.value.trim();
        const password = form.password.value.trim();
        if (!username || !password) {
            e.preventDefault();
            alert('Por favor, ingresa tu usuario y contraseña');
        }
    });
})();

=======
/* ── 1. TOGGLE CONTRASEÑA ────────────────────────────────────── */
(function initPasswordToggle() {
  const toggleBtn     = document.getElementById('togglePassword');
  const passwordInput = document.getElementById('password');
  const toggleIcon    = document.getElementById('toggleIcon');
  if (!toggleBtn || !passwordInput) return;

  toggleBtn.addEventListener('click', () => {
    const isPassword = passwordInput.type === 'password';
    passwordInput.type = isPassword ? 'text' : 'password';
    toggleIcon.className = isPassword ? 'bx bxs-hide' : 'bx bxs-show';
  });
})();

/* ── 2. ENVÍO DEL FORMULARIO DE LOGIN ────────────────────────── */
(function initLoginSubmit() {
  const form = document.getElementById('loginForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const email    = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    // Obtener o crear contenedor de mensajes
    let msgContainer = document.getElementById('loginMsg');
    if (!msgContainer) {
      msgContainer = document.createElement('div');
      msgContainer.id = 'loginMsg';
      form.parentNode.insertBefore(msgContainer, form.nextSibling);
    }

    // Limpiar mensajes previos
    msgContainer.textContent = '';
    msgContainer.className = '';

    // Validación básica del lado del cliente
    if (!email || !password) {
      msgContainer.textContent = 'Correo y contraseña son obligatorios.';
      msgContainer.className = 'msg-error';
      return;
    }

    // Deshabilitar botón mientras se procesa
    const btn = document.getElementById('btnLogin');
    const textoOriginal = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="bx bx-loader-alt bx-spin"></i> Iniciando sesión...';

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (response.ok) {
        msgContainer.textContent = `¡Bienvenido, ${data.usuario.nombre}! Redirigiendo...`;
        msgContainer.className = 'msg-exito';

        // Redirigir a la página principal después de 1.5 segundos
        setTimeout(() => {
          window.location.href = '/';
        }, 1500);
      } else {
        msgContainer.textContent = data.error || 'Error al iniciar sesión.';
        msgContainer.className = 'msg-error';
        btn.disabled = false;
        btn.innerHTML = textoOriginal;
      }
    } catch (err) {
      msgContainer.textContent = 'Error de conexión. Intenta de nuevo.';
      msgContainer.className = 'msg-error';
      btn.disabled = false;
      btn.innerHTML = textoOriginal;
    }
  });
})();
>>>>>>> 6cd218dc9d4b17b0eb39e6b38b87188b139ec1b8
