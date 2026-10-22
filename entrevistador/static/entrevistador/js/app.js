'use strict';
const form = document.querySelector('form[data-draft]');
const statusLine = document.querySelector('#live-status');
const tell = text => { statusLine.textContent = text; };
let dirty = false, timer, saving = Promise.resolve(), submitting = false;
let recordingActive = false, recordingStarting = false, pendingRecording = false;
let updateAvailability = () => {};
if (form) {
  const mode = form.querySelector('[name=mode]');
  function showMode() {
    if ((recordingActive || recordingStarting) && mode.value !== 'Audio') {
      mode.value = 'Audio'; tell('Detén la grabación antes de cambiar a texto.'); return;
    }
    form.querySelectorAll('[data-mode]').forEach(part => { part.hidden = part.dataset.mode !== mode.value; });
  }
  mode?.addEventListener('change', showMode);
  showMode();
  const answerButton = form.querySelector('[value=answer]');
  const transcribeButton = form.querySelector('[value=transcribe]');
  const canAnswer = answerButton && !answerButton.disabled;
  const canTranscribe = transcribeButton && !transcribeButton.disabled;
  updateAvailability = () => {
    if (answerButton) {
      const answer = form.querySelector(mode.value === 'Texto' ? '#written' : '#transcript');
      answerButton.disabled = !canAnswer || !answer.value.trim() || submitting;
    }
    if (transcribeButton) transcribeButton.disabled = !canTranscribe || submitting ||
      !(form.querySelector('#recording').files.length || transcribeButton.dataset.hasRecording === 'true');
  };
  mode?.addEventListener('change', updateAvailability);
  updateAvailability();
  async function saveDraft() {
    clearTimeout(timer);
    if (!dirty || submitting) return saving;
    dirty = false;
    const data = new FormData(form);
    data.delete('recording'); data.delete('document');
    data.set('kind', form.dataset.draft);
    saving = saving.catch(() => {}).then(async () => {
      try {
        const result = await fetch('/borrador/', { method: 'POST', body: data });
        if (!result.ok) throw new Error('No se pudo guardar el borrador. Conserva el texto y vuelve a intentar.');
        tell('Borrador guardado.');
      } catch (error) { dirty = true; tell(error.message); throw error; }
    });
    return saving;
  }
  form.addEventListener('input', event => {
    event.target.setCustomValidity?.('');
    updateAvailability();
    if (event.target.type === 'file') return;
    dirty = true; clearTimeout(timer);
    timer = setTimeout(() => { saveDraft().catch(() => {}); }, 650);
  });
  document.querySelectorAll('a[href]').forEach(link => link.addEventListener('click', async event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    if (link.origin === location.origin) {
      event.preventDefault();
      if (recordingActive || recordingStarting || pendingRecording) { tell('Transcribe la grabación antes de cambiar de página para conservarla.'); return; }
      if (submitting) return;
      try { await saveDraft(); await saving; location.href = link.href; } catch (_) { /* Mantiene el borrador visible. */ }
    }
  }));
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (recordingActive || recordingStarting) { tell('Primero detén la grabación.'); return; }
    if (submitting) return;
    const operation = event.submitter?.value || (form.dataset.draft === 'preparacion' ? 'start' : 'answer');
    if (operation === 'start') {
      const context = form.querySelector('#id_context');
      const document = form.querySelector('#id_document');
      if (!document.files.length && !form.dataset.savedDocument && context.value.trim().length < 40) {
        context.setCustomValidity('Comparte al menos 40 caracteres sobre el puesto o carga un documento.');
        context.reportValidity(); return;
      }
    }
    submitting = true;
    if (event.submitter?.dataset.confirm && !await confirmAction(event.submitter.dataset.confirm)) {
      submitting = false; return;
    }
    clearTimeout(timer);
    try { await saving; } catch (_) { /* El POST principal también conserva el borrador. */ }
    if (!form.reportValidity()) { submitting = false; return; }
    const action = document.createElement('input');
    action.type = 'hidden'; action.name = 'action'; action.value = operation;
    form.append(action);
    dirty = false; pendingRecording = false;
    const labels = { start: 'Preparando tu primera pregunta…', answer: 'Preparando el siguiente paso…',
      transcribe: 'Transcribiendo tu respuesta…', speak: 'Preparando la voz de tu entrevistador…',
      finish: 'Preparando tu evaluación…', clear_recording: 'Eliminando la grabación…' };
    document.querySelector('#processing-title').textContent = labels[operation] || 'Un momento…';
    document.querySelector('#processing').hidden = false;
    document.querySelector('#processing').scrollIntoView({ block: 'nearest' });
    form.setAttribute('aria-busy', 'true');
    tell('');
    form.querySelectorAll('button').forEach(button => { button.disabled = true; });
    // La validación ya se ejecutó. Evita un segundo evento submit reentrante.
    HTMLFormElement.prototype.submit.call(form);
  });
}

let context, stream, source, processor, mute, chunks = [], recorded = 0, limitTimer, recordingTimer;
const recordButton = document.querySelector('#record');
const stopButton = document.querySelector('#stop-recording');
const recordStatus = document.querySelector('#record-status');
let previewUrl;
function wavBlob(samples, rate) {
  const outputRate = 16000, length = Math.floor(samples.length * outputRate / rate);
  const buffer = new ArrayBuffer(44 + length * 2), view = new DataView(buffer);
  const ascii = (offset, text) => [...text].forEach((c, i) => view.setUint8(offset + i, c.charCodeAt(0)));
  ascii(0, 'RIFF'); view.setUint32(4, 36 + length * 2, true); ascii(8, 'WAVE');
  ascii(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
  view.setUint16(22, 1, true); view.setUint32(24, outputRate, true);
  view.setUint32(28, outputRate * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  ascii(36, 'data'); view.setUint32(40, length * 2, true);
  for (let i = 0; i < length; i++) {
    const position = i * rate / outputRate, left = Math.floor(position), fraction = position - left;
    const sample = samples[left] * (1 - fraction) + (samples[Math.min(left + 1, samples.length - 1)] * fraction);
    const clamped = Math.max(-1, Math.min(1, sample));
    view.setInt16(44 + i * 2, clamped * (clamped < 0 ? 32768 : 32767), true);
  }
  return new Blob([buffer], { type: 'audio/wav' });
}
async function releaseRecorder() {
  clearTimeout(limitTimer); clearInterval(recordingTimer);
  document.querySelector('.recorder-panel')?.classList.remove('recording-now');
  stream?.getTracks().forEach(track => track.stop());
  source?.disconnect(); processor?.disconnect(); mute?.disconnect();
  if (context && context.state !== 'closed') await context.close();
  recordingActive = false;
  recordButton.disabled = false; stopButton.disabled = true;
}
recordButton?.addEventListener('click', async () => {
  recordButton.disabled = true; recordingStarting = true;
  try {
    if (!navigator.mediaDevices?.getUserMedia) throw new Error('El micrófono necesita HTTPS o localhost. También puedes cargar un WAV.');
    chunks = []; recorded = 0;
    stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1 }, video: false });
    context = new AudioContext();
    if (!context.audioWorklet) throw new Error('Tu navegador no admite la grabación. Carga un WAV o responde por texto.');
    await context.audioWorklet.addModule(document.querySelector('.recorder').dataset.worklet);
    await context.resume();
    source = context.createMediaStreamSource(stream);
    processor = new AudioWorkletNode(context, 'muro-recorder');
    mute = context.createGain(); mute.gain.value = 0;
    processor.port.onmessage = event => {
      if (recordingActive) { chunks.push(event.data); recorded += event.data.length; }
    };
    source.connect(processor); processor.connect(mute); mute.connect(context.destination);
    recordingActive = true; stopButton.disabled = false;
    recordStatus.textContent = 'Grabando… 0:00';
    document.querySelector('.recorder-panel').classList.add('recording-now');
    const started = Date.now();
    recordingTimer = setInterval(() => {
      const seconds = Math.floor((Date.now() - started) / 1000);
      recordStatus.textContent = `Grabando… ${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
    }, 1000);
    limitTimer = setTimeout(() => stopButton.click(), 180000);
  } catch (error) { await releaseRecorder(); tell(`No se pudo grabar: ${error.message}`); }
  finally { recordingStarting = false; }
});
stopButton?.addEventListener('click', async () => {
  if (!recordingActive) return;
  stopButton.disabled = true;
  const rate = context.sampleRate;
  const samples = new Float32Array(recorded);
  let offset = 0; chunks.forEach(chunk => { samples.set(chunk, offset); offset += chunk.length; });
  await releaseRecorder(); chunks = [];
  if (samples.length < rate / 4) { recordStatus.textContent = 'Graba al menos un segundo.'; return; }
  try {
    const blob = wavBlob(samples, rate);
    const transfer = new DataTransfer(); transfer.items.add(new File([blob], 'respuesta.wav', { type: 'audio/wav' }));
    document.querySelector('#recording').files = transfer.files;
    pendingRecording = true; updateAvailability();
    const preview = document.querySelector('#record-preview');
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = URL.createObjectURL(blob); preview.src = previewUrl; preview.hidden = false;
    recordStatus.textContent = 'Lista. Pulsa Transcribir respuesta.';
  } catch (error) { tell(`No se pudo preparar el audio: ${error.message}`); }
});
window.addEventListener('beforeunload', event => {
  if (recordingActive || recordingStarting || pendingRecording || dirty) { event.preventDefault(); event.returnValue = ''; }
});


function confirmAction(message) {
  const dialog = document.querySelector('#confirm-dialog');
  if (!dialog?.showModal) return Promise.resolve(window.confirm(message));
  return new Promise(resolve => {
    const accept = document.querySelector('#confirm-accept');
    const cancel = document.querySelector('#confirm-cancel');
    document.querySelector('#confirm-message').textContent = message;
    const finish = result => {
      accept.removeEventListener('click', yes);
      cancel.removeEventListener('click', no);
      dialog.removeEventListener('cancel', escape);
      dialog.close(); resolve(result);
    };
    const yes = () => finish(true);
    const no = () => finish(false);
    const escape = event => { event.preventDefault(); finish(false); };
    accept.addEventListener('click', yes); cancel.addEventListener('click', no);
    dialog.addEventListener('cancel', escape);
    dialog.showModal(); cancel.focus();
  });
}

document.querySelectorAll('form[data-confirm]').forEach(resetForm => {
  resetForm.addEventListener('submit', async event => {
    event.preventDefault();
    if (submitting) return;
    const operation = event.submitter?.value || 'reset';
    submitting = true;
    if (!await confirmAction(resetForm.dataset.confirm)) { submitting = false; return; }
    clearTimeout(timer);
    try { await saving; } catch (_) { /* La práctica se va a borrar. */ }
    const action = document.createElement('input');
    action.type = 'hidden'; action.name = 'action'; action.value = operation;
    resetForm.append(action); dirty = false; pendingRecording = false; recordingActive = false;
    HTMLFormElement.prototype.submit.call(resetForm);
  });
});

function updateCounts() {
  document.querySelectorAll('[data-count-for]').forEach(counter => {
    const field = document.getElementById(counter.dataset.countFor);
    counter.textContent = `${field.value.length.toLocaleString('es-PE')} / ${field.maxLength.toLocaleString('es-PE')}`;
  });
}
form?.addEventListener('input', updateCounts);
updateCounts();
form?.addEventListener('keydown', event => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    const answer = form.querySelector('[value=answer]');
    if (answer && !answer.disabled) { event.preventDefault(); form.requestSubmit(answer); }
  }
});
document.querySelector('#id_document')?.addEventListener('change', event => {
  const file = event.target.files[0];
  document.querySelector('#document-feedback').textContent = file ? `Listo para usar: ${file.name}` : '';
  if (file?.size > 5 * 1024 * 1024) {
    event.target.setCustomValidity('El documento debe pesar como máximo 5 MB.');
    event.target.reportValidity();
  }
  form.querySelector('#id_context').setCustomValidity('');
});
document.querySelector('#recording')?.addEventListener('change', event => {
  pendingRecording = event.target.files.length > 0;
  if (event.target.files[0]?.size > 14 * 1024 * 1024) {
    event.target.setCustomValidity('El audio debe pesar como máximo 14 MB.');
    event.target.reportValidity();
  } else event.target.setCustomValidity('');
  updateAvailability();
});
