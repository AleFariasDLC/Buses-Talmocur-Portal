/* ================================================================
   REGISTRO.JS –  Talmocur página de registro
   ================================================================ */

/* ── 1. TOGGLE CONTRASEÑA: mostrar / ocultar ───────────────────── */
(function initPasswordToggle() {
  const toggle = document.getElementById('togglePassword');
  const input  = document.getElementById('password');
  const icon   = document.getElementById('toggleIcon');
  if (!toggle || !input) return;
  toggle.addEventListener('click', () => {
    const isPassword = input.type === 'password';
    input.type = isPassword ? 'text' : 'password';
    icon.className = isPassword ? 'bx bxs-hide' : 'bx bxs-show';
  });
})();

/* ── 1b. TOGGLE CONFIRMAR CONTRASEÑA ─────────────────────────── */
(function initConfirmToggle() {
  const toggle = document.getElementById('toggleConfirm');
  const input  = document.getElementById('confirmPassword');
  const icon   = document.getElementById('toggleIconConfirm');
  if (!toggle || !input) return;
  toggle.addEventListener('click', () => {
    const isPassword = input.type === 'password';
    input.type = isPassword ? 'text' : 'password';
    icon.className = isPassword ? 'bx bxs-hide' : 'bx bxs-show';
  });
})();

/* ── 2. VALIDACIÓN DE CONTRASEÑA: requisitos ─────────────────── */
(function initPasswordValidation() {
  const passwordInput = document.getElementById('password');
  const criteriaList  = document.getElementById('passwordCriteria');
  if (!passwordInput || !criteriaList) return;
    const criteria = {
        length: { regex: /.{8,}/, message: 'Al menos 8 caracteres' },
        uppercase: { regex: /[A-Z]/, message: 'Una letra mayúscula' },
        lowercase: { regex: /[a-z]/, message: 'Una letra minúscula' },
        number: { regex: /[0-9]/, message: 'Un número' },
        special: { regex: /[!@#$%^&*()-_,.?":{}|<>]/, message: 'Un carácter especial' }
    };
    passwordInput.addEventListener('input', () => {
        const value = passwordInput.value;
        criteriaList.innerHTML = '';
        for (const key in criteria) {
            const { regex, message } = criteria[key];
            const isValid = regex.test(value);
            const li = document.createElement('li');
            li.textContent = message;
            li.style.color = isValid ? 'green' : 'red';
            criteriaList.appendChild(li);
        }
    });
})();

/* ── 3. (Validación de confirmar contraseña se hace solo al submit) ── */


/* ── 4. VALIDACIÓN DE CORREO ELECTRÓNICO ─────────────────────── */
(function initEmailValidation() {
  const emailInput = document.getElementById('email');
  if (!emailInput) return;
    const errorMsg = document.getElementById('emailError');
    emailInput.addEventListener('input', () => {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!regex.test(emailInput.value)) {
            errorMsg.textContent = 'Correo electrónico no válido';
            errorMsg.style.color = 'red';
        } else {
            errorMsg.textContent = '';
            errorMsg.style.color = 'green';
        }
    });
})();

<<<<<<< HEAD
/* ── 5. Evitar correos repetidos (simulación) ─────────────────────── */
(function initDuplicateEmailCheck() {
  const emailInput = document.getElementById('email');
  if (!emailInput) return;
    const errorMsg = document.getElementById('emailError');
    const existingEmails = ['user1@example.com', 'user2@example.com']; // Simulación de correos existentes
    emailInput.addEventListener('input', () => {
        if (existingEmails.includes(emailInput.value)) {
            errorMsg.textContent = 'Este correo electrónico ya está en uso';
            errorMsg.style.color = 'red';
        } else {
            errorMsg.textContent = '';
            errorMsg.style.color = 'green';
        }
    });
=======
/* ── 5. ENVÍO DEL FORMULARIO AL BACKEND ──────────────────────── */
(function initFormSubmit() {
  const form = document.getElementById('registroForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Obtener valores
    const nombre          = document.getElementById('nombre').value.trim();
    const email           = document.getElementById('email').value.trim();
    const password        = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    // Obtener o crear contenedor de mensajes
    let msgContainer = document.getElementById('registroMsg');
    if (!msgContainer) {
      msgContainer = document.createElement('div');
      msgContainer.id = 'registroMsg';
      form.parentNode.insertBefore(msgContainer, form.nextSibling);
    }

    // Limpiar mensajes previos
    msgContainer.textContent = '';
    msgContainer.className = '';
    const confirmError = document.getElementById('confirmError');
    if (confirmError) confirmError.textContent = '';

    // Validación rápida del lado del cliente
    if (!nombre || !email || !password || !confirmPassword) {
      msgContainer.textContent = 'Todos los campos son obligatorios.';
      msgContainer.className = 'msg-error';
      return;
    }

    if (password !== confirmPassword) {
      confirmError.textContent = 'Las contraseñas no coinciden.';
      confirmError.style.color = 'red';
      return;
    }

    // Deshabilitar botón mientras se procesa
    const btn = document.getElementById('btnRegistro');
    const textoOriginal = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="bx bx-loader-alt bx-spin"></i> Creando cuenta...';

    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre, email, password, confirmPassword })
      });

      const data = await response.json();

      if (response.ok) {
        msgContainer.textContent = '¡Cuenta creada exitosamente! Redirigiendo al login...';
        msgContainer.className = 'msg-exito';
        form.reset();

        // Redirigir al login después de 2 segundos
        setTimeout(() => {
          window.location.href = '/login';
        }, 2000);
      } else {
        msgContainer.textContent = data.error || 'Error al crear la cuenta.';
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
>>>>>>> 6cd218dc9d4b17b0eb39e6b38b87188b139ec1b8
})();