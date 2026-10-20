# Evidencias reales

- `resultados.txt`: salida íntegra de pytest contra Nginx y PostgreSQL en el proyecto Compose aislado scout-tests. 17 casos aprobados.
- `estado-docker.txt`: estado real de los tres contenedores de prueba saludables.
- `docker-verificacion.txt`: resultado de login después de `down` y `up`, manteniendo el volumen.
- `gateway-extracto.log`: extracto sin secretos de logs reales; correlación de request ID y respuesta 429.
- `interfaz.jpg`, `interfaz-movil.jpg`: capturas reales del resumen con datos ficticios.
- `swagger.jpg`: captura real de GET /api/v1/ramas con HTTP 200. Recortada desde la URL y respuesta para no publicar el Bearer token del bloque cURL.
- `navegador.txt`: pasos manuales ejecutados y observaciones.
- `openapi.json`: contrato exportado desde el gateway.

Regenerar las pruebas: `python scripts/probar.py` tras instalar tests/requirements.txt en un entorno virtual. Los logs completos se guardan localmente en gateway.log (ignorado por Git); no contienen cabeceras de autorización, cuerpos o contraseñas. Para renovar capturas, abrir `/`, ingresar, crear una inscripción ficticia y capturar el resumen; en `/docs` autorizar, ejecutar GET /api/v1/ramas y capturar únicamente la URL y la respuesta, excluyendo el bloque cURL que muestra el token. Para una captura de terminal adicional, ejecutar `docker compose ps` y `docker compose logs --tail=20 gateway backend` y usar la captura del sistema. El informe incluye los extractos textuales auténticos del estado y logs, no una imagen fabricada de terminal.
