# Base de Datos — Talmocur

## Tecnología utilizada

| Componente | Tecnología |
|---|---|
| ORM (mapeo Python ↔ SQL) | SQLAlchemy 2.0 |
| Motor de BD (desarrollo) | SQLite (`data/talmocur.db`) |
| Migración futura posible | PostgreSQL / MySQL (solo cambiar 1 línea en `database.py`) |

El archivo de la base de datos se genera automáticamente en `data/talmocur.db` al correr el servidor por primera vez. **No se sube al repositorio** (está en `.gitignore`). La carpeta `data/` sí existe en el repo gracias a un archivo `.gitkeep`.

---

## Estructura de tablas

### 1. `usuario`
Almacena las cuentas de todos los usuarios del sistema (pasajeros y administradores).
Reemplaza al archivo `data/usuarios.json` que se usó durante el desarrollo inicial.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | String(36) PK | UUID generado automáticamente |
| `nombre` | String(100) | Nombre completo |
| `email` | String(100) UNIQUE | Correo electrónico, usado para el login |
| `password_hash` | String(200) | Contraseña encriptada con bcrypt |
| `fecha_registro` | DateTime | Fecha y hora de creación de la cuenta |
| `rol` | String(20) | `"pasajero"` o `"admin"` |

> El campo `rol` permite distinguir en el futuro a los administradores de los pasajeros sin necesitar tablas separadas para cada tipo de usuario.

---

### 2. `bus`
Representa un bus físico de la flota de Talmocur.

| Campo | Tipo | Descripción |
|---|---|---|
| `patente` | String(10) PK | Identificador único del bus (ej: `"ABCD12"`) |
| `capacidad` | Integer | Cantidad total de asientos del bus |
| `modelo` | String(100) | Modelo del vehículo (opcional) |
| `estado` | String(50) | `"Activo"` o `"En mantención"` |

> Un bus tiene asociados tantos registros en `asiento` como indique su `capacidad`.

---

### 3. `asiento`
Representa un asiento físico dentro de un bus. Son registros estáticos — se crean una vez cuando se ingresa el bus al sistema y no cambian.

| Campo | Tipo | Descripción |
|---|---|---|
| `id_asiento` | Integer PK | Identificador único |
| `numero` | Integer | Número del asiento (1, 2, 3… hasta `bus.capacidad`) |
| `patente` | String(10) FK → `bus` | A qué bus pertenece este asiento |

**¿Por qué los asientos no están "dentro" del bus?**
En bases de datos relacionales no es posible guardar listas dentro de una fila. En cambio, cada asiento guarda una referencia a su bus (`patente`). El resultado es equivalente: desde Python, `bus.asientos` devuelve la lista completa de asientos de ese bus.

**Disponibilidad de un asiento:** un asiento NO tiene campo `ocupado` o `disponible`. La disponibilidad se determina en tiempo real consultando si ese asiento aparece en `asiento_comprado` para un horario y fecha de viaje específicos. Esto evita inconsistencias en los datos.

---

### 4. `recorrido`
Define la ruta que puede seguir un bus: de dónde sale y a dónde llega.

| Campo | Tipo | Descripción |
|---|---|---|
| `id_recorrido` | Integer PK | |
| `origen` | String(100) | Ciudad o terminal de salida |
| `destino` | String(100) | Ciudad o terminal de llegada |
| `tipo` | String(20) | `"ida"` o `"ida_y_vuelta"` |
| `precio_base` | Float | Tarifa base de la ruta en pesos CLP |

> Un `Recorrido` es solo la definición del trayecto. Los horarios concretos van en `horario_viaje`. El `precio_base` del recorrido se usa para mostrar tarifas en `/tarifas`.

---

### 5. `horario_viaje`
Representa un servicio recurrente: un bus específico haciendo un recorrido específico a una hora fija. Es lo que se muestra en el home del portal.

| Campo | Tipo | Descripción |
|---|---|---|
| `id_horario` | Integer PK | |
| `id_recorrido` | Integer FK → `recorrido` | Qué trayecto cubre |
| `patente` | String(10) FK → `bus` | Qué bus lo opera |
| `hora_salida` | Time | Hora de salida diaria |
| `hora_llegada` | Time | Hora de llegada estimada |
| `precio_base` | Float | Precio del pasaje (el admin puede modificarlo) |
| `activo` | Boolean | Si está en `False`, no aparece en el home ni permite compras |

**¿Por qué existe esta tabla y no se guarda la fecha en el viaje?**
Los viajes de Talmocur son recurrentes (el mismo bus sale todos los días a las 8:00am). Si guardáramos una fila por cada día, habría miles de registros innecesarios. En cambio, `horario_viaje` representa el horario fijo, y la fecha concreta del viaje se guarda en `compra.fecha_viaje` cuando el usuario compra un pasaje.

---

### 6. `compra`
Registra una transacción de compra de uno o más asientos. Una compra siempre está asociada a un horario y a una fecha de viaje específica.

| Campo | Tipo | Descripción |
|---|---|---|
| `id_compra` | Integer PK | |
| `id_usuario` | String(36) FK → `usuario` | Quién compró |
| `id_horario` | Integer FK → `horario_viaje` | En qué servicio viajará |
| `fecha_viaje` | Date | El día concreto del viaje |
| `fecha_compra` | DateTime | Cuándo se realizó la compra |
| `monto_total` | Float | Suma de todos los asientos comprados |
| `metodo_pago` | String(50) | Ej: `"Tarjeta"`, `"Transferencia"` |
| `estado` | String(20) | `"confirmada"` o `"cancelada"` |

---

### 7. `asiento_comprado`
Tabla intermedia que indica qué asientos específicos forman parte de una compra. Permite comprar varios asientos en una sola transacción.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | Integer PK | |
| `id_compra` | Integer FK → `compra` | A qué compra pertenece |
| `id_asiento` | Integer FK → `asiento` | Qué asiento se reservó |
| `precio_unitario` | Float | Precio de ese asiento en el momento de la compra |

> La restricción UNIQUE en `(id_compra, id_asiento)` impide que el mismo asiento aparezca dos veces en la misma compra.

---

### 8. `suspension`
Permite al administrador bloquear la venta de pasajes en un horario durante un rango de fechas (ej: por mal tiempo, mantenimiento, feriado).

| Campo | Tipo | Descripción |
|---|---|---|
| `id_suspension` | Integer PK | |
| `id_horario` | Integer FK → `horario_viaje` | Qué horario se suspende |
| `fecha_inicio` | Date | Primer día suspendido |
| `fecha_fin` | Date | Último día suspendido |
| `motivo` | String(300) | Mensaje visible para el usuario (ej: "Suspendido por lluvia") |

> Para saber si un horario está suspendido en una fecha dada, se consulta si existe alguna `suspension` cuyo `fecha_inicio <= fecha <= fecha_fin`.

---

### 9. `aviso`
Mensajes informativos del administrador que se muestran en el portal (ej: alertas de servicio, avisos generales).

| Campo | Tipo | Descripción |
|---|---|---|
| `id_aviso` | Integer PK | |
| `titulo` | String(200) | Título del aviso |
| `mensaje` | String(1000) | Cuerpo del mensaje |
| `activo` | Boolean | Solo los avisos con `activo=True` se muestran |
| `fecha_creacion` | DateTime | Cuándo fue creado |

---

## Diagrama de relaciones

```
usuario ──────────────────────────────────────────────────┐
                                                          │ (compra)
bus ──────────────┐                                       │
  │               │ (horario_viaje)    compra ────────────┘
  │ (asientos)    └──────────────────────│
  │                        │            │
  ▼                        ▼            ▼
asiento            recorrido    asiento_comprado
  ▲                             (asiento + compra)
  └─────────────────────────────────────┘

horario_viaje ──── suspension
```

---

## Cómo consultar datos desde Python

```python
from database import obtener_sesion
from models import Bus, HorarioViaje, Asiento, Compra, AsientoComprado
from datetime import date

db = obtener_sesion()

# ── Ver todos los horarios activos (para el home) ─────────────────
horarios = db.query(HorarioViaje).filter(HorarioViaje.activo == True).all()
for h in horarios:
    print(h.hora_salida, h.recorrido.origen, "→", h.recorrido.destino)

# ── Ver asientos de un bus ────────────────────────────────────────
bus = db.query(Bus).filter(Bus.patente == "ABCD12").first()
print(bus.asientos)   # lista de objetos Asiento

# ── Ver asientos OCUPADOS en un horario para una fecha ────────────
fecha_viaje = date(2026, 6, 20)
id_horario  = 1

ocupados = (
    db.query(AsientoComprado.id_asiento)
    .join(Compra)
    .filter(
        Compra.id_horario  == id_horario,
        Compra.fecha_viaje == fecha_viaje,
        Compra.estado      == "confirmada",
    )
    .all()
)
ids_ocupados = {r.id_asiento for r in ocupados}

# ── Ver asientos DISPONIBLES ──────────────────────────────────────
todos = db.query(Asiento).filter(Asiento.patente == "ABCD12").all()
disponibles = [a for a in todos if a.id_asiento not in ids_ocupados]

db.close()
```

---

## Archivos del backend relevantes

| Archivo | Rol |
|---|---|
| `backend/models.py` | Define todas las tablas como clases Python |
| `backend/database.py` | Crea la conexión a la BD en `data/` y expone `obtener_sesion()` |
| `backend/db_sqlite.py` | Funciones CRUD para usuarios (login, registro) |
| `backend/seed_db.py` | Puebla la BD con datos iniciales (recorridos). Se ejecuta automáticamente al iniciar la app |
| `backend/routes.py` | Endpoints Flask que usan `db_sqlite` para autenticación |
| `data/talmocur.db` | Archivo de la BD — generado automáticamente, **no subir al repo** |
