/* ================================================================
   RECUPERAR.JS — Solicitar enlace de recuperación de contraseña
   ================================================================ */

(function initRecuperar() {
  const form = document.getElementById('recuperarForm');
  if (!form) return;

  function getMsgContainer() {
    let c = document.getElementById('recuperarMsg');
    if (!c) {
      c = document.createElement('div');
      c.id = 'recuperarMsg';
      form.parentNode.insertBefore(c, form.nextSibling);
    }
    return c;
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = document.getElementById('email').value.trim();
    const msg   = getMsgContainer();
    msg.textContent = '';
    msg.className = '';

    if (!email) {
      msg.textContent = 'Ingresa tu correo electrónico.';
      msg.className = 'msg-error';
      return;
    }

    const btn = document.getElementById('btnRecuperar');
    const textoOriginal = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="bx bx-loader-alt bx-spin"></i> Enviando...';

    try {
      const res = await fetch('/api/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      const data = await res.json();

      if (res.ok) {
        msg.className = 'msg-exito';
        msg.textContent = data.message || 'Revisa tu correo.';

        // En desarrollo (sin SMTP) el backend devuelve el enlace para probar.
        if (data.reset_url) {
          const p = document.createElement('p');
          p.style.marginTop = '10px';
          p.style.fontSize = '0.8rem';
          p.innerHTML = 'Modo desarrollo — usa este enlace: ' +
            '<a href="' + data.reset_url + '">restablecer contraseña</a>';
          msg.appendChild(p);
        }
      } else {
        msg.className = 'msg-error';
        msg.textContent = data.error || 'No se pudo procesar la solicitud.';
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
