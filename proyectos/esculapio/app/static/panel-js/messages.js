
const thread = document.getElementById('thread');
if (thread) thread.scrollTop = thread.scrollHeight;

const notifButton = document.getElementById('enableNotifications');
function refreshNotificationButton() {
  if (!('Notification' in window)) {
    notifButton.textContent = 'Notificaciones no disponibles';
    notifButton.disabled = true;
    return;
  }
  if (Notification.permission === 'granted') notifButton.textContent = '🔔 Notificaciones activas';
  else if (Notification.permission === 'denied') notifButton.textContent = '🔕 Bloqueadas por navegador';
  else notifButton.textContent = '🔔 Activar notificaciones';
}
refreshNotificationButton();
notifButton.addEventListener('click', async () => {
  if (!('Notification' in window)) return;
  await Notification.requestPermission();
  refreshNotificationButton();
});

let baselineReady = false;
let lastMessageId = 0;
async function pollMessages() {
  try {
    const response = await fetch('/panel/messages/notifications', {cache: 'no-store'});
    if (!response.ok) return;
    const data = await response.json();
    const navBadge = document.getElementById('navUnread');
    navBadge.textContent = data.human_requests ? '!' : data.unread_count;
    navBadge.title = data.human_requests ? `${data.human_requests} solicitud(es) de atención humana` : `${data.unread_count} mensaje(s) sin leer`;
    navBadge.classList.toggle('hidden', !data.unread_count && !data.human_requests);
    document.getElementById('summaryUnread').textContent = data.unread_count;
    document.getElementById('summaryHuman').textContent = data.human_requests;
    document.title = data.unread_count ? `(${data.unread_count}) Mensajes — ESCULAPIO` : 'Mensajes — ESCULAPIO';

    if (data.latest) {
      if (!baselineReady && lastMessageId === 0) {
        lastMessageId = data.latest.id;

      } else if (data.latest.id > lastMessageId) {
        lastMessageId = data.latest.id;

        if ('Notification' in window && Notification.permission === 'granted') {
          const title = 'Actividad administrativa del consultorio';
          const n = new Notification(title, {body: 'Abre el panel para revisar.'});
          n.onclick = () => { window.focus(); window.location.href = `/panel/messages?phone=${encodeURIComponent(data.latest.phone)}`; };
        }
      }
    }
    baselineReady = true;
  } catch (e) {
    console.debug('No se pudieron actualizar notificaciones', e);
  }
}
pollMessages();
setInterval(pollMessages, 12000);
