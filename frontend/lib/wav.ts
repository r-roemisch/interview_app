// Browsers record webm or mp4, which the transcription model cannot read (ADR-0005).
// This turns any recording the browser can play into a 16 kHz mono WAV file.

const SAMPLE_RATE = 16000; // plenty for speech; 5 minutes is about 10 MB

export async function toWav(recording: Blob): Promise<Blob> {
  // An OfflineAudioContext decodes without playing anything, and resamples to its own rate.
  const context = new OfflineAudioContext(1, 1, SAMPLE_RATE);
  const audio = await context.decodeAudioData(await recording.arrayBuffer());

  // Mix all channels down to one.
  const samples = new Float32Array(audio.length);
  for (let c = 0; c < audio.numberOfChannels; c++) {
    audio.getChannelData(c).forEach((v, i) => (samples[i] += v / audio.numberOfChannels));
  }

  // A 44-byte WAV header, then every sample as a 16-bit integer.
  const view = new DataView(new ArrayBuffer(44 + samples.length * 2));
  const text = (offset: number, s: string) => [...s].forEach((ch, i) => view.setUint8(offset + i, ch.charCodeAt(0)));
  text(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  text(8, "WAVE");
  text(12, "fmt ");
  view.setUint32(16, 16, true); // size of this header part
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, SAMPLE_RATE, true);
  view.setUint32(28, SAMPLE_RATE * 2, true); // bytes per second
  view.setUint16(32, 2, true); // bytes per sample
  view.setUint16(34, 16, true); // bits per sample
  text(36, "data");
  view.setUint32(40, samples.length * 2, true);
  samples.forEach((v, i) => view.setInt16(44 + i * 2, Math.max(-1, Math.min(1, v)) * 0x7fff, true));
  return new Blob([view], { type: "audio/wav" });
}
