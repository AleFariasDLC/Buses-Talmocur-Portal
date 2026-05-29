/* ================================================================
   REGISTRO.JS –  Talmocur página de registro
   ================================================================ */

   /* ── 1. VALIDACIÓN DE CONTRASEÑA: mostrar / ocultar ───────────── */
   (function initPasswordToggle() {
    const toggle = document.getElementById('togglePassword');
    const input  = document.getElementById('password');
    if (!toggle || !input) return;
    toggle.addEventListener('click', () => {
      const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
      input.setAttribute('type', type);
      toggle.textContent = type === 'password' ? 'Mostrar' : 'Ocultar';
    }  );
  })();

/* ── 2. VALIDACIÓN DE CONTRASEÑA: requisitos ─────────────────────── */
(function initPasswordValidation() {
  const passwordInput = document.getElementById('password');
  const criteriaList  = document.getElementById('passwordCriteria');
  if (!passwordInput || !criteriaList) return;
    const criteria = {
        length: { regex: /.{8,}/, message: 'Al menos 8 caracteres' },
        uppercase: { regex: /[A-Z]/, message: 'Una letra mayúscula' },
        lowercase: { regex: /[a-z]/, message: 'Una letra minúscula' },
        number: { regex: /[0-9]/, message: 'Un número' },
        special: { regex: /[!@#$%^&*(),.?":{}|<>]/, message: 'Un carácter especial' }
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
/* ── 3. VALIDACIÓN DE CONTRASEÑA: confirmar contraseña ───────────── */
(function initConfirmPassword() {
  const passwordInput = document.getElementById('password');
  const confirmInput  = document.getElementById('confirmPassword');
    if (!passwordInput || !confirmInput) return;
    const errorMsg = document.getElementById('confirmError');
    confirmInput.addEventListener('input', () => {
        if (confirmInput.value !== passwordInput.value) {
            errorMsg.textContent = 'Las contraseñas no coinciden';
            errorMsg.style.color = 'red';
        } else {
            errorMsg.textContent = '';
            errorMsg.style.color = 'green';
        }
    });
})();

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