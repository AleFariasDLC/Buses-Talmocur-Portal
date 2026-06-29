/* ================================================================
   PERFIL.JS — Cargar y editar los datos del usuario
   ================================================================ */

(function initPerfil() {
  const form      = document.getElementById('perfilForm');
  const cargando  = document.getElementById('perfilCargando');
  if (!form) return;

  const inputNombre  = document.getElementById('nombre');
  const inputEmail   = document.getElementById('email');
  const fechaReg     = document.getElementById('fechaRegistro');
  const btn          = document.getElementById('btnGuardar');

  /* ── Crear/obtener contenedor de mensajes ── */
  function getMsgContainer() {
    let c = document.getElementById('perfilMsg');
    if (!c) {
      c = document.createElement('div');
      c.id = 'perfilMsg';
      form.parentNode.insertBefore(c, form.nextSibling);
    }
    return c;
  }
  function mostrarMensaje(texto, tipo) {
    const c = getMsgContainer();
    c.textContent = texto;
    c.className = (tipo === 'exito') ? 'msg-exito' : 'msg-error';
  }

  /* ── 1. Cargar datos del usuario (GET /api/me) ── */
  async function cargarPerfil() {
    try {
      const res = await fetch('/api/me');
      if (res.status === 401) {
        // No hay sesión → al login
        window.location.href = '/login';
        return;
      }
      if (!res.ok) {
        cargando.textContent = 'No se pudieron cargar tus datos.';
        return;
      }
      const data = await res.json();
      const u = data.usuario;

      inputNombre.value = u.nombre || '';
      inputEmail.value  = u.email || '';

      if (u.fecha_registro) {
        const f = new Date(u.fecha_registro);
        fechaReg.textContent = f.toLocaleDateString('es-CL', {
          year: 'numeric', month: 'long', day: 'numeric'
        });
      }

      cargando.hidden = true;
      form.hidden = false;
    } catch (err) {
      cargando.textContent = 'Error de conexión al cargar tus datos.';
    }
  }

  /* ── 2. Validación visual de la nueva contraseña ── */
  (function initPasswordCriteria() {
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

  /* ── 3. Guardar cambios (PUT /api/me) ── */
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    mostrarMensaje('', 'exito');
    getMsgContainer().className = '';

    const nombre = inputNombre.value.trim();
    const email  = inputEmail.value.trim();

    if (!nombre || !email) {
      mostrarMensaje('Nombre y correo son obligatorios.', 'error');
      return;
    }

    const payload = { nombre, email };

    // Campos de contraseña (solo si el usuario quiere cambiarla)
    const actual  = document.getElementById('currentPassword').value;
    const nueva   = document.getElementById('password').value;
    const confirm = document.getElementById('confirmPassword').value;

    if (nueva || confirm || actual) {
      if (!actual) {
        mostrarMensaje('Ingresa tu contraseña actual para cambiarla.', 'error');
        return;
      }
      if (nueva !== confirm) {
        mostrarMensaje('Las contraseñas nuevas no coinciden.', 'error');
        return;
      }
      payload.currentPassword = actual;
      payload.password = nueva;
      payload.confirmPassword = confirm;
    }

    const textoOriginal = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="bx bx-loader-alt bx-spin"></i> Guardando...';

    try {
      const res = await fetch('/api/me', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (res.ok) {
        mostrarMensaje(data.message || 'Perfil actualizado.', 'exito');
        // Limpiar campos de contraseña
        document.getElementById('currentPassword').value = '';
        document.getElementById('password').value = '';
        document.getElementById('confirmPassword').value = '';
        document.getElementById('passwordCriteria').innerHTML = '';
      } else {
        mostrarMensaje(data.error || 'No se pudo guardar.', 'error');
      }
    } catch (err) {
      mostrarMensaje('Error de conexión. Intenta de nuevo.', 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = textoOriginal;
    }
  });

  cargarPerfil();
})();
