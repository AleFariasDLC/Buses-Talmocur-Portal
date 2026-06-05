/* ================================================================
   LOGIN.JS –  Talmocur página de login
   ================================================================ */

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

