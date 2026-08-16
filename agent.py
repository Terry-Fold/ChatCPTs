import os
import subprocess
import webbrowser
from pathlib import Path

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

def program_from_phrase(text: str) -> str | None:
    phrase = text.lower().strip()
    phrases = {
        "notepad": ("\u0431\u043b\u043e\u043a\u043d\u043e\u0442", "notepad"),
        "calculator": ("\u043a\u0430\u043b\u044c\u043a\u0443\u043b\u044f\u0442\u043e\u0440", "calculator"),
        "explorer": ("\u043f\u0440\u043e\u0432\u043e\u0434\u043d\u0438\u043a", "explorer"),
        "browser": ("\u0431\u0440\u0430\u0443\u0437\u0435\u0440", "browser"),
        "mail": ("\u043f\u043e\u0447\u0442\u0430", "mail", "outlook"),
        "vscode": ("\u043a\u043e\u0434", "code", "visual studio", "vs code", "\u0432\u0441 \u043a\u043e\u0434"),
    }
    for program, keywords in phrases.items():
        if any(keyword in phrase for keyword in keywords):
            return program
    return None

@app.get("/", response_class=HTMLResponse)
def home():
    return """<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>AGAI Agent</title><style>body{font:18px system-ui;max-width:680px;margin:80px auto;padding:0 24px}input{box-sizing:border-box;font:inherit;padding:12px;width:100%}button{font:inherit;margin-top:12px;padding:10px 18px}#result{white-space:pre-wrap;margin-top:24px}</style></head><body><h1>AGAI Agent</h1><p>&#1053;&#1072;&#1087;&#1080;&#1096;&#1080;&#1090;&#1077; &#1082;&#1086;&#1084;&#1072;&#1085;&#1076;&#1091;, &#1085;&#1072;&#1087;&#1088;&#1080;&#1084;&#1077;&#1088;: &#171;&#1086;&#1090;&#1082;&#1088;&#1086;&#1081; &#1082;&#1086;&#1076;&#187;.</p><input id="message" autofocus placeholder="&#1054;&#1090;&#1082;&#1088;&#1086;&#1081; &#1082;&#1086;&#1076;"><button onclick="sendCommand()">&#1042;&#1099;&#1087;&#1086;&#1083;&#1085;&#1080;&#1090;&#1100;</button><div id="result"></div><script>async function sendCommand(){const text=document.getElementById('message').value;const response=await fetch('/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'text',text})});document.getElementById('result').textContent=await response.text()}document.getElementById('message').addEventListener('keydown',event=>{if(event.key==='Enter')sendCommand()})</script></body></html>"""

@app.post("/command")
def command(cmd: Command):
    if cmd.action == "text":
        program = program_from_phrase(cmd.text or "")
        if not program:
            return {"status": "not_understood", "message": "\u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435: \u043e\u0442\u043a\u0440\u043e\u0439 \u043a\u043e\u0434, \u0431\u043b\u043e\u043a\u043d\u043e\u0442, \u043a\u0430\u043b\u044c\u043a\u0443\u043b\u044f\u0442\u043e\u0440, \u043f\u0440\u043e\u0432\u043e\u0434\u043d\u0438\u043a, \u0431\u0440\u0430\u0443\u0437\u0435\u0440 \u0438\u043b\u0438 \u043f\u043e\u0447\u0442\u0443.", "received_text": cmd.text}
        cmd = Command(action="open_program", text=program)
    if cmd.action == "open_notepad":
        subprocess.Popen(PROGRAMS["notepad"])
        return {"status": "ok", "program": "notepad"}
    if cmd.action != "open_program":
        return {"status": "unknown_action"}
    program = (cmd.text or "").lower().strip()
    if program == "browser":
        webbrowser.open("https://www.google.com")
        return {"status": "ok", "program": program}
    if program == "calculator":
        os.startfile("calculator:")
        return {"status": "ok", "program": program}
    if program == "mail":
        os.startfile("mailto:")
        return {"status": "ok", "program": program}
    if program in {"vscode", "code", "visual studio code"}:
        code_locations = [Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Microsoft VS Code" / "Code.exe", Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft VS Code" / "Code.exe", Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft VS Code" / "Code.exe"]
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
    return {"status": "unknown_program", "available_programs": [*PROGRAMS, "browser", "calculator", "mail", "vscode"]}
