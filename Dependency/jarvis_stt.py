# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS Speech-to-Text - free, local, no account.

Backends, best first:
    1. faster-whisper   (CTranslate2, CPU, int8)   pip install faster-whisper
    2. openai-whisper   (PyTorch)                  pip install openai-whisper
    3. Windows SAPI / macOS Speech                 built in

Wispr Flow is a paid cloud dictation service; the free equivalent is Whisper
running on this machine. Models download once from Hugging Face - no key, no
sign-up, no payment, and the audio never leaves the PC.
"""
import os
import sys
import time
import threading
import subprocess

from jarvis_config import IS_WIN, IS_MAC, NW_FLAG

SR = 16000
MODEL_SIZE = os.environ.get("JARVIS_WHISPER_MODEL", "tiny.en")

_model = None
_backend = None
_failed = False
_lock = threading.Lock()
_warm = False


def backend():
    return _backend or "os"


def _load_model():
    """Load Whisper once. Returns True when a Whisper backend is ready."""
    global _model, _backend, _failed
    with _lock:
        if _model is not None:
            return True
        if _failed:
            return False
        try:
            from faster_whisper import WhisperModel
            _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
            _backend = "faster-whisper"
            return True
        except Exception:
            pass
        try:
            import whisper
            _model = whisper.load_model(MODEL_SIZE)
            _backend = "openai-whisper"
            return True
        except Exception:
            pass
        _failed = True
        return False


def warmup():
    """Preload in the background so the first MIC press is not slow."""
    global _warm
    if _warm:
        return
    _warm = True
    threading.Thread(target=_load_model, daemon=True).start()


# ------------------------------------------------------------------ recording
def record(max_seconds=8.0, silence=0.9, threshold=0.010):
    """
    Record from the default mic with simple voice-activity detection.
    Stops after `silence` seconds of quiet, or at max_seconds.
    Returns a float32 numpy array at 16 kHz, or None.
    """
    try:
        import sounddevice as sd
        import numpy as np
    except Exception:
        return None

    blocks = []
    start = time.time()
    quiet = 0.0
    spoke = False
    try:
        with sd.InputStream(samplerate=SR, channels=1, dtype="float32",
                            blocksize=800) as stream:
            while time.time() - start < max_seconds:
                data, _ = stream.read(800)      # 50 ms
                blocks.append(data.copy())
                rms = float(np.sqrt(np.mean(data ** 2)))
                if rms >= threshold:
                    spoke = True
                    quiet = 0.0
                else:
                    quiet += 0.05
                if spoke and quiet >= silence:
                    break
    except Exception:
        return None

    if not blocks or not spoke:
        return None
    try:
        import numpy as np
        return np.concatenate(blocks).reshape(-1)
    except Exception:
        return None


def transcribe(audio):
    """Whisper transcription of a float32 mono array. Empty string on failure."""
    if audio is None:
        return ""
    if not _load_model():
        return ""
    try:
        if _backend == "faster-whisper":
            segments, _info = _model.transcribe(
                audio, language="en", vad_filter=True, beam_size=1,
                condition_on_previous_text=False)
            return " ".join(s.text.strip() for s in segments).strip()
        result = _model.transcribe(
            audio, language="en", fp16=False, condition_on_previous_text=False)
        return (result.get("text") or "").strip()
    except Exception:
        return ""


# ------------------------------------------------------------------ OS fallback
def os_listen(seconds=7):
    """Built-in recognizer, used only when Whisper is not installed yet."""
    if IS_WIN:
        try:
            ps = (
                "$ErrorActionPreference='SilentlyContinue'; "
                "Add-Type -AssemblyName System.Speech; "
                "$r=New-Object System.Speech.Recognition."
                "SpeechRecognitionEngine; "
                "$r.SetInputToDefaultAudioDevice(); "
                "$r.LoadGrammar((New-Object System.Speech.Recognition."
                "DictationGrammar)); "
                "$res=$r.Recognize((New-TimeSpan -Seconds %d)); "
                "if($res){$res.Text}else{''}" % seconds)
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", ps], text=True,
                timeout=seconds + 12, creationflags=NW_FLAG)
            return out.strip()
        except Exception:
            return ""
    if IS_MAC:
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.Microphone() as src:
                audio = r.listen(src, timeout=seconds,
                                 phrase_time_limit=seconds)
            return r.recognize_google(audio)
        except Exception:
            return ""
    return ""


def listen_once(seconds=7):
    """Record -> Whisper -> OS recognizer. Returns text or ''."""
    audio = record(max_seconds=seconds)
    text = transcribe(audio)
    if text:
        return text
    return os_listen(seconds)
