/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * Browser TTS wrapper with female-voice preference.
 *
 * Same behavior as W02's voice.ts:
 *   1. Caches the voice list once voices are loaded.
 *   2. Picks the first English voice matching a female hint.
 *   3. Falls back through non-male, then any English voice.
 *
 * Deliberately a fresh file (not an import from W02) so the
 * two workflows stay independently editable.
 */

export interface SpeakOptions {
  onEnd?: () => void;
  onStart?: () => void;
  rate?: number;
  pitch?: number;
}

export function isSpeechAvailable(): boolean {
  return (
    typeof window !== "undefined" &&
    "speechSynthesis" in window &&
    typeof window.SpeechSynthesisUtterance === "function"
  );
}

// ---------------------------------------------------------------------------
// Voice selection
// ---------------------------------------------------------------------------

const FEMALE_HINTS = [
  "female",
  "samantha",
  "victoria",
  "karen",
  "moira",
  "tessa",
  "fiona",
  "zira",
  "susan",
  "hazel",
  "aria",
  "jenny",
  "michelle",
  "allison",
  "ava",
  "serena",
  "kate",
  "stephanie",
  "google us english",
  "google uk english female",
];

const MALE_HINTS = [
  "male",
  "daniel",
  "alex",
  "fred",
  "david",
  "mark",
  "tom",
  "oliver",
  "diego",
  "jorge",
  "thomas",
  "google uk english male",
];

let cachedVoice: SpeechSynthesisVoice | null = null;

function resolveVoice(): SpeechSynthesisVoice | null {
  if (!isSpeechAvailable()) return null;

  const voices = window.speechSynthesis.getVoices();
  if (!voices.length) return null;

  for (const hint of FEMALE_HINTS) {
    const found = voices.find(
      (v) =>
        v.lang.toLowerCase().startsWith("en") &&
        v.name.toLowerCase().includes(hint),
    );
    if (found) return found;
  }

  for (const voice of voices) {
    if (!voice.lang.toLowerCase().startsWith("en")) continue;
    const lower = voice.name.toLowerCase();
    const isMale = MALE_HINTS.some((h) => lower.includes(h));
    if (!isMale) return voice;
  }

  const english = voices.find((v) =>
    v.lang.toLowerCase().startsWith("en"),
  );
  if (english) return english;

  return voices[0] ?? null;
}

function getActiveVoice(): SpeechSynthesisVoice | null {
  if (cachedVoice) return cachedVoice;
  if (!isSpeechAvailable()) return null;
  cachedVoice = resolveVoice();
  return cachedVoice;
}

if (typeof window !== "undefined" && isSpeechAvailable()) {
  try {
    cachedVoice = resolveVoice();
    window.speechSynthesis.addEventListener(
      "voiceschanged",
      () => {
        cachedVoice = resolveVoice();
      },
    );
  } catch {
    // ignore
  }
}

// ---------------------------------------------------------------------------
// Speak
// ---------------------------------------------------------------------------

function actuallySpeak(
  text: string,
  options: SpeakOptions,
): boolean {
  try {
    window.speechSynthesis.cancel();

    const u = new window.SpeechSynthesisUtterance(text);

    const voice = getActiveVoice();
    if (voice) {
      u.voice = voice;
      u.lang = voice.lang;
    }

    u.rate = options.rate ?? 1.0;
    u.pitch = options.pitch ?? 1.05;
    u.volume = 1.0;

    if (options.onStart) {
      u.addEventListener("start", options.onStart);
    }
    if (options.onEnd) {
      u.addEventListener("end", options.onEnd);
    }

    window.speechSynthesis.speak(u);
    return true;
  } catch {
    return false;
  }
}

export function speak(
  text: string,
  options: SpeakOptions = {},
): boolean {
  if (!isSpeechAvailable()) return false;
  if (!text || !text.trim()) return false;

  if (!getActiveVoice()) {
    try {
      const handler = () => {
        try {
          window.speechSynthesis.removeEventListener(
            "voiceschanged",
            handler,
          );
        } catch {
          // ignore
        }
        actuallySpeak(text, options);
      };

      window.speechSynthesis.addEventListener(
        "voiceschanged",
        handler,
      );

      setTimeout(() => {
        try {
          window.speechSynthesis.removeEventListener(
            "voiceschanged",
            handler,
          );
        } catch {
          // ignore
        }
        actuallySpeak(text, options);
      }, 500);

      return true;
    } catch {
      return actuallySpeak(text, options);
    }
  }

  return actuallySpeak(text, options);
}

export function stopSpeaking(): void {
  if (!isSpeechAvailable()) return;
  try {
    window.speechSynthesis.cancel();
  } catch {
    // ignore
  }
}

export function getActiveVoiceName(): string | null {
  const v = getActiveVoice();
  return v ? v.name : null;
}
