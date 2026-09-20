export default function render({parentElement,data}){
  const el=id=>parentElement.querySelector('#'+id),root=el('voice-preferences');
  for(const [key,color]of Object.entries(data.colors||{}))root.style.setProperty('--ui-'+key,color);
  const applyTheme=()=>{if(!document.documentElement.dataset.petTheme)return;const tokens=getComputedStyle(document.documentElement);for(const name of Object.keys(data.colors||{}))root.style.setProperty('--ui-'+name,tokens.getPropertyValue('--ui-'+name));};
  applyTheme();window.addEventListener('trace-pet-theme',applyTheme);
  let prefs=voicePreferences();
  const consent=el('voice-consent'),spoken=el('voice-spoken'),online=el('voice-online'),choice=el('voice-choice'),status=el('voice-status');
  const supported=Boolean((window.SpeechRecognition||window.webkitSpeechRecognition)&&window.isSecureContext);
  consent.checked=prefs.consent;spoken.checked=prefs.spoken;online.checked=prefs.online;consent.disabled=!supported;
  function populate(){
    choice.replaceChildren();const auto=document.createElement('option');auto.value='auto';auto.textContent='Best available device voice';choice.appendChild(auto);
    for(const v of window.speechSynthesis?.getVoices()||[]){if(!/^en(?:-|$)/i.test(v.lang)||(!v.localService&&!prefs.online))continue;const o=document.createElement('option');o.value=`${v.voiceURI||v.name}|${v.lang}|${v.localService}`;o.textContent=`${v.name} (${v.localService?'device':'online'})`;choice.appendChild(o);}
    choice.value=prefs.voice;el('voice-preview').disabled=!deviceVoice(prefs);
  }
  function save(){prefs={consent:consent.checked,spoken:spoken.checked,online:online.checked,voice:choice.value||'auto'};saveVoicePreferences(prefs);}
  consent.onchange=save;spoken.onchange=()=>{save();if(!prefs.spoken)window.speechSynthesis?.cancel();};
  online.onchange=()=>{prefs.online=online.checked;prefs.voice='auto';populate();save();};choice.onchange=save;
  el('voice-preview').onclick=()=>{status.textContent=speakCue('Hello. I can keep you updated as the investigation moves forward.',prefs)?'Playing your selected voice.':'No suitable voice is available in this browser.';};
  el('voice-silence').onclick=()=>{spoken.checked=false;save();window.speechSynthesis?.cancel();};
  if(!supported)status.textContent='This browser does not support speech input. You can still type your question.';
  populate();window.speechSynthesis?.addEventListener('voiceschanged',populate);
  return()=>{window.speechSynthesis?.removeEventListener('voiceschanged',populate);window.removeEventListener('trace-pet-theme',applyTheme);};
}
