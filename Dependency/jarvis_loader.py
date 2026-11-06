# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS Loader - loads a tool from readable source.

    readable tool on disk  ->  compile() -> module
    already installed      ->  returned as-is

Every tool in the shared build ships as plain source in this folder, so this
is a thin convenience wrapper. An owner build may keep sealed payloads; if the
owner crypto module is not present, the loader simply reports that the tool is
missing instead of failing with a confusing import error.
"""
import os
import sys
import types
import builtins

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TOOLS = {
    "jarvis_video": "jarvis_video.py",
    "jarvis_autoreply": "jarvis_autoreply.py",
    "jarvis_automation": "jarvis_automation.py",
}

# Filled by the single-file build (JARVIS.py) so sealed payloads and tool
# sources can be read from memory instead of disk.
MEM_BLOBS = {}
MEM_SRC = {}

_cache = {}


def _read_enc(fname):
    if fname in MEM_BLOBS:
        return MEM_BLOBS[fname]
    with open(os.path.join(BASE_DIR, fname), "rb") as f:
        return f.read()


def _plain_path(fname):
    return os.path.join(BASE_DIR, fname)


def available(name):
    fname = TOOLS.get(name)
    if not fname:
        return False
    if name in sys.modules or name in MEM_SRC:
        return True
    if os.path.exists(_plain_path(fname)):
        return True
    if (fname + ".enc") in MEM_BLOBS:
        return True
    return os.path.exists(_plain_path(fname + ".enc"))


def _exec(src, name, label):
    mod = types.ModuleType(name)
    mod.__file__ = label
    mod.__package__ = ""
    mod.__dict__["__builtins__"] = builtins
    sys.modules[name] = mod
    exec(compile(src, label, "exec"), mod.__dict__)
    return mod


def _load(name):
    fname = TOOLS[name]

    # Already provided by the bundle or an earlier import.
    if name in sys.modules:
        return sys.modules[name]

    if name in MEM_SRC:
        return _exec(MEM_SRC[name], name, fname + " (bundled)")

    path = _plain_path(fname)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return _exec(f.read(), name, path)

    enc_name = fname + ".enc"
    if not available(name):
        raise ImportError(
            "Tool missing: %s (the readable module is not in this folder)"
            % fname)
    try:
        from jarvis_crypto import decrypt_bytes, SealedToolError
    except Exception as exc:
        raise ImportError(
            "Tool %s is sealed and this copy has no owner key. The shared "
            "build ships readable source instead." % fname) from exc
    try:
        src = decrypt_bytes(_read_enc(enc_name), fname).decode("utf-8")
    except SealedToolError as e:
        raise ImportError(str(e)) from e
    return _exec(src, name, enc_name)


def load(name):
    """Load one tool by short name, cached."""
    if name in _cache:
        return _cache[name]
    if name not in TOOLS:
        raise KeyError("unknown tool: %s" % name)
    mod = _load(name)
    _cache[name] = mod
    return mod


def load_video():
    return load("jarvis_video")


def load_autoreply():
    return load("jarvis_autoreply")


def load_automation():
    return load("jarvis_automation")


def preload(names=("jarvis_autoreply", "jarvis_automation")):
    """Warm the cache; returns {name: module or error string}."""
    out = {}
    for n in names:
        try:
            out[n] = load(n)
        except Exception as e:
            out[n] = "ERROR: %s" % e
    return out
