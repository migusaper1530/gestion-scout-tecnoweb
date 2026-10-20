"""Disposable Compose project. Keep its volume for restart evidence, clean explicitly."""
from pathlib import Path
import json, os, secrets, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work=ROOT/'work'; work.mkdir(exist_ok=True)
from dotenv import dotenv_values
config=dotenv_values(ROOT/'.env')
env={**os.environ,**{k:str(v) for k,v in config.items()},'GATEWAY_PORT':'18080'}
compose=['docker','compose','-p','scout-tests','-f','docker-compose.yml','-f','docker-compose.test.yml']
def run(args,**kwargs): return subprocess.run(args,env=env,check=True,**kwargs)
run(compose+['up','--build','-d','--wait'],timeout=600)
credentials={'usuario':'test-'+secrets.token_hex(6),'password':secrets.token_urlsafe(24)}
run(compose+['exec','-T','backend','python','-c',(ROOT/'tests/crear_usuario.py').read_text()],input=json.dumps(credentials),text=True)
env.update(TEST_USER=credentials['usuario'],TEST_PASSWORD=credentials['password'],BASE_URL='http://127.0.0.1:18080')
evidence=ROOT/'docs/evidencias';evidence.mkdir(exist_ok=True)
with (evidence/'resultados.txt').open('w') as f:
    result=subprocess.run([sys.executable,'-m','pytest','tests/test_integracion.py','-v','--tb=short'],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    f.write(result.stdout);print(result.stdout)
run(compose+['ps'],stdout=(evidence/'estado-docker.txt').open('w'))
# Enrollment fixtures remove only their own records; account persists across restart.
run(compose+['down'])
run(compose+['up','-d','--wait'])
import httpx
r=httpx.post(env['BASE_URL']+'/api/v1/auth/login',data={'username':credentials['usuario'],'password':credentials['password']})
assert r.status_code==200,'El dirigente no sobrevivió al reinicio'
with (evidence/'docker-verificacion.txt').open('w') as f:
    f.write('Migración 001 desde volumen aislado inicialmente vacío; servicios saludables.\n')
    f.write('docker compose down + up --wait: login del dirigente persistente = HTTP 200.\n')
    run(compose+['ps'],stdout=f)
with (evidence/'gateway.log').open('w') as f: run(compose+['logs','--no-color','gateway','backend'],stdout=f)
# Leave container running for inspection. The documented cleanup removes only test data.
sys.exit(result.returncode)
