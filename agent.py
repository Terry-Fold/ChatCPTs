import os
import re
import subprocess
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()


class Command(BaseModel):
    action: str
    text: str | None = None


WINDOWS_DIRECTORY = Path(os.environ["WINDIR"])
PROGRAMS = {
    "notepad": [str(WINDOWS_DIRECTORY / "notepad.exe")],
    "explorer": [str(WINDOWS_DIRECTORY / "explorer.exe")],
}


PHRASES = {
    "notepad": ("блокнот", "notepad"),
    "calculator": ("калькулятор", "калькулятора", "calculator"),
    "explorer": ("проводник", "проводника", "explorer"),
    "google": ("google", "гугл"),
    "yandex": ("яндекс", "yandex"),
    "browser": ("браузер", "браузера", "browser"),
    "mail": ("почта", "почту", "почты", "mail", "outlook"),
    "vscode": ("код", "кода", "code", "visual studio", "vs code", "вс код"),
}


SITE_URLS = {
    "google": "https://www.google.com",
    "yandex": "https://yandex.ru",
}


def normalize_phrase(text: str) -> str:
    phrase = text.casefold().strip()
    return re.sub(r"\s+", " ", phrase)


def program_from_phrase(text: str) -> str | None:
    phrase = normalize_phrase(text)
    for program, keywords in PHRASES.items():
        if any(keyword in phrase for keyword in keywords):
            return program
    return None


def spoken_url(text: str) -> str | None:
    phrase = normalize_phrase(text)

    if not any(word in phrase for word in ("открой", "открыть", "запусти", "запустить")):
        return None

    # Convert common spoken URL words to their URL notation.
    phrase = re.sub(r"\bточка\b", ".", phrase)
    phrase = re.sub(r"\bслэш\b", "/", phrase)
    phrase = re.sub(r"\bслеш\b", "/", phrase)
    phrase = re.sub(r"\bдвойной слэш\b", "//", phrase)
    phrase = re.sub(r"\bдвоеточие\b", ":", phrase)

    # Remove the command part and optional filler words.
    phrase = re.sub(r"^(открой|открыть|запусти|запустить)\s+", "", phrase)
    phrase = re.sub(r"^(сайт|страницу)\s+", "", phrase)
    phrase = phrase.strip(" .")

    if phrase in SITE_URLS:
        return SITE_URLS[phrase]

    if phrase.startswith(("http://", "https://")):
        url = phrase
    elif phrase.startswith(("www.",)) or "." in phrase:
        url = "https://" + phrase
    else:
        return None

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    return url


def find_classic_outlook() -> Path | None:
    outlook_locations = [
        Path(os.environ.get("PROGRAMFILES(X86)", ""))
        / "Microsoft Office"
        / "root"
        / "Office16"
        / "OUTLOOK.EXE",
        Path(os.environ.get("PROGRAMFILES", ""))
        / "Microsoft Office"
        / "root"
        / "Office16"
        / "OUTLOOK.EXE",
    ]
    for outlook_path in outlook_locations:
        if outlook_path.is_file():
            return outlook_path
    return None


@app.get("/", response_class=HTMLResponse)
def home():
    return """<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>AGAI Agent</title><style>body{font:18px system-ui;max-width:680px;margin:80px auto;padding:0 24px}input{box-sizing:border-box;font:inherit;padding:12px;width:100%}button{font:inherit;margin-top:12px;padding:10px 18px}#result{white-space:pre-wrap;margin-top:24px}</style></head><body><h1>AGAI Agent</h1><p>Напишите команду, например: «открой Google» или «открой example точка com».</p><input id="message" autofocus placeholder="Открой example точка ru"><button onclick="sendCommand()">Выполнить</button><div id="result"></div><script>async function sendCommand(){const text=document.getElementById('message').value;const response=await fetch('/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'text',text})});document.getElementById('result').textContent=await response.text()}document.getElementById('message').addEventListener('keydown',event=>{if(event.key==='Enter')sendCommand()})</script></body></html>"""


@app.post("/command")
def command(cmd: Command):
    if cmd.action == "text":
        url = spoken_url(cmd.text or "")
        if url:
            webbrowser.open(url)
            return {"status": "ok", "program": "browser", "url": url}

        program = program_from_phrase(cmd.text or "")
        if not program:
            return {
                "status": "not_understood",
                "message": "Попробуйте: открой Google, Яндекс, сайт example точка com, код, блокнот, калькулятор, проводник, браузер или почту.",
                "received_text": cmd.text,
            }
        cmd = Command(action="open_program", text=program)

    if cmd.action == "open_notepad":
        subprocess.Popen(PROGRAMS["notepad"])
        return {"status": "ok", "program": "notepad"}

    if cmd.action != "open_program":
        return {"status": "unknown_action"}

    program = normalize_phrase(cmd.text or "")

    if program in SITE_URLS:
        url = SITE_URLS[program]
        webbrowser.open(url)
        return {"status": "ok", "program": "browser", "url": url}

    if program == "browser":
        webbrowser.open(SITE_URLS["google"])
        return {"status": "ok", "program": program}

    if program == "calculator":
        os.startfile("calculator:")
        return {"status": "ok", "program": program}

    if program == "mail":
        outlook_path = find_classic_outlook()
        if outlook_path is None:
            return {
                "status": "program_not_found",
                "message": "Classic Microsoft Outlook was not found.",
            }
        subprocess.Popen([str(outlook_path)])
        return {"status": "ok", "program": "outlook", "path": str(outlook_path)}

    if program in {"vscode", "code", "visual studio code"}:
        code_locations = [
            Path(os.environ.get("LOCALAPPDATA", ""))
            / "Programs"
            / "Microsoft VS Code"
            / "Code.exe",
            Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft VS Code" / "Code.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", ""))
            / "Microsoft VS Code"
            / "Code.exe",
        ]
        for code_path in code_locations:
            if code_path.is_file():
                subprocess.Popen([str(code_path)])
                return {"status": "ok", "program": "vscode"}
        return {"status": "program_not_found", "message": "Visual Studio Code was not found."}

    if program in PROGRAMS:
        try:
            subprocess.Popen(PROGRAMS[program])
            return {"status": "ok", "program": program}
        except OSError as error:
            return {"status": "error", "message": str(error)}

    return {
        "status": "unknown_program",
        "available_programs": [*PROGRAMS, "google", "yandex", "browser", "calculator", "mail", "vscode"],
    }
