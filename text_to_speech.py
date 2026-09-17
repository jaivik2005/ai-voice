"""Text-to-speech helper using pyttsx3.

`speak` returns the spoken text on success, or an error string starting
with "Error:" on failure. This keeps the API predictable for callers.
"""
from typing import Union

try:
    import pyttsx3
except Exception:
    pyttsx3 = None


def _init_engine():
    if pyttsx3 is None:
        return None
    try:
        eng = pyttsx3.init()
        eng.setProperty('rate', 175)
        return eng
    except Exception:
        return None


_ENGINE = _init_engine()


def speak(text: str) -> str:
    if not text:
        return "Error: empty text"
    try:
        print(f"🔊 {text}")
        if _ENGINE is None:
            return text
        _ENGINE.say(text)
        _ENGINE.runAndWait()
        return text
    except Exception as e:
        return f"Error: text-to-speech failed: {e}"