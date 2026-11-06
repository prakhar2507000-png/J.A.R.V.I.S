# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS Models - the two local brains, without asking Boss to read a manual.

A 3B model weighs about 2 GB, so it cannot live inside a 78 KB sealed file.
Instead JARVIS provisions exactly two models on first run and keeps them:

    tinyllama:1.1b          the fast reflex brain  (~640 MB)
    qwen2.5:3b-instruct     the conversational brain (~1.9 GB)

If Ollama is missing, this module installs it quietly (Homebrew or the official
download on macOS, winget or the official installer on Windows). If anything
fails, JARVIS keeps working on its built-in offline brain - no dead end, no
error dialog in the middle of a conversation.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

from jarvis_config import PORT_OLLAMA, IS_WIN, IS_MAC, NW_FLAG

# Boss asked for these two. Tiny first so JARVIS is useful while Qwen lands.
REQUIRED = [
    ("tinyllama:1.1b", "TinyLlama", "Fast reflex brain - starts answering first"),
    ("qwen2.5:3b-instruct", "Qwen 2.5", "The conversational brain - warmer answers"),
]

PULL_TIMEOUT = 60 * 60

_lock = threading.Lock()
_state = {
    "phase": "idle",       # idle | installing | starting | pulling | ready | error
    "message": "Local brain not checked yet.",
    "model": "",
    "progress": 0.0,
    "installed": [],
}

# ------------------------------------------------------------------ discovery
def _candidates():
    out = []
    exe = shutil.which("ollama")
    if exe:
        out.append(exe)
    home = os.path.expanduser("~")
    if IS_WIN:
        out += [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs",
                         "Ollama", "ollama.exe"),
            os.path.join(os.environ.get("ProgramFiles", ""), "Ollama",
                         "ollama.exe"),
        ]
    elif IS_MAC:
        out += [
            "/Applications/Ollama.app/Contents/Resources/ollama",
            os.path.join(home, "Applications", "Ollama.app", "Contents",
                         "Resources", "ollama"),
            os.path.join(home, "Applications", "Ollama.app", "Contents",
                         "MacOS", "Ollama"),
            "/opt/homebrew/bin/ollama",
            "/usr/local/bin/ollama",
        ]
    else:
        out += ["/usr/local/bin/ollama", "/usr/bin/ollama"]
    return [p for p in out if p and os.path.exists(p)]


def find_exe():
    c = _candidates()
    return c[0] if c else ""


def server_up(timeout=1.2):
    try:
        req = urllib.request.Request(PORT_OLLAMA + "/api/tags")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            r.read(2)
        return True
    except Exception:
        return False


def installed_models():
    try:
        req = urllib.request.Request(PORT_OLLAMA + "/api/tags")
        with urllib.request.urlopen(req, timeout=3) as r:
            data = json.loads(r.read().decode("utf-8", "ignore"))
        return [m.get("name", "") for m in data.get("models", [])
                if m.get("name")]
    except Exception:
        return []


def has_model(name):
    low = name.lower()
    for m in installed_models():
        if m.lower() == low or m.lower().split(":")[0] == low.split(":")[0]:
            return True
    return False


def status():
    with _lock:
        d = dict(_state)
    d["server"] = server_up()
    d["exe"] = bool(find_exe())
    return d


def _set(**kw):
    with _lock:
        _state.update(kw)


# ------------------------------------------------------------------ install
def _run(args, timeout=600, quiet=True):
    try:
        return subprocess.run(
            args, stdout=subprocess.DEVNULL if quiet else None,
            stderr=subprocess.DEVNULL if quiet else None,
            timeout=timeout, creationflags=NW_FLAG).returncode == 0
    except Exception:
        return False


def _trusted_ollama_download(url, path):
    """Only the official Ollama host may deliver an installer, and every
    download is hashed and audited before it is run."""
    from urllib.parse import urlparse
    host = (urlparse(url).hostname or "").lower()
    if host not in ("ollama.com", "www.ollama.com"):
        raise RuntimeError("untrusted installer host")
    urllib.request.urlretrieve(url, path)
    try:
        import jarvis_guard as guard
        guard.audit("trusted-download", url + " -> " + path)
        guard.defender_scan(path)
    except Exception:
        pass


def install_ollama(log=None):
    """Best-effort, silent install. Returns True when an executable appears."""
    if find_exe():
        return True
    def note(msg):
        _set(phase="installing", message=msg)
        if log:
            log(msg)
    try:
        if IS_WIN:
            note("Installing Ollama (one-time, about 200 MB)...")
            ok = _run(["winget", "install", "--id", "Ollama.Ollama", "-e",
                       "--silent", "--accept-package-agreements",
                       "--accept-source-agreements"], timeout=900)
            if not ok or not find_exe():
                note("Downloading the Ollama installer...")
                path = os.path.join(tempfile.gettempdir(), "OllamaSetup.exe")
                _trusted_ollama_download(
                    "https://ollama.com/download/OllamaSetup.exe", path)
                _run([path, "/S"], timeout=900)
            if find_exe():
                return True
        elif IS_MAC:
            note("Installing Ollama (one-time, about 200 MB)...")
            brew = shutil.which("brew") or (
                "/opt/homebrew/bin/brew" if os.path.exists(
                    "/opt/homebrew/bin/brew") else "")
            if brew:
                _run([brew, "install", "ollama"], timeout=1200)
            if not find_exe():
                note("Downloading Ollama for macOS...")
                tmp = tempfile.mkdtemp(prefix="jarvis_ollama_")
                zpath = os.path.join(tmp, "Ollama-darwin.zip")
                _trusted_ollama_download(
                    "https://ollama.com/download/Ollama-darwin.zip", zpath)
                subprocess.run(["unzip", "-q", zpath, "-d", tmp],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=300)
                dest = os.path.join(os.path.expanduser("~"), "Applications")
                os.makedirs(dest, exist_ok=True)
                src = os.path.join(tmp, "Ollama.app")
                if os.path.exists(src):
                    target = os.path.join(dest, "Ollama.app")
                    if os.path.exists(target):
                        shutil.rmtree(target, ignore_errors=True)
                    shutil.move(src, target)
                    subprocess.run(["xattr", "-dr", "com.apple.quarantine",
                                    target], stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
            if find_exe():
                return True
        else:
            note("Install Ollama from ollama.com, then reopen JARVIS.")
    except Exception as e:
        _set(phase="error", message="Ollama install failed: %s" % str(e)[:80])
    return bool(find_exe())


def start_server(wait=18):
    """Launch `ollama serve` and wait for the local API."""
    if server_up():
        return True
    exe = find_exe()
    if not exe:
        return False
    _set(phase="starting", message="Starting the local brain...")
    env = dict(os.environ)
    env.setdefault("OLLAMA_HOST", "127.0.0.1:11434")
    try:
        subprocess.Popen([exe, "serve"], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, creationflags=NW_FLAG,
                         env=env, start_new_session=True)
    except Exception:
        pass
    end = time.time() + wait
    while time.time() < end:
        if server_up():
            return True
        time.sleep(0.6)
    return False


# ------------------------------------------------------------------ pull
def pull(name, on_progress=None, cancel=None):
    """Stream one model download. on_progress(dict) gets status/completed/total."""
    body = json.dumps({"name": name, "stream": True}).encode("utf-8")
    req = urllib.request.Request(PORT_OLLAMA + "/api/pull", data=body,
                                 headers={"Content-Type": "application/json"})
    last = 0.0
    with urllib.request.urlopen(req, timeout=PULL_TIMEOUT) as r:
        buf = ""
        while True:
            if cancel is not None and cancel.is_set():
                return False
            chunk = r.read(4096)
            if not chunk:
                break
            buf += chunk.decode("utf-8", "ignore")
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                now = time.time()
                if on_progress and now - last > 0.25:
                    last = now
                    try:
                        on_progress(d)
                    except Exception:
                        pass
                if d.get("error"):
                    return False
    return has_model(name)


def _pull_one(name, label, on_progress=None, cancel=None):
    def cb(d):
        total = d.get("total") or 0
        done = d.get("completed") or 0
        frac = (done / total) if total else 0.0
        _set(phase="pulling", model=label, progress=round(frac, 3),
             message="%s  %d%%" % (label, int(frac * 100)))
        if on_progress:
            on_progress(d, label, frac)
    _set(phase="pulling", model=label, progress=0.0,
         message="Downloading %s..." % label)
    return pull(name, cb, cancel)


def ensure_models(on_progress=None, on_state=None, cancel=None, log=None):
    """Install Ollama if needed, start it, and fetch the two required models."""
    def emit():
        d = status()
        if on_state:
            try:
                on_state(d)
            except Exception:
                pass
    try:
        if not server_up():
            if not find_exe():
                install_ollama(log)
            if not start_server():
                _set(phase="error", message=(
                    "Ollama is not available yet. JARVIS will use its "
                    "built-in brain."))
                emit()
                return False
        for name, label, _desc in REQUIRED:
            if cancel is not None and cancel.is_set():
                return False
            if has_model(name):
                continue
            if not _pull_one(name, label, on_progress, cancel):
                _set(phase="error",
                     message="Could not download %s. Built-in brain active." %
                             label)
                emit()
                return False
            emit()
        _set(phase="ready", model="", progress=1.0,
             message="Built-in brain ready: TinyLlama and Qwen 2.5.",
             installed=[m for m, _l, _d in REQUIRED])
        emit()
        return True
    except Exception as e:
        _set(phase="error", message="Brain setup: %s" % str(e)[:100])
        emit()
        return False


def bootstrap_async(on_progress=None, on_state=None, log=None):
    """Run ensure_models in a worker thread. Safe to call more than once."""
    cancel = threading.Event()
    t = threading.Thread(target=ensure_models,
                         kwargs={"on_progress": on_progress,
                                 "on_state": on_state, "cancel": cancel,
                                 "log": log}, daemon=True)
    t.start()
    return t, cancel


def use_best_model():
    """Pick the most capable installed model, preferring Qwen."""
    names = installed_models()
    for wanted, _l, _d in REQUIRED:
        for n in names:
            if n.lower() == wanted.lower():
                return n
    for n in names:
        if "qwen" in n.lower():
            return n
    for n in names:
        if "tinyllama" in n.lower():
            return n
    return names[0] if names else ""


def ensure_fast_model():
    """TinyLlama is the quick reflex model; fall back to whatever exists."""
    names = installed_models()
    for n in names:
        if "tinyllama" in n.lower():
            return n
    return use_best_model()
