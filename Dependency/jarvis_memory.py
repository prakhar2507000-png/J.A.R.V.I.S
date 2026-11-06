# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS Memory — chat transcripts, facts.
"""
import json, os, datetime
from jarvis_config import CONFIG_DIR, CHATS_DIR

MEM_PATH = os.path.join(CONFIG_DIR, "memory.json")

def load_mem():
    try:
        with open(MEM_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
            if isinstance(d, dict):
                d.setdefault("facts", [])
                return d
    except Exception:
        pass
    return {"facts": []}

def save_mem(d):
    try:
        with open(MEM_PATH, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=1)
    except Exception:
        pass

MEM = load_mem()

def save_transcript(lines):
    try:
        os.makedirs(CHATS_DIR, exist_ok=True)
        p = os.path.join(CHATS_DIR,
                         datetime.datetime.now().strftime(
                             "jarvis_%Y-%m-%d_%H%M.txt"))
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return p
    except Exception:
        return ""
