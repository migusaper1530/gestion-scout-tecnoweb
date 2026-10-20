# Ejecución local

Por decisión del autor, Docker se ejecuta únicamente en su equipo. La aplicación se abre en http://localhost:8080, con Nginx como única entrada. No se ha publicado una aplicación en Internet ni se requiere Oracle Cloud, dominio, certificado público o Cloudflare.

## Iniciar

```bash
python3 scripts/configurar.py  # solo la primera vez
docker compose up --build -d --wait
docker compose ps
curl -fsS http://127.0.0.1:8080/health
```

BIND_ADDRESS=127.0.0.1 restringe la escucha al mismo equipo. No cambiarla para esta entrega local. FastAPI y PostgreSQL no publican puertos. La red bridge comunica internamente gateway, backend y db.

## Detener, actualizar y recuperar

`docker compose stop` detiene los servicios. `docker compose start` vuelve a iniciarlos. `docker compose down` elimina contenedores y red, pero conserva el volumen con la base. Luego `docker compose up -d --wait` recupera los datos. **`docker compose down -v` elimina el volumen y la información.**

Antes de actualizar hacer respaldo; después `git pull --ff-only`, `docker compose up --build -d --wait`, `docker compose ps` y la comprobación de /health. Alembic aplica migraciones pendientes al arrancar.

```bash
mkdir -p backups
docker compose exec -T db pg_dump -U scout -d scout -Fc > backups/scout.dump
# Restauración: detener las escrituras y volver a iniciar al terminar.
docker compose stop gateway backend
cat backups/scout.dump | docker compose exec -T db pg_restore -U scout -d scout --clean --if-exists --no-owner --exit-on-error
docker compose up -d --wait
```

La copia contiene hashes de contraseñas: mantenerla privada y fuera de Git. Cambiar POSTGRES_PASSWORD en .env no modifica la contraseña de una base ya creada. Es necesario rotarla también en PostgreSQL durante mantenimiento.

## Alcance académico

La rúbrica original menciona desplegar y entregar un repositorio público. Aquí se entrega un despliegue local con Compose y un repositorio de código público; no se afirma tener alojamiento público. Si el profesor exige específicamente acceso desde Internet, esa parte queda pendiente por la decisión de trabajar solo localmente. No se verificó HTTPS público porque queda fuera de este alcance.
