

function confirmarEliminacionPaciente(form){
  const expected = 'ELIMINAR';
  const typed = prompt(
    'Esta acción eliminará permanentemente al paciente, sus citas y el historial local del bot.\n\nEscribe ELIMINAR para confirmar:'
  );
  if (typed !== expected) {
    if (typed !== null) alert('No se eliminó nada. La palabra de confirmación no coincide.');
    return false;
  }
  form.querySelector('input[name="confirm_delete"]').value = expected;
  return confirm('Última confirmación: ¿eliminar definitivamente a este paciente?');
}

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
