# Trazabilidad de Requisitos vs Implementación

Seguimiento del estado de implementación de cada requisito definido en `requisitos.md`.

**Última actualización:** 22 de mayo de 2025

## Requisitos Funcionales

| ID | Descripción | Prioridad | Estado | Observaciones |
|:---|:------------|:---------:|:------:|:--------------|
| REQ-F01 | Consulta de horarios y tarifas | Alta | 🟡 Parcial | La UI del buscador existe en el home (origen, destino, fecha, pasajeros) pero no es funcional. Requiere base de datos |
| REQ-F02 | Reserva y compra de pasajes | Alta | 🟡 Parcial | Tarjetas de pasajes existen en el home de forma visual (estáticas, datos hardcodeados). Requiere base de datos |
| REQ-F03 | Panel de administrador | Alta | ❌ No iniciado | — |
| REQ-F04 | Login y control de acceso con roles | Alta | 🟡 Parcial | Vistas de login y registro creadas. Backend no funcional, a la espera de base de datos |
| REQ-F05 | Beneficios y descuentos | Baja | ❌ No iniciado | Se planea crear una pestaña dedicada a futuro |

## Requisitos No Funcionales

| ID | Descripción | Prioridad | Estado | Observaciones |
|:---|:------------|:---------:|:------:|:--------------|
| REQ-NF01 | Contraseñas cifradas | Alta | ❌ No iniciado | Se implementará junto con la base de datos |
| REQ-NF02 | Paleta de colores accesible | Media | ✅ Cumplido | El CSS utiliza variables de color consistentes con buen contraste |
| REQ-NF03 | Interfaz en español | Media | ✅ Cumplido | Toda la interfaz está en español |

## Leyenda

| Símbolo | Significado |
|:-------:|:------------|
| ✅ | Cumplido |
| 🟡 | Parcial — existe avance pero no es funcional |
| ❌ | No iniciado |
