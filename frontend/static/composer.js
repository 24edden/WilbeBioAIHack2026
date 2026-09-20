const sessions = new Map();
const MAX_FILE = 20 * 1024 * 1024;
const MAX_TOTAL = 40 * 1024 * 1024;

export default function render(component) {
  const {parentElement, data, key, setTriggerValue, setStateValue} = component;
  let state = sessions.get(key);
  if (!state || state.generation !== data.generation) {
    state = {generation:data.generation, text:data.question||'', serverText:data.question||'', files:data.files||[], busy:false};
    sessions.set(key,state);
  }
  // Within one draft generation, browser edits are authoritative. Late server
  // acknowledgements must not replace text typed while an upload/theme update was in flight.
  const el=id=>parentElement.querySelector('#'+id);
  const form=el('composer'),question=el('question'),picker=el('files'),submit=el('submit'),attach=el('attach'),demo=el('demo'),error=el('composer-error');
  const wrap=el('composer-wrap');
  wrap.style.colorScheme=data.theme==='dark'?'dark':'light';
  for(const [name,color] of Object.entries(data.colors||{}))wrap.style.setProperty('--ui-'+name,color);
  question.value=state.text;
  question.disabled=Boolean(data.readOnly);
  picker.accept=(data.extensions||[]).map(e=>'.'+e).join(',');
  attach.hidden=Boolean(data.readOnly);
  el('drop-hint').hidden=Boolean(data.readOnly);
  el('source-note').textContent=data.note||'';
  const sync=()=>setStateValue('draft',{generation:state.generation,question:state.text,files:state.files});
  function refresh(){
    submit.disabled=Boolean(data.disabled||state.busy);attach.disabled=Boolean(data.readOnly||state.busy);demo.disabled=submit.disabled;
    submit.textContent=state.busy?'Preparing…':data.readOnly?'Start replay  →':'Start investigation  →';
    const list=el('attachments');list.replaceChildren();
    for(let i=0;i<state.files.length&&!data.readOnly;i++){
      const f=state.files[i],chip=document.createElement('div');chip.className='attachment-chip';
      const symbol=document.createElement('i');symbol.textContent='▤';chip.appendChild(symbol);
      const name=document.createElement('span');name.textContent=f.name;const size=document.createElement('small');size.textContent=(f.size/1024).toFixed(1)+' KB';name.appendChild(size);chip.appendChild(name);
      const remove=document.createElement('button');remove.type='button';remove.textContent='×';remove.setAttribute('aria-label','Remove '+f.name);remove.disabled=state.busy;remove.onclick=()=>{state.files.splice(i,1);sync();refresh();};chip.appendChild(remove);list.appendChild(chip);
    }
  }
  const encode=file=>new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(new Error('Could not read '+file.name));reader.readAsDataURL(file);});
  async function add(files){
    if(data.readOnly||state.busy)return;
    error.textContent='';
    if(files.length+state.files.length>20){error.textContent='Attach up to 20 files.';return;}
    if(files.some(f=>f.size>MAX_FILE)){error.textContent='Each file must be 20 MB or smaller.';return;}
    if(files.reduce((n,f)=>n+f.size,0)+state.files.reduce((n,f)=>n+f.size,0)>MAX_TOTAL){error.textContent='Keep total attachments under 40 MB.';return;}
    if(files.some(f=>!data.extensions.includes(f.name.split('.').pop().toLowerCase()))){error.textContent='Supported formats: '+data.extensions.join(', ')+'.';return;}
    state.busy=true;refresh();
    try{const encoded=await Promise.all(files.map(async f=>({name:f.name,size:f.size,data:await encode(f)})));state.files.push(...encoded);sync();}catch(e){error.textContent=e.message;}finally{state.busy=false;refresh();}
  }
  question.oninput=()=>{state.text=question.value;error.textContent='';};
  question.onblur=sync;
  attach.onclick=()=>picker.click();
  picker.onchange=()=>{void add(Array.from(picker.files||[]));picker.value='';};
  form.ondragover=e=>{if(e.dataTransfer?.types.includes('Files')){e.preventDefault();if(!data.readOnly)form.classList.add('is-dragging');}};
  form.ondragleave=e=>{if(!form.contains(e.relatedTarget))form.classList.remove('is-dragging');};
  form.ondrop=e=>{if(e.dataTransfer?.files.length){e.preventDefault();form.classList.remove('is-dragging');void add(Array.from(e.dataTransfer.files));}};
  function send(type){
    if(state.busy||data.disabled)return;
    if(type==='start'&&!question.value.trim()){error.textContent='Enter a scientific question before starting.';question.focus();return;}
    state.text=question.value;state.busy=true;refresh();
    try {
      setTriggerValue('action',{id:crypto.randomUUID(),generation:state.generation,type,question:state.text,files:state.files});
    } catch {
      error.textContent='The connection was interrupted. Your draft is still here; try again.';
    } finally {
      state.busy=false;refresh();
    }
  }
  form.onsubmit=e=>{e.preventDefault();send('start');};
  demo.onclick=()=>send('demo');
  refresh();
  return ()=>{question.oninput=null;question.onblur=null;picker.onchange=null;attach.onclick=null;form.ondragover=null;form.ondragleave=null;form.ondrop=null;form.onsubmit=null;demo.onclick=null;};
}
