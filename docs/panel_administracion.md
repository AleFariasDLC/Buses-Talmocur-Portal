# Documentación: Panel de Administración – Buses Talmocur

Este documento detalla el funcionamiento, reglas de negocio y endpoints del **Panel de Administración** (`/admin`), diseñado para la gestión del servicio de transporte de la empresa Buses Talmocur.

---

## 1. Control de Acceso y Seguridad

El acceso al panel y sus respectivas APIs está restringido exclusivamente a usuarios con el rol `admin`.

*   **Redirección en Frontend:** Al acceder a la ruta `/admin`, el servidor verifica la sesión. Si el usuario no ha iniciado sesión o no cuenta con el rol `admin`, es redirigido automáticamente a la vista de `/login`.
*   **Seguridad en API:** Todos los endpoints del panel de administración en el backend (`backend/app.py`) validan que la sesión activa corresponda a un administrador:
    ```python
    if session.get('user_rol') != 'admin':
        return jsonify({'error': 'Acceso denegado.'}), 403
    ```

---

## 2. Gestión de la Flota (Buses)

Permite controlar los vehículos de transporte de la empresa.

*   **Campos del Bus:** Patente (clave primaria única), Chofer, Modelo, Capacidad (asientos) y Estado (`Activo` o `En mantención`).
*   **Generación de Asientos:** Al crear un bus (`POST /api/buses`), el sistema genera automáticamente `N` registros de asientos en la tabla `asiento` (donde `N` es la capacidad especificada, numerados del 1 al N).
*   **Reglas de Edición:** Una vez creado el bus, la **patente** y la **capacidad** de asientos quedan bloqueadas por motivos de integridad referencial. Solo se permite actualizar el nombre del chofer, el modelo del bus y su estado.
*   **Eliminación Segura:** Al eliminar un bus, el sistema remueve en cascada sus asientos asociados, todos los horarios de viaje asignados y sus suspensiones vigentes en la base de datos.

---

## 3. Gestión de Horarios y Tarifas

Permite programar las salidas diarias de cada bus y asignar el precio de sus pasajes.

*   **Asociación de Recorridos:** Cada viaje programado vincula un bus (patente) a un recorrido registrado (ej: `Curicó → Talca`).
*   **Cálculo Automático:** El administrador define la **hora de salida** y el **precio base**. La hora de llegada se calcula automáticamente sumando **45 minutos** a la hora de salida.
*   **Reglas de Validación de Conflictos:**
    Para evitar que un mismo bus sea programado de forma físicamente imposible, el sistema aplica las siguientes reglas de negocio antes de registrar o editar un horario:
    1.  **Mismo recorrido:** Si el bus tiene otro viaje programado en la misma ruta, debe haber una diferencia mínima de **2 horas** (120 minutos) entre las salidas.
    2.  **Diferente recorrido:** Si el bus tiene programado un viaje en una ruta distinta, debe haber una diferencia mínima de **1 hora** (60 minutos).

---

## 4. Sistema de Avisos a Usuarios

Los administradores pueden publicar avisos directos en la página de inicio de la aplicación web que verán todos los usuarios al ingresar al portal.

*   **Campos del Aviso:**
    *   **Título** y **Mensaje** (límite de 300 caracteres en la interfaz).
    *   **Tipo de Aviso:** Define el color y el icono del aviso. Las opciones son:
        *   `alerta` (⚠️ Alerta)
        *   `info` (ℹ️ Información)
        *   `precio` (💵 Cambio de tarifa)
        *   `emergencia` (🚨 Emergencia)
    *   **Duración (días):** Entero que define el tiempo de vigencia.
*   **Lógica de Vigencia:** Un aviso se considera vigente y se muestra en el portal general si está marcado como `activo` y la fecha actual cumple con:
    $$\text{fecha\_creacion} + \text{duracion\_dias} > \text{fecha\_hoy}$$
    El histórico completo de avisos (tanto vigentes como expirados) puede ser consultado, editado y eliminado por el administrador en su sección respectiva.
