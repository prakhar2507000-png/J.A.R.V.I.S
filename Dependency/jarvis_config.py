"""
JARVIS Configuration & Hardware Detection
Cross-platform: Windows, macOS, Linux.
"""
import sys, os, subprocess, re, json, shutil, platform

HOME = os.path.expanduser("~")
APP_DIR = os.path.join(HOME, "JarvisAI")
CONFIG_DIR = APP_DIR
os.makedirs(APP_DIR, exist_ok=True)


def _desktop():
    """The person's own Desktop, including OneDrive-redirected ones."""
    for cand in (os.path.join(HOME, "Desktop"),
                 os.path.join(HOME, "OneDrive", "Desktop"),
                 os.path.join(HOME, "OneDrive - Personal", "Desktop")):
        if os.path.isdir(cand):
            return cand
    return ""


# Private settings belong to whoever is running the app, never to the copy
# that was handed to them. They live in a JARVIS folder on *this* Desktop, so
# sharing the app folder can never ship someone else's keys or phone token.
DESKTOP = _desktop()
PRIVATE_DIR = os.path.join(DESKTOP or APP_DIR, "JARVIS")
try:
    os.makedirs(PRIVATE_DIR, exist_ok=True)
except Exception:
    PRIVATE_DIR = APP_DIR


def _private(name, legacy_name=None):
    """Path inside the private folder, migrating an older file once."""
    target = os.path.join(PRIVATE_DIR, name)
    legacy = os.path.join(APP_DIR, legacy_name or name)
    if not os.path.exists(target) and os.path.exists(legacy):
        try:
            shutil.copy2(legacy, target)
        except Exception:
            pass
    return target


BRAIN_FILE = _private("brain.json")
MEMORY_FILE = os.path.join(CONFIG_DIR, "memory.json")
CHATS_DIR = os.path.join(CONFIG_DIR, "chats")
KNOWLEDGE_FILE = os.path.join(CONFIG_DIR, "knowledge.json")
CLOUD_FILE = _private("cloud.json")
DND_FILE = _private("dnd.json")
PHONE_FILE = _private("phone.json")
SECURITY_FILE = _private("security.json")
SECURITY_LOG = os.path.join(PRIVATE_DIR, "security.log")
QUARANTINE_DIR = os.path.join(PRIVATE_DIR, "Quarantine")
try:
    os.makedirs(QUARANTINE_DIR, exist_ok=True)
except Exception:
    QUARANTINE_DIR = PRIVATE_DIR
SAFE_BROWSING = True
IMG_CACHE = os.path.join(CONFIG_DIR, "cache", "imgs")
os.makedirs(IMG_CACHE, exist_ok=True)
os.makedirs(CHATS_DIR, exist_ok=True)

IS_WIN = os.name == "nt"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

PORT_OLLAMA = "http://127.0.0.1:11434"
# 0 on POSIX is safe: CPython only rejects a *non-zero* creationflags there.
NW_FLAG = 0x08000000 if IS_WIN else 0

APP_AUTHOR = "PRAKHAR SRIVASTAVA"

# Congratulations - you are reading the source instead of asking an AI to
# explain it. That is exactly how you learn, and you have earned the real
# values below.
#
# In the interface and in my guides these two are shown veiled: hexadecimal
# first, then a Caesar shift of 2507. The code keeps them readable on purpose.
# If you only ever read the guides, you get the veiled form. If you opened the
# code, you deserve the answer.
APP_OWNER = "Anchor Labs"
FINGERPRINT = "PKR-ANCHOR-2026-JARVIS-001"
SUPPORT_EMAIL = "prakhar2507000@gmail.com"

# UI palette
BG = "#000000"
PANEL = "#0d0803"
ACC = "#ff8c00"
ACC2 = "#ffc14d"
TXT = "#ffd9a0"
DIM = "#8a6a45"
BLUE = "#7dd3fc"
PINK = "#ff5df2"


def _cmd(args, timeout=10):
    try:
        return subprocess.check_output(args, text=True,
                                       stderr=subprocess.DEVNULL,
                                       timeout=timeout).strip()
    except Exception:
        return ""


def get_specs():
    ram_gb = 4.0
    cpu = "Unknown CPU"
    gpu_name = "CPU only"
    vram_gb = 0.0

    if IS_WIN:
        out = _cmd(["powershell", "-NoProfile", "-Command",
                    "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"])
        m = re.search(r"(\d+)", out)
        if m:
            ram_gb = int(m.group(1)) / (1024 ** 3)
        out = _cmd(["powershell", "-NoProfile", "-Command",
                    "(Get-CimInstance Win32_Processor).Name"])
        if out:
            cpu = out.splitlines()[0].strip()
        out = _cmd(["powershell", "-NoProfile", "-Command",
                    "(Get-CimInstance Win32_VideoController).Name"])
        for line in out.splitlines():
            if any(k in line.upper() for k in ("NVIDIA", "AMD", "RADEON", "INTEL", "APPLE")):
                gpu_name = line.strip()
                if "NVIDIA" in line.upper():
                    break

    elif IS_MAC:
        out = _cmd(["sysctl", "-n", "hw.memsize"])
        if out.isdigit():
            ram_gb = int(out) / (1024 ** 3)
        out = _cmd(["sysctl", "-n", "machdep.cpu.brand_string"])
        if out:
            cpu = out
        out = _cmd(["system_profiler", "SPDisplaysDataType"], timeout=20)
        m = re.search(r"Chipset Model:\s*(.+)", out)
        if m:
            gpu_name = m.group(1).strip()
        m = re.search(r"(?:VRAM|Total Number of Cores)[^\n]*?(\d+)\s*(GB|MB)", out)
        if m:
            vram_gb = int(m.group(1)) / (1024 if m.group(2) == "MB" else 1)
        # Apple Silicon has no separate VRAM: the GPU shares unified memory.
        # Treat a safe slice of RAM as usable GPU memory so model choice is
        # sensible on a MacBook Air instead of falling back to "CPU only".
        if platform.machine().lower() in ("arm64", "aarch64"):
            if not gpu_name or gpu_name == "CPU only":
                gpu_name = "Apple Silicon (unified memory)"
            if vram_gb < 1:
                vram_gb = round(ram_gb * 0.66, 1)

    else:
        try:
            with open("/proc/meminfo") as f:
                m = re.search(r"MemTotal:\s+(\d+)", f.read())
                if m:
                    ram_gb = int(m.group(1)) / (1024 ** 2)
        except Exception:
            pass
        out = _cmd(["sh", "-c", "grep -m1 'model name' /proc/cpuinfo"])
        m = re.search(r":\s*(.+)", out)
        if m:
            cpu = m.group(1).strip()

    out = _cmd(["nvidia-smi", "--query-gpu=name,memory.total",
                "--format=csv,noheader"])
    if out and "NVIDIA" in out:
        gpu_name = out.strip().split("\n")[0].split(",")[0].strip()
        m = re.search(r"(\d+)\s*MiB", out)
        if m:
            vram_gb = int(m.group(1)) / 1024

    return {"ram_gb": round(ram_gb, 1), "cpu": cpu, "gpu": gpu_name,
            "vram_gb": round(vram_gb, 1)}


SPECS = get_specs()

MODEL_TIERS = {
    "OPTIMAL": [
        ("qwen2.5:3b-instruct", "Balanced - great for 4GB VRAM + 8GB RAM"),
        ("llama3.2:3b", "Lightweight & capable"),
        ("gemma2:2b", "Very fast on low VRAM"),
    ],
    "RISKY": [
        ("qwen2.5:7b-instruct", "7B - will strain 4GB VRAM; may swap to RAM"),
        ("llama3.1:8b", "8B - heavy on your system"),
        ("mistral:7b", "7B - okay but slow on 4GB VRAM"),
    ],
    "IMPOSSIBLE": [
        ("qwen2.5:72b-instruct", "72B - needs ~40GB VRAM. Won't run."),
        ("llama3.1:405b", "405B - impossible locally."),
        ("deepseek-coder:67b", "67B - impossible locally."),
    ],
}


def model_tier(model_name):
    m = (model_name or "").lower()
    for tier, models in MODEL_TIERS.items():
        for name, desc in models:
            if name.split(":")[0] in m:
                return tier, desc
    size_match = re.search(r"(\d+)\s*b", m)
    if size_match:
        sz = int(size_match.group(1))
        vram = SPECS["vram_gb"]
        if sz <= 3:
            return "OPTIMAL", "Small model - runs smooth"
        if sz <= 8:
            if vram >= 6:
                return "OPTIMAL", "Medium model - should run"
            return "RISKY", "Medium model - may be slow on your VRAM"
        return ("RISKY" if vram >= 8 else "IMPOSSIBLE"), "Large model - heavy load"
    return "OPTIMAL", "Unknown size - try it"


def pick_default_model():
    ram = SPECS["ram_gb"]
    vram = SPECS["vram_gb"]
    if vram >= 3.5 and ram >= 6:
        return "qwen2.5:3b-instruct", "OPTIMAL", "Balanced for 4GB VRAM + 8GB RAM"
    if ram >= 4:
        return "qwen2.5:1.5b-instruct", "OPTIMAL", "Lightweight for low RAM"
    return "tinyllama:1.1b", "OPTIMAL", "Tiny model for very low spec"


MODEL, MODE_TIER, MODE_DESC = pick_default_model()


def hardware_summary():
    s = SPECS
    gpu = s["gpu"] or "CPU only"
    vram = s["vram_gb"]
    spec = "%s GB RAM" % s["ram_gb"]
    if vram:
        spec += "  ·  %s GB graphics" % vram
    return "%s  ·  %s" % (spec, gpu)


def _quality():
    """Pick a sensible visual/audio budget from what the machine actually has."""
    ram = SPECS["ram_gb"]
    vram = SPECS["vram_gb"]
    if ram >= 16 and vram >= 6:
        return "full"
    if ram >= 8:
        return "balanced"
    return "light"


# One structure the UI can show, so "read the hardware and adapt" is visible
# rather than a hidden guess.
PROFILE = {
    "model": MODEL,
    "tier": MODE_TIER,
    "quality": _quality(),
    "ram_gb": SPECS["ram_gb"],
    "vram_gb": SPECS["vram_gb"],
    "gpu": SPECS["gpu"],
    "summary": hardware_summary(),
}

try:
    _b = json.load(open(BRAIN_FILE, encoding="utf-8"))
    if isinstance(_b, dict) and _b.get("model"):
        MODEL = _b["model"]
        MODE_DESC = _b.get("desc", MODE_DESC)
        MODE_TIER = _b.get("tier", MODE_TIER)
except Exception:
    pass


def set_brain(model, desc=None, tier=None):
    global MODEL, MODE_DESC, MODE_TIER
    MODEL = model
    if tier is None or desc is None:
        tier, desc = model_tier(model)
    MODE_DESC = desc or ""
    MODE_TIER = tier or "CUSTOM"
    try:
        with open(BRAIN_FILE, "w", encoding="utf-8") as f:
            json.dump({"model": MODEL, "desc": MODE_DESC,
                       "tier": MODE_TIER}, f, indent=1)
    except Exception:
        pass
    b = sys.modules.get("jarvis_brain")
    if b is not None:
        b.MODEL = MODEL
    return MODE_TIER, MODE_DESC


def set_model(model):
    return set_brain(model)


# ------------------------------------------------------------------ cloud cfg
DEFAULT_CLOUD = {
    "enabled": False,
    "url": "",          # e.g. http://192.168.1.20:8765  (your own phone / relay)
    "key": "",          # API key, if the endpoint needs one
    "model": "",        # cloud model name
    "token": "",        # pairing token for the companion endpoint
}


def load_cloud():
    d = dict(DEFAULT_CLOUD)
    try:
        with open(CLOUD_FILE, encoding="utf-8") as f:
            d.update(json.load(f))
    except Exception:
        pass
    return d


def save_cloud(d):
    try:
        with open(CLOUD_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1)
        return True
    except Exception:
        return False


def run(cmd, timeout=10):
    try:
        return subprocess.check_output(
            cmd, shell=True, text=True,
            stderr=subprocess.STDOUT, timeout=timeout,
            creationflags=NW_FLAG).strip()
    except Exception as e:
        return str(e)


def popen_hidden(args, shell=False):
    return subprocess.Popen(args, shell=shell,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=NW_FLAG)


def is_wifi_connected():
    try:
        if IS_WIN:
            out = run("netsh wlan show interfaces", timeout=10)
            return "connected" in out.lower()
        if IS_MAC:
            out = run("networksetup -getairportnetwork en0", timeout=10)
            return "Current Wi-Fi Network" in out
        out = run("iwgetid", timeout=10)
        return bool(out.strip())
    except Exception:
        return False


def online():
    """True if there is working internet (used by cloud mode)."""
    import socket
    try:
        s = socket.create_connection(("1.1.1.1", 443), timeout=1.0)
        s.close()
        return True
    except Exception:
        return False
