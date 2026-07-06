# models.py
# Define todas las tablas de la base de datos como clases Python.
# SQLAlchemy las traduce automáticamente a SQL.

from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float,
    ForeignKey, Integer, String, Time, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ─────────────────────────────────────────────
# 1. Usuario  (autenticación de pasajeros y administradores)
# ─────────────────────────────────────────────
class Usuario(Base):
    __tablename__ = "usuario"

    id             = Column(String(36),  primary_key=True)          # UUID
    nombre         = Column(String(100), nullable=False)
    email          = Column(String(100), nullable=False, unique=True)
    password_hash  = Column(String(200), nullable=False)
    fecha_registro = Column(DateTime,    default=lambda: datetime.now(timezone.utc))
    rol            = Column(String(20),  nullable=False, default="pasajero")
    # rol: "pasajero" | "admin"

    compras = relationship("Compra", back_populates="usuario")

    def __repr__(self):
        return f"<Usuario(email={self.email}, rol={self.rol})>"


# ─────────────────────────────────────────────
# 2. Bus
# ─────────────────────────────────────────────
class Bus(Base):
    __tablename__ = "bus"

    patente   = Column(String(10),  primary_key=True)
    capacidad = Column(Integer,     nullable=False)   # determina cuántos Asiento se crean
    modelo    = Column(String(100))                   # opcional
    chofer    = Column(String(100))                   # nombre del conductor (opcional)
    estado    = Column(String(50),  nullable=False, default="Activo")
    # estado: "Activo" | "En mantención"

    asientos  = relationship("Asiento",      back_populates="bus")
    horarios  = relationship("HorarioViaje", back_populates="bus")

    def __repr__(self):
        return f"<Bus(patente={self.patente}, estado={self.estado})>"


# ─────────────────────────────────────────────
# 3. Asiento  (asientos físicos del bus — estáticos)
# ─────────────────────────────────────────────
class Asiento(Base):
    __tablename__ = "asiento"

    id_asiento = Column(Integer,    primary_key=True, autoincrement=True)
    numero     = Column(Integer,    nullable=False)   # 1, 2, 3 … bus.capacidad
    patente    = Column(String(10), ForeignKey("bus.patente"), nullable=False)

    __table_args__ = (
        UniqueConstraint("numero", "patente", name="uq_asiento_bus"),
    )

    bus              = relationship("Bus",             back_populates="asientos")
    asientos_compra  = relationship("AsientoComprado", back_populates="asiento")

    def __repr__(self):
        return f"<Asiento(numero={self.numero}, bus={self.patente})>"


# ─────────────────────────────────────────────
# 4. Recorrido  (origen → destino, tipo de viaje)
# ─────────────────────────────────────────────
class Recorrido(Base):
    __tablename__ = "recorrido"

    id_recorrido = Column(Integer,     primary_key=True, autoincrement=True)
    origen       = Column(String(100), nullable=False)
    destino      = Column(String(100), nullable=False)
    tipo         = Column(String(20),  nullable=False, default="ida")
    # tipo: "ida" | "ida_y_vuelta"
    precio_base  = Column(Float,       nullable=False, default=0.0)
    # tarifa base de la ruta (en pesos CLP)

    horarios = relationship("HorarioViaje", back_populates="recorrido")

    def __repr__(self):
        return f"<Recorrido({self.origen} → {self.destino}, {self.tipo})>"


# ─────────────────────────────────────────────
# 5. HorarioViaje  (horario recurrente: bus + recorrido + hora)
# ─────────────────────────────────────────────
class HorarioViaje(Base):
    __tablename__ = "horario_viaje"

    id_horario    = Column(Integer,     primary_key=True, autoincrement=True)
    id_recorrido  = Column(Integer,     ForeignKey("recorrido.id_recorrido"), nullable=False)
    patente       = Column(String(10),  ForeignKey("bus.patente"),            nullable=False)
    hora_salida   = Column(Time,        nullable=False)
    hora_llegada  = Column(Time,        nullable=False)
    precio_base   = Column(Float,       nullable=False)
    activo        = Column(Boolean,     nullable=False, default=True)
    # activo=False deshabilita el horario completo (no aparece en el home ni permite compras)

    recorrido    = relationship("Recorrido",    back_populates="horarios")
    bus          = relationship("Bus",          back_populates="horarios")
    compras      = relationship("Compra",       back_populates="horario")
    suspensiones = relationship("Suspension",   back_populates="horario")

    def __repr__(self):
        return f"<HorarioViaje(id={self.id_horario}, salida={self.hora_salida})>"


# ─────────────────────────────────────────────
# 6. Compra  (una transacción de uno o más asientos)
# ─────────────────────────────────────────────
class Compra(Base):
    __tablename__ = "compra"

    id_compra    = Column(Integer,     primary_key=True, autoincrement=True)
    id_usuario   = Column(String(36),  ForeignKey("usuario.id"),              nullable=False)
    id_horario   = Column(Integer,     ForeignKey("horario_viaje.id_horario"), nullable=False)
    fecha_viaje  = Column(Date,        nullable=False)    # día concreto en que viajará
    fecha_compra = Column(DateTime,    default=lambda: datetime.now(timezone.utc))
    monto_total  = Column(Float,       nullable=False)
    metodo_pago  = Column(String(50),  nullable=False)
    estado       = Column(String(20),  nullable=False, default="confirmada")
    # estado: "confirmada" | "cancelada"

    usuario          = relationship("Usuario",         back_populates="compras")
    horario          = relationship("HorarioViaje",    back_populates="compras")
    asientos_compra  = relationship("AsientoComprado", back_populates="compra",
                                   cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Compra(id={self.id_compra}, estado={self.estado})>"


# ─────────────────────────────────────────────
# 7. AsientoComprado  (qué asientos forman parte de una compra)
# ─────────────────────────────────────────────
class AsientoComprado(Base):
    __tablename__ = "asiento_comprado"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    id_compra       = Column(Integer, ForeignKey("compra.id_compra"),   nullable=False)
    id_asiento      = Column(Integer, ForeignKey("asiento.id_asiento"), nullable=False)
    precio_unitario = Column(Float,   nullable=False)
    nombre_pasajero = Column(String(100), nullable=True)
    rut_pasajero    = Column(String(20), nullable=True)
    email_pasajero  = Column(String(100), nullable=True)
    telefono_pasajero = Column(String(30), nullable=True)
    tipo_pasaje     = Column(String(30), nullable=True)
    observaciones   = Column(String(500), nullable=True)

    __table_args__ = (
        UniqueConstraint("id_compra", "id_asiento", name="uq_asiento_por_compra"),
    )

    compra  = relationship("Compra",  back_populates="asientos_compra")
    asiento = relationship("Asiento", back_populates="asientos_compra")

    def __repr__(self):
        return f"<AsientoComprado(compra={self.id_compra}, asiento={self.id_asiento})>"


# ─────────────────────────────────────────────
# 8. Suspension  (bloqueo temporal de un horario por rango de fechas)
# ─────────────────────────────────────────────
class Suspension(Base):
    __tablename__ = "suspension"

    id_suspension = Column(Integer,     primary_key=True, autoincrement=True)
    id_horario    = Column(Integer,     ForeignKey("horario_viaje.id_horario"), nullable=False)
    fecha_inicio  = Column(Date,        nullable=False)
    fecha_fin     = Column(Date,        nullable=False)
    motivo        = Column(String(300))  # mensaje visible para el usuario

    horario = relationship("HorarioViaje", back_populates="suspensiones")

    def __repr__(self):
        return f"<Suspension(horario={self.id_horario}, {self.fecha_inicio}→{self.fecha_fin})>"


# ─────────────────────────────────────────────
# 9. Aviso  (notificaciones del admin para los usuarios)
# ─────────────────────────────────────────────
class Aviso(Base):
    __tablename__ = "aviso"

    id_aviso       = Column(Integer,      primary_key=True, autoincrement=True)
    titulo         = Column(String(200),  nullable=False)
    mensaje        = Column(String(1000), nullable=False)
    tipo           = Column(String(20),   nullable=False, default="info")
    # tipo: "alerta" | "info" | "precio" | "emergencia"
    duracion_dias  = Column(Integer,      nullable=False, default=1)
    # Días de vigencia desde fecha_creacion. 0 = nunca se muestra.
    activo         = Column(Boolean,      nullable=False, default=True)
    fecha_creacion = Column(DateTime,     default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Aviso(titulo={self.titulo}, tipo={self.tipo}, activo={self.activo})>"



# ─────────────────────────────────────────────
# 10. TokenRecuperacion  (recuperación de contraseña por enlace temporal)
# ─────────────────────────────────────────────
class TokenRecuperacion(Base):
    __tablename__ = "token_recuperacion"

    id               = Column(Integer,    primary_key=True, autoincrement=True)
    id_usuario       = Column(String(36), ForeignKey("usuario.id"), nullable=False)
    token            = Column(String(128), nullable=False, unique=True, index=True)
    fecha_expiracion = Column(DateTime,   nullable=False)
    usado            = Column(Boolean,    nullable=False, default=False)

    usuario = relationship("Usuario")

    def esta_vigente(self) -> bool:
        """True si el token no fue usado y no ha expirado."""
        ahora = datetime.now(timezone.utc)
        exp = self.fecha_expiracion
        # SQLite guarda datetimes "naive"; los tratamos como UTC para comparar
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return (not self.usado) and ahora < exp

    def __repr__(self):
        return f"<TokenRecuperacion(usuario={self.id_usuario}, usado={self.usado})>"
