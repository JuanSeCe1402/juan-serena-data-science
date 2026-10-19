const btn = document.querySelector('.menu-toggle');
const nav = document.querySelector('.nav');
if (btn && nav) {
  const setOpen = open => {
    nav.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', String(open));
    btn.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú');
  };
  btn.addEventListener('click', () => setOpen(!nav.classList.contains('open')));
  nav.addEventListener('click', e => {if (e.target.closest('a')) setOpen(false);});
  document.addEventListener('keydown', e => {
    if(e.key === 'Escape' && nav.classList.contains('open')) {setOpen(false);btn.focus();}
  });
  window.matchMedia('(min-width:901px)').addEventListener('change', () => setOpen(false));
}

const error = document.querySelector('[data-error]');
if (error) error.focus();

const trainingButton = document.querySelector('[data-training]');
if (trainingButton) {
  trainingButton.form.addEventListener('submit', () => {
    trainingButton.disabled = true;
    trainingButton.textContent = 'Evaluando la demo…';
    const status = document.querySelector('[data-training-status]');
    if (status) status.textContent = 'Generando datos y evaluando el modelo. Espera unos segundos.';
  });
}
