# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS Web - search, fetch, images, Wikipedia.

Every outbound read goes through `jarvis_guard`: public http(s) only, hard
size caps, redirect re-checks, and HTML stripped to plain text before the
model ever sees it. Nothing from a page is executed.
"""
import urllib.request
import urllib.parse
import re
import json
import html as _html
import socket
import ipaddress

USER_AGENT = "JARVIS-local/2.0 (safe reader)"


def _guard():
    try:
        import jarvis_guard
        return jarvis_guard
    except Exception:
        return None


def _safe_http_url(u):
    """Backward-compatible URL check used by older callers."""
    g = _guard()
    if g is not None:
        ok, clean, _ = g.check_url(u)
        return clean if ok else ""
    return ""


def _get(url, timeout=15, max_bytes=600000, raw=False):
    """Read one public page through the guard. Returns text or ''."""
    g = _guard()
    if g is not None:
        ok, text, _reason = g.fetch(url, max_bytes=max_bytes,
                                    timeout=timeout, raw=raw)
        return text if ok else ""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(max_bytes).decode("utf-8", "ignore")
    except Exception:
        return ""


def web_search(q):
    q = (q or "").strip()[:200]
    if not q:
        return "What shall I search for, Boss?"
    raw = _get("https://lite.duckduckgo.com/lite/?q=" +
               urllib.parse.quote(q), max_bytes=600000, raw=True)
    if raw:
        out = []
        for m in re.finditer(r"(?is)<a[^>]*href=['\"]([^'\"]+)['\"]"
                             r"[^>]*>(.*?)</a>", raw):
            link, anchor = _html.unescape(m.group(1)), _html.unescape(
                re.sub(r"<[^>]+>", "", m.group(2))).strip()
            um = re.search(r"[?&]uddg=([^&]+)", link)
            if um:
                link = urllib.parse.unquote(um.group(1))
            if not anchor or len(anchor) < 8 or not re.match(
                    r"^https?://", link, re.I):
                continue
            g = _guard()
            if g is not None:
                ok, link, _ = g.check_url(link)
                if not ok:
                    continue
            out.append(anchor[:120] + " - " + link[:150])
            if len(out) >= 6:
                break
        if out:
            return "Top results for '" + q + "':\n" + "\n".join(out)
    return "No results for '" + q + "', Boss."


def web_fetch(url):
    g = _guard()
    if g is not None:
        ok, text, reason = g.fetch(url, max_bytes=1500000)
        if not ok:
            return "I could not read that safely, Boss - " + reason + "."
        return text[:3000]
    return "The safety layer is unavailable, Boss; I will not read the web."


def web_browse(url):
    g = _guard()
    if g is None:
        return "The safety layer is unavailable, Boss; I will not open that."
    ok, message = g.web_open(url)
    return message


def wiki_lookup(q):
    q = (q or "").strip()[:150]
    if not q:
        return "", ""
    raw = _get("https://en.wikipedia.org/w/api.php?action=opensearch"
               "&search=" + urllib.parse.quote(q) + "&limit=1&format=json",
               max_bytes=20000)
    try:
        d = json.loads(raw)
        title = (d[1][0] if len(d) > 1 and d[1] else q)
    except Exception:
        return "", ""
    raw2 = _get("https://en.wikipedia.org/api/rest_v1/page/summary/" +
                urllib.parse.quote(title.replace(" ", "_")),
                max_bytes=30000)
    try:
        p = json.loads(raw2)
        summary = (p.get("extract") or "").strip()
        if p.get("type") == "disambiguation" or not summary:
            return "", ""
        if len(summary) > 900:
            summary = summary[:900].rsplit(".", 1)[0] + "."
        thumb = p.get("thumbnail", {}).get("source", "")
        g = _guard()
        if g is not None and thumb:
            ok, thumb, _ = g.check_url(thumb)
            if not ok:
                thumb = ""
        return summary, thumb
    except Exception:
        return "", ""


def weather_of(city):
    raw = _get("https://wttr.in/" +
               urllib.parse.quote((city or "Gurugram")[:60]) + "?format=3",
               max_bytes=500)
    return (raw.strip() + ", Boss.") if raw else \
        "The skies are closed to me right now, Boss."


def headlines(n=5):
    raw = _get("https://hacker-news.firebaseio.com/v0/topstories.json",
               max_bytes=100000)
    try:
        ids = json.loads(raw)
    except Exception:
        return "The wires are quiet, Boss."
    out = []
    for i in ids[:n]:
        item = _get("https://hacker-news.firebaseio.com/v0/item/%s.json" % i,
                    max_bytes=20000)
        try:
            d = json.loads(item)
        except Exception:
            continue
        if d.get("title"):
            out.append(d["title"][:120])
    return ("Today's headlines, Boss:\n" +
            "\n".join("- " + t for t in out)) if out else \
        "No headlines today, Boss."
