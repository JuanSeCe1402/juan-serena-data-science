document.addEventListener('submit', e => {
 const f=e.target;
 if(f.dataset.confirm && !window.confirm(f.dataset.confirm)) {e.preventDefault();return;}
 if(f.dataset.deleteConfirm && typeof confirmarEliminacionPaciente==='function' && !confirmarEliminacionPaciente(f)){e.preventDefault();return;}
 if(f.dataset.cancelConfirm) {
   if(document.body.dataset.demo==='true') {
     if(!window.confirm('¿Cancelar esta cita ficticia?')) {e.preventDefault();return;}
     const field=f.querySelector('[name=reason]');if(field)field.value='Demostración administrativa';
   } else if(typeof prepararCancelacion==='function' && !prepararCancelacion(f)) e.preventDefault();
 }
});
document.addEventListener('change',e=>{if(e.target.matches('[data-sync-days]') && typeof syncWorkDays==='function')syncWorkDays();});
const error=document.querySelector('.alert.error');if(error)error.focus();
