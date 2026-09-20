const VOICE_KEY='trace.pet.voice.v1';
const VOICE_EVENT='trace-pet-voice-change';
function voicePreferences(){try{return {consent:false,spoken:false,online:false,voice:'auto',...JSON.parse(localStorage.getItem(VOICE_KEY)||'{}')};}catch{return {consent:false,spoken:false,online:false,voice:'auto'};}}
function saveVoicePreferences(value){try{localStorage.setItem(VOICE_KEY,JSON.stringify(value));}catch{}window.dispatchEvent(new CustomEvent(VOICE_EVENT,{detail:value}));}
function deviceVoice(prefs){
  const voices=(window.speechSynthesis?.getVoices()||[]).filter(v=>/^en(?:-|$)/i.test(v.lang)&&(v.localService===true||prefs.online));
  const id=v=>`${v.voiceURI||v.name}|${v.lang}|${v.localService}`;
  const selected=voices.find(v=>id(v)===prefs.voice);
  const quality=v=>(/natural|neural|enhanced|premium/i.test(v.name)?4:0)+(v.default?1:0);
  return selected||voices.filter(v=>v.localService===true).sort((a,b)=>quality(b)-quality(a))[0];
}
function speakCue(text,prefs){
  const voice=deviceVoice(prefs);
  if(!voice||!window.SpeechSynthesisUtterance)return false;
  window.speechSynthesis.cancel();
  const utterance=new window.SpeechSynthesisUtterance(text);utterance.voice=voice;utterance.lang=voice.lang;utterance.rate=.96;
  window.speechSynthesis.speak(utterance);return true;
}
