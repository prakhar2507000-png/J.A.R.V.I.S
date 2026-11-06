# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS Mobile - the iPhone / iPad / Android companion.

Python and Tkinter cannot run on iOS, so JARVIS does the honest thing: the
desktop app hosts a tiny web app on your Wi-Fi and the phone talks to it.

    http://<this-pc>:8765/?k=<token>

Open that in Safari, then Share -> Add to Home Screen. It behaves like an app:
full-screen, dark, offline-capable shell, text chat, and spoken replies in the
same British voice (the server renders the WAV so the phone needs no voice).

No cloud, no account, no port forwarding. The token keeps other devices on the
network out.
"""
import base64
import json
import os
import secrets
import socket
import struct
import threading
import time
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

PORT = 8765
_TOKEN = ""
_SERVER = None


# ------------------------------------------------------------------ helpers
def lan_ip():
    """Best-effort LAN address of this machine (no traffic is sent)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.4)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def _answer(text):
    """Short, spoken-style answer for the phone."""
    text = (text or "").strip()[:1000]
    if not text:
        return ""
    try:
        from jarvis_brain import (chat, SYSTEM_PROMPT, mood_line,
                                  quick_for, humanize)
        from jarvis_memory import MEM
    except Exception:
        return "My core is unreachable, Boss."
    quick = quick_for(text)
    if quick:
        return quick
    mem_txt = ""
    try:
        if MEM.get("facts"):
            mem_txt = ("Things Boss told you to remember: " +
                       "; ".join(MEM["facts"][-10:]) + ". ")
    except Exception:
        pass
    try:
        reply = chat([
            {"role": "system", "content": SYSTEM_PROMPT + " " + mem_txt +
             mood_line() + " This reply is being read on Boss's phone: keep it "
             "to two short sentences."},
            {"role": "user", "content": text},
        ], predict=220)
    except Exception:
        return "My core is unreachable, Boss. Is Ollama running?"
    parts = humanize(reply or "")
    return " ".join(parts).strip() or "I have nothing useful to say. Rare, I know."


def _audio_b64(text):
    try:
        from jarvis_voice import render_wav
        wav = render_wav(text)
        if not wav:
            return ""
        return "data:audio/wav;base64," + base64.b64encode(wav).decode("ascii")
    except Exception:
        return ""


def _icon_png(size=180):
    """A crisp home-screen icon, generated without Pillow (iOS needs PNG)."""
    raw = bytearray()
    cx = cy = (size - 1) / 2.0
    outer = size * 0.325
    ring = size * 0.055
    inner = size * 0.145
    for y in range(size):
        raw.append(0)                       # PNG filter: none
        for x in range(size):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if abs(d - outer) <= ring or d <= inner:
                raw.extend((255, 140, 0, 255))
            else:
                raw.extend((0, 0, 0, 255))

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
            chunk(b"IEND", b""))


ICON_PNG = _icon_png(180)


# ------------------------------------------------------------------ page
PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, maximum-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="JARVIS">
<meta name="theme-color" content="#000000">
<link rel="apple-touch-icon" sizes="180x180" href="__ICON__">
<link rel="icon" type="image/png" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<title>J.A.R.V.I.S.</title>
<style>
  :root { color-scheme: dark; --acc:#ff8c00; --txt:#ffd9a0; --dim:#8a6a45; }
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  html { height: 100%; height: -webkit-fill-available; }
  html, body { margin: 0; background: #000; -webkit-text-size-adjust: 100%; }
  body { min-height: 100vh; min-height: 100dvh;
         font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
         color: var(--txt); display: flex; flex-direction: column;
         overscroll-behavior: none; touch-action: manipulation;
         padding: env(safe-area-inset-top) env(safe-area-inset-right)
                  env(safe-area-inset-bottom) env(safe-area-inset-left); }
  header { display: flex; align-items: center; gap: 10px; padding: 14px 16px 8px;
           font-size: 12px; letter-spacing: .18em; color: var(--acc); }
  .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--acc);
         box-shadow: 0 0 10px var(--acc); animation: pulse 2.4s infinite; }
  @keyframes pulse { 50% { opacity: .35; } }
  header b { font-weight: 700; }
  header span { color: var(--dim); letter-spacing: .06em; margin-left: auto; }
  #log { flex: 1; overflow-y: auto; padding: 8px 16px 16px;
         display: flex; flex-direction: column; gap: 10px; }
  .m { max-width: 86%; padding: 10px 13px; border-radius: 16px; font-size: 15px;
       line-height: 1.4; white-space: pre-wrap; word-wrap: break-word; }
  .u { align-self: flex-end; background: #16110a; border: 1px solid #2b1d0c;
       border-bottom-right-radius: 5px; color: #ffe9c9; }
  .j { align-self: flex-start; background: #0c0905; border: 1px solid #472d0d;
       border-bottom-left-radius: 5px; }
  .j b { color: var(--acc); font-weight: 600; }
  .sys { align-self: center; color: var(--dim); font-size: 11px; letter-spacing: .08em; }
  footer { padding: 8px 12px calc(10px + env(safe-area-inset-bottom));
           border-top: 1px solid #21160a; display: flex; gap: 8px; align-items: flex-end;
           background: #050301; }
  textarea { flex: 1; resize: none; min-height: 44px; max-height: 130px; padding: 12px 14px;
             border-radius: 22px; border: 1px solid #3a2509; background: #120c04;
             color: var(--txt); font: inherit; font-size: 15px; outline: none; }
  button { border: 0; border-radius: 50%; width: 46px; height: 46px; flex: 0 0 46px;
           background: var(--acc); color: #1a0d00; font-size: 19px; font-weight: 700; }
  button:disabled { opacity: .4; }
  button.ghost { background: #120c04; color: var(--dim); border: 1px solid #3a2509;
                 font-size: 16px; }
  #sound { background: none; color: var(--dim); border: 0; width: auto;
           height: auto; padding: 4px 0; font-size: 10px; letter-spacing: .12em;
           margin-left: 8px; }
  #speak { align-self: center; background: none; color: var(--dim); width: auto;
           height: auto; border-radius: 0; font-size: 11px; letter-spacing: .1em; }
</style>
</head>
<body>
<header><i class="dot"></i><b>J.A.R.V.I.S.</b><button id="sound" aria-label="Sound">SOUND</button><span id="mode">MOBILE</span></header>
<div id="log" aria-live="polite">
  <div class="m j"><b>Jarvis:</b> Mobile link established, Boss. Do try not to type with your thumbs.</div>
</div>
<footer>
  <textarea id="box" rows="1" placeholder="Ask Jarvis..." enterkeyhint="send"
            autocomplete="off" autocapitalize="sentences" spellcheck="true"></textarea>
  <button id="mic" class="ghost" aria-label="Dictate" hidden>&#127908;</button>
  <button id="send" aria-label="Send">&#9658;</button>
</footer>
<script>
const KEY = new URLSearchParams(location.search).get('k') || localStorage.getItem('jk') || '';
if (KEY) localStorage.setItem('jk', KEY);
const log = document.getElementById('log');
const box = document.getElementById('box');
const send = document.getElementById('send');
const mic = document.getElementById('mic');
const soundBtn = document.getElementById('sound');
let audio = new Audio();
let speak = localStorage.getItem('jspeak') !== '0';
soundBtn.textContent = speak ? 'SOUND ON' : 'SOUND OFF';

// iOS will not let a page make noise until the user has touched it once.
let audioCtx = null;
function unlockAudio() {
  try {
    const C = window.AudioContext || window.webkitAudioContext;
    if (!C) return;
    if (!audioCtx) audioCtx = new C();
    if (audioCtx.state === 'suspended') audioCtx.resume();
  } catch (e) {}
}
document.addEventListener('touchstart', unlockAudio, {once: true});
document.addEventListener('click', unlockAudio, {once: true});
soundBtn.onclick = () => {
  speak = !speak;
  localStorage.setItem('jspeak', speak ? '1' : '0');
  soundBtn.textContent = speak ? 'SOUND ON' : 'SOUND OFF';
  if (speak) unlockAudio();
};

function add(who, text) {
  const d = document.createElement('div');
  d.className = 'm ' + who;
  if (who === 'j') d.innerHTML = '<b>Jarvis:</b> ' + escapeHtml(text);
  else d.textContent = text;
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
  return d;
}
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
async function ask() {
  const text = box.value.trim();
  if (!text) return;
  box.value = '';
  box.style.height = '44px';
  add('u', text);
  send.disabled = true;
  const thinking = add('j', '...');
  try {
    const r = await fetch('/api/chat?k=' + encodeURIComponent(KEY), {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text})
    });
    const d = await r.json();
    thinking.remove();
    add('j', d.reply || 'No reply.');
    if (speak && d.audio) { audio.src = d.audio; audio.play().catch(() => {}); }
    if (navigator.vibrate) navigator.vibrate(12);
  } catch (e) {
    thinking.remove();
    add('j', 'I cannot reach my core, Boss.');
  }
  send.disabled = false;
  box.focus();
}
send.onclick = ask;
box.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask(); }
});
box.addEventListener('input', () => {
  box.style.height = '44px';
  box.style.height = Math.min(130, box.scrollHeight) + 'px';
});

// Dictation uses Safari's own recogniser when iOS exposes it. It is optional:
// typing works everywhere, and nothing is uploaded by JARVIS.
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SR) {
  mic.hidden = false;
  let rec = null;
  mic.onclick = () => {
    try {
      if (rec) { rec.stop(); rec = null; mic.textContent = '\u{1F3A4}'; return; }
      rec = new SR();
      rec.lang = 'en-GB';
      rec.interimResults = false;
      rec.maxAlternatives = 1;
      mic.textContent = '\u25A0';
      rec.onresult = ev => {
        const said = ev.results[0][0].transcript;
        box.value = said;
        mic.textContent = '\u{1F3A4}';
        rec = null;
        ask();
      };
      rec.onerror = () => { mic.textContent = '\u{1F3A4}'; rec = null; };
      rec.onend = () => { mic.textContent = '\u{1F3A4}'; rec = null; };
      rec.start();
    } catch (e) { mic.textContent = '\u{1F3A4}'; rec = null; }
  };
}
</script>
</body>
</html>
"""

MANIFEST = json.dumps({
    "name": "J.A.R.V.I.S.",
    "short_name": "JARVIS",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#000000",
    "theme_color": "#000000",
    "icons": [{
        "src": "/apple-touch-icon.png",
        "sizes": "180x180",
        "type": "image/png",
    }],
})


# ------------------------------------------------------------------ server
class Handler(BaseHTTPRequestHandler):
    server_version = "JarvisMobile/1.0"

    def log_message(self, *args):
        pass

    def _send(self, code, body, ctype="application/json", extra=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        if ctype.startswith("text/html"):
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self' data:; script-src 'unsafe-inline'; "
                "style-src 'unsafe-inline'; img-src 'self' data:; "
                "media-src data:; connect-src 'self'; frame-ancestors 'none'")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def _authed(self, q):
        key = (q.get("k") or [""])[0] or \
            (self.headers.get("X-Jarvis-Token") or "")
        return bool(_TOKEN) and key == _TOKEN

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path in ("/", "/index.html"):
            # The shell is public; it contains no data and no token. Every API
            # call still requires the token, which the page keeps locally.
            # Serving it without a token is what lets an iOS home-screen icon
            # reopen the app after Safari forgets the original query string.
            icon = "data:image/png;base64," + base64.b64encode(
                ICON_PNG).decode("ascii")
            self._send(200, PAGE.replace("__ICON__", icon), "text/html")
            return
        if u.path == "/apple-touch-icon.png":
            self._send(200, ICON_PNG, "image/png", {
                "Cache-Control": "public, max-age=86400"})
            return
        if u.path == "/manifest.webmanifest":
            self._send(200, MANIFEST, "application/manifest+json")
            return
        if u.path == "/api/ping":
            self._send(200, json.dumps({"ok": True}))
            return
        if u.path == "/api/chat":
            if not self._authed(q):
                self._send(403, json.dumps({"error": "bad token"}))
                return
            text = (q.get("text") or [""])[0]
            self._chat(text)
            return
        self._send(404, "not found", "text/plain")

    def do_POST(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path != "/api/chat":
            self._send(404, "not found", "text/plain")
            return
        if not self._authed(q):
            self._send(403, json.dumps({"error": "bad token"}))
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(min(n, 20000)) or b"{}")
            text = str(data.get("text") or "")
        except Exception:
            text = ""
        self._chat(text)

    def _chat(self, text):
        t0 = time.time()
        reply = _answer(text)
        audio = _audio_b64(reply) if reply else ""
        self._send(200, json.dumps({
            "reply": reply,
            "audio": audio,
            "ms": int((time.time() - t0) * 1000),
        }))


class MobileServer:
    def __init__(self, port=PORT):
        self.port = port
        self.httpd = None
        self.thread = None
        self.token = ""
        self.ip = lan_ip()

    @property
    def url(self):
        return "http://%s:%d/?k=%s" % (self.ip, self.port, self.token)

    def start(self):
        global _TOKEN, _SERVER
        if self.httpd is not None:
            return self
        self.token = secrets.token_urlsafe(16)
        _TOKEN = self.token
        self.httpd = ThreadingHTTPServer(("0.0.0.0", self.port), Handler)
        self.httpd.daemon_threads = True
        self.thread = threading.Thread(target=self.httpd.serve_forever,
                                       daemon=True)
        self.thread.start()
        _SERVER = self
        return self

    def stop(self):
        if self.httpd is not None:
            try:
                self.httpd.shutdown()
            except Exception:
                pass
            self.httpd = None


def start(port=PORT):
    try:
        return MobileServer(port).start()
    except Exception:
        return None


def current():
    return _SERVER
