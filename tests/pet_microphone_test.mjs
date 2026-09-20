// Exercise the actual recognition lifecycle without capturing a person's microphone.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
const source=await readFile(new URL('../frontend/static/microphone.js',import.meta.url),'utf8');
let consent=false,current,stopped=0,finished=0,typed='',releaseMedia;
class Recognition{constructor(){current=this;}start(){}stop(){this.onend?.();}abort(){this.onend?.();}}
const listeners=new Map(),input={value:'Existing draft',addEventListener:(k,v)=>listeners.set(k,v),removeEventListener:k=>listeners.delete(k)};
const button={dataset:{},style:{setProperty(){}},setAttribute(k,v){this[k]=v;}},status={textContent:''};
const context=vm.createContext({window:{SpeechRecognition:Recognition,isSecureContext:true,speechSynthesis:{cancel(){}},addEventListener(){},removeEventListener(){}},
  navigator:{mediaDevices:{getUserMedia:()=>new Promise(resolve=>releaseMedia=resolve)}},cancelAnimationFrame(){},requestAnimationFrame(){return 1;},
  voicePreferences:()=>({consent}),VOICE_EVENT:'change',Uint8Array});
vm.runInContext(source+';this.mount=mountMicrophone;',context);
let cleanup=context.mount({button,input,status,readOnly:false,onInput:t=>typed=t,onFinish:()=>finished++});
button.onclick();assert.match(status.textContent,/Settings/);assert.equal(current,undefined);
consent=true;button.onclick();assert.equal(button['aria-pressed'],'true');
current.onresult({results:[[{transcript:'additional evidence'}]]});
assert.equal(typed,'Existing draft additional evidence');assert.equal(finished,0);
current.onerror({error:'not-allowed'});current.onend();assert.match(status.textContent,/denied/);assert.equal(button['aria-pressed'],'false');
releaseMedia({getTracks:()=>[{stop:()=>stopped++}]});await new Promise(resolve=>setImmediate(resolve));assert.equal(stopped,1);
button.onclick();assert.equal(button['aria-pressed'],'true');listeners.get('keydown')();assert.equal(button['aria-pressed'],'false');
cleanup();assert.equal(button.onclick,null);assert.equal(listeners.size,0);
releaseMedia({getTracks:()=>[{stop:()=>stopped++}]});await new Promise(resolve=>setImmediate(resolve));assert.equal(stopped,2);
console.log('Consent, draft-only dictation, error persistence, manual editing and late microphone cleanup passed.');
