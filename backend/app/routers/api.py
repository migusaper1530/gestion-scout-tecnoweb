from fastapi import APIRouter, Depends, Response, Query, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Rama, Scout, Actividad, Inscripcion, Dirigente
from ..schemas import RamaIn, RamaOut, ScoutIn, ScoutOut, ActividadIn, ActividadOut, InscripcionIn, InscripcionOut, InscripcionUpdate, DirigenteOut
from ..security import current_user, password_hash, dummy_hash, token_for
from ..repositories.scout import RamaRepository, ScoutRepository
from ..repositories.actividad import ActividadRepository, InscripcionRepository
from ..services.negocio import GestionService, requerido
from ..config import settings

router = APIRouter(prefix='/api/v1')
business = APIRouter(dependencies=[Depends(current_user)])
def service(db: Session = Depends(get_db)): return GestionService(db)

@router.post('/auth/login', tags=['Acceso'])
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(Dirigente).where(Dirigente.usuario == form.username))
    valid = password_hash.verify(form.password, user.password_hash if user else dummy_hash)
    if not valid or not user or not user.activo:
        raise HTTPException(401, 'Usuario o contraseña incorrectos', headers={'WWW-Authenticate': 'Bearer'})
    return {'access_token': token_for(user.id), 'token_type': 'bearer', 'expires_in': settings.token_minutes * 60}

@business.get('/auth/me', response_model=DirigenteOut, tags=['Acceso'])
def me(user=Depends(current_user)): return user

@business.get('/resumen', tags=['Resumen'])
def resumen(db: Session = Depends(get_db)):
    return {'grupo': settings.group_name, **{name: db.scalar(select(func.count()).select_from(model)) for name, model in [('ramas', Rama), ('scouts', Scout), ('actividades', Actividad)]}, 'inscripciones': db.scalar(select(func.count()).select_from(Inscripcion).where(Inscripcion.estado == 'inscrito'))}

@business.get('/ramas', response_model=list[RamaOut], tags=['Ramas'])
def ramas(db: Session = Depends(get_db)): return RamaRepository(db).listar()
@business.get('/ramas/{id}', response_model=RamaOut, tags=['Ramas'])
def rama(id: int, db: Session = Depends(get_db)): return requerido(RamaRepository(db).obtener(id))
@business.post('/ramas', response_model=RamaOut, status_code=201, tags=['Ramas'])
def crear_rama(data: RamaIn, db: Session = Depends(get_db)):
    obj = Rama(**data.model_dump()); db.add(obj); db.commit(); return obj
@business.put('/ramas/{id}', response_model=RamaOut, tags=['Ramas'])
def editar_rama(id: int, data: RamaIn, db: Session = Depends(get_db)):
    obj = requerido(db.get(Rama, id))
    for k, v in data.model_dump().items(): setattr(obj, k, v)
    db.commit(); return obj

@business.get('/scouts', response_model=list[ScoutOut], tags=['Scouts'])
def scouts(rama_id: int | None = Query(None, gt=0), db: Session = Depends(get_db)): return ScoutRepository(db).listar(rama_id)
@business.get('/scouts/{id}', response_model=ScoutOut, tags=['Scouts'])
def scout(id: int, db: Session = Depends(get_db)): return requerido(ScoutRepository(db).obtener(id))
@business.post('/scouts', response_model=ScoutOut, status_code=201, tags=['Scouts'])
def crear_scout(data: ScoutIn, svc=Depends(service)): return svc.guardar_scout(data)
@business.put('/scouts/{id}', response_model=ScoutOut, tags=['Scouts'])
def editar_scout(id: int, data: ScoutIn, svc=Depends(service)): return svc.guardar_scout(data, id)

@business.get('/actividades', response_model=list[ActividadOut], tags=['Actividades'])
def actividades(rama_id: int | None = Query(None, gt=0), svc=Depends(service)): return [svc.actividad_out(a) for a in svc.actividades.listar(rama_id)]
@business.get('/actividades/{id}', response_model=ActividadOut, tags=['Actividades'])
def actividad(id: int, svc=Depends(service)): return svc.actividad_out(requerido(svc.actividades.obtener(id)))
@business.post('/actividades', response_model=ActividadOut, status_code=201, tags=['Actividades'])
def crear_actividad(data: ActividadIn, svc=Depends(service)): return svc.guardar_actividad(data)
@business.put('/actividades/{id}', response_model=ActividadOut, tags=['Actividades'])
def editar_actividad(id: int, data: ActividadIn, svc=Depends(service)): return svc.guardar_actividad(data, id)

@business.get('/inscripciones', response_model=list[InscripcionOut], tags=['Inscripciones'])
def inscripciones(actividad_id: int | None = Query(None, gt=0), scout_id: int | None = Query(None, gt=0), db: Session = Depends(get_db)): return InscripcionRepository(db).listar(actividad_id, scout_id)
@business.get('/inscripciones/{id}', response_model=InscripcionOut, tags=['Inscripciones'])
def inscripcion(id: int, db: Session = Depends(get_db)): return requerido(db.get(Inscripcion, id))
@business.post('/inscripciones', response_model=InscripcionOut, status_code=201, tags=['Inscripciones'])
def crear_inscripcion(data: InscripcionIn, svc=Depends(service)): return svc.crear_inscripcion(data)
@business.put('/inscripciones/{id}', response_model=InscripcionOut, tags=['Inscripciones'])
def editar_inscripcion(id: int, data: InscripcionUpdate, svc=Depends(service)): return svc.cambiar_inscripcion(id, data.estado)
@business.delete('/inscripciones/{id}', status_code=204, tags=['Inscripciones'])
def eliminar_inscripcion(id: int, svc=Depends(service)):
    svc.cambiar_inscripcion(id, eliminar=True); return Response(status_code=204)

# Explicit delete routes keep referenced objects and return 409 via the DB handler.
@business.delete('/ramas/{id}', status_code=204, tags=['Ramas'])
def eliminar_rama(id: int, db: Session = Depends(get_db)):
    db.delete(requerido(db.get(Rama, id))); db.commit(); return Response(status_code=204)
@business.delete('/scouts/{id}', status_code=204, tags=['Scouts'])
def eliminar_scout(id: int, db: Session = Depends(get_db)):
    db.delete(requerido(db.get(Scout, id))); db.commit(); return Response(status_code=204)
@business.delete('/actividades/{id}', status_code=204, tags=['Actividades'])
def eliminar_actividad(id: int, db: Session = Depends(get_db)):
    db.delete(requerido(db.get(Actividad, id))); db.commit(); return Response(status_code=204)
router.include_router(business)
