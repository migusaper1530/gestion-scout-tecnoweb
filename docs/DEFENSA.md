# Defensa oral: Gestión Scout

**Problema:** un dirigente necesita organizar integrantes y cupos sin hojas separadas. Se modela un solo grupo, con ramas configurables. Solo los dirigentes acceden; no hay cuentas de menores.

| Concepto | Cómo explicarlo con el proyecto |
|---|---|
| API Gateway | Nginx es el punto HTTP público. Entrega HTML y dirige `/api/v1`, `/docs` y `/openapi.json` al backend. |
| Proxy inverso | El cliente conoce Nginx; Nginx hace la solicitud a `backend:8000`. No publicamos ese puerto ni el de PostgreSQL. |
| Características transversales | Nginx registra método, ruta, estado, duración y request ID; limita solicitudes por IP, especialmente login. |
| Microservicio | FastAPI concentra el dominio scout y expone un contrato HTTP JSON. Hay un solo servicio de negocio: no se divide artificialmente en cuatro servicios. |
| ORM | SQLAlchemy representa filas mediante clases como Scout; genera SQL parametrizado y maneja sesiones y transacciones. |
| DTO | `ActividadIn` valida campos y fechas; `ActividadOut` añade cupos disponibles. El hash del dirigente nunca forma parte de la salida. |
| Repository | `ActividadRepository.inscritos` reúne consultas; el servicio decide si aún se puede inscribir. |
| Inyección de dependencias | `Depends(get_db)` proporciona una sesión por solicitud; `Depends(current_user)` exige una cuenta activa. |
| JWT | Token firmado con HS256, con sub, iat y exp. No es cifrado. El navegador lo conserva en memoria y lo envía con Bearer. |
| Hash | Argon2 convierte la contraseña en un valor verificable, no reversible. La contraseña no se guarda en texto plano. |
| Transacción | Se bloquea la fila de la actividad con FOR UPDATE, se cuenta, se valida y se confirma. Dos solicitudes al último cupo se serializan: una obtiene 201 y la otra 409. |
| Bridge | Los tres servicios resuelven sus nombres por la red de Compose. Solo Nginx publica un puerto del host. |
| Volumen | `postgres_data` persiste los datos aunque se eliminen los contenedores. `down -v` borra ese volumen. |
| Healthcheck | PostgreSQL responde pg_isready; FastAPI ejecuta SELECT 1; Nginx consulta ese health a través del proxy. |
| Migración | Alembic aplica la revisión 001 una sola vez y conserva el historial en alembic_version. No dependemos de create_all. |
| Git Flow | Se inició main, se trabajó en feature/* sobre develop y se estabiliza en release/1.0.0; main representa la entrega etiquetada. |

## Demostración de cinco minutos

1. `docker compose ps`: mostrar los tres servicios saludables y un único puerto publicado.
2. Entrar por http://localhost:8080 y mostrar el resumen.
3. Crear una rama y dos scouts ficticios. Crear una actividad con cupo 1.
4. Inscribir al primero; explicar el conflicto al intentar inscribir al segundo.
5. Cancelar la primera inscripción e inscribir al segundo. Mostrar Swagger con Authorize.
6. Mostrar `docs/evidencias/resultados.txt` y la prueba de dos solicitudes concurrentes.
7. Mostrar los logs con el mismo request ID y el historial de ramas de Git.

## Decisiones y límites que hay que reconocer

- El navegador y Swagger comparten origen; CORS no es necesario. Las dos características del gateway son logging y rate limiting.
- Todas las operaciones de capacidad bloquean la actividad antes de contar. Las claves foráneas impiden huérfanos y la restricción UNIQUE evita duplicados incluso frente a concurrencia.
- Una inscripción cancelada conserva su historial y puede reactivarse; eliminarla también libera cupo.
- El login no tiene registro público ni refresh token. Recargar la pestaña pide iniciar sesión otra vez.
- Los datos de ejemplo son ficticios y el comando seed es idempotente por nombre/título. No elimina ni reprograma registros existentes.
- Se eligió ejecución local: Docker corre en el equipo del estudiante y Nginx escucha en 127.0.0.1:8080. No hay URL pública de la aplicación. Si el profesor exige Internet, ese requisito se declara pendiente.
- No confiamos en X-Forwarded-For recibido del cliente. Nginx genera un request ID y sobrescribe los encabezados del proxy.
