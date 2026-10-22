/* Captura PCM mono sin depender de los formatos de MediaRecorder del navegador. */
class MuroRecorder extends AudioWorkletProcessor {
  process(inputs) {
    const channel = inputs[0]?.[0];
    if (channel) this.port.postMessage(channel.slice());
    return true;
  }
}
registerProcessor('muro-recorder', MuroRecorder);
