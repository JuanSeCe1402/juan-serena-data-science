
const monthNames = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
let calendarCursor = new Date();
calendarCursor = new Date(calendarCursor.getFullYear(), calendarCursor.getMonth(), 1);
let calendarEvents = [];

function isoLocalDate(d){
  const y=d.getFullYear(), m=String(d.getMonth()+1).padStart(2,'0'), day=String(d.getDate()).padStart(2,'0');
  return `${y}-${m}-${day}`;
}

function escapeHtml(value){
  return String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[ch]));
}

async function loadCalendar(){
  const y=calendarCursor.getFullYear(), m=calendarCursor.getMonth();
  const start=new Date(y,m,1), end=new Date(y,m+1,0);
  document.getElementById('calendarTitle').textContent =
    `${monthNames[m][0].toUpperCase()+monthNames[m].slice(1)} ${y}`;

  try{
    const response=await fetch(`/panel/calendar/events?start=${isoLocalDate(start)}&end=${isoLocalDate(end)}`, {cache:'no-store'});
    const data=await response.json();
    calendarEvents=data.events || [];
  }catch(e){
    calendarEvents=[];
  }
  renderCalendar();
}

function renderCalendar(){
  const grid=document.getElementById('calendarGrid');
  grid.innerHTML='';
  const y=calendarCursor.getFullYear(), m=calendarCursor.getMonth();
  const first=new Date(y,m,1), last=new Date(y,m+1,0);
  const mondayOffset=(first.getDay()+6)%7;
  const today=isoLocalDate(new Date());

  for(let i=0;i<mondayOffset;i++){
    const blank=document.createElement('div');
    blank.className='calendar-day blank';
    grid.appendChild(blank);
  }

  for(let day=1; day<=last.getDate(); day++){
    const d=new Date(y,m,day);
    const iso=isoLocalDate(d);
    const events=calendarEvents.filter(ev=>ev.date===iso);
    const cell=document.createElement('button');
    cell.type='button';
    cell.className='calendar-day';
    cell.setAttribute('aria-describedby','calendarTitle');
    if(iso===today)cell.setAttribute('aria-current','date');
    if(iso===today) cell.classList.add('today');

    cell.innerHTML=`<span class="calendar-number">${day}</span>
      ${events.length ? `<span class="calendar-count">${events.length} cita${events.length===1?'':'s'}</span>` : ''}
      <span class="calendar-dots">${events.slice(0,6).map(ev=>`<i class="${ev.type==='laboratorio'?'lab':'consult'}"></i>`).join('')}</span>`;

    cell.addEventListener('click',()=>showCalendarDay(iso, events));
    grid.appendChild(cell);
  }
}

function showCalendarDay(iso, events){
  const detail=document.getElementById('calendarDayDetail');
  const [y,m,d]=iso.split('-');

  if(!events.length){
    detail.innerHTML=`<div class="calendar-detail-head">
      <strong>${d}/${m}/${y}</strong>
      <a class="button-link" href="/panel?new_date=${encodeURIComponent(iso)}">Agregar cita</a>
    </div>
    <p class="empty">No hay citas agendadas este día.</p>`;
    return;
  }

  detail.innerHTML=`<div class="calendar-detail-head">
    <strong>${d}/${m}/${y} · ${events.length} cita${events.length===1?'':'s'}</strong>
    <a class="button-link" href="/panel?new_date=${encodeURIComponent(iso)}">Agregar cita</a>
  </div>`+
  events.map(ev=>`<div class="calendar-event">
    <div class="calendar-event-time">${escapeHtml(ev.start)}–${escapeHtml(ev.end)}</div>
    <div>
      <strong>${escapeHtml(ev.name)}</strong><br>
      <small>${escapeHtml(ev.type_label)} · ${escapeHtml(ev.reason)}</small>
    </div>
    <div class="calendar-event-actions">
      <a class="button-link secondary" href="${escapeHtml(ev.patient_url)}">Paciente</a>
      <a class="button-link" href="${escapeHtml(ev.reschedule_url)}">Reagendar</a>
    </div>
  </div>`).join('');
}

document.getElementById('calendarPrev').addEventListener('click',()=>{
  calendarCursor=new Date(calendarCursor.getFullYear(),calendarCursor.getMonth()-1,1);
  loadCalendar();
});
document.getElementById('calendarNext').addEventListener('click',()=>{
  calendarCursor=new Date(calendarCursor.getFullYear(),calendarCursor.getMonth()+1,1);
  loadCalendar();
});
document.getElementById('calendarToday').addEventListener('click',()=>{
  const n=new Date();
  calendarCursor=new Date(n.getFullYear(),n.getMonth(),1);
  loadCalendar();
});

async function actualizarBadgeMensajes(){
  try {
    const response = await fetch('/panel/messages/notifications', {cache:'no-store'});
    if (!response.ok) return;
    const data = await response.json();
    const badge = document.getElementById('navUnread');
    const total = Number(data.unread_count || 0);
    const human = Number(data.human_requests || 0);
    badge.textContent = human > 0 ? '!' : total;
    badge.classList.toggle('hidden', total === 0 && human === 0);
  } catch(e) {}
}

loadCalendar();
actualizarBadgeMensajes();
setInterval(actualizarBadgeMensajes, 12000);
