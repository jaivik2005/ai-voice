"""Audio capture and Whisper-based transcription helpers.

Provides small, robust wrappers that always return strings (empty on
failure) and raise only for programmer errors.
"""
from typing import Tuple
import wave
import os

try:
    import sounddevice as sd
except Exception:
    sd = None

try:
    import numpy as np
except Exception:
    np = None

try:
    from faster_whisper import WhisperModel
except Exception:
    WhisperModel = None


# Initialize the model once. Use CPU by default for Windows compatibility.
if WhisperModel is not None:
    try:
        model = WhisperModel("base", device="cpu", compute_type="int8")
    except Exception:
        model = None
else:
    model = None


def record_audio(filename: str = "input.wav", duration: int = 5, samplerate: int = 16000) -> str:
    """Record audio from the default microphone and write WAV file.

    Returns the path to the saved file. On error returns an empty string.
    """
    if sd is None:
        print("Audio recording error: sounddevice is unavailable")
        return ""
    if np is None:
        print("Audio recording error: NumPy is unavailable")
        return ""

    try:
        print("🎤 Listening...")
        audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
        sd.wait()
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(samplerate)
            wf.writeframes(audio.tobytes())
        return filename
    except Exception as e:
        print(f"Audio recording error: {e}")
        return ""


def has_audio_backend() -> bool:
    return sd is not None and np is not None


def transcribe(filename: str = "input.wav") -> str:
    """Transcribe a WAV file with Faster-Whisper.

    Always returns a string (empty on failure).
    """
    if not os.path.exists(filename):
        print("Transcription error: file not found")
        return ""
    if model is None:
        print("Transcription error: Whisper model failed to initialize")
        return ""

    try:
        segments, info = model.transcribe(filename)
        # segments can be an iterator or list depending on model version
        text_parts = []
        for seg in segments:
            # seg may be dict-like or object
            txt = getattr(seg, 'text', None) or seg.get('text') if isinstance(seg, dict) else None
            if txt:
                text_parts.append(txt)
        text = " ".join(text_parts).strip()
        print(f"You said: {text}")
        return text
    except Exception as e:
        print(f"Transcription error: {e}")
        return ""