# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS Voice - free, no API key, no account, cross-platform.

Primary : edge-tts neural voices (free, needs internet)
Fallback: Windows SAPI5 / macOS say / Linux espeak (free, offline, instant)

Prosody: a human never speaks a paragraph at one flat pitch. Every sentence is
shaped on its own - rate, pitch and volume rise on exclamations and good news,
drop on apologies and trailing thoughts, and carry a small random wobble - so
the delivery breathes instead of droning.
"""
import sys
import os
import re
import random
import shutil
import subprocess
import threading
import tempfile
import time

from xml.sax.saxutils import escape as _xml_escape

from jarvis_config import NW_FLAG, IS_WIN, IS_MAC

VOICE_ON = True
_proc = None
_lock = threading.Lock()
_edge_ok = None          # None = untried, True = works, False = disabled
_edge_cool = 0.0         # do not hammer the free service after a failure
_online_cache = (0.0, False)

# Caption hook: the UI passes a callback so the subtitle appears at the exact
# moment the voice starts, not seconds earlier while speech is still being
# synthesised.
on_start = None
_start_cb = None
_started = False

# Piper: local neural British voice. No account, no key, works offline.
# One light British voice everywhere, matching the boot greeting. The old male
# Alan voice was the "deep, uncanny" one - it is deliberately gone.
_PIPER_NAME = "en_GB-cori-high"
_EDGE_VOICE = "en-GB-SoniaNeural"
_PIPER_DIR = os.path.join(os.path.expanduser("~"), ".cache", "jarvis-piper")
_piper_voice = None
_piper_state = None      # None = untried, True = loaded, False = unavailable
_piper_fetching = False
_piper_lock = threading.Lock()

_SENT_RE = re.compile(r"[^.!?;]+[.!?;]*", re.UNICODE)

# Boss can slow the butler down or speed him up from Settings › Voice.
RATE_SCALE = 1.0
_mac_voice = None
_mac_voice_tried = False
_win_voice = None
_win_voice_tried = False


def set_speed(scale):
    """0.8 = measured, 1.3 = mildly alarmed. Clamped to sane values."""
    global RATE_SCALE
    try:
        RATE_SCALE = max(0.72, min(1.35, float(scale)))
    except Exception:
        RATE_SCALE = 1.0
    return RATE_SCALE


def speed():
    return RATE_SCALE


def _pick_mac_voice():
    """Prefer the light British voices; never the deep male ones."""
    global _mac_voice, _mac_voice_tried
    if _mac_voice_tried:
        return _mac_voice
    _mac_voice_tried = True
    try:
        out = subprocess.check_output(["say", "-v", "?"], text=True,
                                      stderr=subprocess.DEVNULL, timeout=8)
        voices = {}
        for line in out.splitlines():
            m = re.match(r"^(.+?)\s{2,}([a-z]{2}_[A-Z]{2})\b", line)
            if m:
                voices.setdefault(m.group(2), []).append(m.group(1).strip())
        # Light, warm, British first. Daniel/Oliver/Arthur/Ryan/George are
        # intentionally last: they are the deep register this build avoids.
        order = ["Kate", "Serena", "Samantha", "Karen", "Moira", "Tessa",
                 "Libby", "Sonia", "Martha", "Daniel", "Oliver", "Arthur",
                 "Ryan", "George"]
        for name in order:
            for v in voices.get("en_GB", []):
                if v.startswith(name):
                    _mac_voice = v
                    return _mac_voice
        for name in order:
            for v in voices.get("en_US", []):
                if v.startswith(name):
                    _mac_voice = v
                    return _mac_voice
        if voices.get("en_GB"):
            _mac_voice = voices["en_GB"][0]
        elif voices.get("en_US"):
            _mac_voice = voices["en_US"][0]
    except Exception:
        _mac_voice = "Kate"
    return _mac_voice


def _pick_win_voice():
    """Pick the lightest installed English voice, not the deepest one."""
    global _win_voice, _win_voice_tried
    if _win_voice_tried:
        return _win_voice
    _win_voice_tried = True
    try:
        ps = ("Add-Type -AssemblyName System.Speech;"
              "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
              "$s.GetInstalledVoices()|%{$_.VoiceInfo.Name+'|'+" 
              "$_.VoiceInfo.Culture.Name}")
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", ps], text=True,
            stderr=subprocess.DEVNULL, timeout=8, creationflags=NW_FLAG)
        rows = [l.strip() for l in out.splitlines() if "|" in l]
        # Names known to be light/female. Deep male names are pushed last.
        prefer = ("hazel", "zira", "susan", "eva", "libby", "sonia", "kate",
                  "serena", "samantha", "female")
        avoid = ("david", "mark", "george", "ryan", "daniel", "james",
                 "richard", "male")
        gb, other = [], []
        for line in rows:
            name, culture = line.rsplit("|", 1)
            name, culture = name.strip(), culture.strip()
            if not culture.lower().startswith("en"):
                continue
            score = 2 if any(w in name.lower() for w in prefer) else 0
            if any(w in name.lower() for w in avoid):
                score -= 5
            if culture.lower().startswith("en-gb"):
                score += 3
            (gb if culture.lower().startswith("en-gb") else other).append(
                (score, name))
        pool = sorted(gb, key=lambda x: -x[0]) or sorted(other,
                                                         key=lambda x: -x[0])
        if pool:
            _win_voice = pool[0][1]
            return _win_voice
    except Exception:
        pass
    return _win_voice


def voice_status():
    """What will speak right now, and whether it needs the internet."""
    piper = piper_model_path() is not None
    try:
        import edge_tts  # noqa: F401
        edge_pkg = True
    except Exception:
        edge_pkg = False
    if IS_MAC:
        name = _pick_mac_voice()
        if piper:
            return {"engine": "Piper", "voice": _PIPER_NAME,
                    "offline": True, "detail": "Neural British voice, on disk"}
        return {"engine": "macOS Voice", "voice": name or "System",
                "offline": True, "detail": "Built into macOS - works offline"}
    if IS_WIN:
        name = _pick_win_voice()
        if piper:
            return {"engine": "Piper", "voice": _PIPER_NAME,
                    "offline": True, "detail": "Neural British voice, on disk"}
        return {"engine": "Windows Voice", "voice": name or "System",
                "offline": True, "detail": "Built into Windows - works offline"}
    if piper:
        return {"engine": "Piper", "voice": _PIPER_NAME, "offline": True,
                "detail": "Neural British voice, on disk"}
    return {"engine": "eSpeak", "voice": "en-gb", "offline": True,
            "detail": "Built into Linux - works offline"}


def available_offline():
    """True when at least one voice works with the network switched off."""
    if piper_model_path():
        return True
    if IS_MAC:
        return shutil.which("say") is not None
    if IS_WIN:
        return True
    return any(shutil.which(x) for x in ("espeak-ng", "espeak"))

_SAD = ("sorry", "unfortunately", "afraid", "cannot", "can't", "unable",
        "failed", "problem", "error")
_GLAD = ("great", "perfect", "excellent", "glad", "happy", "wonderful",
         "done", "ready", "sure", "absolutely")
_ALERT = ("warning", "careful", "danger", "stop", "alert", "attention")


def _clean(text):
    t = re.sub(r"\[ACTION:.*?\]", "", text or "")
    t = re.sub(r"[*_`#>]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:600]


def _online():
    global _online_cache
    now = time.time()
    stamp, value = _online_cache
    if now - stamp < 30:
        return value
    try:
        import socket
        s = socket.create_connection(("1.1.1.1", 443), timeout=0.8)
        s.close()
        value = True
    except Exception:
        value = False
    _online_cache = (now, value)
    return value


def _edge_ready():
    global _edge_ok
    if _edge_ok is False:
        return False
    if _edge_ok is True:
        return True
    try:
        import edge_tts  # noqa: F401
    except Exception:
        _edge_ok = False
        return False
    if not _online():
        return False
    if time.time() - _edge_cool < 20:
        return False
    _edge_ok = True
    return True


# ------------------------------------------------------------------ prosody
def _split_sentences(text, limit=160):
    """Break a reply into speakable lines, keeping punctuation."""
    out = []
    for m in _SENT_RE.finditer(text):
        s = m.group(0).strip()
        while len(s) > limit:
            cut = s.rfind(",", 0, limit)
            if cut < 60:
                cut = s.rfind(" ", 0, limit)
            if cut < 60:
                cut = limit
            out.append(s[:cut].strip())
            s = s[cut:].strip(" ,;")
        if s:
            out.append(s)
    return out or [text]


def _prosody(sentence, cheerful, index, total):
    """Return (rate, pitch, volume) as edge-tts strings for one sentence."""
    low = sentence.lower()
    rate = pitch = vol = 0.0

    if "!" in sentence:
        rate += 4
        pitch += 7
        vol += 7
    if "?" in sentence:
        rate -= 2
        pitch += 4
        vol += 1
    if "..." in sentence or "\u2026" in sentence:
        rate -= 8
        pitch -= 5
        vol -= 5
    if any(w in low for w in _SAD):
        rate -= 5
        pitch -= 6
        vol -= 4
    if any(w in low for w in _GLAD):
        rate += 3
        pitch += 5
        vol += 5
    if any(w in low for w in _ALERT):
        rate += 2
        pitch -= 4
        vol += 8

    # a lift on the opening line, a settle on the closing one
    if index == 0:
        pitch += 2
    if total > 1 and index == total - 1:
        rate -= 2

    # the human wobble - never the same twice
    rate += random.uniform(-3.5, 3.5)
    pitch += random.uniform(-3.0, 3.0)
    vol += random.uniform(-2.0, 2.0)

    if cheerful:
        rate += 5
        pitch += 3
        vol += 2

    # The Settings › Voice speed control, applied to every engine.
    rate += (RATE_SCALE - 1.0) * 100.0

    rate = max(-40.0, min(40.0, rate))
    pitch = max(-20.0, min(20.0, pitch))
    vol = max(-15.0, min(15.0, vol))
    return ("%+d%%" % round(rate), "%+dHz" % round(pitch),
            "%+d%%" % round(vol))


def _named(percent, ladder):
    """Map a percentage onto a small named ladder (SAPI prosody)."""
    i = 2 + int(round(max(-2.0, min(2.0, percent / 8.0))))
    return ladder[max(0, min(len(ladder) - 1, i))]


# ------------------------------------------------------------------ playback
def _play_mp3(path):
    if IS_MAC:
        subprocess.run(["afplay", path], timeout=60)
        return True
    if IS_WIN:
        ps = (
            "Add-Type -AssemblyName presentationCore;"
            "$m=New-Object System.Windows.Media.MediaPlayer;"
            "$m.Open([uri]'" + path + "');"
            "for($i=0;$i -lt 40 -and -not $m.NaturalDuration.HasTimeSpan;$i++)"
            "{Start-Sleep -Milliseconds 100};"
            "$m.Play();"
            "$d=if($m.NaturalDuration.HasTimeSpan)"
            "{$m.NaturalDuration.TimeSpan.TotalSeconds}else{4};"
            "Start-Sleep -Milliseconds ([int](($d+0.5)*1000));"
            "$m.Close()"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       timeout=90, creationflags=NW_FLAG,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    for exe in ("ffplay", "mpg123", "cvlc"):
        try:
            if subprocess.call(["which", exe], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL) == 0:
                if exe == "ffplay":
                    subprocess.run(["ffplay", "-nodisp", "-autoexit",
                                    "-loglevel", "quiet", path], timeout=90)
                else:
                    subprocess.run([exe, path], timeout=90)
                return True
        except Exception:
            continue
    return False


def _edge(text, cheerful):
    """Free Microsoft neural voice, one prosody shape per sentence."""
    global _edge_cool
    try:
        import edge_tts
        import asyncio
    except Exception:
        return False
    folder = None
    try:
        voice = _EDGE_VOICE
        chunks = _split_sentences(text)
        if len(chunks) > 4:                      # keep latency sane
            chunks = chunks[:3] + [" ".join(chunks[3:])]

        folder = tempfile.mkdtemp(prefix="jarvis_tts_")
        paths = [os.path.join(folder, "seg%d.mp3" % i)
                 for i in range(len(chunks))]
        shapes = [_prosody(c, cheerful, i, len(chunks))
                  for i, c in enumerate(chunks)]

        def _speak_one(i, chunk):
            rate, pitch, vol = shapes[i]
            comm = edge_tts.Communicate(chunk, voice=voice, rate=rate,
                                        pitch=pitch, volume=vol)
            asyncio.run(asyncio.wait_for(comm.save(paths[i]), timeout=12))

        async def go():
            # One connection at a time: the free endpoint drops parallel
            # sockets, which is what used to silence every reply.
            for i, chunk in enumerate(chunks):
                tries = 1 if i == 0 else 2
                got = False
                for attempt in range(tries):
                    try:
                        rate, pitch, vol = shapes[i]
                        c = edge_tts.Communicate(chunk, voice=voice,
                                                 rate=rate, pitch=pitch,
                                                 volume=vol)
                        await asyncio.wait_for(c.save(paths[i]), timeout=7)
                        got = True
                        break
                    except Exception:
                        await asyncio.sleep(0.3)
                if not got:
                    # Service is down: stop here so the local British voice
                    # can take over straight away instead of stalling.
                    return False
                await asyncio.sleep(0.1)
            return True

        try:
            asyncio.run(go())
        except Exception:
            # one bad sentence must not silence the whole reply
            for i, chunk in enumerate(chunks):
                try:
                    _speak_one(i, chunk)
                except Exception:
                    continue
        played = False
        for path in paths:
            if not os.path.exists(path) or os.path.getsize(path) < 600:
                continue
            if played:
                time.sleep(0.12)                 # a breath between sentences
            else:
                _begin()
            _play_mp3(path)
            played = True
        if not played:
            _edge_cool = time.time()
        return played
    except Exception:
        _edge_cool = time.time()
        return False
    finally:
        if folder:
            try:
                shutil.rmtree(folder, ignore_errors=True)
            except Exception:
                pass


# ------------------------------------------------------------------ piper
def piper_model_path():
    """Where the local British voice lives, if it is already downloaded."""
    env = os.environ.get("JARVIS_PIPER_MODEL")
    if env and os.path.exists(env):
        return env
    name = _PIPER_NAME + ".onnx"
    here = ""
    try:
        if __file__ and not str(__file__).startswith("<"):
            here = os.path.dirname(os.path.abspath(__file__))
    except Exception:
        here = os.getcwd()
    for folder in (_PIPER_DIR, here):
        cand = os.path.join(folder, name)
        if os.path.exists(cand):
            return cand
    return None


def prefetch(download=True):
    """Fetch the Piper voice in the background so replies stay British offline."""
    global _piper_fetching
    if _piper_fetching or not download:
        return
    _piper_fetching = True

    def _get():
        global _piper_fetching
        try:
            from piper.download_voices import download_voice
            os.makedirs(_PIPER_DIR, exist_ok=True)
            download_voice(_PIPER_NAME, _PIPER_DIR)
        except Exception:
            pass
        finally:
            _piper_fetching = False

    if piper_model_path() is None and _online():
        threading.Thread(target=_get, daemon=True).start()


def _piper_load():
    global _piper_voice, _piper_state
    with _piper_lock:
        if _piper_state is True:
            return _piper_voice
        if _piper_state is False:
            return None
        path = piper_model_path()
        if not path:
            _piper_state = False
            return None
        try:
            from piper import PiperVoice
            _piper_voice = PiperVoice.load(path)
            _piper_state = True
            return _piper_voice
        except Exception:
            _piper_state = False
            return None


def _read_wav(path):
    """Return (rate, float samples in -1..1) from a mono 16-bit WAV."""
    import wave
    import numpy as np
    with wave.open(path, "rb") as w:
        rate = w.getframerate()
        channels = w.getnchannels()
        width = w.getsampwidth()
        raw = w.readframes(w.getnframes())
    if width != 2:
        raise ValueError("expects 16-bit audio")
    data = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    return rate, data


def _write_wav(path, rate, samples):
    import wave
    import numpy as np
    pcm = np.clip(samples, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(rate))
        w.writeframes(pcm.tobytes())


def _shape_pitch(data, ratio):
    """Resample for a small pitch lift/drop. +-4% keeps voices natural."""
    if abs(ratio - 1.0) < 0.004 or len(data) < 32:
        return data
    import numpy as np
    out_len = max(1, int(len(data) / ratio))
    idx = np.arange(out_len, dtype=np.float32) * ratio
    idx = np.clip(idx, 0, len(data) - 1)
    lo = np.floor(idx).astype(np.int32)
    hi = np.minimum(lo + 1, len(data) - 1)
    frac = idx - lo
    return data[lo] * (1.0 - frac) + data[hi] * frac


def _play_wav(path):
    if IS_WIN:
        import winsound
        winsound.PlaySound(path, winsound.SND_FILENAME)
        return True
    if IS_MAC:
        subprocess.run(["afplay", path], timeout=120)
        return True
    for exe, args in (("paplay", []), ("aplay", ["-q"]),
                      ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet"])):
        try:
            if subprocess.call(["which", exe], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL) == 0:
                subprocess.run([exe] + args + [path], timeout=120)
                return True
        except Exception:
            continue
    return False


def _synth_piper(text, cheerful):
    """Build one WAV worth of speech. Returns (rate, samples) or (None, None)."""
    voice = _piper_load()
    if voice is None:
        return None, None
    folder = None
    try:
        from piper import SynthesisConfig
        import wave
        chunks = _split_sentences(text)
        if len(chunks) > 6:
            chunks = chunks[:5] + [" ".join(chunks[5:])]

        folder = tempfile.mkdtemp(prefix="jarvis_piper_")
        rate = None
        joined = None
        for i, chunk in enumerate(chunks):
            rate_pct, pitch_pct, vol_pct = _prosody(chunk, cheerful, i, len(chunks))
            seg = os.path.join(folder, "seg%d.wav" % i)
            cfg = SynthesisConfig(
                length_scale=max(0.72, min(1.28,
                    1.0 / (1.0 + float(rate_pct.strip("%")) / 100.0))),
                volume=max(0.45, min(1.6,
                    1.0 + float(vol_pct.strip("%")) / 100.0)),
                normalize_audio=True,
            )
            with wave.open(seg, "wb") as w:
                voice.synthesize_wav(chunk, w, syn_config=cfg)

            seg_rate, data = _read_wav(seg)
            rate = seg_rate
            shift = max(-11.0, min(11.0, float(pitch_pct.strip("Hz"))))
            data = _shape_pitch(data, 1.0 + shift / 240.0)
            if joined is None:
                joined = data
            else:
                gap = 0.06 + 0.05 * (i % 3)         # a natural breath
                joined = _concat(joined, _silence(rate, gap), data)
        return rate, joined
    finally:
        if folder:
            try:
                shutil.rmtree(folder, ignore_errors=True)
            except Exception:
                pass


def render_wav(text, cheerful=False):
    """British speech as WAV bytes, without playing it (phone / downloads)."""
    try:
        rate, joined = _synth_piper(_clean(text), cheerful)
        if joined is None or not len(joined):
            return b""
        folder = tempfile.mkdtemp(prefix="jarvis_wav_")
        try:
            out = os.path.join(folder, "reply.wav")
            _write_wav(out, rate, joined)
            with open(out, "rb") as f:
                return f.read()
        finally:
            shutil.rmtree(folder, ignore_errors=True)
    except Exception:
        return b""


def _piper(text, cheerful):
    """
    Local British neural voice. Every sentence gets its own pace and loudness,
    plus a small pitch shift, so the delivery rises and falls like a person.
    """
    folder = None
    try:
        rate, joined = _synth_piper(text, cheerful)
        if joined is None or not len(joined):
            return False
        folder = tempfile.mkdtemp(prefix="jarvis_piper_")
        out = os.path.join(folder, "reply.wav")
        _write_wav(out, rate, joined)
        if not os.path.exists(out) or os.path.getsize(out) < 1200:
            return False
        _begin()
        return _play_wav(out)
    except Exception:
        return False
    finally:
        if folder:
            try:
                shutil.rmtree(folder, ignore_errors=True)
            except Exception:
                pass


def _silence(rate, seconds):
    import numpy as np
    return np.zeros(max(1, int(rate * seconds)), dtype=np.float32)


def _concat(*parts):
    import numpy as np
    return np.concatenate([p for p in parts if p is not None and len(p)])


# ------------------------------------------------------------------ native
def _win_ssml(text, cheerful):
    chunks = _split_sentences(text)
    parts = []
    for i, chunk in enumerate(chunks):
        rate, pitch, _vol = _prosody(chunk, cheerful, i, len(chunks))
        r = _named(float(rate.strip("%")),
                   ["x-slow", "slow", "medium", "fast", "x-fast"])
        p = _named(float(pitch.strip("Hz")),
                   ["x-low", "low", "medium", "high", "x-high"])
        parts.append('<prosody rate="%s" pitch="%s">%s</prosody>'
                     '<break time="110ms"/>' % (r, p, _xml_escape(chunk)))
    return ('<speak version="1.0" '
            'xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-GB">'
            + "".join(parts) + '</speak>')


def _native(text, cheerful=False):
    """Built-in OS speech. Instant, offline, still shaped per sentence."""
    global _proc
    folder = None
    try:
        if IS_WIN:
            # SSML goes through a file: quoting or a stray $ / backtick in a
            # reply can no longer break the PowerShell command line.
            folder = tempfile.mkdtemp(prefix="jarvis_ssml_")
            xml_path = os.path.join(folder, "speech.xml")
            txt_path = os.path.join(folder, "speech.txt")
            with open(xml_path, "w", encoding="utf-8") as f:
                f.write(_win_ssml(text, cheerful))
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
            ps = (
                "Add-Type -AssemblyName System.Speech; "
                "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "%s"
                "$x=[IO.File]::ReadAllText('%s'); "
                "$p=[IO.File]::ReadAllText('%s'); "
                "try{$s.SpeakSsml($x)}catch{$s.Speak($p)}" % (
                    ("try{$s.SelectVoice('%s')}catch{}; " %
                     _pick_win_voice().replace("'", "''")
                     if _pick_win_voice() else
                     "try{$s.SelectVoiceByHints('Male')}catch{}; "),
                    xml_path.replace("'", "''"), txt_path.replace("'", "''")))
            _begin()
            _proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", ps],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=NW_FLAG)
            _proc.wait(timeout=90)
            return True

        chunks = _split_sentences(text)
        if len(chunks) > 5:
            chunks = chunks[:4] + [" ".join(chunks[4:])]

        for i, chunk in enumerate(chunks):
            rate, pitch, _vol = _prosody(chunk, False, i, len(chunks))
            r = float(rate.strip("%"))
            p = float(pitch.strip("Hz"))
            if i:
                time.sleep(0.12)
            _begin()
            if IS_MAC:
                _proc = subprocess.Popen(
                    ["say", "-v", _pick_mac_voice() or "Kate",
                     "-r", str(int(190 * (1 + r / 100.0))), chunk],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                _proc.wait(timeout=60)
            else:
                spoken = False
                for exe in ("espeak-ng", "espeak"):
                    try:
                        if subprocess.call(["which", exe],
                                           stdout=subprocess.DEVNULL,
                                           stderr=subprocess.DEVNULL) == 0:
                            _proc = subprocess.Popen(
                                [exe, "-v", "en-gb",
                                 "-s", str(int(165 * (1 + r / 100.0))),
                                 "-p", str(int(max(0, min(99, 50 + p)))),
                                 chunk],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
                            _proc.wait(timeout=60)
                            spoken = True
                            break
                    except Exception:
                        continue
                if not spoken:
                    return False
        return True
    except Exception:
        return False
    finally:
        if folder:
            try:
                shutil.rmtree(folder, ignore_errors=True)
            except Exception:
                pass


def warm():
    """Load the local British voice in the background, ready for the first reply."""
    def probe():
        try:
            if IS_MAC:
                _pick_mac_voice()
            elif IS_WIN:
                _pick_win_voice()
        except Exception:
            pass
    threading.Thread(target=probe, daemon=True).start()
    threading.Thread(target=_piper_load, daemon=True).start()
    prefetch()


def _begin():
    """Fire the caption hook once, when sound actually leaves the speaker."""
    global _started
    if _started:
        return
    _started = True
    cb = _start_cb
    if cb is None:
        return
    try:
        cb()
    except Exception:
        pass


def say(text, cheerful=False, on_start=None):
    global _start_cb, _started
    if not VOICE_ON:
        return
    clean = _clean(text)
    if not clean:
        return

    def _speak(cb=on_start):
        global _edge_cool, _start_cb, _started
        with _lock:
            _start_cb = cb
            _started = False
            try:
                if _edge_ready():
                    if _edge(clean, cheerful):
                        return
                    _edge_cool = time.time()   # offline voice for a while
                if _piper(clean, cheerful):
                    return
                prefetch()
                _native(clean, cheerful)
            finally:
                # If no engine managed to speak, still show the caption.
                _begin()
                _start_cb = None

    threading.Thread(target=_speak, daemon=True).start()


def stop():
    global _proc
    try:
        if _proc and _proc.poll() is None:
            _proc.kill()
    except Exception:
        pass
    if IS_WIN:
        try:
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass
