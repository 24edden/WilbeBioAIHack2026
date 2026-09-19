// Browser-only voice. No microphone starts, remote synthesis or model calls on mount.
const sessions = new Map();

export function navigationTarget(text) {
  const normalized = String(text).trim().toLowerCase().replace(/[.!?]+$/, '').replace(/\s+/g, ' ');
  const match = /^(?:show|open|go to) (?:the )?(evidence|question|investigation|results)$/.exec(normalized);
  return match ? match[1] : null;
}

export function localVoice(voices) {
  const local = voices.filter(voice => voice.localService === true && /^en(?:-|$)/i.test(voice.lang));
  const quality = voice => (/natural|neural|enhanced|premium/i.test(voice.name || '') ? 4 : 0) + (voice.default ? 1 : 0);
  return local.sort((a, b) => quality(b) - quality(a))[0] || null;
}

export default function render(component) {
  const {parentElement, data, key, setTriggerValue} = component;
  const state = sessions.get(key) || {consent: false, spoken: false, mode: 'dictation', text: '', setupOpen: false, controlsOpen: false,
    seenAnnouncements: new Set(), recognition: null, listening: false, utterance: null, speechTimer: null, cleanupTimer: null,
    voiceId: 'auto', onlineVoices: false};
  if (state.cleanupTimer !== null) clearTimeout(state.cleanupTimer);
  if (state.speechTimer !== null) clearTimeout(state.speechTimer);
  state.cleanupTimer = state.speechTimer = null;
  sessions.set(key, state);
  const el = id => parentElement.querySelector(`#${id}`);
  const details = parentElement.querySelector('details');
  details.dataset.theme = data.theme === 'astral' ? 'astral' : 'dark';
  const consent = el('consent'), mode = el('mode'), listen = el('listen'), stop = el('stop');
  const transcript = el('transcript'), apply = el('apply'), status = el('status');
  const spoken = el('spoken'), speechStatus = el('speech-status');
  const voiceChoice = el('voice-choice'), onlineVoices = el('online-voices'), preview = el('preview');
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const synthesis = window.speechSynthesis;
  let recognition = state.recognition, listening = state.listening, disposed = false;
  const supported = Boolean(Recognition && window.isSecureContext);
  const setupMode = data.setupMode !== false;

  details.open = setupMode ? state.setupOpen : state.controlsOpen;
  el('voice-title').textContent = setupMode ? 'Voice setup' : 'Voice';
  el('recognition-settings').hidden = !setupMode;
  el('playback-settings').hidden = !setupMode;
  el('settings').hidden = setupMode;
  consent.checked = state.consent;
  spoken.checked = state.spoken;
  onlineVoices.checked = state.onlineVoices;
  mode.value = state.mode;
  transcript.value = state.text;
  if (!data.dictationEnabled && mode.value === 'dictation') mode.value = state.mode = 'command';
  mode.querySelector('[value="dictation"]').disabled = !data.dictationEnabled;

  function update() {
    const command = mode.value === 'command';
    listen.disabled = !supported || !consent.checked || listening;
    stop.disabled = !listening;
    listen.dataset.listening = String(listening);
    listen.textContent = listening ? 'Listening...' : 'Start microphone';
    mode.disabled = listening;
    el('commands').hidden = !command;
    apply.textContent = command ? 'Go' : 'Use as question';
    apply.disabled = listening || (command ? !navigationTarget(transcript.value) : !data.dictationEnabled || !transcript.value.trim());
    consent.disabled = !supported;
    el('voice-input').hidden = !setupMode && !state.consent && !state.text;
    el('voice-off').hidden = setupMode || state.consent;
    el('silence').hidden = !state.spoken && !state.utterance;
    el('voice-summary').textContent = setupMode ? 'Optional' : listening ? 'Listening' : state.spoken ? 'Spoken updates on' : state.consent ? 'Ready' : 'Off';
  }

  function stopSpeech() {
    if (state.speechTimer !== null) clearTimeout(state.speechTimer);
    state.speechTimer = null;
    if (state.utterance && synthesis) synthesis.cancel();
    state.utterance = null;
  }

  const voiceId = voice => `${voice.voiceURI || voice.name}|${voice.lang}|${voice.localService}`;
  function availableVoices() {
    return synthesis ? synthesis.getVoices().filter(voice => /^en(?:-|$)/i.test(voice.lang) && (voice.localService === true || state.onlineVoices)) : [];
  }
  function selectedVoice() {
    const available = availableVoices();
    return available.find(voice => voiceId(voice) === state.voiceId) || localVoice(available);
  }
  function populateVoices() {
    const available = availableVoices();
    voiceChoice.replaceChildren();
    const automatic = document.createElement('option');
    automatic.value = 'auto'; automatic.textContent = 'Best available device voice';
    voiceChoice.appendChild(automatic);
    for (const voice of available) {
      const option = document.createElement('option');
      option.value = voiceId(voice);
      option.textContent = `${voice.name || voice.lang} (${voice.localService ? 'device' : 'online'})`;
      voiceChoice.appendChild(option);
    }
    if (state.voiceId !== 'auto' && !available.some(voice => voiceId(voice) === state.voiceId)) state.voiceId = 'auto';
    voiceChoice.value = state.voiceId;
    voiceChoice.disabled = !synthesis;
    preview.disabled = !selectedVoice() || !window.SpeechSynthesisUtterance;
  }
  function speak(text) {
    if (!synthesis || !window.SpeechSynthesisUtterance || listening || disposed) return false;
    const voice = selectedVoice();
    if (!voice) {
      speechStatus.textContent = 'No device English voice is available yet. You can use on-screen updates or explicitly include online voices.';
      return false;
    }
    stopSpeech();
    const utterance = new window.SpeechSynthesisUtterance(text);
    utterance.voice = voice;
    utterance.lang = voice.lang;
    utterance.rate = 0.96;
    utterance.onerror = () => { speechStatus.textContent = 'Speech could not play. On-screen updates remain available.'; };
    synthesis.speak(utterance);
    state.utterance = utterance;
    update();
    speechStatus.textContent = voice.localService ? 'Using a local device voice.' : 'Using your selected online browser voice.';
    return true;
  }
  function announce(force = false) {
    if (!state.spoken || (!force && state.seenAnnouncements.has(data.announcementId))) return;
    if (!speak(data.announcement)) return;
    state.seenAnnouncements.add(data.announcementId);
  }

  details.ontoggle = () => { state[setupMode ? 'setupOpen' : 'controlsOpen'] = details.open; };
  el('settings').onclick = () => {
    state.setupOpen = true;
    const id = window.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setTriggerValue('action', {id, type: 'navigate', target: 'evidence'});
  };
  consent.onchange = () => {
    state.consent = consent.checked;
    if (!state.consent && recognition) recognition.abort();
    update();
  };
  mode.onchange = () => { state.mode = mode.value; update(); };
  transcript.oninput = () => { state.text = transcript.value; update(); };
  function bindRecognition() {
    if (!recognition) return;
    recognition.onresult = event => {
      if (disposed) return;
      const text = Array.from(event.results, result => result[0].transcript).join(' ').slice(0, 8000);
      transcript.value = state.text = text;
      update();
    };
    recognition.onerror = event => {
      const messages = {
        'not-allowed': 'Microphone permission was denied. Use typed input or change browser permissions.',
        'service-not-allowed': 'Speech recognition is unavailable in this browser. Use typed input.',
        'audio-capture': 'No microphone is available. Use typed input.',
        'network': 'The browser speech service could not connect. Use typed input.',
        'no-speech': 'No speech was detected. Try again or type your question.',
        'aborted': 'Microphone is off.',
      };
      status.textContent = messages[event.error] || 'Speech recognition stopped. Use typed input or try again.';
    };
    recognition.onend = () => {
      listening = state.listening = false;
      if (disposed) return;
      if (status.textContent === 'Listening. Select Stop when finished.') status.textContent = 'Microphone is off. Review the text before applying.';
      update();
    };
  }
  bindRecognition();
  listen.onclick = () => {
    if (!supported || !consent.checked || listening) return;
    stopSpeech();
    recognition = state.recognition = new Recognition();
    recognition.lang = 'en-GB';
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    bindRecognition();
    try {
      recognition.start();
      listening = state.listening = true;
      status.textContent = 'Listening. Select Stop when finished.';
    } catch {
      status.textContent = 'The microphone could not start. Use typed input or try again.';
    }
    update();
  };
  stop.onclick = () => { if (recognition) recognition.stop(); };
  apply.onclick = () => {
    if (apply.disabled) return;
    const id = window.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const target = navigationTarget(transcript.value);
    if (mode.value === 'command') {
      if (!target) return;
      setTriggerValue('action', {id, type: 'navigate', target});
      status.textContent = 'Navigation requested. Unavailable steps stay locked.';
    } else if (data.dictationEnabled && transcript.value.trim()) {
      setTriggerValue('action', {id, type: 'dictation', text: transcript.value.trim()});
      status.textContent = 'Text applied to the question draft. Review before submitting.';
    }
  };
  spoken.disabled = !synthesis || !window.SpeechSynthesisUtterance;
  spoken.onchange = () => {
    state.spoken = spoken.checked;
    if (state.spoken) announce(true);
    else { stopSpeech(); speechStatus.textContent = 'Spoken updates are off.'; }
    update();
  };
  el('silence').onclick = () => {
    state.spoken = spoken.checked = false;
    stopSpeech();
    speechStatus.textContent = 'Spoken updates are off.';
    update();
  };
  voiceChoice.onchange = () => { state.voiceId = voiceChoice.value; stopSpeech(); populateVoices(); };
  onlineVoices.onchange = () => {
    state.onlineVoices = onlineVoices.checked;
    stopSpeech();
    populateVoices();
    speechStatus.textContent = state.onlineVoices ? 'Online voices are available in the list. Choose one and select Preview voice.' : 'Only local device voices are available in the list.';
  };
  preview.onclick = () => speak("Hello. I can keep you updated as the investigation moves forward.");
  const voicesChanged = () => { populateVoices(); announce(); };
  if (synthesis) synthesis.addEventListener('voiceschanged', voicesChanged);
  if (!supported) status.textContent = 'Voice input is unavailable in this browser or connection. Continue with typed input.';
  else if (listening) status.textContent = 'Listening. Select Stop when finished.';
  if (spoken.disabled) speechStatus.textContent = 'Speech playback is unavailable. On-screen updates remain available.';
  onlineVoices.disabled = spoken.disabled;
  populateVoices();
  update();
  // Debounce data-driven stage changes; checking the option itself speaks immediately.
  if (state.spoken) state.speechTimer = setTimeout(() => announce(), 600);

  return () => {
    disposed = true;
    if (synthesis) synthesis.removeEventListener('voiceschanged', voicesChanged);
    // Streamlit cleans up immediately before same-key data updates. A short grace
    // period lets the next renderer take ownership without interrupting dictation.
    state.cleanupTimer = setTimeout(() => {
      if (recognition) { recognition.onresult = null; recognition.onerror = null; recognition.onend = null; recognition.abort(); }
      stopSpeech();
      sessions.delete(key);
    }, 50);
  };
}
