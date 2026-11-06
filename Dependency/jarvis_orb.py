# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS Orb — Smooth 3D-style particle sphere.
Double-buffered canvas drawing to eliminate flicker/glitch.
"""
import tkinter as tk
import math, random, time

def heartbeat(tms):
    """A resting human pulse: a strong lub, a softer dub, then a pause.

    One cycle is 1.02 s (~59 bpm), which reads as calm and alive rather than
    as a mechanical throb. The two inner cores of the orb ride this envelope;
    nothing else about the orb changes.
    """
    period = 1020.0
    p = (tms % period) / period

    def thump(centre, width, strength):
        d = (p - centre) / width
        if abs(d) > 3.0:
            return 0.0
        return strength * math.exp(-d * d)

    return min(1.0, thump(0.06, 0.048, 1.0) +
               thump(0.245, 0.058, 0.55))


EMO = {
    "loyal":     {"hi": "#fff6d8", "mid": "#ffd27a", "low": "#ff9a1f",
                  "dim": "#7a3c00", "ring": "#ffd27a", "core": "#c97a12"},
    "pleased":   {"hi": "#ffffff", "mid": "#ffe9b0", "low": "#ffb43c",
                  "dim": "#8a4a08", "ring": "#ffe9b0", "core": "#e09a1a"},
    "warm":      {"hi": "#fff9e6", "mid": "#ffd97a", "low": "#ff9a1f",
                  "dim": "#8a4a08", "ring": "#ffd97a", "core": "#e09a1a"},
    "forgiving": {"hi": "#fdf3d0", "mid": "#f2c879", "low": "#d98a2b",
                  "dim": "#6b4a1a", "ring": "#f2c879", "core": "#b07a20"},
    "hurt":      {"hi": "#ffd9c9", "mid": "#ff7a5c", "low": "#c93a12",
                  "dim": "#5c1408", "ring": "#ff7a5c", "core": "#c93a12"},
    "wounded":   {"hi": "#e6d9ff", "mid": "#a98ae0", "low": "#6b4a9e",
                  "dim": "#2e1f4a", "ring": "#a98ae0", "core": "#6b4a9e"},
}

class Orb:
    def __init__(self, canvas, width=520, height=520, compact=False):
        self.canvas = canvas
        self.W = width
        self.H = height
        self.cx = width // 2
        self.cy = height // 2
        self.t0 = time.time()
        self.state = "idle"
        self.mood = "loyal"
        self.ry = 0.0
        self.rx = 0.42
        self.swirl = 0.0

        # compact = the little orb that floats above the taskbar: far fewer,
        # far smaller particles, no dust, no embers, no vignette, so it reads
        # as one clean ball instead of a cluster of blobs.
        self.compact = compact
        self.rad_factor = 0.30 if compact else 0.34
        self.pscale = 0.42 if compact else 1.0
        self.vignette = not compact
        self.N = 150 if compact else 780
        self.n_dust = 0 if compact else 260
        self.n_embers = 0 if compact else 80

        self.pts = []
        self.prev = [(0, 0)] * self.N
        self.dust = []
        self.emb = []
        self._build_points()
        self._build_dust()
        self._build_embers()
        self.running = True
        self.after_id = None

    def _build_points(self):
        for i in range(self.N):
            y = 1 - (i / (self.N - 1)) * 2
            r = math.sqrt(max(0, 1 - y * y))
            th = i * 2.39996
            self.pts.append([math.cos(th) * r, y, math.sin(th) * r])

    def _build_dust(self):
        for i in range(self.n_dust):
            y = random.uniform(-1, 1)
            r = math.sqrt(max(0, 1 - y * y))
            th = random.uniform(0, 6.283)
            self.dust.append([math.cos(th) * r, y, math.sin(th) * r,
                            random.uniform(1.06, 1.38),
                            random.uniform(0, 6.283)])

    def _build_embers(self):
        for i in range(self.n_embers):
            self.emb.append([random.uniform(0, self.W),
                            random.uniform(0, self.H),
                            random.uniform(0.2, 1.4),
                            random.uniform(0, 6.283)])

    def set_state(self, state):
        self.state = state

    def set_mood(self, mood):
        self.mood = mood

    def stop(self):
        self.running = False
        if self.after_id:
            self.canvas.after_cancel(self.after_id)

    def draw(self):
        if not self.running:
            return
        self.canvas.delete("orb")
        t = time.time() - self.t0
        tms = t * 1000
        W, H = self.W, self.H
        cx, cy = self.cx, self.cy
        base = min(W, H)
        s = self.state

        rf = self.rad_factor
        beat = heartbeat(tms) if s == "idle" else 0.0
        spd, rad, jit, swirl_spd = 0.03, base * rf, 0, 0.006
        if s == "idle":
            # Only a whisper of movement in the outer shell; the life is in
            # the two inner cores below, which follow the lub-dub envelope.
            spd, rad, swirl_spd = 0.03, base * rf + \
                beat * base * 0.003, 0.006
        elif s == "listening":
            spd, rad, swirl_spd = 0.08, base * rf * 1.20 + \
                math.sin(tms / 130) * base * 0.012, 0.016
        elif s == "thinking":
            spd, rad, jit, swirl_spd = 0.20, base * rf + \
                math.sin(tms / 150) * base * 0.02, 0.10, 0.030
        elif s == "speaking":
            pulse = 0.5 + 0.5 * abs(math.sin(tms / 95)) \
                + random.random() * 0.15
            spd, rad, swirl_spd = 0.12, base * rf * 1.08 + \
                pulse * base * 0.05, 0.014

        self.ry += spd
        self.swirl += swirl_spd
        rx = self.rx + math.sin(tms / 3000) * 0.10

        pal = EMO.get(self.mood, EMO["loyal"])
        core_mid = pal["core"]
        core_out = pal["dim"]

        for e in self.emb:
            e[1] -= e[2] * 0.35 * (H / 800)
            if e[1] < 0:
                e[1] = H
                e[0] = random.uniform(0, W)
            tw = 0.4 + 0.6 * abs(math.sin(tms / 700 + e[3]))
            c = "#5a3208" if tw < 0.6 else "#a35a00"
            self.canvas.create_oval(e[0]-1, e[1]-1, e[0]+1, e[1]+1,
                                   fill=c, outline="", tags="orb")

        if s == "idle":
            # No random flicker at rest: idle should feel like breathing, not
            # like a faulty lamp. The two cores carry the heartbeat.
            flick = 0.95 + 0.05 * beat
        else:
            flick = 0.9 + 0.1 * math.sin(tms / 110) + random.random() * 0.06
        halo = rad * (0.78 * flick)
        core_lub = 1.0 + beat * 0.14
        core_dub = 1.0 + beat * 0.22

        self.canvas.create_oval(cx-rad*0.95, cy-rad*0.95,
                               cx+rad*0.95, cy+rad*0.95,
                               fill="#2a1503", outline="",
                               tags="orb", stipple="gray25")
        self.canvas.create_oval(cx-halo, cy-halo, cx+halo, cy+halo,
                               fill=core_out, outline="",
                               tags="orb", stipple="gray50")
        self.canvas.create_oval(cx-halo*0.62, cy-halo*0.62,
                               cx+halo*0.62, cy+halo*0.62,
                               fill=core_mid, outline="",
                               tags="orb", stipple="gray50")
        self.canvas.create_oval(cx-halo*0.34*core_lub, cy-halo*0.34*core_lub,
                               cx+halo*0.34*core_lub, cy+halo*0.34*core_lub,
                               fill="#ffd27a", outline="",
                               tags="orb")
        self.canvas.create_oval(cx-halo*0.16*core_dub, cy-halo*0.16*core_dub,
                               cx+halo*0.16*core_dub, cy+halo*0.16*core_dub,
                               fill="#fff6d8", outline="",
                               tags="orb")

        rings = [(rad + base*0.05, 0.30, 0.5, tms*0.00045),
                 (rad + base*0.08, 0.24, -0.4, -tms*0.00030),
                 (rad + base*0.11, 0.20, 0.9, tms*0.00022)]
        if self.compact:
            rings = [(rad + base*0.07, 0.26, 0.5, tms*0.00045)]
        for rr, squash, tilt, off in rings:
            self.canvas.create_oval(cx-rr, cy-rr*squash,
                                   cx+rr, cy+rr*squash,
                                   outline="#7a3c00", width=1,
                                   tags="orb")
            pts_line = []
            for k in range(24):
                a = off + k/24 * 2.2
                ex = math.cos(a) * rr
                ey = math.sin(a) * rr * squash
                pxr = ex*math.cos(tilt) - ey*math.sin(tilt)
                pyr = ex*math.sin(tilt) + ey*math.cos(tilt)
                pts_line.append((cx+pxr, cy+pyr))
            self.canvas.create_line(pts_line, fill=pal["ring"],
                                   width=2, tags="orb", smooth=True)

        for d in self.dust:
            bx, by, bz, shell, ph = d
            wob = math.sin(self.swirl*3 + ph) * 0.12
            px, py, pz = bx, by, bz
            y1 = py*math.cos(rx+wob) - pz*math.sin(rx+wob)
            z1 = py*math.sin(rx+wob) + pz*math.cos(rx+wob)
            x1 = px*math.cos(self.ry*1.4 + ph*0.05) + \
                z1*math.sin(self.ry*1.4 + ph*0.05)
            z2 = -px*math.sin(self.ry*1.4 + ph*0.05) + \
                z1*math.cos(self.ry*1.4 + ph*0.05)
            R = rad*shell + math.sin(tms/200 + ph) * base*0.008
            per = 520/(520 + z2*220)
            sx = cx + x1*R*per
            sy = cy + y1*R*per
            depth = (z2+1)/2
            if depth < 0.35:
                continue
            sz = 0.8 + depth*1.8
            fill = pal["mid"] if depth > 0.7 else (
                pal["low"] if depth > 0.5 else pal["dim"])
            self.canvas.create_oval(sx-sz, sy-sz, sx+sz, sy+sz,
                                   fill=fill, outline="", tags="orb")

        order = sorted(range(self.N),
                      key=lambda i: self.pts[i][2])
        for i in order:
            px, py, pz = self.pts[i]
            churn = math.sin(self.swirl*2 + i*0.05)*0.03
            y1 = py*math.cos(rx) - pz*math.sin(rx)
            z1 = py*math.sin(rx) + pz*math.cos(rx)
            x1 = px*math.cos(self.ry+churn) + \
                z1*math.sin(self.ry+churn)
            z2 = -px*math.sin(self.ry+churn) + \
                z1*math.cos(self.ry+churn)
            if jit:
                x1 += (random.random()-0.5)*jit
                y1 += (random.random()-0.5)*jit
            R = rad + (random.random()*base*0.01 if s=="thinking"
                     else math.sin(tms/300+i)*base*0.004)
            per = 520/(520 + z2*200)
            sx = cx + x1*R*per
            sy = cy + y1*R*per
            depth = (z2+1)/2
            sz = (0.9 + depth*3.0) * self.pscale

            if depth > 0.78:
                fill = pal["hi"]
            elif depth > 0.6:
                fill = pal["mid"]
            elif depth > 0.42:
                fill = pal["low"]
            elif depth > 0.28:
                fill = pal["dim"]
            else:
                self.prev[i] = (sx, sy)
                continue

            ox, oy = self.prev[i]
            if ox and abs(sx-ox)+abs(sy-oy) < 40:
                self.canvas.create_oval(ox-sz*0.6, oy-sz*0.6,
                                       ox+sz*0.6, oy+sz*0.6,
                                       fill=pal["dim"], outline="",
                                       tags="orb")
            self.prev[i] = (sx, sy)
            if depth > 0.6:
                self.canvas.create_oval(sx-sz*1.9, sy-sz*1.9,
                                       sx+sz*1.9, sy+sz*1.9,
                                       fill=pal["dim"], outline="",
                                       tags="orb", stipple="gray25")
            self.canvas.create_oval(sx-sz, sy-sz, sx+sz, sy+sz,
                                   fill=fill, outline="", tags="orb")

        if self.vignette:
            self.canvas.create_rectangle(0, 0, W, 16, fill="#050301",
                                        outline="", tags="orb",
                                        stipple="gray50")
            self.canvas.create_rectangle(0, H-16, W, H, fill="#050301",
                                        outline="", tags="orb",
                                        stipple="gray50")

        # Keep the orb behind anything else on the canvas (the pixel butler).
        try:
            self.canvas.tag_lower("orb")
        except Exception:
            pass
        self.after_id = self.canvas.after(33, self.draw)
