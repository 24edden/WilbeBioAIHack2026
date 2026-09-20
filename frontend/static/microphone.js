// Explicit click + consent only. The volume meter is local; recognition is browser-provided.
function mountMicrophone({button,input,status,onInput,onFinish,readOnly}){
  if(!button)return()=>{};
  const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
  let recognition=null,listening=false,disposed=false,stream=null,context=null,frame=0,startingText='',failed=false;
  function paint(){button.setAttribute('aria-pressed',String(listening));button.setAttribute('aria-label',listening?'Stop microphone':'Dictate question');button.dataset.listening=String(listening);button.disabled=Boolean(readOnly);}
  function releaseMeter(){cancelAnimationFrame(frame);frame=0;stream?.getTracks().forEach(track=>track.stop());stream=null;context?.close().catch(()=>{});context=null;button.style.setProperty('--voice-level','0');}
  async function meter(){
    try{
      const media=await navigator.mediaDevices.getUserMedia({audio:true});
      if(disposed||!listening){media.getTracks().forEach(track=>track.stop());return;}
      stream=media;const Audio=window.AudioContext||window.webkitAudioContext;if(!Audio){releaseMeter();return;}
      context=new Audio();const analyser=context.createAnalyser();analyser.fftSize=256;context.createMediaStreamSource(stream).connect(analyser);const buffer=new Uint8Array(analyser.fftSize);
      const draw=()=>{if(!listening||disposed)return;analyser.getByteTimeDomainData(buffer);const rms=Math.sqrt(buffer.reduce((sum,v)=>sum+((v-128)/128)**2,0)/buffer.length);button.style.setProperty('--voice-level',String(Math.min(1,rms*8)));frame=requestAnimationFrame(draw);};draw();
    }catch{/* Recognition can continue without the optional level meter. */}
  }
  function end(){listening=false;releaseMeter();paint();}
  button.onclick=()=>{
    if(readOnly)return;
    if(listening){recognition?.stop();end();return;}
    if(!voicePreferences().consent){status.textContent='Enable microphone input in Settings first.';return;}
    if(!Recognition||!window.isSecureContext){status.textContent='Speech input is unavailable in this browser. You can still type.';return;}
    window.speechSynthesis?.cancel();failed=false;startingText=input.value.trim();recognition=new Recognition();recognition.lang='en-GB';recognition.interimResults=true;recognition.continuous=false;
    recognition.onresult=event=>{
      if(disposed||!voicePreferences().consent)return;
      const words=Array.from(event.results,result=>result[0].transcript).join(' ');
      input.value=(startingText+(startingText?' ':'')+words).slice(0,12000);onInput(input.value);
      status.textContent='Listening. Text remains a draft until you start the investigation.';
    };
    recognition.onerror=event=>{failed=true;status.textContent=({'not-allowed':'Microphone permission was denied. You can still type.','no-speech':'No speech detected. Try again or type.','audio-capture':'No microphone is available.','network':'The browser speech service could not connect.'})[event.error]||'Speech input stopped. You can still type.';end();};
    recognition.onend=()=>{end();if(!disposed){if(!failed)status.textContent='Microphone off. Review your draft before starting.';onFinish();}};
    try{recognition.start();listening=true;status.textContent='Listening. Select the microphone again to stop.';paint();void meter();}catch{status.textContent='The microphone could not start.';end();}
  };
  const manual=()=>{if(listening){recognition?.abort();end();}};
  const preferenceChanged=()=>{if(!voicePreferences().consent)manual();};
  input.addEventListener('keydown',manual);window.addEventListener(VOICE_EVENT,preferenceChanged);paint();
  return()=>{disposed=true;if(recognition){recognition.onresult=null;recognition.onend=null;recognition.onerror=null;recognition.abort();}end();button.onclick=null;input.removeEventListener('keydown',manual);window.removeEventListener(VOICE_EVENT,preferenceChanged);};
}
