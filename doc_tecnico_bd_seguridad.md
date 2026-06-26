# Documento Técnico — Base de Datos y Seguridad de Contraseñas

**Proyecto:** Portal Talmocur  
**Autor:** Generado para el equipo — Diego Pezoa  
**Fecha:** Junio 2026

---

## 1. ¿Qué tecnología usamos para la base de datos?

### SQLite
SQLite es un motor de base de datos relacional que guarda toda la información en **un solo archivo** (`data/talmocur.db`). A diferencia de PostgreSQL o MySQL, no requiere instalar ni configurar ningún servidor externo — Python puede trabajar con él directamente.

**¿Por qué SQLite para desarrollo?**
- Cero configuración: el archivo se crea solo al arrancar la app.
- Portabilidad: cualquier miembro del equipo puede clonar el repo y ejecutar la app sin instalar nada adicional.
- Es adecuado para proyectos académicos y prototipos. Si el proyecto escalara a producción, se reemplazaría por PostgreSQL con solo cambiar una línea en `database.py`.

### SQLAlchemy (ORM)
SQLAlchemy es una librería Python que actúa como intermediario entre el código Python y la base de datos. Su rol es el de **ORM** (*Object Relational Mapper*): permite trabajar con las tablas de la BD como si fueran clases y objetos Python, sin escribir SQL manualmente.

**Ejemplo concreto:** en vez de escribir:
```sql
SELECT * FROM usuario WHERE email = 'juan@example.com';
```
escribimos Python:
```python
db.query(Usuario).filter(Usuario.email == 'juan@example.com').first()
```
El resultado es el mismo, pero el código es más legible, más seguro (evita inyección SQL) y más fácil de mantener.

---

## 2. ¿Dónde vive la base de datos?

```
Proyecto/
├── backend/
│   └── database.py   ← configura la conexión
└── data/
    └── talmocur.db   ← aquí vive la BD (NO en el repo)
```

La BD se almacena en `data/talmocur.db`. Esta ruta se calcula de forma **absoluta** en `database.py` usando `__file__`, lo que significa que no importa desde qué carpeta se ejecute el programa: siempre apuntará al mismo lugar.

El archivo `data/talmocur.db` está en el `.gitignore` — no se sube al repositorio. Cada desarrollador tiene su propia BD local que se genera automáticamente al ejecutar `python app.py`.

---

## 3. Estructura de la base de datos

La BD tiene **9 tablas**. A continuación se explica cada una en lenguaje simple:

### 3.1 `usuario`
Guarda los datos de cada persona registrada en el portal.

| Campo | ¿Qué guarda? | Ejemplo |
|-------|-------------|---------|
| `id` | Identificador único (UUID) | `"a1b2c3-..."` |
| `nombre` | Nombre completo | `"Juan Pérez"` |
| `email` | Correo — se usa para iniciar sesión | `"juan@gmail.com"` |
| `password_hash` | La contraseña **cifrada** (nunca en texto plano) | `"$2b$12$..."` |
| `fecha_registro` | Cuándo se creó la cuenta | `2026-06-18 18:00:00` |
| `rol` | Si es pasajero o administrador | `"pasajero"` o `"admin"` |

> **Usuario administrador predefinido:** al arrancar la app por primera vez, `seed_db.py` crea automáticamente la cuenta `admin@talmocur.cl` con rol `"admin"` si no existe. Su contraseña está guardada únicamente como hash bcrypt en la BD — nunca en texto plano en el código fuente.

### 3.2 `bus`
Representa cada bus físico de la flota de Talmocur.

| Campo | ¿Qué guarda? | Ejemplo |
|-------|-------------|---------|
| `patente` | Identificador único del bus | `"ABCD12"` |
| `capacidad` | Cuántos asientos tiene | `45` |
| `modelo` | Modelo del vehículo (opcional) | `"Mercedes Benz O500"` |
| `estado` | Si está disponible o en mantención | `"Activo"` |

### 3.3 `asiento`
Un registro por cada asiento físico de cada bus. Si un bus tiene 45 asientos, hay 45 filas en esta tabla para ese bus.

| Campo | ¿Qué guarda? |
|-------|-------------|
| `id_asiento` | Identificador único |
| `numero` | Número del asiento (1, 2, 3…) |
| `patente` | A qué bus pertenece |

> **¿Cómo sé si un asiento está disponible?** No hay campo "disponible" en esta tabla. Para saber si un asiento está ocupado, se consulta la tabla `asiento_comprado`: si el asiento aparece allí para un horario y fecha específicos, está ocupado.

### 3.4 `recorrido`
Define las rutas que opera Talmocur: de dónde a dónde.

| Campo | ¿Qué guarda? | Ejemplo |
|-------|-------------|---------|
| `id_recorrido` | Identificador único | `1` |
| `origen` | Ciudad de partida | `"Curicó"` |
| `destino` | Ciudad de llegada | `"Talca"` |
| `tipo` | Tipo de viaje | `"ida"` |
| `precio_base` | Tarifa en pesos CLP | `3500.0` |

> **Datos actuales en la BD:** Curicó → Talca y Talca → Curicó, ambas a $3.500.

### 3.5 `horario_viaje`
Un horario recurrente: "el bus ABCD12 sale de Curicó hacia Talca todos los días a las 08:00". Es lo que se mostrará en el home del portal.

| Campo | ¿Qué guarda? | Ejemplo |
|-------|-------------|---------|
| `id_horario` | Identificador único | `1` |
| `id_recorrido` | Qué ruta cubre | FK → `recorrido` |
| `patente` | Qué bus lo hace | FK → `bus` |
| `hora_salida` | Hora de salida diaria | `08:00` |
| `hora_llegada` | Hora de llegada estimada | `08:45` |
| `precio_base` | Precio del pasaje (modificable por el admin) | `3500.0` |
| `activo` | Si se muestra en el portal | `True` / `False` |

### 3.6 `compra`
Registra cada vez que un usuario compra uno o más pasajes.

| Campo | ¿Qué guarda? |
|-------|-------------|
| `id_compra` | Identificador único |
| `id_usuario` | Quién compró |
| `id_horario` | En qué servicio viajará |
| `fecha_viaje` | El día concreto del viaje |
| `fecha_compra` | Cuándo realizó la compra |
| `monto_total` | Total pagado |
| `metodo_pago` | Tarjeta, transferencia, etc. |
| `estado` | `"confirmada"` o `"cancelada"` |

### 3.7 `asiento_comprado`
Tabla puente que relaciona una compra con los asientos específicos reservados. Permite comprar varios asientos en una sola transacción.

| Campo | ¿Qué guarda? | Ejemplo |
|-------|-------------|---------|
| `id` | Identificador único | `1` |
| `id_compra` | A qué compra pertenece | FK → `compra` |
| `id_asiento` | Qué asiento fue reservado | FK → `asiento` |
| `precio_unitario` | Precio de ese asiento al momento de comprar | `3500.0` |

> La combinación `(id_compra, id_asiento)` es única — el mismo asiento no puede aparecer dos veces en la misma compra.

### 3.8 `suspension`
Permite al administrador bloquear un horario por un rango de fechas (ej: feriado, mal tiempo).

| Campo | ¿Qué guarda? | Ejemplo |
|-------|-------------|---------|
| `id_suspension` | Identificador único | `1` |
| `id_horario` | Qué horario se suspende | FK → `horario_viaje` |
| `fecha_inicio` | Primer día bloqueado | `2026-07-01` |
| `fecha_fin` | Último día bloqueado | `2026-07-03` |
| `motivo` | Mensaje visible para el usuario | `"Suspendido por lluvia"` |

### 3.9 `aviso`
Mensajes informativos del administrador para los usuarios del portal (ej: "Servicio suspendido el 25 de diciembre").

| Campo | ¿Qué guarda? | Ejemplo |
|-------|-------------|---------|
| `id_aviso` | Identificador único | `1` |
| `titulo` | Título del aviso | `"Suspensión temporal"` |
| `mensaje` | Cuerpo del mensaje | `"Los buses no operarán el 25/12."` |
| `activo` | Si se muestra en el portal | `True` / `False` |
| `fecha_creacion` | Cuándo fue creado | `2026-06-18 20:00:00` |

---

## 4. Relaciones entre tablas

```
usuario ──────────────────────────────────────────────────────┐
                                                              │
bus ─────────────┐                                            │
  │              │─── horario_viaje ──── recorrido            │
  │ (asientos)   │         │                                  │
  ▼              │         ├──── suspension                   │
asiento          │         │                                  │
  ▲              │         └──── compra ──────────────────────┘
  │              │                  │
  └──────────────┴──── asiento_comprado
```

**En palabras simples:**
- Un **bus** tiene muchos **asientos**.
- Un **bus** puede tener muchos **horarios de viaje**, cada uno en un **recorrido** (ruta).
- Un **usuario** puede hacer muchas **compras**.
- Una **compra** pertenece a un **horario de viaje** y a un **usuario**, y puede incluir varios **asientos comprados**.
- Un **horario** puede tener **suspensiones** (bloqueos temporales).

---

## 5. ¿Cómo funciona el hasheo de contraseñas?

### El problema
Si guardamos la contraseña `"MiClave123!"` directamente en la BD, cualquiera que acceda al archivo `talmocur.db` puede verla. Esto es un riesgo de seguridad grave.

### La solución: bcrypt
Usamos la librería **bcrypt**, que aplica una función de hash criptográfico a la contraseña. El resultado es una cadena irreversible: no existe forma de reconstruir la contraseña original a partir del hash.

### ¿Qué es un hash?
Es una función matemática de **una sola dirección**:
```
"MiClave123!"  →  hash()  →  "$2b$12$eImiTXuWVxfM37uY3Jaln..."
```
- Siempre produce la misma salida para la misma entrada.
- Es imposible (computacionalmente) hacer el proceso inverso.
- Si alguien roba la BD, solo ve hashes — no contraseñas.

### Proceso de registro

```python
# En backend/routes.py — endpoint POST /api/register

password_hash = bcrypt.hashpw(
    password.encode('utf-8'),   # convierte la contraseña a bytes
    bcrypt.gensalt()            # genera una "sal" aleatoria única
).decode('utf-8')              # convierte el resultado a string

# Se guarda password_hash en la BD, NUNCA la contraseña original
db.crear_usuario(nombre, email, password_hash)
```

**¿Qué es la "sal" (salt)?**  
Es un valor aleatorio que bcrypt agrega a la contraseña antes de hashear. Esto garantiza que dos usuarios con la misma contraseña tengan hashes distintos, haciendo inútiles los ataques de diccionario.

### Proceso de login

```python
# En backend/routes.py — endpoint POST /api/login

# Se busca el usuario en la BD
usuario = db.buscar_usuario_por_email(email)

# bcrypt compara la contraseña ingresada con el hash guardado
if bcrypt.checkpw(
    password.encode('utf-8'),
    usuario['password_hash'].encode('utf-8')
):
    # contraseña correcta → crear sesión
```

bcrypt sabe cómo comparar aunque el hash contenga una sal aleatoria, porque la sal también está codificada dentro del hash.

### Resumen visual

```
REGISTRO:
  contraseña "MiClave123!"
       │
       ▼
  bcrypt.hashpw(contraseña + sal aleatoria)
       │
       ▼
  "$2b$12$eImiT..." ← guardado en BD

LOGIN:
  contraseña "MiClave123!" + hash de BD
       │
       ▼
  bcrypt.checkpw() → True / False
```

---

## 6. ¿Cómo se inicializa la BD automáticamente?

Al ejecutar `python app.py`, ocurre lo siguiente en orden:

1. **`database.py`** calcula la ruta absoluta a `data/talmocur.db` usando `os.path.abspath(__file__)`.
2. **`crear_tablas()`** le dice a SQLAlchemy que cree todas las tablas si no existen (`CREATE TABLE IF NOT EXISTS`). Si ya existen, las deja intactas.
3. **`seed_db.py`** (función `seed()`) ejecuta tres verificaciones:
   - Si la tabla `recorrido` está vacía, inserta los datos iniciales (Curicó ↔ Talca, $3.500).
   - Si no existe el usuario `admin@talmocur.cl`, lo crea con rol `"admin"` y contraseña hasheada con bcrypt.

Este proceso es **idempotente**: se puede ejecutar muchas veces sin problemas — nunca borrará datos existentes.

---

## 7. ¿Cómo agregar más datos a futuro?

Para agregar nuevos recorridos, horarios, buses, etc., edita `backend/seed_db.py`:

```python
def seed(quiet=False):
    crear_tablas(quiet=quiet)
    db = obtener_sesion()
    try:
        # ── Recorridos ──
        if db.query(Recorrido).count() == 0:
            recorridos = [
                Recorrido(origen="Curicó", destino="Talca",  tipo="ida", precio_base=3500.0),
                Recorrido(origen="Talca",  destino="Curicó", tipo="ida", precio_base=3500.0),
                # Agregar aquí nuevos recorridos:
                # Recorrido(origen="Curicó", destino="Santiago", tipo="ida", precio_base=8000.0),
            ]
            db.add_all(recorridos)
            db.commit()

        # ── Usuario administrador ──
        # Agregar aquí más usuarios admin si el proyecto lo requiere:
        # if no existe 'otro@talmocur.cl':
        #     db.add(Usuario(email="otro@talmocur.cl", rol="admin", ...))
        #     db.commit()

        # ── Buses (ejemplo a futuro) ──
        # if db.query(Bus).count() == 0:
        #     buses = [Bus(patente="ABCD12", capacidad=45, estado="Activo")]
        #     db.add_all(buses)
        #     db.commit()
    finally:
        db.close()
```

> **Importante:** el seed solo se ejecuta cuando las tablas están vacías. Si ya tienes datos y quieres reiniciar, borra manualmente `data/talmocur.db` y reinicia la app.
