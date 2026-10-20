/**
 * CureVerseAI — Disease → Biological Impact
 * Browser voice wrapper.
 *
 * Thin layer over window.speechSynthesis. Picks a
 * female English voice when available, falls back to
 * any English voice, falls back to the default.
 *
 * Behavior:
 *
 *   - speak(text) — cancels any in-flight utterance and
 *     speaks the new text. Speaking a new phrase
 *     interrupts the previous one, so rapid clicks do
 *     not queue up.
 *
 *   - stop() — cancels any in-flight utterance.
 *
 *   - setMuted(bool) — suppresses speak() while muted.
 *     Does not affect an utterance already in flight;
 *     call stop() for that.
 *
 * Browsers only allow speech synthesis after the user
 * has interacted with the page. The disease submit
 * button counts as interaction, so by the time the
 * journey needs to speak, speech is enabled.
 *
 * No API keys, no external services. Uses whatever
 * voices the browser ships with.
 */

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let muted = false;
let cachedVoice: SpeechSynthesisVoice | null = null;
let voiceResolved = false;

// ---------------------------------------------------------------------------
// Voice selection
// ---------------------------------------------------------------------------

/**
 * Pick the best available voice for narration.
 *
 * Preference:
 *   1. A female English voice (voice.name contains
 *      "female" or matches a small allowlist)
 *   2. Any English voice
 *   3. The default voice
 *
 * Result is cached for the lifetime of the page.
 */
function resolveVoice(): SpeechSynthesisVoice | null {
  if (voiceResolved) return cachedVoice;

  if (typeof window === "undefined") return null;

  const synth = window.speechSynthesis;
  if (!synth) return null;

  const voices = synth.getVoices();
  if (!voices || voices.length === 0) return null;

  // Explicit female names first.
  const femaleNames = [
    "Samantha",
    "Karen",
    "Moira",
    "Tessa",
    "Victoria",
    "Google UK English Female",
    "Google US English",
    "Microsoft Zira",
    "Microsoft Hazel",
  ];

  for (const name of femaleNames) {
    const v = voices.find((v) => v.name === name);
    if (v) {
      cachedVoice = v;
      voiceResolved = true;
      return v;
    }
  }

  // Fallback: any voice with "female" in its name.
  const female = voices.find(
    (v) =>
      v.name.toLowerCase().includes("female") &&
      v.lang.toLowerCase().startsWith("en"),
  );
  if (female) {
    cachedVoice = female;
    voiceResolved = true;
    return female;
  }

  // Fallback: any English voice.
  const english = voices.find((v) =>
    v.lang.toLowerCase().startsWith("en"),
  );
  if (english) {
    cachedVoice = english;
    voiceResolved = true;
    return english;
  }

  // Fallback: default.
  cachedVoice = voices[0] ?? null;
  voiceResolved = true;
  return cachedVoice;
}

/**
 * Voices load asynchronously in most browsers. Call
 * this once on mount to trigger loading and refresh the
 * cache when the voices list becomes available.
 */
export function primeVoices(): void {
  if (typeof window === "undefined") return;
  const synth = window.speechSynthesis;
  if (!synth) return;

  const tryLoad = () => {
    const voices = synth.getVoices();
    if (voices.length > 0) {
      voiceResolved = false;
      resolveVoice();
    }
  };

  tryLoad();
  synth.addEventListener?.("voiceschanged", tryLoad);
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export function setMuted(value: boolean): void {
  muted = value;
}

export function isMuted(): boolean {
  return muted;
}

export function stop(): void {
  if (typeof window === "undefined") return;
  window.speechSynthesis?.cancel();
}

/**
 * Speak the given text using the resolved voice.
 *
 * Cancels any utterance currently in flight before
 * speaking the new text — rapid clicks do not queue.
 */
export function speak(text: string): void {
  if (typeof window === "undefined") return;
  if (muted) return;

  const synth = window.speechSynthesis;
  if (!synth) return;

  const trimmed = (text ?? "").trim();
  if (!trimmed) return;

  synth.cancel();

  const utterance = new SpeechSynthesisUtterance(trimmed);

  const voice = resolveVoice();
  if (voice) {
    utterance.voice = voice;
    utterance.lang = voice.lang;
  }

  utterance.rate = 0.9;
  utterance.pitch = 1.1;
  utterance.volume = 1.0;

  synth.speak(utterance);
}
