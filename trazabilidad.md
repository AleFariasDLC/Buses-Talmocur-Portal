# Trazabilidad de Requisitos vs Implementación

Seguimiento del estado de implementación de cada requisito definido en `requisitos.md`.

**Última actualización:** 18 de junio de 2026

## Requisitos Funcionales

| ID | Descripción | Prioridad | Estado | Observaciones |
|:---|:------------|:---------:|:------:|:--------------|
| REQ-F01 | Consulta de horarios y tarifas | Alta | 🟡 Parcial | El buscador del home carga origen/destino desde la BD. La página `/tarifas` muestra tarifas reales desde la BD. Falta conectar búsqueda por fecha y mostrar resultados de horarios. |
| REQ-F02 | Reserva y compra de pasajes | Alta | 🟡 Parcial | Tarjetas de pasajes en el home de forma visual (datos estáticos). Requiere completar horarios en BD y lógica de compra. |
| REQ-F03 | Panel de administrador | Alta | ❌ No iniciado | — |
| REQ-F04 | Login y control de acceso con roles | Alta | 🟡 Parcial | Login y registro funcionales con BD SQLite. Hasheo bcrypt activo. Falta distinguir rol `admin` vs `pasajero` en la UI. |
| REQ-F05 | Beneficios y descuentos | Baja | ❌ No iniciado | Se planea crear una pestaña dedicada a futuro. |

## Requisitos No Funcionales

| ID | Descripción | Prioridad | Estado | Observaciones |
|:---|:------------|:---------:|:------:|:--------------|
| REQ-NF01 | Contraseñas cifradas | Alta | ✅ Cumplido | Las contraseñas se hashean con bcrypt antes de guardarlas. Ninguna contraseña se almacena en texto plano. Verificado en `backend/db_sqlite.py` y `backend/routes.py`. |
| REQ-NF02 | Paleta de colores accesible | Media | ✅ Cumplido | El CSS utiliza variables de color consistentes con buen contraste. |
| REQ-NF03 | Interfaz en español | Media | ✅ Cumplido | Toda la interfaz está en español. |

## Leyenda

| Símbolo | Significado |
|:-------:|:------------|
| ✅ | Cumplido |
| 🟡 | Parcial — existe avance pero no es funcional o completo |
| ❌ | No iniciado |

## Archivos clave por requisito

| ID | Archivos relevantes |
|:---|:--------------------|
| REQ-F01 | `backend/models.py` (Recorrido, HorarioViaje), `backend/app.py` (/api/origenes), `templates/home.html`, `templates/tarifas.html` |
| REQ-F02 | `templates/home.html`, `backend/models.py` (Compra, AsientoComprado) |
| REQ-F03 | — (pendiente) |
| REQ-F04 | `backend/routes.py`, `backend/db_sqlite.py`, `backend/utils.py`, `templates/login.html`, `templates/registro.html` |
| REQ-NF01 | `backend/routes.py` (hasheo en `/api/register`), `backend/db_sqlite.py` |
