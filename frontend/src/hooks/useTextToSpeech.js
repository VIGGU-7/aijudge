import { useState, useCallback, useRef, useEffect } from "react";

export function useTextToSpeech() {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const utteranceRef = useRef(null);
  const retryRef = useRef(false);
  const unlockedRef = useRef(false);

  useEffect(() => {
    if (!window.speechSynthesis) return undefined;
    const synth = window.speechSynthesis;
    const warmVoices = () => {
      try {
        synth.getVoices();
      } catch {}
    };
    warmVoices();
    synth.addEventListener?.("voiceschanged", warmVoices);
    return () => synth.removeEventListener?.("voiceschanged", warmVoices);
  }, []);

  const pickVoice = useCallback(() => {
    const voices = window.speechSynthesis.getVoices();
    return (
      voices.find((voice) => voice.name.includes("Google") && voice.lang.startsWith("en")) ||
      voices.find((voice) => voice.name.toLowerCase().includes("female") && voice.lang.startsWith("en")) ||
      voices.find((voice) => voice.lang.startsWith("en")) ||
      voices[0]
    );
  }, []);

  const waitForVoices = useCallback(() => {
    if (!window.speechSynthesis) return Promise.resolve([]);
    const existing = window.speechSynthesis.getVoices();
    if (existing.length > 0) return Promise.resolve(existing);

    return new Promise((resolve) => {
      const synth = window.speechSynthesis;
      const onVoices = () => {
        synth.removeEventListener?.("voiceschanged", onVoices);
        resolve(synth.getVoices());
      };
      synth.addEventListener?.("voiceschanged", onVoices);
      window.setTimeout(() => {
        synth.removeEventListener?.("voiceschanged", onVoices);
        resolve(synth.getVoices());
      }, 800);
    });
  }, []);

  const prepare = useCallback(async () => {
    if (!window.speechSynthesis) return false;
    const synth = window.speechSynthesis;
    await waitForVoices();
    synth.resume();

    if (unlockedRef.current) return true;

    return new Promise((resolve) => {
      const utterance = new SpeechSynthesisUtterance(" ");
      utterance.volume = 0;
      utterance.rate = 1;
      utterance.pitch = 1;
      const preferred = pickVoice();
      if (preferred) utterance.voice = preferred;

      const finish = () => {
        unlockedRef.current = true;
        resolve(true);
      };

      utterance.onend = finish;
      utterance.onerror = finish;

      try {
        synth.speak(utterance);
        window.setTimeout(finish, 150);
      } catch {
        finish();
      }
    });
  }, [pickVoice, waitForVoices]);

  const speak = useCallback(async (text, options = {}) => {
    if (!window.speechSynthesis || !text?.trim()) return false;
    const synth = window.speechSynthesis;
    await prepare();
    synth.cancel();
    synth.resume();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = options.rate || 0.95;
    utterance.pitch = options.pitch || 1;
    utterance.volume = options.volume || 1;

    const preferred = pickVoice();
    if (preferred) utterance.voice = preferred;

    utterance.onstart = () => {
      retryRef.current = false;
      setIsSpeaking(true);
    };
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => {
      setIsSpeaking(false);
    };
    utteranceRef.current = utterance;

    synth.speak(utterance);
    return true;
  }, [pickVoice, prepare]);

  const stop = useCallback(() => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, []);

  return { speak, stop, isSpeaking, prepare, utteranceRef };
}
