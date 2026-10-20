from sqlalchemy import select
from ..models import Rama, Scout

class RamaRepository:
    def __init__(self, db): self.db = db
    def listar(self): return self.db.scalars(select(Rama).order_by(Rama.id)).all()
    def obtener(self, id): return self.db.get(Rama, id)

class ScoutRepository:
    def __init__(self, db): self.db = db
    def listar(self, rama_id=None):
        q = select(Scout).order_by(Scout.id)
        if rama_id is not None: q = q.where(Scout.rama_id == rama_id)
        return self.db.scalars(q).all()
    def obtener(self, id, bloquear=False):
        q = select(Scout).where(Scout.id == id)
        return self.db.scalar(q.with_for_update() if bloquear else q)
