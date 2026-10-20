'use strict';
// Tokens remain in tab memory and disappear on reload. No user HTML is injected.
let token = null, expiresAt = 0, expiryTimer = null, view = 'resumen', editing = null;
let data = {ramas: [], scouts: [], actividades: [], inscripciones: []};
const $ = s => document.querySelector(s);
const labels = {resumen:'Resumen', ramas:'Ramas', scouts:'Scouts', actividades:'Actividades', inscripciones:'Inscripciones'};
const singular = {ramas:'rama',scouts:'scout',actividades:'actividad',inscripciones:'inscripción'};
function node(tag, text, cls) { const e = document.createElement(tag); if(text !== undefined) e.textContent = text; if(cls) e.className = cls; return e; }
function notify(text, error=false) { $('#notice').textContent=text; $('#notice').className=error?'error':''; $('#notice').hidden=false; }
function logout() { token=null; clearTimeout(expiryTimer); $('#app').hidden=true; $('#login').hidden=false; $('#login-form').reset(); if($('#editor').open) $('#editor').close(); }
async function api(path, options={}) {
  if(token && Date.now()>=expiresAt) { logout(); throw Error('La sesión venció. Vuelve a ingresar.'); }
  const headers = {...(options.body && !(options.body instanceof URLSearchParams)?{'Content-Type':'application/json'}:{}),...(token?{Authorization:`Bearer ${token}`}:{})};
  let response;
  try { response=await fetch('/api/v1'+path,{...options,headers}); } catch { throw Error('No se pudo conectar al servidor. Revisa la conexión.'); }
  if(response.status===204) return null;
  const result=await response.json().catch(()=>({detail:'El servidor no está disponible. Intenta nuevamente.'}));
  if(!response.ok) {
    if(response.status===401 && token) logout();
    const message=Array.isArray(result.detail)?result.detail.map(e=>`${e.loc.slice(1).join('.')}: ${e.msg}`).join('; '):result.detail;
    throw Error(message || `Error ${response.status}`);
  }
  return result;
}
$('#logout').onclick=logout;
$('#login-form').onsubmit=async e=>{
  e.preventDefault(); const button=e.target.querySelector('button'); button.disabled=true; $('#login-error').textContent='';
  try {
    const auth=await api('/auth/login',{method:'POST',body:new URLSearchParams(new FormData(e.target))});
    token=auth.access_token; expiresAt=Date.now()+auth.expires_in*1000;
    expiryTimer=setTimeout(()=>{logout();$('#login-error').textContent='La sesión venció. Ingresa nuevamente.';},auth.expires_in*1000);
    $('#login').hidden=true; $('#app').hidden=false; await show('resumen');
  } catch(error){$('#login-error').textContent=error.message;} finally {button.disabled=false;}
};
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>show(b.dataset.view));
const formatDate=s=>new Intl.DateTimeFormat('es-BO',{timeZone:'America/La_Paz',dateStyle:'medium',timeStyle:'short'}).format(new Date(s));
const ramaName=id=>data.ramas.find(r=>r.id===id)?.nombre || 'Todas las ramas';
const scoutName=id=>{const s=data.scouts.find(s=>s.id===id);return s?`${s.nombres} ${s.apellidos}`:`Scout ${id}`;};
const actividadName=id=>data.actividades.find(a=>a.id===id)?.titulo || `Actividad ${id}`;
async function show(next=view) {
  view=next; $('#view-title').textContent=labels[view]; $('#notice').hidden=true;
  document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===view));
  $('#content').replaceChildren(node('p','Cargando información…','loading'));
  try {
    const [resumen,ramas,scouts,actividades,inscripciones]=await Promise.all(['/resumen','/ramas','/scouts','/actividades','/inscripciones'].map(p=>api(p)));
    data={ramas,scouts,actividades,inscripciones}; $('#group-label').textContent=resumen.grupo;
    $('#content').replaceChildren();
    if(view==='resumen') renderSummary(resumen); else renderList();
  }catch(error){$('#content').replaceChildren(node('p','No se pudieron cargar los datos.'));notify(error.message,true);}
}
function action(text,fn,cls='secondary'){const b=node('button',text,cls);b.type='button';b.onclick=fn;return b;}
function renderSummary(r) {
  const hero=node('div',undefined,'hero'), intro=node('div');intro.append(node('span','PLANIFICA. PARTICIPA. EXPLORA.','eyebrow'),node('h2',r.grupo),node('p','Un vistazo a las aventuras que estamos construyendo.','muted'));hero.append(intro,action('+ Nueva actividad',()=>{view='actividades';openEditor();},''));
  const stats=node('div',undefined,'stats');for(const [key,name] of [['scouts','Scouts registrados'],['actividades','Actividades creadas'],['inscripciones','Inscripciones activas']]){const card=node('div',undefined,'stat');card.append(node('span',name),node('strong',r[key]),node('small',key==='scouts'?`${r.ramas} ramas en el grupo`:'Información actualizada'));stats.append(card);}
  const panel=node('section',undefined,'panel');panel.append(node('h3','Próximas actividades'));
  const future=data.actividades.filter(a=>new Date(a.inicio)>new Date()&&a.estado==='abierta').slice(0,4);
  if(!future.length) panel.append(node('p','Todavía no hay actividades próximas. Crea la primera.','empty'));
  for(const a of future){const line=node('div');line.append(node('strong',a.titulo),node('p',`${formatDate(a.inicio)} · ${a.lugar} · ${a.cupos_disponibles} cupos disponibles`,'muted'));panel.append(line);}
  $('#content').append(hero,stats,panel);
}
function renderList(filter='') {
  const panel=node('section',undefined,'panel'), bar=node('div',undefined,'toolbar');bar.append(node('h2',labels[view]));
  if(['scouts','actividades','inscripciones'].includes(view)) {
    const select=node('select'); select.setAttribute('aria-label','Filtrar registros');select.append(new Option(view==='inscripciones'?'Todas las actividades':'Todas las ramas',''));
    for(const item of (view==='inscripciones'?data.actividades:data.ramas)) select.append(new Option(item.nombre||item.titulo,item.id));
    select.value=filter;select.onchange=()=>{$('#content').replaceChildren();renderList(select.value);};bar.append(select);
  }
  bar.append(action('+ Nueva '+singular[view],()=>openEditor(),''));panel.append(bar);
  const items=data[view].filter(i=>!filter || (view==='inscripciones'?i.actividad_id===Number(filter):i.rama_id===Number(filter)||(view==='actividades'&&!i.rama_id)));
  const columns={ramas:['Nombre','Descripción'],scouts:['Integrante','Rama','Estado'],actividades:['Actividad','Inicio · La Paz','Cupos','Estado'],inscripciones:['Scout','Actividad','Registro · La Paz','Estado']};
  if(!items.length) panel.append(node('p','Sin registros. Agrega uno para comenzar.','empty'));
  else {
    const table=node('table'),head=node('tr');for(const c of [...columns[view],'Acciones'])head.append(node('th',c));const thead=node('thead');thead.append(head);table.append(thead);const body=node('tbody');
    for(const i of items){
      const values={ramas:()=>[i.nombre,i.descripcion],scouts:()=>[`${i.nombres} ${i.apellidos}`,ramaName(i.rama_id),i.activo?'Activo':'Inactivo'],actividades:()=>[`${i.titulo} · ${ramaName(i.rama_id)}`,formatDate(i.inicio),`${i.cupos_disponibles} / ${i.cupo_maximo} libres`,i.estado],inscripciones:()=>[scoutName(i.scout_id),actividadName(i.actividad_id),formatDate(i.fecha_registro),i.estado]}[view]();
      const tr=node('tr');for(const value of values) tr.append(node('td',value));
      const controls=node('td');controls.append(action('Editar',()=>openEditor(i)),action('Eliminar',()=>remove(i),'danger'));
      if(view==='inscripciones')controls.prepend(action(i.estado==='inscrito'?'Cancelar':'Reactivar',()=>changeStatus(i)));
      tr.append(controls);body.append(tr);
    }
    table.append(body);const wrap=node('div',undefined,'table-wrap');wrap.append(table);panel.append(wrap);
  }
  $('#content').append(panel);
}
async function remove(i){if(!confirm(`¿Eliminar esta ${singular[view]}? Esta acción no se puede deshacer.`))return;try{await api(`/${view}/${i.id}`,{method:'DELETE'});await show();notify('Registro eliminado.');}catch(e){notify(e.message,true);}}
async function changeStatus(i){try{await api(`/inscripciones/${i.id}`,{method:'PUT',body:JSON.stringify({estado:i.estado==='inscrito'?'cancelado':'inscrito'})});await show();notify('Inscripción actualizada.');}catch(e){notify(e.message,true);}}
function localInput(s){return new Date(new Date(s).getTime()-4*3600000).toISOString().slice(0,16);}
function field(name,label,type='text',value='',options=null) {
 const l=node('label',label);let input;
 if(options){input=node('select');for(const [v,t] of options)input.append(new Option(t,v));input.value=String(value??'');}
 else {input=node(type==='textarea'?'textarea':'input');if(type!=='textarea') input.type=type;if(type==='checkbox')input.checked=value;else input.value=value;}
 input.name=name;if(!['descripcion','activo','rama_id_optional'].includes(name)) input.required=true;
 if(type==='number'){input.min=1;input.max=10000;}if(type==='text')input.maxLength=160;if(['nombres','apellidos','nombre'].includes(name))input.maxLength=100;
 l.append(input);$('#fields').append(l);
}
function openEditor(i=null){
 editing={entity:view,id:i?.id}; $('#fields').replaceChildren();$('#form-error').textContent='';$('#dialog-title').textContent=(i?'Editar ':'Nueva ')+singular[view];
 const ramas=data.ramas.map(r=>[r.id,r.nombre]),future=new Date(Date.now()+7*86400000);
 if(view==='ramas'){field('nombre','Nombre','text',i?.nombre||'');field('descripcion','Descripción','textarea',i?.descripcion||'');}
 if(view==='scouts'){field('nombres','Nombres','text',i?.nombres||'');field('apellidos','Apellidos','text',i?.apellidos||'');field('rama_id','Rama','select',i?.rama_id||'', [['','Selecciona una rama'],...ramas]);field('activo','Scout activo','checkbox',i?.activo??true);}
 if(view==='actividades'){
  field('titulo','Título','text',i?.titulo||'');field('descripcion','Descripción','textarea',i?.descripcion||'');field('lugar','Lugar','text',i?.lugar||'');field('inicio','Inicio (hora de La Paz)','datetime-local',localInput(i?.inicio||future));field('fin','Fin (hora de La Paz)','datetime-local',localInput(i?.fin||new Date(future.getTime()+3*3600000)));field('cupo_maximo','Cupo máximo','number',i?.cupo_maximo||10);field('rama_id_optional','Destinatarios','select',i?.rama_id||'',[['','Todas las ramas'],...ramas]);field('estado','Estado','select',i?.estado||'abierta',[['abierta','Abierta'],['cerrada','Cerrada'],['cancelada','Cancelada']]);
 }
 if(view==='inscripciones'){
  if(!i){field('scout_id','Scout','select','',[['','Selecciona un scout'],...data.scouts.filter(s=>s.activo).map(s=>[s.id,scoutName(s.id)])]);field('actividad_id','Actividad','select','',[['','Selecciona una actividad'],...data.actividades.map(a=>[a.id,`${a.titulo} (${a.cupos_disponibles} libres)`])]);}
  field('estado','Estado','select',i?.estado||'inscrito',[['inscrito','Inscrito'],['cancelado','Cancelado']]);
 }
 $('#editor').showModal();
}
$('#close-dialog').onclick=$('#cancel-dialog').onclick=()=>$('#editor').close();
$('#edit-form').onsubmit=async e=>{
 e.preventDefault();const submit=e.target.querySelector('button[type=submit]');submit.disabled=true;const payload=Object.fromEntries(new FormData(e.target));
 try{
  if(editing.entity==='scouts')payload.activo=e.target.elements.activo.checked;
  for(const k of ['scout_id','actividad_id','rama_id','cupo_maximo'])if(k in payload)payload[k]=Number(payload[k]);
  if(editing.entity==='actividades'){
   payload.rama_id=payload.rama_id_optional?Number(payload.rama_id_optional):null;delete payload.rama_id_optional;
   payload.inicio=new Date(payload.inicio+':00-04:00').toISOString();payload.fin=new Date(payload.fin+':00-04:00').toISOString();
   if(payload.inicio>=payload.fin)throw Error('El inicio debe ser anterior al fin.');
  }
  await api('/'+editing.entity+(editing.id?'/'+editing.id:''),{method:editing.id?'PUT':'POST',body:JSON.stringify(payload)});$('#editor').close();await show(editing.entity);notify('Cambios guardados.');
 }catch(error){$('#form-error').textContent=error.message;}finally{submit.disabled=false;}
};
