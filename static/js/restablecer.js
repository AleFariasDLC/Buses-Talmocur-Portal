/* ================================================================
   RESTABLECER.JS — Definir nueva contraseña usando el token del correo
   ================================================================ */

/* ── Toggle mostrar/ocultar contraseña ── */
(function initToggle() {
  const toggle = document.getElementById('togglePassword');
  const input  = document.getElementById('password');
  const icon   = document.getElementById('toggleIcon');
  if (!toggle || !input) return;
  toggle.addEventListener('click', () => {
    const isPwd = input.type === 'password';
    input.type = isPwd ? 'text' : 'password';
    icon.className = isPwd ? 'bx bxs-hide' : 'bx bxs-show';
  });
})();

/* ── Criterios de contraseña en vivo ── */
(function initCriteria() {
  const passwordInput = document.getElementById('password');
  const criteriaList  = document.getElementById('passwordCriteria');
  if (!passwordInput || !criteriaList) return;
  const criteria = {
    length:    { regex: /.{8,}/,                    message: 'Al menos 8 caracteres' },
    uppercase: { regex: /[A-Z]/,                    message: 'Una letra mayúscula' },
    lowercase: { regex: /[a-z]/,                    message: 'Una letra minúscula' },
    number:    { regex: /[0-9]/,                    message: 'Un número' },
    special:   { regex: /[!@#$%^&*()\-_,.?":{}|<>]/, message: 'Un carácter especial' }
  };
  passwordInput.addEventListener('input', () => {
    const value = passwordInput.value;
    criteriaList.innerHTML = '';
    if (!value) return;
    for (const key in criteria) {
      const { regex, message } = criteria[key];
      const li = document.createElement('li');
      li.textContent = message;
      li.style.color = regex.test(value) ? 'green' : 'red';
      criteriaList.appendChild(li);
    }
  });
})();

/* ── Envío del formulario ── */
(function initSubmit() {
  const form = document.getElementById('restablecerForm');
  if (!form) return;

  // Leer token de la URL: /restablecer?token=XXXX
  const params = new URLSearchParams(window.location.search);
  const token = params.get('token') || '';

  function getMsgContainer() {
    let c = document.getElementById('restablecerMsg');
    if (!c) {
      c = document.createElement('div');
      c.id = 'restablecerMsg';
      form.parentNode.insertBefore(c, form.nextSibling);
    }
    return c;
  }

  // Si no hay token, avisar de inmediato
  if (!token) {
    const msg = getMsgContainer();
    msg.className = 'msg-error';
    msg.textContent = 'Enlace inválido. Solicita un nuevo correo de recuperación.';
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const password = document.getElementById('password').value;
    const confirm  = document.getElementById('confirmPassword').value;
    const msg = getMsgContainer();
    msg.textContent = '';
    msg.className = '';

    if (!token) {
      msg.className = 'msg-error';
      msg.textContent = 'Enlace inválido. Solicita un nuevo correo de recuperación.';
      return;
    }
    if (password !== confirm) {
      msg.className = 'msg-error';
      msg.textContent = 'Las contraseñas no coinciden.';
      return;
    }

    const btn = document.getElementById('btnRestablecer');
    const textoOriginal = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="bx bx-loader-alt bx-spin"></i> Guardando...';

    try {
      const res = await fetch('/api/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, password, confirmPassword: confirm })
      });
      const data = await res.json();

      if (res.ok) {
        msg.className = 'msg-exito';
        msg.textContent = (data.message || 'Contraseña actualizada.') + ' Redirigiendo...';
        form.reset();
        document.getElementById('passwordCriteria').innerHTML = '';
        setTimeout(() => { window.location.href = '/login'; }, 2000);
      } else {
        msg.className = 'msg-error';
        msg.textContent = data.error || 'No se pudo restablecer la contraseña.';
        btn.disabled = false;
        btn.innerHTML = textoOriginal;
      }
    } catch (err) {
      msg.className = 'msg-error';
      msg.textContent = 'Error de conexión. Intenta de nuevo.';
      btn.disabled = false;
      btn.innerHTML = textoOriginal;
    }
  });
})();
