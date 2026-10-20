# Gestión Scout · Tecnologías Web

**Autor:** Miguel Alejandro Sánchez Pérez. **Backend asignado:** FastAPI (Python).

Aplicación académica para un grupo scout: sus dirigentes administran ramas, scouts, actividades e inscripciones. El grupo y los nombres de ramas son configurables. Solo los dirigentes tienen cuenta. No hay registro público, pagos, mensajería, archivos ni datos reales de menores.

**Ejecución exclusivamente local**, por decisión del autor. Aplicación: http://localhost:8080 · Swagger: http://localhost:8080/docs · OpenAPI: http://localhost:8080/openapi.json. El repositorio público contiene el código; no hospeda la aplicación.

## Arquitectura

```text
Dirigente → navegador (HTML/CSS/JS)
                ↓ HTTP http://localhost:8080
        Nginx: frontend + API Gateway
                ↓ HTTP backend:8000
        FastAPI: JWT / DTO / servicios / repositorios
                ↓ PostgreSQL protocol db:5432
        PostgreSQL → volumen postgres_data
```

Nginx sirve frontend/ y conserva las rutas `/api/v1`, `/docs` y `/openapi.json` al reenviar al backend. Solo gateway publica `127.0.0.1:8080`; backend y db no tienen ports en Compose. La red scout_net usa bridge. Los contenedores lógicos C4 incluyen el frontend ejecutado en el navegador; sus archivos se entregan desde el mismo contenedor Docker de Nginx. Diagramas y fuentes: [docs/diagramas](docs/diagramas).

## Arranque desde una clonación limpia

Requisitos: Git, Python 3 (para generar configuración), Docker Engine con acceso al motor y Docker Compose. Comprobar `docker version` y `docker compose version`. La [instalación oficial para Ubuntu](https://docs.docker.com/engine/install/ubuntu/) explica cómo configurar el repositorio. Si aparece permission denied, usar una sesión con permisos Docker; después de agregar el usuario al grupo docker hay que cerrar e iniciar sesión de nuevo.

```bash
git clone https://github.com/migusaper1530/gestion-scout-tecnoweb.git
cd gestion-scout-tecnoweb
python3 scripts/configurar.py
docker compose up --build -d --wait
docker compose ps
curl -fsS http://localhost:8080/health
```

El configurador genera .env con secretos aleatorios y permisos 600; nunca sobrescribe un archivo existente. No subirlo a Git. Después de esa configuración inicial, también se puede ejecutar `docker compose up --build` en primer plano. `docker-compose up` es la sintaxis antigua que menciona el profesor; aquí se utiliza el plugin moderno `docker compose` con el mismo archivo.

Crear cuenta del dirigente (contraseña interactiva, mínimo 12 caracteres):

```bash
docker compose exec backend python -m app.cli create-dirigente --usuario miguel --nombre 'Miguel Alejandro Sánchez Pérez'
docker compose exec backend python -m app.cli seed
```

El seed genera tres ramas, seis scouts y tres actividades futuras ficticias; repetirlo conserva los existentes y no duplica los ejemplos. Si pasó la fecha de una actividad ya generada, editar su horario desde la interfaz o crear otra: seed no modifica datos existentes.

En el equipo de desarrollo ya hay una cuenta `miguel` y una inscripción de demostración. Su contraseña aleatoria se guarda **solo localmente** en `work/acceso-local.txt` (ignorado por Git). No es una contraseña por defecto y no existe al clonar.

## Primera inscripción en la página

1. Abrir http://localhost:8080 e ingresar con la cuenta creada.
2. Consultar Ramas y Scouts; crear nuevos registros si no se usó seed.
3. En Actividades, crear una actividad abierta, con inicio futuro, fin posterior y cupos positivos. Elegir una rama o Todas las ramas.
4. En Inscripciones, Nueva inscripción, seleccionar un scout activo y una actividad compatible. Guardar.
5. Cancelar libera cupo; Reactivar vuelve a validar todas las reglas. El resumen muestra las inscripciones activas.

Las fechas se reciben con zona horaria y se muestran en America/La_Paz (UTC-4). El formulario interpreta sus horas como hora de La Paz, aunque el equipo use otra zona.

## Configuración y archivos

| Variable | Uso / valor inicial |
|---|---|
| POSTGRES_PASSWORD | Secreto aleatorio; nunca vacío |
| JWT_SECRET | Secreto aleatorio de al menos 32 caracteres |
| GROUP_NAME | Nombre del grupo; editar y recrear backend |
| TOKEN_MINUTES | Duración JWT: 30 minutos; entre 1 y 1440 |
| BIND_ADDRESS / GATEWAY_PORT | 127.0.0.1 / 8080; solo este equipo |
| API_RATE / LOGIN_RATE | 20r/s / 5r/m por IP; burst 50 / 5 |
| PUBLIC_SCHEME | http para este despliegue local |

Cambiar valores: editar .env y `docker compose up -d --force-recreate`. Los nombres y descripciones de ramas se modifican por CRUD. DATABASE_URL se compone internamente en Compose y no publica PostgreSQL. Las dependencias directas están en backend/requirements.txt; backend/requirements.lock fija todas las resueltas para construir la imagen. Las bases Python y Nginx están fijadas por versión y digest; PostgreSQL por versión.

```text
backend/app/routers/       Contrato y controladores HTTP
backend/app/schemas.py    DTO de entrada y salida (Pydantic)
backend/app/services/     Reglas y transacciones
backend/app/repositories/ Consultas de ramas/scouts/actividades/inscripciones
backend/app/models.py     ORM SQLAlchemy y restricciones
backend/app/security.py   Hash Argon2, JWT y dependencia de autenticación
backend/alembic/          Migración 001 versionada
frontend/                Página sin compilación; fetch a rutas relativas
gateway/                 Dockerfile y plantilla Nginx
scripts/                 Configuración, pruebas e informe reproducible
tests/                   Integración HTTP real y concurrencia
docs/                    Informe, C4, defensa y evidencias
```

## Reglas de negocio y persistencia

- Scout activo, rama compatible, actividad abierta y aún no iniciada, cupo disponible.
- UNIQUE(scout_id, actividad_id) en PostgreSQL impide duplicados. Para volver a participar se reactiva el registro cancelado.
- Crear, cancelar, reactivar y eliminar inscripciones bloquea la fila de la actividad (`SELECT ... FOR UPDATE`) antes de modificar su cupo. Con READ COMMITTED, una transacción que esperó vuelve a contar los cambios confirmados.
- La actualización de actividad usa el mismo bloqueo: no permite cupo inferior a sus inscritos. Un cambio de rama incompatible requiere cancelar inscripciones primero; se bloquean también scouts al cambiar la rama destinataria.
- Claves foráneas RESTRICT impiden huérfanos y borrados en cascada. Las referencias o duplicados devuelven 409 comprensible.
- Inicio anterior a fin, fechas con zona horaria, textos no vacíos y cupos positivos se validan mediante DTO y restricciones de BD.
- PUT reemplaza los campos de ramas, scouts y actividades; en inscripciones actualiza únicamente estado, conservando sus dos referencias y fecha de registro.

No se usa create_all al arrancar. start.sh espera acceso a PostgreSQL y ejecuta `alembic upgrade head` antes de Uvicorn. Comprobar:

```bash
docker compose exec backend alembic current
docker compose exec db psql -U scout -d scout -c 'SELECT * FROM alembic_version;'
```

## API y ejemplos cURL

El contrato completo está en Swagger y en docs/evidencias/openapi.json. Para Authorize de Swagger ingresar usuario y contraseña; tokenUrl es `/api/v1/auth/login`, accesible a través de Nginx.

| Método | URL bajo /api/v1 | Cuerpo / filtros | Respuesta |
|---|---|---|---|
| POST | /auth/login | form username, password | 200 JWT, expires_in |
| GET | /auth/me | Bearer | 200 dirigente sin hash |
| GET | /resumen | Bearer | cantidades y grupo |
| GET, POST | /ramas | Rama JSON en POST | 200 lista / 201 creado |
| GET, PUT, DELETE | /ramas/{id} | Rama JSON en PUT | 200 / 200 / 204 |
| GET, POST | /scouts | ?rama_id=1; Scout JSON | 200 / 201 |
| GET, PUT, DELETE | /scouts/{id} | Scout JSON en PUT | 200 / 200 / 204 |
| GET, POST | /actividades | ?rama_id=1 incluye generales; Actividad JSON | 200 / 201 |
| GET, PUT, DELETE | /actividades/{id} | Actividad JSON en PUT | 200 / 200 / 204 |
| GET, POST | /inscripciones | ?actividad_id=1&scout_id=1; Inscripción JSON | 200 / 201 |
| GET, PUT, DELETE | /inscripciones/{id} | {"estado":"cancelado"} en PUT | 200 / 200 / 204 |

HTTP de error: 401 token ausente/inválido/vencido o login incorrecto; 404 referencia inexistente; 409 regla/duplicado/referencia; 422 entrada inválida; 429 límite de Nginx. Los endpoints de negocio siempre requieren Bearer en el backend.

Ejemplos copiables en Bash (se requiere Python 3 para leer JSON). No guardar el token en archivos públicos ni capturarlo en pantalla:

```bash
export BASE_URL=http://localhost:8080
read -r -p 'Usuario: ' SCOUT_USER
read -r -s -p 'Contraseña: ' SCOUT_PASSWORD; echo
TOKEN=$(curl -fsS "$BASE_URL/api/v1/auth/login" \
  --data-urlencode "username=$SCOUT_USER" --data-urlencode "password=$SCOUT_PASSWORD" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
unset SCOUT_PASSWORD
curl -fsS "$BASE_URL/api/v1/resumen" -H "Authorization: Bearer $TOKEN"
RAMA_ID=$(curl -fsS -X POST "$BASE_URL/api/v1/ramas" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"nombre":"Rama de demostración","descripcion":"Ficticia"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
SCOUT_ID=$(curl -fsS -X POST "$BASE_URL/api/v1/scouts" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d "{\"nombres\":\"Scout\",\"apellidos\":\"Ficticio\",\"rama_id\":$RAMA_ID,\"activo\":true}" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
# Fechas futuras calculadas al ejecutar, con offset explícito.
ACTIVIDAD_JSON=$(RAMA_ID="$RAMA_ID" python3 - <<'PY'
import os,json
from datetime import datetime,timedelta,timezone
inicio=datetime.now(timezone.utc)+timedelta(days=7)
print(json.dumps(dict(titulo='Salida ficticia',descripcion='Ejemplo',lugar='Parque',inicio=inicio.isoformat(),fin=(inicio+timedelta(hours=2)).isoformat(),cupo_maximo=5,rama_id=int(os.environ['RAMA_ID']),estado='abierta')))
PY
)
ACTIVIDAD_ID=$(curl -fsS -X POST "$BASE_URL/api/v1/actividades" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d "$ACTIVIDAD_JSON" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
INSCRIPCION_ID=$(curl -fsS -X POST "$BASE_URL/api/v1/inscripciones" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d "{\"scout_id\":$SCOUT_ID,\"actividad_id\":$ACTIVIDAD_ID}" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["id"])')
curl -fsS "$BASE_URL/api/v1/actividades/$ACTIVIDAD_ID" -H "Authorization: Bearer $TOKEN"
curl -fsS -X PUT "$BASE_URL/api/v1/inscripciones/$INSCRIPCION_ID" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{"estado":"cancelado"}'
curl -fsS -X DELETE "$BASE_URL/api/v1/inscripciones/$INSCRIPCION_ID" -H "Authorization: Bearer $TOKEN"
unset TOKEN
```

Ejemplo de respuesta de una actividad recién inscrita: `{"id":1,"titulo":"Salida ficticia","descripcion":"Ejemplo","lugar":"Parque","inicio":"2030-01-20T12:00:00Z","fin":"2030-01-20T14:00:00Z","cupo_maximo":5,"rama_id":1,"estado":"abierta","inscritos":1,"cupos_disponibles":4}`. IDs y fechas son ilustrativos; los comandos calculan fechas futuras reales.

## Gateway: dos características comprobadas

1. **Logging centralizado:** JSON en stdout con method, path, status, duration y request_id; Nginx genera y propaga X-Request-ID, FastAPI lo incluye en su log y respuesta. Se registra `$uri`, sin query strings, cuerpos, tokens o contraseñas.
2. **Rate limiting:** limit_req por IP en la API; login tiene zona propia, más estricta; HTTP 429 en JSON. API_RATE y LOGIN_RATE son configurables. No requiere CORS porque frontend y API comparten origen. No se cuenta JWT del backend como característica de Nginx.

Nginx sobrescribe encabezados reenviados e identifica al cliente por su conexión; Uvicorn no confía en proxy headers arbitrarios. Para esta entrega se usa HTTP en loopback; no se afirma configurar o probar HTTPS público.

```bash
docker compose logs --tail=30 gateway backend
# Desde una terminal: debe aparecer al menos un 429, sin autenticarse.
for i in $(seq 1 15); do
  curl -s -o /dev/null -w '%{http_code}\n' -X POST "$BASE_URL/api/v1/auth/login" \
    -d 'username=inexistente&password=incorrecta'
done
```

Después de esa prueba esperar a que se recargue el límite o reiniciar solo gateway antes de volver a entrar. Docker ps muestra 8000/tcp y 5432/tcp internos; únicamente una flecha `127.0.0.1:8080->80` representa un puerto publicado.

## Pruebas ejecutadas y reproducción

**17 pruebas de integración aprobadas** con PostgreSQL 17.6 real, Python 3.13 en backend y solicitudes HTTP a Nginx. Incluyen CRUD de las cuatro entidades, autenticación válida/incorrecta/ausente/expirada, 422, referencias, duplicados, rama, inactivos, cupos, cancelación/reactivación y competencia de dos solicitudes por el último cupo (201 y 409). No se usó SQLite ni un mock de PostgreSQL.

Se comprobó migración 001 desde el volumen de pruebas vacío, healthchecks y persistencia del dirigente después de down/up. También se usó el navegador para login, inscripción, cancelación, reactivación, resumen y Authorize + GET de Swagger. Las capturas y logs son auténticos. No se ejecutó Postman: no se presenta como herramienta utilizada.

```bash
python3 -m venv .venv
.venv/bin/pip install -r tests/requirements.txt
.venv/bin/python scripts/probar.py
```

El script usa proyecto Compose `scout-tests`, puerto 18080 y volumen propio; crea un usuario aleatorio y eleva el límite general de la API para que no interfiera con el CRUD. Mantiene el límite estricto de login. Deja su volumen y contenedores para inspección. Para liberar solo los contenedores de prueba: `docker compose -p scout-tests -f docker-compose.yml -f docker-compose.test.yml down`. Si se desea repetir específicamente la migración desde cero, se puede eliminar **solo el volumen de pruebas** añadiendo `-v`; esto borra únicamente los datos de scout-tests, no los de gestion-scout.

Evidencias: [docs/evidencias/README.md](docs/evidencias/README.md). Informe PDF y fuente editable: [docs/informe.pdf](docs/informe.pdf) y [scripts/generar_informe.py](scripts/generar_informe.py). Regenerar: instalar `docs/requirements.txt` y ejecutar `python scripts/generar_informe.py`. El generador usa las evidencias existentes; no inventa pruebas ni toma capturas automáticamente.

## Operación y problemas habituales

[Guía de operación local y respaldo/restauración](docs/DESPLIEGUE.md). `docker compose stop` detiene; `docker compose up -d --wait` inicia; `docker compose down` conserva el volumen; **down -v elimina la información**.

- Puerto ocupado: cambiar GATEWAY_PORT en .env y usar esa URL. Probar con `docker compose ps`.
- Backend no saludable: revisar `docker compose logs backend db`; verificar .env y migración. No borrar volúmenes para ocultar un problema.
- Error 409 al borrar una rama/scout/actividad: primero resolver sus referencias; no hay cascadas.
- Error 401 tras 30 minutos o al recargar la página: volver a entrar; el token se mantiene solo en memoria.
- Error 429: esperar o reiniciar gateway durante una demostración controlada. No cambiar de usuario para evadir el límite, porque se aplica por IP.
- Redockerizar no cambia los datos del volumen; las contraseñas de PostgreSQL existentes tampoco cambian solo editando .env.
- Swagger carga sus assets desde el CDN predeterminado de FastAPI. Se necesita conexión para cargar esos recursos; la aplicación y la API siguen siendo locales.

## Git Flow y entrega

Historial real desde el inicio: main → develop → feature/backend, feature/interfaz-gateway, feature/pruebas y feature/documentacion; integración con merges no fast-forward. Estabilización en release/1.0.0, integración a main/develop y etiqueta v1.0.0. Los commits se atribuyen al asistente con identidad local Codex <codex@localhost>; no se suplanta el correo personal del estudiante. No se fabrican commits vacíos ni hotfix sin incidencia.

```bash
git log --graph --oneline --all --decorate
```

Repositorio público autorizado: https://github.com/migusaper1530/gestion-scout-tecnoweb. Para Moodle entregar su enlace y docs/informe.pdf. Revisar los pendientes indicados en el informe antes de subirlo. [Guía breve de defensa](docs/DEFENSA.md).

| Rúbrica | Archivos / evidencia | Estado |
|---|---|---|
| Caso de negocio y C4 · 20 | README, docs/diagramas, informe páginas 1-3 | Documentado; diagramas renderizados |
| API Gateway · 25 | gateway/, gateway-extracto.log, pruebas 02 y 99 | Nginx real, logging y 429 verificados |
| Backend y BD · 30 | backend/app, alembic, tests/test_integracion.py | CRUD, JWT, patrones y concurrencia verificados |
| Docker Compose · 15 | Dockerfiles, docker-compose.yml, docker-verificacion.txt | Tres healthchecks, bridge, migración y persistencia verificados |
| Git Flow, README y Moodle · 10 | ramas y etiqueta, README, informe.pdf | Git y documentación preparados/publicados; envío Moodle pendiente del alumno |

No hay URL pública de aplicación por decisión del autor. Si el docente exige despliegue externo, esa exigencia queda pendiente. No se ha accedido ni enviado nada a Moodle.
