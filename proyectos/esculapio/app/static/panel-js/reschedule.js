
const appointmentId=Number(document.getElementById('reschedule-context').dataset.id);
const appointmentType=document.getElementById('reschedule-context').dataset.type;
const originalDate=document.getElementById('reschedule-context').dataset.date;
const originalTime=document.getElementById('reschedule-context').dataset.time;

async function cargarHorariosReagendar(){
  const day=document.getElementById('reschedule_day').value;
  const select=document.getElementById('reschedule_time');
  select.innerHTML='<option value="">Cargando…</option>';
  try{
    const response=await fetch(`/panel/slots?day=${encodeURIComponent(day)}&appointment_type=${encodeURIComponent(appointmentType)}&exclude_appointment_id=${appointmentId}`);
    const data=await response.json();
    if(!data.slots || !data.slots.length){
      select.innerHTML='<option value="">Sin horarios disponibles</option>';
      return;
    }
    select.innerHTML=data.slots.map(slot => `<option value="${slot}" ${day===originalDate && slot===originalTime?'selected':''}>${slot}</option>`).join('');
  }catch(e){
    select.innerHTML='<option value="">Error al cargar horarios</option>';
  }
}
document.getElementById('reschedule_day').addEventListener('change',cargarHorariosReagendar);
cargarHorariosReagendar();


async function actualizarBadgeMensajes(){
  try {
    const response = await fetch('/panel/messages/notifications', {cache:'no-store'});
    if (!response.ok) return;
    const data = await response.json();
    const badge = document.getElementById('navUnread');
    if (!badge) return;
    const total = Number(data.unread_count || 0);
    const human = Number(data.human_requests || 0);
    badge.textContent = human > 0 ? '!' : total;
    badge.classList.toggle('hidden', total === 0 && human === 0);
  } catch(e) {}
}
actualizarBadgeMensajes();
setInterval(actualizarBadgeMensajes, 12000);
