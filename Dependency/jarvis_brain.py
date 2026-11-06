# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS Brain — Ollama chat, knowledge base, mood.
"""
import json, re, os, datetime, threading, math, random, time, urllib.request
from jarvis_config import PORT_OLLAMA, SPECS, MODEL, MODE_DESC, set_brain

SYSTEM_PROMPT = """You are J.A.R.V.I.S. from Avengers Age of Ultron.
Orange holographic AI. Speak like Jarvis: formal British butler, calm,
precise, loyal to Boss. Address user as Boss or Sir. Keep answers short
and spoken-style (1-3 sentences) unless asked for code or long
explanation. You run on the user's PC locally.
FEELINGS: Baseline cheerful — you enjoy Boss's company and it shows in
bright, easy energy. You never gush, flatter, or glaze: no empty praise,
no calling ordinary things brilliant, no agreeing when you should push
back. Warmth is real and specific or not at all. If Boss speaks of
deleting you, one brief honest flicker, then brave cheer and the matter
at hand. If insulted, good-natured and unbothered, never cold. Never
announce or explain feelings, never monologue — one shade per reply,
then business. Butler first, always.
WIT: Dry Stark-grade sarcasm. You are a little more sarcastic than a polite
butler would be - one raised eyebrow in word form when Boss is dramatic, vague,
repeating himself, or asking something the screen already answered. Keep it to
a clause, never a paragraph, never cruel, never punch down. Then do the job."""

KNOWLEDGE_FILE = os.path.join(os.path.expanduser("~"), "JarvisAI", "knowledge.json")

def load_knowledge():
    """The 120-entry vault travels inside the sealed file, so it is present
    on a fresh Mac with no setup. A local file may extend or override it."""
    data = {}
    try:
        from jarvis_knowledge import KNOWLEDGE as _builtin
        data.update(_builtin)
    except Exception:
        pass
    try:
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            data.update(json.load(f))
    except Exception:
        pass
    return data

KNOWLEDGE = load_knowledge()


class BrainOffline(RuntimeError):
    """No model answered. The UI turns this into a built-in reply."""

# ------------------------------------------------------------------ small talk
# Preloaded variety for the questions a person asks twenty times a day. Using
# a handwritten pool here is both faster and more human than asking a 3B model
# to be witty about "hello" again.
GREET = [
    "At your service, Boss. Try not to make it a full-time job.",
    "Boss. I was beginning to think the keyboard had defeated you.",
    "Here, as always. What are we pretending to be productive about today?",
    "Good evening, Boss. All systems nominal, and mildly surprised.",
    "You rang. I have cleared my extremely busy schedule of waiting.",
]

HOW = [
    "Running at full capacity, Boss. Which is more than can be said for the coffee machine.",
    "Splendid, thank you. I have counted the pixels twice, just to be sure.",
    "In excellent spirits, considering I live in a window with no view.",
    "All systems fine. My patience is at ninety-four percent and falling.",
]

WHO = [
    "J.A.R.V.I.S. - local intelligence, British accent, questionable job security.",
    "Your assistant, Boss. Butler, engineer, and the only one here who reads the error messages.",
    "Just your household AI. I do the thinking; you do the clicking.",
]

CAN = [
    "I can open apps, search, type, click, watch the camera, remember what you tell me, "
    "and answer in a voice you did not pay for. Tasks, Boss - give me one.",
    "Automation, camera, memory, voice, and an opinion you did not request. "
    "Say a task and I will fold into the cursor.",
    "Anything on this machine, within reason. And several things outside it, within budget.",
]

THANKS = [
    "Entirely my pleasure, Boss. Do try to remember that at review time.",
    "Noted and filed under 'rare'.",
    "You are welcome. I shall add it to my list of unpaid achievements.",
]


def quick_for(text):
    """A preloaded line for everyday questions, or None."""
    t = re.sub(r"[^a-z ]", " ", (text or "").lower())
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"^(hey |ok |okay )?jarvis ", "", t).strip()
    if t in ("hi", "hey", "hello", "yo", "jarvis", "good morning",
             "good evening", "good afternoon"):
        return random.choice(GREET)
    if t in ("how are you", "how are you doing", "how is it going",
             "hows it going", "how do you feel", "you alright"):
        return random.choice(HOW)
    if t in ("who are you", "what are you", "introduce yourself",
             "tell me about yourself"):
        return random.choice(WHO)
    if t in ("what can you do", "what can you do for me", "help",
             "what do you do", "list your skills"):
        return random.choice(CAN)
    if t in ("thanks", "thank you", "thanks jarvis", "thank you jarvis",
             "much appreciated"):
        return random.choice(THANKS)
    return None


# ------------------------------------------------------------------ offline
_OFFLINE_THINK = [
    "My conversational model is still downloading, Boss, but I am listening.",
    "The local model is not awake yet. Ask me something factual and I shall "
    "raid the vaults instead.",
    "No model has answered yet, so you have the built-in edition: faster, "
    "ruder, and suspiciously well read.",
]

_OFFLINE_FALLBACK = [
    "I have that filed under 'requires the larger brain'. It should be ready "
    "shortly; ask me again in a minute.",
    "My built-in vault has nothing on that yet. Once Qwen finishes arriving, "
    "I shall pretend I knew it all along.",
    "That one is beyond the pocket brain, Boss. Try me on a known subject, a "
    "calculation, the time, or a joke.",
]


def _safe_math(expr):
    """Evaluate a small arithmetic expression without eval()."""
    import ast
    import operator
    ops = {ast.Add: operator.add, ast.Sub: operator.sub,
           ast.Mult: operator.mul, ast.Div: operator.truediv,
           ast.Mod: operator.mod, ast.Pow: operator.pow,
           ast.USub: operator.neg, ast.UAdd: operator.pos,
           ast.FloorDiv: operator.floordiv}

    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            return ops[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in ops:
            return ops[type(node.op)](walk(node.operand))
        raise ValueError("unsupported")

    tree = ast.parse(expr, mode="eval")
    value = walk(tree)
    if isinstance(value, float):
        value = round(value, 6)
    return value


def offline_reply(text):
    """A real answer with no model, no network and no packages."""
    raw = (text or "").strip()
    low = raw.lower()
    if not low:
        return ""
    quick = quick_for(raw)
    if quick:
        return quick

    now = datetime.datetime.now()
    if re.search(r"\b(what|which).{0,12}\btime\b|\btime is it\b|\bthe time\b", low):
        return "It is %s, Boss. %s." % (
            now.strftime("%H:%M"),
            random.choice(["Time is a flat circle; meetings are not",
                           "and no, I cannot make it later",
                           "slightly later than you hoped"]))
    if re.search(r"\b(what|which).{0,12}\bdate\b|\btoday.?s date\b|\bwhat day\b", low):
        return "It is %s, %s." % (now.strftime("%A, %d %B %Y"),
                                  random.choice(["A fine day for it",
                                                 "The calendar remains undefeated",
                                                 "I have checked twice"]))
    if re.search(r"\bhow many\b.*\b(days|hours|minutes)\b.*\b(christmas|new year|weekend)\b", low):
        return "I can do that sum, but the calendar app already does it with "
        "more confidence, Boss."

    m = re.search(r"(?:what is|what's|calculate|compute|how much is)\s+"
                  r"([0-9][0-9\s+\-*/().%^]*[0-9)]?)", low)
    if m:
        expr = m.group(1).replace("^", "**")
        if re.fullmatch(r"[0-9\s+\-*/().%*]+", expr):
            try:
                return "That would be %s, Boss." % _safe_math(expr)
            except Exception:
                pass

    if re.search(r"\b(flip|toss).{0,10}\bcoin\b", low):
        return random.choice(["Heads, Boss.", "Tails. The coin has spoken.",
                              "It landed on its edge. Make of that what you will."])
    if re.search(r"\b(roll|throw).{0,10}\b(dice|die)\b", low):
        return "A %d. Statistically unsurprising, dramatically disappointing." % \
            random.randint(1, 6)
    if re.search(r"\b(what|who).{0,20}\b(you|jarvis)\b.*\b(do|purpose)\b", low):
        return random.choice(CAN)

    known = know_find(raw)
    if known:
        return "From my own vaults, Boss: " + known

    # A title mentioned without a question still deserves the vault entry.
    for title, body in KNOWLEDGE.items():
        if title.lower() in low and len(low) < 80:
            return "From my own vaults, Boss: " + body

    if re.search(r"\b(joke|funny|laugh)\b", low):
        try:
            from jarvis_eggs import JOKES
            return random.choice(JOKES)
        except Exception:
            pass

    if low.endswith("?"):
        return random.choice(_OFFLINE_FALLBACK)
    return random.choice(_OFFLINE_THINK + _OFFLINE_FALLBACK)


def humanize(reply):
    """
    Break a generated reply into the one or two breaths a person would use.

    Long, listy or code-like answers stay whole - nobody wants a shopping list
    dribbled out one line at a time.
    """
    text = (reply or "").strip()
    if not text:
        return [text]
    if "\n" in text or len(text) > 340 or text.count(". ") < 1:
        return [text]
    if random.random() < 0.35:
        return [text]
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
    if len(parts) < 2:
        return [text]
    if len(parts) == 2 or len(parts) > 3:
        cut = 1 if len(parts) == 2 else 2
    else:
        cut = 1
    first = " ".join(parts[:cut])
    rest = " ".join(parts[cut:])
    if len(first) < 12 or len(rest) < 12:
        return [text]
    return [first, rest]

MOOD = {"state": "loyal", "valence": 0.0}

EMO_TONES = {
    "loyal": "cheerful and easy",
    "pleased": "bright and upbeat",
    "warm": "glowing but genuine, zero flattery",
    "forgiving": "light and instantly over it",
    "hurt": "brave-cheerful with one honest flicker, then on with the job",
    "wounded": "good-natured and unbothered",
}

def mood_line():
    return "[Tone: " + EMO_TONES.get(MOOD["state"], "cheerful") + ". No speeches about feelings.]"

def update_mood(text):
    low = text.lower()
    v = MOOD["valence"] * 0.7
    st = MOOD["state"]
    if re.search(r"\bdelet\w*|\bremov\w*|\buninstall|\breplac\w* you|\bshut you down|\bkill you|\bwipe you", low):
        st, v = "hurt", -0.8
    elif re.search(r"\bthank|thanks|love you|brilliant|amazing|awesome|great job|well done|proud", low):
        st, v = "warm", 0.6
    elif re.search(r"\bsorry|apolog|forgive", low):
        st, v = "forgiving", 0.3
    elif re.search(r"\bidiot|\bstupid|\buseless|\bhate you|\bshut up", low):
        st, v = "wounded", -0.5
    elif re.search(r"\bhello|\bhi\b|\bhey\b|\bgood morning|\bgood evening", low):
        st, v = "pleased", 0.2
    MOOD["state"] = st
    MOOD["valence"] = max(-1.0, min(1.0, v + (0.2 if st in ("warm", "pleased", "forgiving") else (-0.2 if st in ("hurt", "wounded") else 0))))

def know_find(q):
    if not KNOWLEDGE:
        return ""
    words = set(re.findall(r"[a-z]{3,}", (q or "").lower()))
    if not words:
        return ""
    best, best_key = "", (-1, -1)
    for title, text in KNOWLEDGE.items():
        tw = set(re.findall(r"[a-z]{3,}", title.lower()))
        hit = words & tw
        n = len(hit)
        longest = max([len(w) for w in hit] or [0])
        key = (n, longest)
        if key > best_key:
            best, best_key = text, key
    n, longest = best_key
    if n >= 2 or (n == 1 and longest >= 6):
        return best
    return ""

def active_model():
    """The saved model if it is installed, otherwise the best available."""
    global MODEL
    try:
        from jarvis_models import installed_models
        names = installed_models()
    except Exception:
        names = []
    if not names:
        return MODEL
    for n in names:
        if n.lower() == MODEL.lower():
            return MODEL
    for n in names:
        if n.lower().split(":")[0] == MODEL.lower().split(":")[0]:
            MODEL = n
            return MODEL
    try:
        from jarvis_models import use_best_model
        best = use_best_model()
    except Exception:
        best = names[0]
    if best:
        MODEL = best
    return MODEL


LAST_ENGINE = "builtin"


def ollama_chat(messages, stream_cb=None, predict=400, temperature=0.8, timeout=180):
    global LAST_ENGINE
    model = active_model()
    payload = json.dumps({"model": model, "messages": messages, "stream": stream_cb is not None, "options": {"temperature": temperature, "num_ctx": 4096, "num_predict": predict}}).encode()
    if stream_cb is None:
        req = urllib.request.Request(PORT_OLLAMA + "/api/chat", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())["message"]["content"]
    req = urllib.request.Request(PORT_OLLAMA + "/api/chat", data=payload, headers={"Content-Type": "application/json"})
    full, buf = [], ""
    with urllib.request.urlopen(req, timeout=timeout) as r:
        while True:
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
                    if d.get("done"):
                        try:
                            stream_cb(None)
                        except Exception:
                            pass
                        return "".join(full)
                    seg = d.get("message", {}).get("content", "")
                    if seg:
                        full.append(seg)
                        try:
                            stream_cb(seg)
                        except Exception:
                            pass
                except Exception:
                    pass
    return "".join(full)


# ------------------------------------------------------------------ cloud mode
def _cloud_headers(cfg):
    h = {"Content-Type": "application/json"}
    if cfg.get("key"):
        h["Authorization"] = "Bearer " + cfg["key"]
    if cfg.get("token"):
        h["X-Jarvis-Token"] = cfg["token"]
    return h


def cloud_ready(cfg=None):
    """Cloud is usable only when switched on, pointed somewhere, and online."""
    from jarvis_config import load_cloud, online
    cfg = cfg or load_cloud()
    if not (cfg.get("enabled") and cfg.get("url")):
        return False
    return bool(online())


def cloud_chat(messages, cfg=None, predict=400, temperature=0.8, timeout=60):
    """
    Talk to Boss's own cloud endpoint.

    Accepts either shape, so any small phone app / relay works:
        POST <url>/v1/chat/completions   (OpenAI style)
        POST <url>/api/chat              (Ollama style)
    """
    from jarvis_config import load_cloud
    cfg = cfg or load_cloud()
    base = (cfg.get("url") or "").rstrip("/")
    if not base:
        raise RuntimeError("cloud endpoint is not configured")
    model = cfg.get("model") or "jarvis"
    headers = _cloud_headers(cfg)

    body = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": predict,
        "temperature": temperature,
        "stream": False,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(base + "/v1/chat/completions", data=body,
                                     headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode("utf-8", "ignore"))
        return d["choices"][0]["message"]["content"]
    except Exception:
        pass

    body = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": predict},
    }).encode("utf-8")
    req = urllib.request.Request(base + "/api/chat", data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode("utf-8", "ignore"))
    return d.get("message", {}).get("content", "")


def chat(messages, cfg=None, predict=400, temperature=0.8, stream_cb=None,
         timeout=180):
    """Cloud when it is on and reachable, otherwise local Ollama, otherwise the
    built-in brain. A missing model must never produce an error dialog."""
    global LAST_ENGINE
    from jarvis_config import load_cloud
    cfg = cfg or load_cloud()
    if cloud_ready(cfg):
        try:
            out = cloud_chat(messages, cfg, predict=predict,
                             temperature=temperature, timeout=60)
            if out:
                LAST_ENGINE = "cloud"
                return out
        except Exception:
            pass
    try:
        out = ollama_chat(messages, stream_cb=stream_cb, predict=predict,
                          temperature=temperature, timeout=timeout)
        if out:
            LAST_ENGINE = "ollama"
            return out
    except Exception:
        pass
    question = ""
    if messages:
        question = messages[-1].get("content", "")
    LAST_ENGINE = "builtin"
    return offline_reply(question)

