from sqlalchemy import select, func
from ..models import Actividad, Inscripcion

class ActividadRepository:
    def __init__(self, db): self.db = db
    def obtener(self, id, bloquear=False):
        q = select(Actividad).where(Actividad.id == id)
        return self.db.scalar(q.with_for_update() if bloquear else q)
    def listar(self, rama_id=None):
        q = select(Actividad).order_by(Actividad.inicio)
        if rama_id is not None: q = q.where((Actividad.rama_id == rama_id) | Actividad.rama_id.is_(None))
        return self.db.scalars(q).all()
    def inscritos(self, id):
        return self.db.scalar(select(func.count()).select_from(Inscripcion).where(Inscripcion.actividad_id == id, Inscripcion.estado == 'inscrito'))

class InscripcionRepository:
    def __init__(self, db): self.db = db
    def obtener(self, id): return self.db.get(Inscripcion, id)
    def listar(self, actividad_id=None, scout_id=None):
        q = select(Inscripcion).order_by(Inscripcion.id)
        if actividad_id is not None: q = q.where(Inscripcion.actividad_id == actividad_id)
        if scout_id is not None: q = q.where(Inscripcion.scout_id == scout_id)
        return self.db.scalars(q).all()
