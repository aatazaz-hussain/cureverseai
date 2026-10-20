/**
 * CureVerseAI — Medicine domain
 * Browser speech synthesis wrapper.
 *
 * Copied from
 * frontend/app/domains/drug_development/reverse-disease-engineering/voice.ts
 * verbatim, with the namespace comment updated. Behaviour is
 * intentionally identical across workflows.
 */

export interface VoiceState {
  available: boolean;
  enabled: boolean;
  activeVoiceName: string | null;
}

const FEMALE_VOICE_HINTS = [
  "female",
  "samantha",
  "victoria",
  "karen",
  "moira",
  "tessa",
  "fiona",
  "google uk english female",
  "google us english",
  "microsoft aria",
  "microsoft jenny",
  "microsoft zira",
  "microsoft hazel",
];

let cachedVoice: SpeechSynthesisVoice | null = null;
let listenersBound = false;

function pickVoice(): SpeechSynthesisVoice | null {
  if (typeof window === "undefined") return null;
  if (!("speechSynthesis" in window)) return null;

  const voices = window.speechSynthesis.getVoices();
  if (!voices || voices.length === 0) return null;

  const english = voices.filter((v) =>
    v.lang.toLowerCase().startsWith("en"),
  );
  const pool = english.length > 0 ? english : voices;

  for (const hint of FEMALE_VOICE_HINTS) {
    const match = pool.find((v) =>
      v.name.toLowerCase().includes(hint),
    );
    if (match) return match;
  }

  return pool[0] ?? null;
}

function ensureVoicesLoaded(): void {
  if (typeof window === "undefined") return;
  if (!("speechSynthesis" in window)) return;
  if (listenersBound) return;

  listenersBound = true;

  const refresh = () => {
    cachedVoice = pickVoice();
  };

  window.speechSynthesis.addEventListener(
    "voiceschanged",
    refresh,
  );
  refresh();
}

export function isSpeechAvailable(): boolean {
  if (typeof window === "undefined") return false;
  return "speechSynthesis" in window;
}

export function getActiveVoiceName(): string | null {
  ensureVoicesLoaded();
  if (!cachedVoice) cachedVoice = pickVoice();
  return cachedVoice ? cachedVoice.name : null;
}

export function speak(
  text: string,
  options?: { rate?: number; pitch?: number },
): void {
  if (typeof window === "undefined") return;
  if (!("speechSynthesis" in window)) return;
  if (!text || !text.trim()) return;

  ensureVoicesLoaded();
  if (!cachedVoice) cachedVoice = pickVoice();

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = options?.rate ?? 1.0;
  utterance.pitch = options?.pitch ?? 1.0;
  utterance.volume = 1.0;

  if (cachedVoice) {
    utterance.voice = cachedVoice;
    utterance.lang = cachedVoice.lang;
  }

  window.speechSynthesis.speak(utterance);
}

export function stopSpeaking(): void {
  if (typeof window === "undefined") return;
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
}
