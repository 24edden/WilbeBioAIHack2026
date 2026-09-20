const spokenCues=new Set();
export default function render({data}){
  const prefs=voicePreferences();
  if(prefs.spoken&&data.cue&&!spokenCues.has(data.id)){
    spokenCues.add(data.id);speakCue(data.cue,prefs);
  }
  const changed=()=>{if(!voicePreferences().spoken)window.speechSynthesis?.cancel();};
  window.addEventListener(VOICE_EVENT,changed);
  return()=>window.removeEventListener(VOICE_EVENT,changed);
}
