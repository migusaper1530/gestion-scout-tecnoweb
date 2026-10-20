from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select
from ..models import Rama, Scout, Actividad, Inscripcion
from ..repositories.scout import ScoutRepository
from ..repositories.actividad import ActividadRepository, InscripcionRepository


def requerido(obj, mensaje='Registro no encontrado'):
    if obj is None: raise HTTPException(404, mensaje)
    return obj

def conflicto(mensaje):
    raise HTTPException(409, mensaje)

class GestionService:
    def __init__(self, db):
        self.db = db
        self.actividades = ActividadRepository(db)
        self.scouts = ScoutRepository(db)
        self.inscripciones = InscripcionRepository(db)

    def rama(self, id):
        if id is not None: requerido(self.db.get(Rama, id), 'Rama no encontrada')

    def guardar_scout(self, data, id=None):
        self.rama(data.rama_id)
        scout = requerido(self.scouts.obtener(id, True)) if id else Scout()
        # Serialize branch changes against enrollment's scout row lock.
        if id and scout.rama_id != data.rama_id:
            incompatible = self.db.scalar(select(Actividad.id).join(Inscripcion, Inscripcion.actividad_id == Actividad.id).where(Inscripcion.scout_id == id, Inscripcion.estado == 'inscrito', Actividad.rama_id.is_not(None), Actividad.rama_id != data.rama_id).limit(1))
            if incompatible: conflicto('Cancele las inscripciones incompatibles antes de cambiar de rama')
        for k, v in data.model_dump().items(): setattr(scout, k, v)
        self.db.add(scout)
        self.db.commit()
        return scout

    def guardar_actividad(self, data, id=None):
        actividad = requerido(self.actividades.obtener(id, True)) if id else Actividad()
        self.rama(data.rama_id)
        if id:
            if data.cupo_maximo < self.actividades.inscritos(id): conflicto('El cupo es menor a las inscripciones activas')
            if data.rama_id is not None:
                incompatible = self.db.scalar(select(Scout.id).join(Inscripcion, Inscripcion.scout_id == Scout.id).where(Inscripcion.actividad_id == id, Inscripcion.estado == 'inscrito', Scout.rama_id != data.rama_id).limit(1))
                if incompatible: conflicto('Hay inscritos de otra rama; cancele sus inscripciones primero')
        for k, v in data.model_dump().items(): setattr(actividad, k, v)
        self.db.add(actividad)
        self.db.commit()
        return self.actividad_out(actividad)

    def actividad_out(self, actividad):
        count = self.actividades.inscritos(actividad.id)
        return {**{c.name: getattr(actividad, c.name) for c in Actividad.__table__.columns}, 'inscritos': count, 'cupos_disponibles': actividad.cupo_maximo - count}

    def validar_inscripcion(self, actividad, scout):
        if not scout.activo: conflicto('El scout está inactivo')
        if actividad.rama_id and actividad.rama_id != scout.rama_id: conflicto('La actividad pertenece a otra rama')
        if actividad.estado != 'abierta': conflicto('La actividad no está abierta')
        if actividad.inicio <= datetime.now(timezone.utc): conflicto('La actividad ya comenzó')
        if self.actividades.inscritos(actividad.id) >= actividad.cupo_maximo: conflicto('No hay cupos disponibles')

    def crear_inscripcion(self, data):
        # PostgreSQL READ COMMITTED: every capacity-changing operation first locks
        # the same activity row. A waiting transaction then sees the committed count.
        actividad = requerido(self.actividades.obtener(data.actividad_id, True), 'Actividad no encontrada')
        scout = requerido(self.scouts.obtener(data.scout_id, True), 'Scout no encontrado')
        if data.estado == 'inscrito': self.validar_inscripcion(actividad, scout)
        obj = Inscripcion(**data.model_dump())
        self.db.add(obj)
        self.db.commit()
        return obj

    def cambiar_inscripcion(self, id, estado=None, eliminar=False):
        obj = requerido(self.inscripciones.obtener(id))
        actividad = requerido(self.actividades.obtener(obj.actividad_id, True))
        # Refresh after lock: concurrent requests might have changed/deleted it.
        self.db.expire(obj)
        obj = requerido(self.db.scalar(select(Inscripcion).where(Inscripcion.id == id)))
        if eliminar: self.db.delete(obj)
        else:
            if estado == 'inscrito' and obj.estado != 'inscrito':
                scout = requerido(self.scouts.obtener(obj.scout_id, True))
                self.validar_inscripcion(actividad, scout)
            obj.estado = estado
        self.db.commit()
        return obj
