
function prepararCancelacion(form){
  if (!confirm('¿Cancelar esta cita? Se le avisará al paciente por WhatsApp automáticamente.')) return false;
  const motivo = prompt('Motivo (opcional):', '');
  form.querySelector('input[name="reason"]').value = motivo || '';
  return true;
}

async function cargarHorarios(){
  const day = document.getElementById('manual_day').value;
  const type = document.getElementById('manual_type').value;
  const select = document.getElementById('manual_time');
  select.innerHTML = '<option value="">Cargando…</option>';
  if (!day) { select.innerHTML = '<option value="">Elige fecha</option>'; return; }
  try {
    const response = await fetch(`/panel/slots?day=${encodeURIComponent(day)}&appointment_type=${encodeURIComponent(type)}`);
    const data = await response.json();
    if (!data.slots || data.slots.length === 0) {
      select.innerHTML = '<option value="">Sin horarios disponibles</option>';
      return;
    }
    select.innerHTML = data.slots.map(s => `<option value="${s}">${s}</option>`).join('');
  } catch (e) {
    select.innerHTML = '<option value="">Error al cargar</option>';
  }
}
document.getElementById('manual_day').addEventListener('change', cargarHorarios);
document.getElementById('manual_type').addEventListener('change', cargarHorarios);
if (document.getElementById('manual_day').value) {
  cargarHorarios();
}


const serverPanelOrder = (() => {
  try { return JSON.parse(document.getElementById('panel-context').dataset.order || '[]'); }
  catch (e) { return []; }
})();

async function saveDashboardOrder(){
  const order = Array.from(document.querySelectorAll('#dashboardGrid > .card'))
    .map(card => card.dataset.panelId)
    .filter(Boolean);
  try {
    await fetch('/panel/layout', {
      method:'POST',
      headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content},
      body:JSON.stringify({order})
    });
  } catch(e) {
    console.debug('No se pudo guardar el orden del panel', e);
  }
}

function initializeDashboardLayout(){
  const grid = document.getElementById('dashboardGrid');
  const toolbar = document.querySelector('.dashboard-toolbar');
  document.querySelectorAll('main > section > .alert').forEach(alert => toolbar.before(alert));
  const cards = Array.from(document.querySelectorAll('main > section > .card'));
  const byId = new Map();

  cards.forEach((card, index) => {
    if (!card.dataset.panelId) card.dataset.panelId = `panel-${index+1}`;
    byId.set(card.dataset.panelId, card);
  });

  const ordered = [];
  serverPanelOrder.forEach(id => {
    if (byId.has(id)) {
      ordered.push(byId.get(id));
      byId.delete(id);
    }
  });
  byId.forEach(card => ordered.push(card));

  ordered.forEach(card => {
    const heading = card.querySelector('h2');
    if (heading && !heading.querySelector('.panel-move-controls')) {
      const controls = document.createElement('span');
      controls.className = 'panel-move-controls';
      controls.innerHTML = `
        <button type="button" class="panel-arrow" data-dir="-1" title="Mover arriba" aria-label="Mover módulo arriba"><span aria-hidden="true">↑</span></button>
        <button type="button" class="panel-arrow" data-dir="1" title="Mover abajo" aria-label="Mover módulo abajo"><span aria-hidden="true">↓</span></button>
        <span class="drag-handle" draggable="true" title="Arrastrar panel">⋮⋮</span>`;
      heading.appendChild(controls);
    }
    grid.appendChild(card);
  });

  document.querySelectorAll('main > section').forEach(section => section.remove());

  let dragged = null;
  grid.addEventListener('dragstart', e => {
    if (!e.target.classList.contains('drag-handle')) { e.preventDefault(); return; }
    dragged = e.target.closest('.card');
    if (!dragged) return;
    dragged.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
  });
  grid.addEventListener('dragover', e => {
    e.preventDefault();
    if (!dragged) return;
    const candidates = [...grid.querySelectorAll('.card:not(.dragging)')];
    const after = candidates.find(el => {
      const r = el.getBoundingClientRect();
      return e.clientY < r.top + r.height / 2;
    });
    if (after) grid.insertBefore(dragged, after);
    else grid.appendChild(dragged);
  });
  grid.addEventListener('dragend', () => {
    if (dragged) dragged.classList.remove('dragging');
    dragged = null;
    saveDashboardOrder();
  });

  grid.addEventListener('click', e => {
    const btn = e.target.closest('.panel-arrow');
    if (!btn) return;
    const card = btn.closest('.card');
    const dir = Number(btn.dataset.dir);
    if (dir < 0 && card.previousElementSibling) {
      grid.insertBefore(card, card.previousElementSibling);
    } else if (dir > 0 && card.nextElementSibling) {
      grid.insertBefore(card.nextElementSibling, card);
    }
    saveDashboardOrder();
  });

  document.getElementById('resetLayout').addEventListener('click', async () => {
    localStorage.removeItem('unused-dashboard-order');
    try {
      await fetch('/panel/layout', {
        method:'POST',
        headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content},
        body:JSON.stringify({order:[]})
      });
      location.reload();
    } catch(e) {}
  });
}


initializeDashboardLayout();

async function actualizarBadgeMensajes(){
  try {
    const response = await fetch('/panel/messages/notifications', {cache: 'no-store'});
    if (!response.ok) return;
    const data = await response.json();
    const badge = document.getElementById('navUnread');
    const total = Number(data.unread_count || 0);
    const human = Number(data.human_requests || 0);
    badge.textContent = human > 0 ? '!' : total;
    badge.classList.toggle('hidden', total === 0 && human === 0);
    if (human > 0) badge.title = `${human} solicitud(es) de atención humana`;
    else if (total > 0) badge.title = `${total} mensaje(s) sin leer`;
    else badge.title = '';
  } catch (e) {
    console.debug('No se pudo actualizar el contador de mensajes', e);
  }
}
actualizarBadgeMensajes();
setInterval(actualizarBadgeMensajes, 12000);
