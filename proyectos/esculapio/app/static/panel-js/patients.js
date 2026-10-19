

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
