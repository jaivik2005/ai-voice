"""CLI entry point. Text mode is always available; microphone mode is optional."""
import argparse
from core.assistant import FileAssistant
from voice.speech_to_text import has_audio_backend, record_audio, transcribe
from voice.text_to_speech import speak


def main():
    parser = argparse.ArgumentParser(description="Safe Linux voice file assistant")
    parser.add_argument("command", nargs="*", help="Run one command without entering interactive mode")
    parser.add_argument("--voice", action="store_true", help="Use microphone input")
    args = parser.parse_args()
    assistant = FileAssistant()
    if args.command:
        print(assistant.handle(" ".join(args.command)))
        return
    print("AI File Assistant — type 'exit' to quit. Destructive actions require ‘yes’.")
    while True:
        if args.voice and has_audio_backend():
            wav = record_audio()
            command = transcribe(wav) if wav else ""
        else:
            try:
                command = input("You: ")
            except EOFError:
                return
        if command.lower().strip() in {"exit", "quit"}:
            speak("Goodbye.")
            return
        if command.strip():
            reply = assistant.handle(command)
            print(f"Assistant: {reply}")
            if args.voice:
                # URLs and detailed citations stay on screen; voice remains concise.
                speak(reply.split("\n", 1)[0][:350])


if __name__ == "__main__":
    main()
