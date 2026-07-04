# Trazabilidad de Requisitos vs Implementación

Seguimiento del estado de implementación de cada requisito definido en `requisitos.md`.

**Última actualización:** 3 de julio de 2026

## Requisitos Funcionales

| ID | Descripción | Prioridad | Estado | Observaciones |
|:---|:------------|:---------:|:------:|:--------------|
| REQ-F01 | Consulta de horarios y tarifas | Alta | ✅ Cumplido | El buscador del home carga origen/destino dinámicamente desde la BD. La página `/tarifas` muestra tarifas reales y las tarjetas de pasaje permiten iniciar el flujo de selección de asientos. |
| REQ-F02 | Reserva y compra de pasajes | Alta | ✅ Cumplido | Flujo interactivo completo de selección de asientos (`templates/compra_pasajes_asientos.html`) e integración con `/api/confirmar-compra` para persistir la compra en la BD SQLite y generar boleta. |
| REQ-F03 | Panel de administrador | Alta | ✅ Cumplido | Panel desarrollado en `/admin` para gestionar la flota de buses (con autogeneración de asientos), configurar horarios/precios con validación de conflictos, y enviar comunicados (avisos) activos. |
| REQ-F04 | Login y control de acceso con roles | Alta | ✅ Cumplido | Autenticación de usuarios con hasheo bcrypt. El sistema discrimina el rol del usuario, redirigiendo al administrador al panel `/admin` y a los clientes al portal principal. APIs del panel administrativo protegidas. |
| REQ-F05 | Beneficios y descuentos | Baja | ❌ No iniciado | Se planea crear una pestaña dedicada a futuro. |

## Requisitos No Funcionales

| ID | Descripción | Prioridad | Estado | Observaciones |
|:---|:------------|:---------:|:------:|:--------------|
| REQ-NF01 | Contraseñas cifradas | Alta | ✅ Cumplido | Las contraseñas se hashean con bcrypt antes de guardarlas. Ninguna contraseña se almacena en texto plano. Verificado en `backend/db_sqlite.py` y `backend/routes.py`. |
| REQ-NF02 | Paleta de colores accesible | Media | ✅ Cumplido | El CSS utiliza variables de color consistentes con buen contraste. |
| REQ-NF03 | Idioma Exclusivo en Español | Media | ✅ Cumplido | Toda la interfaz está en español. |

## Leyenda

| Símbolo | Significado |
|:-------:|:------------|
| ✅ | Cumplido |
| 🟡 | Parcial — existe avance pero no es funcional o completo |
| ❌ | No iniciado |

## Archivos clave por requisito

| ID | Archivos relevantes |
|:---|:--------------------|
| REQ-F01 | `backend/models.py` (Recorrido, HorarioViaje), `backend/app.py` (/api/origenes, /api/recorridos), `templates/home.html`, `templates/tarifas.html`, `static/js/home.js` |
| REQ-F02 | `templates/compra_pasajes.html`, `templates/compra_pasajes_asientos.html`, `templates/boleta.html`, `static/js/asientos.js`, `static/js/compra_pasajes.js`, `static/js/boleta.js`, `backend/routes.py` (/api/confirmar-compra), `backend/models.py` (Compra, AsientoComprado) |
| REQ-F03 | `templates/admin.html`, `backend/app.py` (rutas /admin, /api/buses, /api/horarios, /api/avisos), [panel_administracion.md](file:///c:/Users/dipez/OneDrive/Documentos/Universidad/Metodoogias/Proyecto/panel_administracion.md) |
| REQ-F04 | `backend/routes.py` (rutas /api/login, /api/register, /api/me), `backend/db_sqlite.py`, `backend/utils.py`, `templates/login.html`, `templates/registro.html` |
| REQ-NF01 | `backend/routes.py` (hasheo en `/api/register`), `backend/db_sqlite.py` |

