// Appearance and tooltip dismissal never dispatch an investigation or a server rerun.
export default function render({data}) {
  const key='trace.pet.theme.v1',event='trace-pet-theme';
  let mode=data.fallback;
  try {const stored=localStorage.getItem(key);if(stored==='light'||stored==='dark')mode=stored;}catch{}
  let style=document.getElementById('pet-client-theme');
  if(!style){style=document.createElement('style');style.id='pet-client-theme';document.head.appendChild(style);}
  const label=()=>{
    const p=document.querySelector('.st-key-theme_toggle button p');
    const text=mode==='dark'?'☀ Light mode':'☾ Dark mode';
    if(p&&p.textContent!==text)p.textContent=text;
  };
  function paint(){
    style.textContent=':root,.stApp{'+Object.entries(data.palettes[mode]).map(([k,v])=>'--ui-'+k+':'+v+'!important').join(';')+';color-scheme:'+mode+'!important}';
    document.documentElement.dataset.petTheme=mode;
    window.dispatchEvent(new CustomEvent(event,{detail:{mode,colors:data.palettes[mode]}}));label();
  }
  const click=e=>{if(e.target.closest?.('.st-key-theme_toggle button')){e.preventDefault();e.stopImmediatePropagation();mode=mode==='light'?'dark':'light';try{localStorage.setItem(key,mode);}catch{}paint();}};
  const escape=e=>{if(e.key==='Escape')document.querySelectorAll('.trace-help-anchor').forEach(el=>el.dataset.dismissed='true');};
  const reset=e=>{const el=e.target.closest?.('.trace-help-anchor');if(el)delete el.dataset.dismissed;};
  document.addEventListener('click',click,true);document.addEventListener('keydown',escape,true);
  document.addEventListener('pointerout',reset);document.addEventListener('focusout',reset);paint();
  return()=>{document.removeEventListener('click',click,true);document.removeEventListener('keydown',escape,true);document.removeEventListener('pointerout',reset);document.removeEventListener('focusout',reset);};
}
