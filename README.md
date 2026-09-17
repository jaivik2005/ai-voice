# AI Voice Assistant

A local-first Linux file-management assistant. It converts supported natural-language commands into allow-listed `pathlib` operations; it never runs model-provided shell commands. Destructive actions always require a separate `yes`.

```bash
python main.py "create a folder called Project in Documents"
python main.py
```

Supported operations include creating folders/files, listing directories, filename/extension/size/date search, deletion, rename, move, copy, opening with `xdg-open`, and reading TXT/Markdown/PDF/DOCX documents. Configure allowed roots in `.env` using `.env.example`. Audit history is stored in SQLite under `~/.local/share/ai-voice-assistant` by default.
