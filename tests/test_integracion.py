"""Run only against the isolated scout-tests Compose project through Nginx."""
import os
import secrets
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import httpx
import pytest
import jwt

BASE = os.environ.get('BASE_URL', 'http://127.0.0.1:18080').rstrip('/')
USER = os.environ['TEST_USER']
PASSWORD = os.environ['TEST_PASSWORD']
SECRET = os.environ['JWT_SECRET']

@pytest.fixture(scope='session')
def client():
    with httpx.Client(base_url=BASE, timeout=15) as c:
        bad = c.post('/api/v1/auth/login', data={'username': USER, 'password': 'incorrecta'})
        assert bad.status_code == 401
        auth = c.post('/api/v1/auth/login', data={'username':USER, 'password':PASSWORD})
        assert auth.status_code == 200, auth.text
        c.headers['Authorization'] = 'Bearer ' + auth.json()['access_token']
        yield c

def call(c, method, path, status=200, **kw):
    r = c.request(method, '/api/v1'+path, **kw)
    assert r.status_code == status, f'{method} {path}: {r.status_code}: {r.text}'
    return r.json() if r.content else None

@pytest.fixture
def records(client):
    prefix = secrets.token_hex(5)
    r = call(client,'POST','/ramas',201,json={'nombre':'Prueba '+prefix})
    other = call(client,'POST','/ramas',201,json={'nombre':'Otra '+prefix})
    scouts = [call(client,'POST','/scouts',201,json={'nombres':'Ficticio','apellidos':str(n),'rama_id':r['id']}) for n in range(3)]
    start = datetime.now(timezone.utc)+timedelta(days=3)
    body = {'titulo':'Prueba '+prefix,'lugar':'Parque ficticio','inicio':start.isoformat(),'fin':(start+timedelta(hours=2)).isoformat(),'cupo_maximo':2,'rama_id':r['id'],'estado':'abierta'}
    activity=call(client,'POST','/actividades',201,json=body)
    yield {'rama':r,'otra':other,'scouts':scouts,'actividad':activity,'body':body}
    for a in call(client,'GET',f"/inscripciones?actividad_id={activity['id']}"):
        call(client,'DELETE',f"/inscripciones/{a['id']}",204)
    call(client,'DELETE',f"/actividades/{activity['id']}",204)
    for s in scouts: call(client,'DELETE',f"/scouts/{s['id']}",204)
    for rama in [r,other]: call(client,'DELETE',f"/ramas/{rama['id']}",204)

def enroll(c,r,n=0,status=201):
    return call(c,'POST','/inscripciones',status,json={'scout_id':r['scouts'][n]['id'],'actividad_id':r['actividad']['id']})

def test_01_autenticacion(client):
    assert client.get('/api/v1/auth/me').status_code==200
    for token in ['', 'invalido', jwt.encode({'sub':'1','iat':datetime.now(timezone.utc)-timedelta(hours=2),'exp':datetime.now(timezone.utc)-timedelta(hours=1)},SECRET,algorithm='HS256')]:
        with httpx.Client(base_url=BASE) as c:
            if token: c.headers['Authorization']='Bearer '+token
            assert c.get('/api/v1/scouts').status_code==401

def test_02_gateway_swagger_health(client):
    for path in ['/','/app.js','/docs','/openapi.json','/health']:
        r=client.get(path); assert r.status_code==200; assert len(r.headers['x-request-id'])==32
    schema=client.get('/openapi.json').json()
    assert schema['components']['securitySchemes']['OAuth2PasswordBearer']['flows']['password']['tokenUrl']=='/api/v1/auth/login'
    assert client.get('/health').json()['database']=='ok'

def test_03_crud_rama(client,records):
    id=records['otra']['id']; body={'nombre':'Editada '+secrets.token_hex(4),'descripcion':'Texto'}
    assert call(client,'PUT',f'/ramas/{id}',json=body)['descripcion']=='Texto'
    assert call(client,'GET',f'/ramas/{id}')['nombre']==body['nombre']
    assert any(r['id']==id for r in call(client,'GET','/ramas'))

def test_04_crud_scout_filtros(client,records):
    s=records['scouts'][0]; body={k:s[k] for k in ['nombres','apellidos','rama_id','activo']};body['nombres']='Actualizado'
    assert call(client,'PUT',f"/scouts/{s['id']}",json=body)['nombres']=='Actualizado'
    assert call(client,'GET',f"/scouts/{s['id']}")['id']==s['id']
    assert len(call(client,'GET',f"/scouts?rama_id={records['rama']['id']}"))==3

def test_05_crud_actividad(client,records):
    a=records['actividad']; b={**records['body'],'titulo':'Título actualizado'}
    assert call(client,'PUT',f"/actividades/{a['id']}",json=b)['titulo']==b['titulo']
    assert call(client,'GET',f"/actividades/{a['id']}")['cupos_disponibles']==2
    assert any(i['id']==a['id'] for i in call(client,'GET',f"/actividades?rama_id={records['rama']['id']}"))

def test_06_crud_inscripcion_y_reactivar(client,records):
    i=enroll(client,records);id=i['id']
    assert call(client,'GET',f'/inscripciones/{id}')['estado']=='inscrito'
    assert len(call(client,'GET',f"/inscripciones?scout_id={i['scout_id']}"))==1
    call(client,'PUT',f'/inscripciones/{id}',json={'estado':'cancelado'})
    assert call(client,'GET',f"/actividades/{records['actividad']['id']}")['cupos_disponibles']==2
    assert call(client,'PUT',f'/inscripciones/{id}',json={'estado':'inscrito'})['estado']=='inscrito'
    call(client,'DELETE',f'/inscripciones/{id}',204)
    assert call(client,'GET',f"/actividades/{records['actividad']['id']}")['cupos_disponibles']==2

def test_07_duplicado_y_cupo(client,records):
    enroll(client,records);enroll(client,records,0,409);enroll(client,records,1);enroll(client,records,2,409)
    call(client,'PUT',f"/actividades/{records['actividad']['id']}",409,json={**records['body'],'cupo_maximo':1})

def test_08_ultimo_cupo_concurrente(client,records):
    call(client,'PUT',f"/actividades/{records['actividad']['id']}",json={**records['body'],'cupo_maximo':1})
    def attempt(n):
        return httpx.post(BASE+'/api/v1/inscripciones',headers={'Authorization':client.headers['Authorization']},json={'scout_id':records['scouts'][n]['id'],'actividad_id':records['actividad']['id']},timeout=15).status_code
    with ThreadPoolExecutor(max_workers=2) as pool: result=list(pool.map(attempt,[0,1]))
    assert sorted(result)==[201,409],result
    assert call(client,'GET',f"/actividades/{records['actividad']['id']}")['inscritos']==1

def test_09_rama_inactivos_y_referencias(client,records):
    s=records['scouts'][0]; b={k:s[k] for k in ['nombres','apellidos','rama_id','activo']}
    call(client,'PUT',f"/scouts/{s['id']}",json={**b,'activo':False});enroll(client,records,0,409)
    call(client,'PUT',f"/scouts/{s['id']}",json={**b,'rama_id':records['otra']['id']});enroll(client,records,0,409)
    call(client,'POST','/inscripciones',404,json={'scout_id':2147483647,'actividad_id':records['actividad']['id']})
    call(client,'POST','/scouts',404,json={'nombres':'Ficticio','apellidos':'Prueba','rama_id':2147483647})
    enroll(client,records,1)
    call(client,'DELETE',f"/scouts/{records['scouts'][1]['id']}",409)
    call(client,'DELETE',f"/actividades/{records['actividad']['id']}",409)
    call(client,'DELETE',f"/ramas/{records['rama']['id']}",409)

def test_10_estado_y_fechas(client,records):
    id=records['actividad']['id']
    for state in ['cerrada','cancelada']:
        call(client,'PUT',f'/actividades/{id}',json={**records['body'],'estado':state});enroll(client,records,0,409)
    past=datetime.now(timezone.utc)-timedelta(days=1)
    call(client,'PUT',f'/actividades/{id}',json={**records['body'],'inicio':past.isoformat()});enroll(client,records,0,409)

@pytest.mark.parametrize('change',[{'cupo_maximo':0},{'titulo':' '},{'fin':'2000-01-01T00:00:00Z'},{'inicio':'2030-01-01T09:00:00'},{'estado':'cualquiera'}])
def test_11_validacion(client,records,change):
    call(client,'POST','/actividades',422,json={**records['body'],**change})

def test_12_reactivar_sin_cupo_y_rama_cambiante(client,records):
    i=enroll(client,records)
    call(client,'PUT',f"/inscripciones/{i['id']}",json={'estado':'cancelado'})
    call(client,'PUT',f"/actividades/{records['actividad']['id']}",json={**records['body'],'cupo_maximo':1})
    enroll(client,records,1)
    call(client,'PUT',f"/inscripciones/{i['id']}",409,json={'estado':'inscrito'})
    s=records['scouts'][1];body={k:s[k] for k in ['nombres','apellidos','rama_id','activo']}
    call(client,'PUT',f"/scouts/{s['id']}",409,json={**body,'rama_id':records['otra']['id']})
    call(client,'PUT',f"/actividades/{records['actividad']['id']}",409,json={**records['body'],'rama_id':records['otra']['id']})

def test_99_rate_limiting_login(client):
    statuses=[client.post('/api/v1/auth/login',data={'username':'inexistente','password':'incorrecta'}).status_code for _ in range(15)]
    assert 429 in statuses,statuses
    # Nginx JSON response, not an exception or an application-side limiter.
    assert client.get('/health').status_code==200
