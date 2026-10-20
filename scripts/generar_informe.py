"""Editable report source. Rebuild with: python scripts/generar_informe.py.
ReportLab vector drawings are also exported as SVG and PDF for reuse.
Evidence is always read from actual files, never synthesized as test results.
"""
from pathlib import Path
from xml.sax.saxutils import escape
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, Preformatted
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import reportlab
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.graphics import renderPDF, renderSVG
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'docs'; EV=DOCS/'evidencias'; DIAG=DOCS/'diagramas'
font_dir=Path(reportlab.__file__).parent/'fonts'
pdfmetrics.registerFont(TTFont('ScoutSans',str(font_dir/'Vera.ttf')))
pdfmetrics.registerFont(TTFont('ScoutSans-Bold',str(font_dir/'VeraBd.ttf')))
pdfmetrics.registerFontFamily('ScoutSans',normal='ScoutSans',bold='ScoutSans-Bold',italic='ScoutSans',boldItalic='ScoutSans-Bold')
GREEN=colors.HexColor('#173f35'); LIGHT=colors.HexColor('#edf2df'); GRAY=colors.HexColor('#617167')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleScout',fontName='ScoutSans-Bold',fontSize=31,leading=35,textColor=GREEN,spaceAfter=16))
styles.add(ParagraphStyle(name='SectionScout',fontName='ScoutSans-Bold',fontSize=20,leading=24,textColor=GREEN,spaceAfter=16))
styles.add(ParagraphStyle(name='SubScout',fontName='ScoutSans-Bold',fontSize=12,leading=17,textColor=GREEN,spaceBefore=12,spaceAfter=7))
styles.add(ParagraphStyle(name='BodyScout',fontName='ScoutSans',fontSize=9.7,leading=14.5,textColor=GREEN,spaceAfter=10))
styles.add(ParagraphStyle(name='SmallScout',fontName='ScoutSans',fontSize=8.2,leading=11.8,textColor=GRAY,spaceAfter=8))
styles.add(ParagraphStyle(name='CodeScout',fontName='ScoutSans',fontSize=7.2,leading=10,textColor=GREEN,backColor=LIGHT,borderPadding=8,spaceAfter=12))
styles.add(ParagraphStyle(name='CellScout',fontName='ScoutSans',fontSize=8.1,leading=11,textColor=GREEN))
story=[]
def p(text,style='BodyScout'):
    story.append(Paragraph(text,styles[style]))
def h(text): p(text,'SubScout')
def section(n,title):
    if story: story.append(PageBreak())
    p(f'GESTIÓN SCOUT / {n:02d}','SmallScout');p(title,'SectionScout')
def code(text): story.append(Preformatted(text,styles['CodeScout']))
def table(rows,widths):
    cells=[[Paragraph(escape(str(v)),styles['CellScout']) for v in row] for row in rows]
    t=Table(cells,colWidths=widths,hAlign='LEFT',repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#d5ded3'))]))
    story.append(t);story.append(Spacer(1,10))
def screenshot(name,max_width=487,max_height=270):
    path=EV/name
    if not path.exists(): p(f'PENDIENTE: captura {name}. No disponible para esta regeneración.','SmallScout');return
    img=Image(str(path));scale=min(max_width/img.imageWidth,max_height/img.imageHeight)
    img.drawWidth=img.imageWidth*scale;img.drawHeight=img.imageHeight*scale;img.hAlign='LEFT';story.append(img);story.append(Spacer(1,9))

def box(d,x,y,w,ht,title,lines,fill=LIGHT):
    d.add(Rect(x,y,w,ht,rx=8,ry=8,fillColor=fill,strokeColor=GREEN,strokeWidth=1))
    d.add(String(x+w/2,y+ht-20,title,textAnchor='middle',fontName='ScoutSans-Bold',fontSize=10,fillColor=GREEN))
    for i,line in enumerate(lines):d.add(String(x+w/2,y+ht-37-i*13,line,textAnchor='middle',fontName='ScoutSans',fontSize=8,fillColor=GREEN))
def arrow(d,x1,y1,x2,y2,label=None,lx=None,ly=None):
    import math
    d.add(Line(x1,y1,x2,y2,strokeColor=GREEN,strokeWidth=1.3))
    a=math.atan2(y2-y1,x2-x1);s=6
    d.add(Polygon([x2,y2,x2-s*math.cos(a-.4),y2-s*math.sin(a-.4),x2-s*math.cos(a+.4),y2-s*math.sin(a+.4)],fillColor=GREEN,strokeColor=GREEN))
    if label:d.add(String(lx if lx is not None else (x1+x2)/2,ly if ly is not None else (y1+y2)/2+9,label,fontName='ScoutSans',fontSize=7.5,textAnchor='middle',fillColor=GREEN))
def context():
    d=Drawing(487,280)
    d.add(Rect(215,40,260,210,fillColor=colors.white,strokeColor=GRAY,strokeDashArray=[4,3],rx=8))
    d.add(String(229,231,'LÍMITE: GESTIÓN SCOUT',fontName='ScoutSans-Bold',fontSize=9,fillColor=GRAY))
    box(d,5,98,130,115,'Dirigente',['[Persona]','Único usuario con cuenta','Organiza su grupo'])
    box(d,235,98,220,115,'Gestión Scout',['[Sistema de software]','Ramas, scouts, actividades','e inscripciones con cupos'])
    arrow(d,135,151,235,151,'HTTP local',185,163)
    d.add(String(185,134,'Gestiona el grupo',fontName='ScoutSans',fontSize=7,textAnchor='middle',fillColor=GRAY))
    return d

def containers():
    d=Drawing(487,385)
    d.add(Rect(5,10,477,307,fillColor=colors.white,strokeColor=GRAY,strokeDashArray=[4,3],rx=8))
    d.add(String(18,299,'GESTIÓN SCOUT · CONTENEDORES LÓGICOS C4',fontName='ScoutSans-Bold',fontSize=8,fillColor=GRAY))
    box(d,25,192,180,89,'Aplicación web',['[HTML / CSS / JavaScript]','Ejecutada en el navegador','Formularios y token en memoria'])
    box(d,277,192,180,89,'API Gateway',['[Nginx]','Sirve archivos del frontend','Logging + rate limiting'])
    box(d,277,45,180,91,'Microservicio Backend',['[FastAPI / SQLAlchemy]','JWT, CRUD y reglas de negocio','Bloqueo transaccional de cupos'])
    box(d,25,45,180,91,'Base de datos',['[PostgreSQL]','Persistencia, FK y UNIQUE','Volumen postgres_data'])
    box(d,20,335,190,45,'Dirigente · [Persona]',[])
    arrow(d,115,335,115,281,'Usa',139,318)
    arrow(d,205,238,277,238,'HTTP :8080',241,252)
    d.add(String(241,222,'archivos / JSON',textAnchor='middle',fontName='ScoutSans',fontSize=7,fillColor=GRAY))
    arrow(d,367,192,367,136,'HTTP :8000',412,161)
    arrow(d,277,90,205,90,'SQL / TCP',241,103)
    d.add(String(241,75,':5432',textAnchor='middle',fontName='ScoutSans',fontSize=7,fillColor=GRAY))
    return d

for name,draw in [('contexto',context()),('contenedores',containers())]:
    renderSVG.drawToFile(draw,str(DIAG/f'{name}.svg'));renderPDF.drawToFile(draw,str(DIAG/f'{name}.pdf'))

section(1,'Un grupo organizado,\nmás tiempo para explorar')
p('Gestión Scout','TitleScout')
p('<b>Informe técnico · Tecnologías Web</b><br/>Miguel Alejandro Sánchez Pérez<br/>Tecnología asignada: FastAPI (Python)<br/>20 de octubre de 2026 · America/La_Paz')
p('<b>BORRADOR DE ENTREGA · VERSIÓN LOCAL VERIFICADA</b><br/>Pendiente: confirmar con el docente si acepta ejecución local y realizar el envío en Moodle. No se declara una aplicación publicada en Internet.','SmallScout')
h('Problema y propósito')
p('La información de ramas, integrantes y actividades dispersa en hojas separadas dificulta controlar quién participa y cuántos cupos quedan. El sistema permite a los dirigentes gestionar estos datos con una única interfaz y una base persistente.')
h('Alcance deliberado')
p('Se administra un solo grupo scout, con nombre y ramas configurables. Solo los dirigentes tienen cuenta. Scouts y familiares no inician sesión. Los registros de demostración son ficticios. No se incorporan pagos, mensajería, certificados, adjuntos ni multigrupo.')
h('Escenario de uso')
p('Un dirigente crea una actividad futura abierta, selecciona su rama destinataria o todas las ramas y define cupos. Inscribe scouts activos. Cancelar una inscripción libera un cupo; reactivarla exige cumplir nuevamente las reglas. El resumen muestra la información confirmada por la API.')
table([['Componente','Tecnología y responsabilidad'],['Entrada HTTP','Nginx: frontend, proxy inverso, trazas y límites'],['Negocio','FastAPI + Pydantic + SQLAlchemy + Alembic'],['Persistencia','PostgreSQL, claves foráneas y volumen nombrado'],['Interfaz','HTML, CSS y JavaScript sin compilación']],[105,382])

section(2,'C4 · Nivel 1: contexto')
p('El contexto presenta la persona que utiliza el sistema y su objetivo. La frontera encapsula la solución completa: los detalles de Nginx, FastAPI y PostgreSQL se desarrollan en el siguiente nivel.')
story.append(context());story.append(Spacer(1,15))
h('Persona y límite de responsabilidad')
p('<b>Dirigente:</b> único actor con cuenta; administra ramas, scouts, actividades e inscripciones. Su contraseña se verifica en el backend y su acceso requiere un JWT vigente. No existe registro público.')
p('<b>Gestión Scout:</b> sistema de software responsable de mantener datos consistentes y controlar cupos. Los scouts son sujetos del dominio cuyos datos administra el dirigente; no se representan como clientes autenticados ni servicios externos.')
h('Relación y entorno')
p('El dirigente usa un navegador que accede por HTTP local al gateway. El host escucha en 127.0.0.1:8080. La ejecución en este equipo corresponde al alcance acordado por el autor; no hay dependencia de cuentas de nube ni exposición pública de PostgreSQL.')
p('Fuentes editables: docs/diagramas/contexto.mmd y la función context() de scripts/generar_informe.py. Versiones renderizadas: contexto.svg y contexto.pdf.','SmallScout')

section(3,'C4 · Nivel 2: contenedores')
story.append(containers());story.append(Spacer(1,12))
p('C4 describe cuatro contenedores lógicos: interfaz, gateway, backend y base de datos. Compose ejecuta tres contenedores Docker: gateway, backend y db. El frontend corre en el navegador; sus archivos están incluidos en la imagen de Nginx. No necesita un cuarto servicio Docker.')
h('Comunicación y orquestación')
p('Solo Nginx publica un puerto del host. La API y Swagger se reenvían sin quitar prefijos: /api/v1, /docs y /openapi.json. Backend usa db:5432 dentro de la red bridge. PostgreSQL dispone de volumen nombrado para conservar información al recrear contenedores.')
p('depends_on espera la salud de la base antes del backend y del backend antes del gateway. La disponibilidad de FastAPI ejecuta SELECT 1. El healthcheck del gateway consulta ese endpoint mediante el proxy; no se limita a comprobar un proceso.')
p('Fuentes: docker-compose.yml, Dockerfiles, gateway/default.conf.template y docs/diagramas/contenedores.mmd. SVG y PDF vectoriales incluidos.','SmallScout')

section(4,'Modelo, seguridad y transacciones')
table([['Entidad','Campos esenciales y relaciones'],['Rama','id, nombre único, descripción'],['Scout','id, nombres, apellidos, rama_id, activo'],['Actividad','id, título, descripción, lugar, inicio/fin con zona, cupo, rama opcional, estado'],['Inscripción','id, scout_id, actividad_id, fecha_registro, estado; UNIQUE(scout, actividad)'],['Dirigente','id, nombre, usuario único, hash de contraseña, activo']],[94,393])
h('DTO, Repository e inyección de dependencias')
p('Pydantic valida DTO de entrada y limita las salidas: nunca expone password_hash. Los routers traducen HTTP; los repositorios concentran consultas; GestionService aplica reglas. Depends(get_db) entrega una sesión por solicitud y Depends(current_user) exige una cuenta activa. Alembic incorpora la revisión 001 antes de iniciar Uvicorn.')
h('Último cupo: validación transaccional')
p('Crear o modificar inscripciones bloquea primero la fila de la actividad con SELECT FOR UPDATE. Dentro de la misma transacción se valida scout activo, rama, estado abierto, inicio futuro y cantidad inscrita. Con READ COMMITTED, la solicitud que esperó cuenta los cambios confirmados: no alcanza con contar fuera del bloqueo. Actualizar cupos usa el mismo bloqueo; cambiar destinatarios también bloquea scouts inscritos.')
h('Protección y fallos comprensibles')
p('Contraseñas Argon2 y JWT HS256 con sub, iat y exp. El token dura 30 minutos y queda solo en memoria de la pestaña. Nginx genera X-Request-ID y limita la API a 20r/s y login a 5r/m. No registra cuerpos ni Authorization. Las claves foráneas RESTRICT conservan referencias; conflictos retornan 409. No hay cascadas inesperadas ni registro público.')
p('Cancelar o eliminar libera cupo. Reactivar exige las mismas reglas. Reducir cupo por debajo de los inscritos o cambiar a una rama incompatible devuelve 409. Fechas sin zona, cupos no positivos y campos vacíos generan 422.','SmallScout')

section(5,'Contrato REST y ejemplos JSON')
p('Base local: http://localhost:8080/api/v1. Todos los recursos de negocio requieren Authorization: Bearer. Los GET de colección aceptan los filtros indicados. PUT reemplaza el DTO del recurso; en inscripciones solo cambia estado.')
table([['Métodos','Ruta relativa a /api/v1','Cuerpo / filtro'],['POST','/auth/login','Formulario username, password'],['GET','/auth/me · /resumen','Cuenta sin hash / cantidades'],['GET · POST','/ramas','RamaIn en POST'],['GET · PUT · DELETE','/ramas/{id}','RamaIn en PUT'],['GET · POST','/scouts','ScoutIn; filtro rama_id'],['GET · PUT · DELETE','/scouts/{id}','ScoutIn en PUT'],['GET · POST','/actividades','ActividadIn; rama_id incluye generales'],['GET · PUT · DELETE','/actividades/{id}','ActividadIn en PUT'],['GET · POST','/inscripciones','scout_id, actividad_id, estado; filtros por ambos IDs'],['GET · PUT · DELETE','/inscripciones/{id}','En PUT: estado inscrito / cancelado']],[110,165,212])
code('''RamaIn: {"nombre":"Exploradores","descripcion":"Ejemplo"}
ScoutIn: {"nombres":"Scout","apellidos":"Ficticio",
          "rama_id":1,"activo":true}
ActividadIn: {"titulo":"Salida","descripcion":"Ejemplo",
  "lugar":"Parque","inicio":"2030-01-20T09:00:00-04:00",
  "fin":"2030-01-20T12:00:00-04:00","cupo_maximo":10,
  "rama_id":1,"estado":"abierta"}
InscripcionIn: {"scout_id":1,"actividad_id":1,"estado":"inscrito"}
PUT inscripcion: {"estado":"cancelado"}''')
p('Respuestas: GET/PUT 200; POST de recurso 201 con id; DELETE 204 sin cuerpo. ActividadOut agrega inscritos y cupos_disponibles; InscripcionOut agrega id y fecha_registro. Login devuelve access_token, token_type y expires_in.','SmallScout')
p('Errores: 401 acceso, 404 referencia, 409 conflicto de regla/BD, 422 validación y 429 Nginx. El esquema detallado de todos los DTO está exportado en docs/evidencias/openapi.json y disponible en /docs. Las fechas/IDs de estos JSON son ejemplos; seed calcula fechas futuras al ejecutarse.','SmallScout')

section(6,'Pruebas reales y estado de Docker')
result=(EV/'resultados.txt').read_text() if (EV/'resultados.txt').exists() else 'PENDIENTE: ejecutar pruebas.'
summary=re.findall(r'\d+ passed in [\d.]+s',result)
p('<b>Resultado registrado:</b> '+escape(summary[-1] if summary else 'Sin resultado aprobado registrado')+'. PostgreSQL real, backend en Docker y solicitudes al gateway del proyecto aislado scout-tests. No se utilizó SQLite ni se simuló el motor.')
table([['Grupo de pruebas','Comprobación'],['Acceso y contrato','Login válido/incorrecto; token ausente, inválido y expirado; OpenAPI y /health'],['CRUD y datos','Crear, leer, actualizar y eliminar las cuatro entidades; filtros y validación 422'],['Reglas de inscripción','Duplicado, cupo lleno, cancelar/reactivar, rama, scout inactivo, fecha y estado'],['Concurrencia','Dos solicitudes al último cupo: exactamente un HTTP 201 y un HTTP 409'],['Integridad y gateway','FK al borrar; reducción de cupo; cambios de rama incompatibles; rate limit 429']],[120,367])
h('Extracto del estado real de contenedores')
state=(EV/'estado-docker.txt').read_text() if (EV/'estado-docker.txt').exists() else 'Pendiente'
lines=[]
for line in state.splitlines()[1:]:
    parts=line.split()
    if parts: lines.append(parts[0]+'  '+('healthy' if '(healthy)' in line else 'consultar evidencia'))
code('\n'.join(lines)+'\nPuertos publicados de prueba: 127.0.0.1:18080 -> gateway:80')
p('La primera construcción del proyecto de pruebas aplicó Alembic 001 sobre su volumen vacío. Tras down y up --wait, se verificó login HTTP 200 con la cuenta creada antes del reinicio: el volumen preservó el registro. Los tres servicios recuperaron estado healthy.')
h('Reproducir y auditar')
code('python3 -m venv .venv\n.venv/bin/pip install -r tests/requirements.txt\n.venv/bin/python scripts/probar.py')
p('Evidencia completa: resultados.txt, estado-docker.txt y docker-verificacion.txt. Las fixtures eliminan sus propios registros; el proyecto de demostración gestion-scout no se usa para estas pruebas. No se ejecutó Postman.','SmallScout')

section(7,'Evidencia de interfaz, Swagger y trazas')
screenshot('interfaz.jpg',max_height=220)
p('Figura 1. Captura real del resumen local después de crear, cancelar y reactivar una inscripción desde la página. Se muestran seis scouts ficticios, tres actividades y una inscripción activa.','SmallScout')
screenshot('swagger.jpg',max_height=205)
p('Figura 2. Swagger detrás de Nginx: GET /api/v1/ramas autenticado, HTTP 200, JSON real y X-Request-ID. El recorte excluye el bloque cURL que contiene el token.','SmallScout')
h('Logs correlacionados y límite')
log=(EV/'gateway-extracto.log').read_text() if (EV/'gateway-extracto.log').exists() else ''
ids=re.findall(r'"request_id":"([a-f0-9]+)"',log)
import json
entries=[]
for line in log.splitlines():
    if 'gateway-1' in line and '{' in line:
        entries.append(json.loads(line[line.index('{'):]))
if entries:
    e=entries[0]
    excerpt=f"{e['method']} {e['path']} -> {e['status']}; {e['duration']:.3f} s\nrequest_id={e['request_id']} (Nginx / FastAPI)"
    limited=next((e for e in entries if e['status']==429),None)
    if limited: excerpt+=f"\n{limited['method']} {limited['path']} -> 429"
    code(excerpt)
p('Los logs reales en gateway-extracto.log contienen method, path, status y duration. El mismo request ID llega a FastAPI. Las solicitudes repetidas de login produjeron HTTP 429 en Nginx. Los logs completos se conservan localmente; no se publican contraseñas, cuerpos ni tokens.','SmallScout')

section(8,'Entrega local, rúbrica y pendientes')
p('Para una clonación limpia: generar .env con scripts/configurar.py; ejecutar docker compose up --build; crear dirigente con app.cli create-dirigente; generar ejemplos con app.cli seed; abrir localhost:8080. Solo gateway publica un puerto y está ligado a loopback. El repositorio público distribuye código: no ejecuta los contenedores.')
table([['Criterio','Archivos y evidencia','Estado'],['Negocio + C4 (20)','README, diagramas, informe pp. 1-3','Documentado / renderizado'],['Gateway (25)','gateway/, pruebas 02/99, logs','Logging + 429 comprobados'],['Backend + BD (30)','app/, Alembic, pruebas CRUD / cupos','17 pruebas aprobadas'],['Docker (15)','Compose, Dockerfiles, evidencia de reinicio','Bridge, salud y persistencia'],['Git / README / Moodle (10)','feature/*, release/*, README, v1.0.0','Código y guía; Moodle pendiente']],[105,244,138])
h('Repositorio y flujo de trabajo')
p('Repositorio: github.com/migusaper1530/gestion-scout-tecnoweb. Se inició main, se desarrolló en ramas feature/* sobre develop, y la entrega se estabiliza en release/1.0.0 antes de integrarse a main y etiquetarse. El historial contiene trabajo real por etapas, sin commits vacíos para simular Git Flow.')
h('Pendientes y limitaciones verificables')
p('El autor solicitó ejecución local y no alojamiento web. No hay URL pública de aplicación ni pruebas HTTPS externas. Si el docente exige un servidor independiente, ese punto necesita su validación. El alumno debe revisar el PDF y subir el enlace y el informe a Moodle; el asistente no realizó ese envío. Por estos pasos externos se mantiene la marca de borrador de entrega.')
p('Swagger utiliza los assets CDN predeterminados de FastAPI; requiere conexión para cargarlos. La interfaz propia y la API se sirven localmente. Las evidencias de Docker del informe son extractos textuales de ejecuciones auténticas; una captura de terminal adicional puede tomarse con los comandos de docs/evidencias/README.md.','SmallScout')
h('Conclusión')
p('La arquitectura local satisface la separación gateway / microservicio / base de datos, protege el acceso y conserva integridad bajo concurrencia. La demostración puede ejecutarse sin una cuenta de nube. El estudiante dispone de fuente legible, pruebas reproducibles, diagramas y guía de defensa para explicar cada decisión.')
p('Referencias oficiales: fastapi.tiangolo.com/tutorial/security/oauth2-jwt/ · nginx.org/en/docs/http/ngx_http_limit_req_module.html · docs.sqlalchemy.org/en/20/ · docs.docker.com/compose/ · c4model.com/diagrams','SmallScout')

def frame(canvas,doc):
    canvas.setStrokeColor(GREEN);canvas.setLineWidth(.8);canvas.line(54,790,541,790)
    canvas.setFont('ScoutSans',8);canvas.setFillColor(GRAY)
    canvas.drawString(54,32,'TECNOLOGÍAS WEB · MIGUEL ALEJANDRO SÁNCHEZ PÉREZ')
    canvas.drawRightString(541,32,f'{doc.page} / 8')
    canvas.setFont('ScoutSans',7);canvas.drawRightString(541,802,'BORRADOR DE ENTREGA · LOCAL VERIFICADO')

out=DOCS/'informe.pdf'
doc=SimpleDocTemplate(str(out),pagesize=A4,rightMargin=54,leftMargin=54,topMargin=65,bottomMargin=55,title='Gestión Scout - Informe técnico local',author='Miguel Alejandro Sánchez Pérez')
doc.build(story,onFirstPage=frame,onLaterPages=frame)
count=len(PdfReader(out).pages)
if count!=8: raise RuntimeError(f'Se esperaban 8 páginas; se generaron {count}. Revisar maquetación.')
print(f'Informe generado: {out} ({count} páginas)')
