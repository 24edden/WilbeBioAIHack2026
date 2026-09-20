// Browser-only voice. No microphone starts, remote synthesis or model calls on mount.
const sessions = new Map();

export function waveformLevels(samples) {
  return Array.from({length: 5}, (_, index) => {
    const start = Math.floor(index * samples.length / 5), end = Math.floor((index + 1) * samples.length / 5);
    let sum = 0;
    for (let i = start; i < end; i++) sum += ((samples[i] - 128) / 128) ** 2;
    return Math.min(1, Math.sqrt(sum / Math.max(1, end - start)) * 6);
  });
}

// Analyser audio stays in this browser. It is never recorded or connected to speakers.
export class MicrophoneMeter {
  constructor(onLevels = () => {}) {
    this.onLevels = onLevels;
    this.stopped = false;
    this.active = false;
    this.frame = null;
  }
  async start() {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext || !window.navigator?.mediaDevices?.getUserMedia) return;
    try {
      this.context = new AudioContext();
      // Resume while still in the click gesture; permission can resolve later.
      const ready = this.context.resume().catch(() => {});
      const stream = await window.navigator.mediaDevices.getUserMedia({audio: true});
      if (this.stopped) { stream.getTracks().forEach(track => track.stop()); return; }
      this.stream = stream;
      await ready;
      if (this.stopped) return;
      this.analyser = this.context.createAnalyser();
      this.analyser.fftSize = 256;
      this.input = this.context.createMediaStreamSource(stream);
      this.input.connect(this.analyser);
      this.samples = new Uint8Array(this.analyser.fftSize);
      this.active = true;
      const tick = () => {
        if (this.stopped) return;
        this.analyser.getByteTimeDomainData(this.samples);
        this.onLevels(waveformLevels(this.samples));
        this.frame = window.requestAnimationFrame(tick);
      };
      tick();
    } catch {
      this.stop(); // Speech recognition can still work without an analyser.
    }
  }
  stop() {
    this.stopped = true;
    this.active = false;
    if (this.frame !== null) window.cancelAnimationFrame(this.frame);
    this.stream?.getTracks().forEach(track => track.stop());
    this.input?.disconnect();
    this.analyser?.disconnect();
    if (this.context && this.context.state !== 'closed') this.context.close().catch(() => {});
    this.stream = this.input = this.analyser = null;
    this.onLevels([0, 0, 0, 0, 0]);
  }
}

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
    voiceId: 'auto', onlineVoices: false, phase: 'idle', meter: null, speechTimerReset: null};
  if (state.cleanupTimer !== null) clearTimeout(state.cleanupTimer);
  if (state.speechTimer !== null) clearTimeout(state.speechTimer);
  state.cleanupTimer = state.speechTimer = null;
  sessions.set(key, state);
  const el = id => parentElement.querySelector(`#${id}`);
  const details = parentElement.querySelector('details');
  const syncTheme = () => { details.dataset.theme = document.documentElement?.dataset.traceTheme || (data.theme === 'astral' ? 'astral' : 'dark'); };
  syncTheme();
  window.addEventListener('trace-theme-change', syncTheme);
  const consent = el('consent'), mode = el('mode'), listen = el('listen');
  const transcript = el('transcript'), apply = el('apply'), status = el('status');
  const spoken = el('spoken'), speechStatus = el('speech-status');
  const voiceChoice = el('voice-choice'), onlineVoices = el('online-voices'), preview = el('preview');
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const synthesis = window.speechSynthesis;
  let recognition = state.recognition, listening = state.listening, disposed = false;
  const supported = Boolean(Recognition && window.isSecureContext);
  const setupMode = data.setupMode !== false;
  const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

  function paintLevels(levels) {
    if (disposed) return;
    listen.dataset.meter = state.meter?.active ? 'live' : 'fallback';
    listen.dataset.audioActive = String(listening && levels.some(value => value > .12));
    for (let i = 0; i < 5; i++) {
      el(`wave-${i}`).style.transform = `scaleY(${reducedMotion ? .5 : .18 + levels[i] * 1.1})`;
    }
  }
  if (state.meter) state.meter.onLevels = paintLevels;
  paintLevels([0, 0, 0, 0, 0]);

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
    listen.disabled = !supported || !consent.checked || state.phase === 'finishing';
    listen.dataset.listening = String(listening);
    listen.dataset.phase = state.phase;
    listen.setAttribute('aria-label', listening ? 'Finish dictation' : 'Start microphone');
    listen.setAttribute('aria-pressed', String(listening));
    el('mic-label').textContent = {starting: 'Connecting microphone', listening: 'Listening', speaking: 'Recognising your voice', finishing: 'Finishing dictation', error: 'Let’s try again'}[state.phase] || (command ? 'Navigate by voice' : 'Speak your question');
    el('mic-hint').textContent = !supported ? 'Type your question in this browser.' : !state.consent ? 'Enable voice input above, then tap the microphone.' : listening ? 'Tap the microphone again when you’re finished.' : 'Tap the microphone and start speaking.';
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
    if (!state.consent) {
      state.meter?.stop();
      if (recognition) recognition.abort();
      listening = state.listening = false;
      state.phase = 'idle';
      status.textContent = 'Microphone is off.';
    }
    update();
  };
  mode.onchange = () => { state.mode = mode.value; update(); };
  transcript.oninput = () => { state.text = transcript.value; update(); };
  function bindRecognition() {
    if (!recognition) return;
    const bound = recognition;
    const isCurrent = () => !disposed && state.recognition === bound;
    recognition.onstart = recognition.onaudiostart = () => {
      if (!isCurrent() || !listening || state.phase === 'finishing') return;
      state.phase = 'listening';
      status.textContent = 'Ready for your voice.';
      update();
    };
    recognition.onspeechstart = () => {
      if (!isCurrent() || !listening || state.phase === 'finishing') return;
      state.phase = 'speaking';
      status.textContent = 'Speech detected. Your words appear below.';
      update();
    };
    recognition.onspeechend = () => {
      if (!isCurrent() || !listening || state.phase === 'finishing') return;
      state.phase = 'listening';
      status.textContent = 'Listening for your next words.';
      update();
    };
    recognition.onaudioend = () => {
      if (!isCurrent()) return;
      state.meter?.stop();
      if (disposed || !listening || state.phase === 'error') return;
      state.phase = 'finishing';
      status.textContent = 'Finishing the transcript.';
      update();
    };
    recognition.onresult = event => {
      if (!isCurrent()) return;
      const text = Array.from(event.results, result => result[0].transcript).join(' ').slice(0, 8000);
      transcript.value = state.text = text;
      if (listening && state.phase !== 'finishing') {
        state.phase = 'speaking';
        status.textContent = 'Recognising your words.';
        clearTimeout(state.speechTimerReset);
        state.speechTimerReset = setTimeout(() => {
          if (!disposed && listening && state.phase === 'speaking') {
            state.phase = 'listening';
            update();
          }
        }, 900);
      }
      update();
    };
    recognition.onerror = event => {
      if (!isCurrent()) return;
      state.meter?.stop();
      listening = state.listening = false;
      state.phase = event.error === 'aborted' ? 'idle' : 'error';
      const messages = {
        'not-allowed': 'Microphone permission was denied. Use typed input or change browser permissions.',
        'service-not-allowed': 'Speech recognition is unavailable in this browser. Use typed input.',
        'audio-capture': 'No microphone is available. Use typed input.',
        'network': 'The browser speech service could not connect. Use typed input.',
        'no-speech': 'No speech was detected. Try again or type your question.',
        'aborted': 'Microphone is off.',
      };
      status.textContent = messages[event.error] || 'Speech recognition stopped. Use typed input or try again.';
      update();
    };
    recognition.onend = () => {
      if (!isCurrent()) return;
      listening = state.listening = false;
      state.meter?.stop();
      clearTimeout(state.speechTimerReset);
      if (disposed) return;
      if (state.phase !== 'error') {
        state.phase = 'idle';
        status.textContent = state.text ? 'Ready to review. Your microphone is off.' : 'Microphone is off.';
      }
      update();
    };
  }
  bindRecognition();
  listen.onclick = () => {
    if (!supported || !consent.checked || state.phase === 'finishing') return;
    if (listening) {
      state.phase = 'finishing';
      state.meter?.stop();
      status.textContent = 'Finishing the transcript.';
      try { recognition.stop(); } catch { recognition.abort(); }
      update();
      return;
    }
    stopSpeech();
    recognition = state.recognition = new Recognition();
    recognition.lang = 'en-GB';
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    bindRecognition();
    try {
      listening = state.listening = true;
      state.phase = 'starting';
      status.textContent = 'Waiting for microphone access.';
      recognition.start();
      state.meter?.stop();
      state.meter = new MicrophoneMeter(paintLevels);
      void state.meter.start();
    } catch {
      listening = state.listening = false;
      state.phase = 'error';
      state.meter?.stop();
      status.textContent = 'The microphone could not start. Use typed input or try again.';
    }
    update();
  };
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
  else if (listening) status.textContent = state.phase === 'starting' ? 'Waiting for microphone access.' : 'Microphone is on. Tap it again to finish.';
  if (spoken.disabled) speechStatus.textContent = 'Speech playback is unavailable. On-screen updates remain available.';
  onlineVoices.disabled = spoken.disabled;
  populateVoices();
  update();
  // Debounce data-driven stage changes; checking the option itself speaks immediately.
  if (state.spoken) state.speechTimer = setTimeout(() => announce(), 600);

  return () => {
    disposed = true;
    window.removeEventListener('trace-theme-change', syncTheme);
    if (synthesis) synthesis.removeEventListener('voiceschanged', voicesChanged);
    // Streamlit cleans up immediately before same-key data updates. A short grace
    // period lets the next renderer take ownership without interrupting dictation.
    state.cleanupTimer = setTimeout(() => {
      if (recognition) {
        for (const name of ['onresult', 'onerror', 'onend', 'onstart', 'onaudiostart', 'onaudioend', 'onspeechstart', 'onspeechend']) recognition[name] = null;
        recognition.abort();
      }
      clearTimeout(state.speechTimerReset);
      state.meter?.stop();
      stopSpeech();
      sessions.delete(key);
    }, 50);
  };
}
