from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, CheckConstraint, UniqueConstraint, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Rama(Base):
    __tablename__ = 'ramas'
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str] = mapped_column(Text, default='')

class Scout(Base):
    __tablename__ = 'scouts'
    id: Mapped[int] = mapped_column(primary_key=True)
    nombres: Mapped[str] = mapped_column(String(100))
    apellidos: Mapped[str] = mapped_column(String(100))
    rama_id: Mapped[int] = mapped_column(ForeignKey('ramas.id', ondelete='RESTRICT'), index=True)
    activo: Mapped[bool] = mapped_column(default=True)

class Actividad(Base):
    __tablename__ = 'actividades'
    __table_args__ = (CheckConstraint('inicio < fin', name='fechas_validas'), CheckConstraint('cupo_maximo > 0', name='cupo_positivo'), CheckConstraint("estado IN ('abierta','cerrada','cancelada')", name='estado_actividad'))
    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(160))
    descripcion: Mapped[str] = mapped_column(Text, default='')
    lugar: Mapped[str] = mapped_column(String(160))
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fin: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cupo_maximo: Mapped[int]
    rama_id: Mapped[int | None] = mapped_column(ForeignKey('ramas.id', ondelete='RESTRICT'), index=True)
    estado: Mapped[str] = mapped_column(String(20), default='abierta')

class Inscripcion(Base):
    __tablename__ = 'inscripciones'
    __table_args__ = (UniqueConstraint('scout_id', 'actividad_id', name='scout_actividad_unicos'), CheckConstraint("estado IN ('inscrito','cancelado')", name='estado_inscripcion'))
    id: Mapped[int] = mapped_column(primary_key=True)
    scout_id: Mapped[int] = mapped_column(ForeignKey('scouts.id', ondelete='RESTRICT'), index=True)
    actividad_id: Mapped[int] = mapped_column(ForeignKey('actividades.id', ondelete='RESTRICT'), index=True)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    estado: Mapped[str] = mapped_column(String(20), default='inscrito')

class Dirigente(Base):
    __tablename__ = 'dirigentes'
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    usuario: Mapped[str] = mapped_column(String(120), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    activo: Mapped[bool] = mapped_column(default=True)
