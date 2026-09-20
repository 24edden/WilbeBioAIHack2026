import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const source = await readFile(new URL('../frontend/static/voice.js', import.meta.url), 'utf8');
const {default: render, navigationTarget, localVoice} = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
assert.equal(navigationTarget('Show the results.'), 'results');
assert.equal(navigationTarget('go to evidence'), 'evidence');
assert.equal(navigationTarget('submit my question'), null);
assert.equal(navigationTarget('cancel investigation'), null);
assert.equal(navigationTarget('I think we should show results'), null);
assert.equal(localVoice([{lang:'en-GB',localService:false}]), null);
assert.equal(localVoice([{lang:'fr-FR',localService:true}]), null);
assert.equal(localVoice([{lang:'en-GB',localService:true,name:'Local'}]).name, 'Local');
assert.equal(localVoice([{lang:'en-GB',localService:true,name:'Basic',default:true},
  {lang:'en-GB',localService:true,name:'Enhanced voice'}]).name, 'Enhanced voice');

let starts = 0, aborts = 0, speaks = 0, activeRecognition, lastUtterance;
const voices = [{name:'Local',voiceURI:'local',lang:'en-GB',localService:true},
  {name:'Online Natural',voiceURI:'online',lang:'en-GB',localService:false}];
class Recognition {
  constructor() { activeRecognition = this; }
  start() { starts++; }
  stop() { this.onend?.(); }
  abort() { aborts++; this.onend?.(); }
}
globalThis.window = {
  isSecureContext:true, SpeechRecognition:Recognition,
  SpeechSynthesisUtterance:class { constructor(text) { this.text=text; } },
  speechSynthesis:{
    getVoices:()=>voices,
    speak:utterance=>{ lastUtterance=utterance; assert.equal(utterance.rate,.96); speaks++; },
    cancel:()=>{}, addEventListener:()=>{}, removeEventListener:()=>{},
  },
};
globalThis.document={createElement:()=>({value:'',textContent:''})};
function mount(key, data = {}) {
  const elements = new Map();
  const element = id => {
    if (!elements.has(id)) elements.set(id,{value:'',textContent:'',checked:false,disabled:false,dataset:{},children:[],
      replaceChildren(){this.children=[];},appendChild(child){this.children.push(child);},querySelector:()=>element('dictation-option')});
    return elements.get(id);
  };
  const actions=[];
  const cleanup=render({
    key, parentElement:{querySelector:selector=>element(selector)},
    data:{dictationEnabled:true,announcement:'Review evidence.',announcementId:'evidence',...data},
    setTriggerValue:(name,value)=>actions.push({name,value}),
  });
  return {element,actions,cleanup};
}
let widget=mount('first');
assert.equal(starts,0);
assert.equal(speaks,0);
assert.equal(widget.element('#listen').disabled,true);
widget.element('#listen').onclick();
assert.equal(starts,0);
widget.element('#consent').checked=true;
widget.element('#consent').onchange();
widget.element('#listen').onclick();
assert.equal(starts,1);
// A same-key Streamlit data rerender must preserve the active mic and consent.
widget.cleanup();
widget=mount('first', {announcementId:'question',announcement:'Set your question.'});
await new Promise(resolve=>setTimeout(resolve,70));
assert.equal(aborts,0);
assert.equal(starts,1);
assert.equal(widget.element('#stop').disabled,false);
assert.equal(widget.element('#consent').checked,true);
activeRecognition.onresult({results:[[{transcript:'Why did treatment fail?'}]]});
assert.equal(widget.actions.length,0);
widget.element('#stop').onclick();
widget.element('#apply').onclick();
assert.equal(widget.actions[0].value.type,'dictation');
assert.equal(widget.actions[0].value.text,'Why did treatment fail?');
widget.element('#spoken').checked=true;
widget.element('#spoken').onchange();
assert.equal(speaks,1);
assert.equal(lastUtterance.voice.localService,true);
assert.equal(widget.element('#voice-choice').children.some(option=>option.textContent.includes('(online)')),false);
widget.cleanup();
widget=mount('first', {announcementId:'question',announcement:'Set your question.'});
await new Promise(resolve=>setTimeout(resolve,650));
assert.equal(speaks,1); // Same milestone must not repeat on data rerender.
widget.cleanup();
await new Promise(resolve=>setTimeout(resolve,70));
assert.equal(aborts,1);

widget=mount('voice-choice');
const initialSpeaks=speaks;
widget.element('#online-voices').checked=true;
widget.element('#online-voices').onchange();
assert.equal(speaks,initialSpeaks); // Listing remote voices never enables playback.
assert.equal(widget.element('#voice-choice').children.some(option=>option.textContent.includes('(online)')),true);
widget.element('#voice-choice').value='online|en-GB|false';
widget.element('#voice-choice').onchange();
assert.equal(speaks,initialSpeaks); // Choosing also waits for explicit preview/enable.
widget.element('#preview').onclick();
assert.equal(lastUtterance.voice.localService,false);
assert.equal(speaks,initialSpeaks+1);
widget.element('#online-voices').checked=false;
widget.element('#online-voices').onchange();
widget.element('#preview').onclick();
assert.equal(lastUtterance.voice.localService,true);
widget.cleanup();

// Settings live in the first step; changing steps preserves preferences/text.
widget=mount('setup', {setupMode:true});
assert.equal(widget.element('#recognition-settings').hidden,false);
widget.element('#consent').checked=true;
widget.element('#consent').onchange();
widget.element('#transcript').value='Keep my reviewed question';
widget.element('#transcript').oninput();
widget.element('#voice-choice').value='local|en-GB|true';
widget.element('#voice-choice').onchange();
widget.cleanup();
widget=mount('setup', {setupMode:false});
assert.equal(widget.element('#recognition-settings').hidden,true);
assert.equal(widget.element('#playback-settings').hidden,true);
assert.equal(widget.element('#voice-input').hidden,false);
assert.equal(widget.element('#consent').checked,true);
assert.equal(widget.element('#transcript').value,'Keep my reviewed question');
assert.equal(widget.element('#voice-choice').value,'local|en-GB|true');
widget.element('#settings').onclick();
assert.equal(widget.actions[0].value.target,'evidence');
widget.cleanup();
widget=mount('setup', {setupMode:true});
assert.equal(widget.element('details').open,true);
assert.equal(widget.element('#transcript').value,'Keep my reviewed question');
widget.cleanup();

widget=mount('commands', {dictationEnabled:false});
assert.equal(widget.element('#mode').value,'command');
widget.element('#transcript').value='show results';
widget.element('#transcript').oninput();
widget.element('#apply').onclick();
assert.equal(widget.actions[0].value.target,'results');
widget.element('#transcript').value='cancel investigation';
widget.element('#transcript').oninput();
assert.equal(widget.element('#apply').disabled,true);
widget.cleanup();

delete window.SpeechRecognition;
widget=mount('unsupported');
assert.equal(widget.element('#listen').disabled,true);
assert.match(widget.element('#status').textContent,/unavailable/);
widget.cleanup();
process.stdout.write(JSON.stringify({passed:true}));
