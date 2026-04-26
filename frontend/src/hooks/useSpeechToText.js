import { useState, useCallback, useRef } from "react";

export function useSpeechToText() {
  const [transcript, setTranscript] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState("");
  const recognitionRef = useRef(null);

  const startListening = useCallback(async () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      const message = "Speech recognition is not supported in this browser";
      console.warn(message);
      setError(message);
      return false;
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      const message = "Microphone access is not supported in this browser";
      console.warn(message);
      setError(message);
      return false;
    }

    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }

    try {
      const permissionStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      permissionStream.getTracks().forEach((track) => track.stop());
    } catch (err) {
      const message =
        err?.name === "NotAllowedError"
          ? "Microphone permission was denied"
          : err?.name === "NotFoundError"
            ? "No microphone was found on this device"
            : err?.message || "Could not access microphone";
      console.error(message);
      setError(message);
      return false;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    let finalTranscript = "";

    recognition.onresult = (event) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript + " ";
        } else {
          interim += event.results[i][0].transcript;
        }
      }
      setTranscript(finalTranscript + interim);
    };

    recognition.onstart = () => {
      setError("");
      setIsListening(true);
    };
    recognition.onend = () => {
      setIsListening(false);
      recognitionRef.current = null;
    };
    recognition.onerror = (e) => {
      console.error("Speech error:", e.error);
      const errorMessages = {
        "audio-capture": "Microphone access failed",
        "not-allowed": "Microphone permission was denied",
        "no-speech": "No speech detected. Try speaking closer to the mic.",
        "network": "Speech recognition network error",
      };
      setError(errorMessages[e.error] || `Speech recognition error: ${e.error}`);
      setIsListening(false);
      recognitionRef.current = null;
    };

    recognitionRef.current = recognition;
    setError("");
    setTranscript("");
    try {
      recognition.start();
      return true;
    } catch (err) {
      const message = err?.message || "Could not start speech recognition";
      console.error(message);
      setError(message);
      recognitionRef.current = null;
      return false;
    }
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsListening(false);
  }, []);

  const resetTranscript = useCallback(() => {
    setTranscript("");
  }, []);

  const clearError = useCallback(() => {
    setError("");
  }, []);

  return { transcript, isListening, error, startListening, stopListening, resetTranscript, setTranscript, clearError };
}
