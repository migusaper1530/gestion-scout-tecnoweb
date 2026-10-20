import logging
import time
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from .db import get_db
from .routers.api import router

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
app = FastAPI(title='Gestión Scout', version='1.0.0', description='Gestión de un grupo scout. Acceso exclusivo para dirigentes.')
app.include_router(router)

@app.exception_handler(IntegrityError)
async def integrity_error(request, exc):
    # Session context is closed/rolled back by get_db; never expose SQL or values.
    return JSONResponse(status_code=409, content={'detail': 'Conflicto: registro duplicado o con referencias. Revise las inscripciones y relaciones antes de eliminar o modificar.'})

@app.middleware('http')
async def request_log(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    rid = request.headers.get('x-request-id', 'sin-gateway')
    logging.info('request_id=%s method=%s path=%s status=%s duration_ms=%.1f', rid, request.method, request.url.path, response.status_code, (time.perf_counter() - start)*1000)
    response.headers['X-Request-ID'] = rid
    return response

@app.get('/health', include_in_schema=False)
def health(db: Session = Depends(get_db)):
    try: db.execute(text('SELECT 1'))
    except OperationalError: raise HTTPException(503, 'Base de datos no disponible')
    return {'status': 'ok', 'database': 'ok'}
