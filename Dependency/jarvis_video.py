# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS Video Generation - readable source module.
Generates AI video clips via Pollinations API (free tier).
Decrypted at runtime by jarvis_loader.py.
"""
import urllib.request, urllib.parse, os, time
from jarvis_config import IMG_CACHE

def generate_video_clips(topic, count=5):
    paths = []
    os.makedirs(IMG_CACHE, exist_ok=True)
    for i in range(count):
        q = urllib.parse.quote(f"{topic}, cinematic shot {i+1}, vertical video")
        url = f"https://gen.pollinations.ai/video/{q}?model=wan-fast&duration=4&aspectRatio=9:16"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JARVIS-local/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if len(data) > 50000:
                p = os.path.join(IMG_CACHE, f"vid_{int(time.time())+i}.mp4")
                with open(p, "wb") as f:
                    f.write(data)
                paths.append(p)
        except Exception:
            pass
    return paths
