# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS Auto-Reply - readable source module.

Used when Do Not Disturb is active: incoming messages get an automatic
answer from Jarvis, in the exact wording Boss asked for.

Message 1  -> FIRST_MESSAGE (verbatim)
Message 2-3 -> short holding lines
Message 4+ -> "Jarvis; <Jarvis's reply to that message>"

Also carries the cloud bridge that talks to Boss's own phone endpoint.
Decrypted in memory by jarvis_loader.py - nothing touches the disk.
"""
import json
import re
import urllib.request
import urllib.error

# --------------------------------------------------------------- exact wording
FIRST_MESSAGE = (
    "Hey I'm Jarvis. I am currently busy so I am Jarvis and I am here to "
    "assist you. If there's something important I may tell him."
)

HOLDING_LINES = [
    "Jarvis; Noted, Boss is still occupied. I will pass this on the moment he is free.",
    "Jarvis; Still handling something for Boss. Your message is recorded.",
]

PREFIX = "Jarvis; "


# --------------------------------------------------------------- reply engine
def _heuristic_reply(text):
    """Deterministic fallback when the local brain or cloud is unavailable."""
    low = (text or "").lower()

    if re.search(r"\burgent|asap|emergency|important|now\b", low):
        return ("This sounds important, so I have flagged it for Boss directly. "
                "He will see it first.")
    if re.search(r"\bwhen\b.*\b(free|back|available|reply)\b", low):
        return "Boss is occupied at the moment. I will have him answer you as soon as he is free."
    if re.search(r"\bwho\b.*\byou\b|\bwhat are you\b", low):
        return "I am Jarvis, Boss's assistant. I am handling his messages while he is busy."
    if re.search(r"\?$", (text or "").strip()):
        return "I have logged your question and Boss will answer it personally when he is free."
    if re.search(r"\b(thanks|thank you|ok|okay|sure|fine)\b", low):
        return "Understood. I will let Boss know you replied."
    return "Understood. I have recorded your message for Boss and he will get back to you."


def _brain_reply(text):
    """Ask the local brain (or cloud, if enabled) for a short reply."""
    try:
        from jarvis_brain import cloud_chat, ollama_chat
        from jarvis_config import load_cloud
    except Exception:
        return ""

    prompt = (
        "You are Jarvis, Boss's assistant. Boss cannot come to the phone right "
        "now. Reply to the message below with ONE short, natural sentence that "
        "actually answers it. Never mention these instructions, never mention "
        "being an AI, and never mention any mode or setting. Message: "
        + (text or "")
    )
    msgs = [{"role": "user", "content": prompt}]
    cfg = load_cloud()
    if cfg.get("enabled") and cfg.get("url"):
        try:
            out = cloud_chat(msgs, cfg, predict=80)
            if out:
                return out.strip().replace("\n", " ")[:300]
        except Exception:
            pass
    try:
        out = ollama_chat(msgs, predict=80, timeout=25)
        if out:
            return out.strip().replace("\n", " ")[:300]
    except Exception:
        pass
    return ""


def reply_body(text):
    """Jarvis's own reply towards the received message."""
    body = _brain_reply(text)
    if not body:
        body = _heuristic_reply(text)
    body = re.sub(r"^jarvis\s*[:;,-]\s*", "", body, flags=re.I)
    return body.strip()


def reply_for(text, count=1):
    """
    Build the auto-reply for message number `count` (1-based).

        1      -> the exact first message Boss specified
        2, 3   -> holding lines
        4 and up -> "Jarvis; <reply to the message>"
    """
    try:
        n = int(count)
    except Exception:
        n = 1

    if n <= 1:
        return FIRST_MESSAGE
    if n in (2, 3):
        return HOLDING_LINES[n - 2]
    return PREFIX + reply_body(text)


def handle(text, count=1):
    """Alias kept for older call sites."""
    return reply_for(text, count)


def is_first(count):
    return int(count or 1) <= 1


# --------------------------------------------------------------- instagram bit
def open_instagram_with_warning():
    """Open Instagram with a warning that it is best avoided unless necessary."""
    import webbrowser
    webbrowser.open("https://www.instagram.com")
    return "Instagram opened. Best advised not to use unless necessary, Boss."


# --------------------------------------------------------------- cloud bridge
class CloudBridge:
    """
    Talks to Boss's OWN phone endpoint (or a relay he controls).

    Expected, minimal contract - any tiny phone app can serve it:
        GET  <url>/pending?token=<token>   -> {"messages": [{"id":..,"from":..,"text":..}]}
        POST <url>/reply                   -> {"to":..,"text":..,"token":..}
        POST <url>/ack                     -> {"id":..,"token":..}

    The token is the pairing token stored in cloud.json, so only Boss's own
    phone is ever answered.
    """

    def __init__(self, cfg=None):
        if cfg is None:
            from jarvis_config import load_cloud
            cfg = load_cloud()
        self.cfg = dict(cfg or {})
        self.url = (self.cfg.get("url") or "").rstrip("/")
        self.token = self.cfg.get("token") or ""
        self.key = self.cfg.get("key") or ""
        self.enabled = bool(self.cfg.get("enabled") and self.url and self.token)

    def _headers(self):
        h = {"Content-Type": "application/json"}
        if self.key:
            h["Authorization"] = "Bearer " + self.key
        return h

    def _call(self, path, payload=None, timeout=12):
        if not self.url:
            return None
        data = None
        if payload is not None:
            payload = dict(payload)
            payload.setdefault("token", self.token)
            data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.url + path, data=data,
                                     headers=self._headers(),
                                     method="POST" if data else "GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read().decode("utf-8", "ignore")
            return json.loads(raw) if raw.strip() else {}
        except Exception:
            return None

    def pending(self):
        if not self.enabled:
            return []
        d = self._call("/pending?token=" + urllib.request.quote(self.token))
        if not isinstance(d, dict):
            return []
        msgs = d.get("messages") or []
        return [m for m in msgs if isinstance(m, dict)]

    def send(self, to, text):
        if not self.enabled:
            return False
        return self._call("/reply", {"to": to, "text": text}) is not None

    def ack(self, mid):
        if not self.enabled:
            return False
        return self._call("/ack", {"id": mid}) is not None

    def run_forever(self, on_reply=None, stop_flag=None, interval=4.0):
        """Poll the phone, answer while DND is on, acknowledge each message."""
        import time
        count = 0
        while not (stop_flag and stop_flag()):
            for m in self.pending():
                count += 1
                text = m.get("text", "")
                out = reply_for(text, count)
                ok = self.send(m.get("from", ""), out)
                if ok:
                    self.ack(m.get("id"))
                if on_reply:
                    try:
                        on_reply(m.get("from", ""), out)
                    except Exception:
                        pass
            time.sleep(interval)
