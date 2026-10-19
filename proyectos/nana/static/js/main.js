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
