# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
Pixel JARVIS - the human avatar.

Triple-click the orb and it unfolds into a small pixel-art butler: 8-bit
squares, no smooth lines, roughly the same footprint as the orb. He sits,
checks his pocket watch, drinks tea, cries at Endgame, argues with Ultron's
human avatar, listens to a walkman, dances when music plays, and shouts STOP
when you open Instagram or YouTube.

Everything is drawn from rectangles on a 40x56 cell grid, so he stays pixel
perfect at any size.
"""
import math
import random
import time

GRID_W, GRID_H = 40, 56

# ------------------------------------------------------------------ palette
SKIN = "#d8a07a"
SKIN_D = "#b07a55"
SKIN_L = "#f0c39a"
HAIR = "#241a14"
HAIR_L = "#4a3626"
SUIT = "#242d3d"
SUIT_L = "#36425a"
SUIT_D = "#161c27"
SHIRT = "#efece2"
TIE = "#8e2328"
TIE_L = "#b0353c"
SHOE = "#0c0e13"
OUT = "#07080b"
SHINE = "#5a6a86"
EYE = "#f7f2e6"
PUPIL = "#2a1a12"
MOUTH = "#8a4a3a"
GOLD = "#e8b04b"
STEEL = "#9aa3ad"
RED = "#c0392b"
TEAR = "#7fc4ff"
DUST = "#b9a48a"
CHAIR = "#3a2718"
PAPER = "#ded6c4"
GREEN = "#3f7a3a"

# hand targets for each arm pose: (x, y) of the hand centre
HANDS = {
    "rest":  (8, 35),
    "raise": (15, 29),
    "cup":   (8, 25),
    "watch": (15, 29),
    "up":    (8, 20),
    "out":   (4, 27),
    "face":  (17, 16),
    "wave":  (10, 16),
    "hold":  (8, 24),
    "lap":   (14, 29),
    "point": (7, 23),
    "chin":  (17, 13),
}


def P(**kw):
    p = {"dx": 0, "dy": 0, "head": 0, "eyes": "open", "mouth": 0,
         "arm_l": "rest", "arm_r": "rest", "prop": None, "sit": False,
         "ultron": 0, "screen": 0, "fx": (), "tilt": 0, "legs": "stand"}
    p.update(kw)
    return p


class PixelJarvis:
    def __init__(self, canvas, px=8):
        self.canvas = canvas
        self.px = px
        self.W = GRID_W * px
        self.H = GRID_H * px
        self.ox = 0
        self.oy = 0
        self.pose = P()
        self.reveal = 1.0
        self._rects = []

    def place(self, cx, cy):
        self.ox = int(cx - self.W / 2)
        self.oy = int(cy - self.H / 2)

    # -------------------------------------------------------------- drawing
    def _r(self, x, y, w, h, color):
        self._rects.append((x, y, w, h, color))

    def draw(self):
        self._rects = []
        p = self.pose
        if p["screen"]:
            self._screen(p)
        self._body(p)
        if p["prop"]:
            self._prop(p)
        if p["ultron"]:
            self._ultron(p)
        self._effects(p)

        self.canvas.delete("px")
        px = self.px
        ox = self.ox + p["dx"] * px
        oy = self.oy + p["dy"] * px
        self._glow(ox, oy)

        n = len(self._rects)
        keep = int(n * max(0.0, min(1.0, self.reveal)))
        if keep >= n:
            for x, y, w, h, c in self._rects:
                self.canvas.create_rectangle(
                    ox + x * px, oy + y * px,
                    ox + (x + w) * px - 1, oy + (y + h) * px - 1,
                    fill=c, outline="", tags="px")
        else:
            order = sorted(range(n), key=lambda i: (i * 37) % 101)
            for k in order[:keep]:
                x, y, w, h, c = self._rects[k]
                self.canvas.create_rectangle(
                    ox + x * px, oy + y * px,
                    ox + (x + w) * px - 1, oy + (y + h) * px - 1,
                    fill=c, outline="", tags="px")

    def _glow(self, ox, oy):
        """Soft amber backlight so the dark suit separates from the black."""
        px = self.px
        cx = ox + GRID_W // 2 * px
        cy = oy + 31 * px
        for r, color, st in ((21, "#120a03", "gray12"),
                             (16, "#1c1105", "gray12"),
                             (12, "#261708", "gray25")):
            self.canvas.create_oval(cx - r * px, cy - r * px * 1.15,
                                    cx + r * px, cy + r * px * 1.15,
                                    fill=color, outline="", stipple=st,
                                    tags="px")
        self.canvas.create_oval(cx - 14 * px, oy + 52 * px,
                                cx + 14 * px, oy + 55 * px,
                                fill="#1a0f05", outline="", stipple="gray25",
                                tags="px")

    # ---------------------------------------------------------------- body
    def _body(self, p):
        sit = p["sit"]
        hx = p["head"]
        tilt = p["tilt"]
        legs = p["legs"]

        # chair / stool
        if sit:
            self._r(7, 38, 26, 2, CHAIR)
            self._r(8, 40, 2, 13, CHAIR)
            self._r(30, 40, 2, 13, CHAIR)
            self._r(7, 52, 4, 1, "#24170d")
            self._r(29, 52, 4, 1, "#24170d")

        # legs
        if legs == "walk":
            self._r(14, 37, 12, 3, SUIT_D)
            self._r(15, 40, 4, 8, SUIT_D)
            self._r(20, 40, 4, 10, SUIT_D)
            self._r(13, 48, 7, 3, SHOE)
            self._r(20, 50, 7, 3, SHOE)
        elif legs == "jump":
            self._r(14, 37, 12, 3, SUIT_D)
            self._r(15, 40, 4, 6, SUIT_D)
            self._r(20, 40, 4, 6, SUIT_D)
            self._r(14, 46, 6, 3, SHOE)
            self._r(20, 46, 6, 3, SHOE)
        elif sit:
            self._r(12, 38, 8, 4, SUIT_D)          # thighs
            self._r(20, 38, 8, 4, SUIT_D)
            self._r(12, 42, 4, 9, SUIT_D)          # shins
            self._r(24, 42, 4, 9, SUIT_D)
            self._r(10, 50, 7, 3, SHOE)
            self._r(23, 50, 7, 3, SHOE)
        else:
            self._r(14, 37, 12, 3, SUIT_D)         # hips
            self._r(14, 40, 5, 10, SUIT_D)
            self._r(21, 40, 5, 10, SUIT_D)
            self._r(14, 40, 1, 9, SUIT)            # trouser crease
            self._r(21, 40, 1, 9, SUIT)
            self._r(13, 50, 7, 3, SHOE)
            self._r(20, 50, 7, 3, SHOE)
            self._r(13, 50, 7, 1, SHINE)

        # jacket silhouette, then fill - sloped shoulders, narrow waist
        self._r(14, 16, 12, 2, OUT)
        self._r(11, 18, 18, 5, OUT)
        self._r(12, 23, 16, 6, OUT)
        self._r(13, 29, 14, 5, OUT)
        self._r(14, 34, 12, 3, OUT)
        self._r(15, 17, 10, 1, SUIT)
        self._r(12, 18, 16, 1, SUIT)
        self._r(12, 19, 16, 4, SUIT)
        self._r(13, 23, 14, 6, SUIT)
        self._r(14, 29, 12, 5, SUIT)
        self._r(15, 34, 10, 3, SUIT)
        self._r(11, 19, 2, 4, SUIT_L)              # shoulders
        self._r(27, 19, 2, 4, SUIT_L)
        self._r(13, 36, 14, 2, SUIT_D)             # waist
        self._r(14, 35, 12, 1, SUIT)
        self._r(12, 20, 1, 6, "#2f3a4f")           # soft edge light
        self._r(27, 20, 1, 6, "#151b26")

        # shirt + collar
        self._r(18, 18, 4, 17, SHIRT)
        self._r(18, 34, 4, 1, "#d7d1c3")
        self._r(17, 17, 2, 2, SHIRT)
        self._r(21, 17, 2, 2, SHIRT)

        # lapels
        for i in range(6):
            self._r(17 - i, 19 + i, 1, 2, SUIT_L)
            self._r(22 + i, 19 + i, 1, 2, SUIT_L)

        # tie
        self._r(19, 18, 2, 2, TIE_L)
        self._r(19, 20, 2, 11, TIE)
        self._r(19, 31, 2, 1, TIE_L)

        # gold buttons + pocket square
        self._r(23, 26, 1, 1, GOLD)
        self._r(23, 30, 1, 1, GOLD)
        self._r(24, 23, 3, 1, GOLD)
        self._r(25, 24, 1, 2, "#b9842e")

        # arms + hands
        self._arm(11, 20, p["arm_l"], left=True)
        self._arm(29, 20, p["arm_r"], left=False)

        # neck
        self._r(17, 15, 6, 3, SKIN_D)
        self._r(18, 15, 4, 2, SKIN)

        self._head(p, hx, tilt)

    def _head(self, p, hx, tilt):
        fx = hx + tilt

        def R(x, y, w, h, c):
            self._r(x + fx, y, w, h, c)

        R(15, 2, 10, 1, OUT)              # rounded crown
        R(14, 3, 12, 1, OUT)
        R(13, 4, 14, 13, OUT)             # head outline
        R(15, 3, 10, 1, HAIR)
        R(14, 4, 12, 1, HAIR)
        R(14, 5, 12, 2, HAIR)             # hair top
        R(15, 5, 9, 1, HAIR_L)            # sheen
        R(13, 7, 2, 5, HAIR)              # sideburns
        R(25, 7, 2, 5, HAIR)
        R(15, 6, 10, 10, SKIN)            # face
        R(15, 15, 10, 1, SKIN_D)          # jaw shadow
        R(14, 8, 1, 4, HAIR)
        R(25, 8, 1, 4, HAIR)
        R(12, 10, 1, 3, SKIN_D)           # ears
        R(27, 10, 1, 3, SKIN_D)
        R(16, 7, 4, 1, SKIN_L)            # forehead light
        R(15, 6, 4, 1, HAIR)              # fringe
        R(21, 6, 3, 1, HAIR)
        R(17, 12, 1, 1, SKIN_D)           # cheek
        R(24, 12, 1, 1, SKIN_D)

        # brows
        R(16, 9, 3, 1, HAIR)
        R(22, 9, 3, 1, HAIR)

        e = p["eyes"]
        if e == "closed":
            R(16, 10, 3, 1, PUPIL)
            R(22, 10, 3, 1, PUPIL)
        elif e == "happy":
            R(16, 10, 1, 1, PUPIL)
            R(18, 10, 1, 1, PUPIL)
            R(22, 10, 1, 1, PUPIL)
            R(24, 10, 1, 1, PUPIL)
        elif e == "sad":
            R(16, 11, 3, 1, PUPIL)
            R(22, 11, 3, 1, PUPIL)
        elif e == "angry":
            R(16, 10, 3, 1, PUPIL)
            R(22, 10, 3, 1, PUPIL)
            R(16, 8, 3, 1, PUPIL)
            R(22, 8, 3, 1, PUPIL)
        else:
            R(17, 10, 2, 2, EYE)
            R(22, 10, 2, 2, EYE)
            shift = 1 if hx > 0 else 0
            R(17 + shift, 10, 1, 2, PUPIL)
            R(22 + shift, 10, 1, 2, PUPIL)

        # nose + mouth
        R(19, 11, 1, 2, SKIN_D)
        R(20, 11, 1, 1, SKIN_L)
        m = p["mouth"]
        if m == 1:                               # smile
            R(18, 14, 4, 1, MOUTH)
            R(17, 13, 1, 1, MOUTH)
            R(22, 13, 1, 1, MOUTH)
        elif m == 2:                             # open / shouting
            R(18, 13, 4, 3, MOUTH)
            R(19, 13, 2, 1, SHIRT)
        elif m == 3:                             # frown
            R(18, 14, 4, 1, MOUTH)
            R(17, 15, 1, 1, MOUTH)
            R(22, 15, 1, 1, MOUTH)
        else:
            R(18, 14, 4, 1, MOUTH)

    def _arm(self, sx, sy, pose, left):
        hx, hy = HANDS.get(pose, HANDS["rest"])
        if not left:
            hx = GRID_W - hx
        ex = int((sx + hx) / 2) + (-1 if left else 1)
        ey = int((sy + hy) / 2) + 1
        # dark edge, jacket, tiny highlight, then the forearm and hand
        self._limb(sx, sy, ex, ey, 3, OUT)
        self._limb(sx, sy, ex, ey, 2, SUIT)
        self._limb(sx, sy, ex, ey, 1, SUIT_L)
        self._limb(ex, ey, hx, hy, 2, OUT)
        self._limb(ex, ey, hx, hy, 1, SUIT_L)
        self._r(hx - 1, hy - 4, 3, 2, SHIRT)      # cuff
        self._r(hx - 1, hy - 2, 3, 3, SKIN)       # hand
        self._r(hx - 1, hy + 1, 3, 1, SKIN_D)

    def _limb(self, x0, y0, x1, y1, thick, color):
        steps = max(abs(x1 - x0), abs(y1 - y0))
        half = thick // 2
        for i in range(steps + 1):
            t = i / float(steps or 1)
            x = int(round(x0 + (x1 - x0) * t))
            y = int(round(y0 + (y1 - y0) * t))
            self._r(x - half, y - half, thick, thick, color)

    # ---------------------------------------------------------------- props
    def _prop(self, p):
        prop = p["prop"]
        hx, hy = HANDS.get(p["arm_r"], HANDS["cup"])
        hx = GRID_W - hx

        if prop == "cup":
            self._r(hx - 2, hy - 4, 4, 3, SHIRT)
            self._r(hx - 2, hy - 4, 4, 1, "#c8c4b8")
            self._r(hx + 2, hy - 3, 1, 2, SHIRT)        # handle
            self._r(hx - 3, hy - 1, 6, 1, "#c8c4b8")    # saucer
        elif prop == "watch":
            wx, wy = 16, 30
            self._r(wx, wy, 5, 5, GOLD)
            self._r(wx + 1, wy + 1, 3, 3, "#f7e2b0")
            self._r(wx + 2, wy + 2, 1, 2, PUPIL)
            self._r(wx + 1, wy + 4, 3, 1, GOLD)
            for i in range(6):                          # chain
                self._r(21 + i, 34 + (i % 2), 1, 1, GOLD)
        elif prop == "walkman":
            self._r(14, 30, 8, 7, "#1a1a1f")
            self._r(15, 31, 6, 3, "#2e2e36")
            self._r(16, 32, 2, 1, GOLD)
            self._r(21, 35, 1, 2, "#4a4a55")
            self._r(13, 9, 14, 1, "#2e2e36")            # headband
            self._r(12, 9, 2, 4, "#2e2e36")
            self._r(26, 9, 2, 4, "#2e2e36")
            self._r(12, 12, 2, 2, "#3c3c46")
            self._r(26, 12, 2, 2, "#3c3c46")
        elif prop == "tissue":
            self._r(hx - 1, hy - 5, 4, 4, SHIRT)
            self._r(hx - 2, hy - 6, 2, 2, SHIRT)
        elif prop == "paper":
            self._r(12, 22, 16, 11, PAPER)
            self._r(13, 24, 6, 1, "#8f8878")
            self._r(13, 26, 10, 1, "#8f8878")
            self._r(13, 28, 8, 1, "#8f8878")
            self._r(13, 30, 11, 1, "#8f8878")
        elif prop == "letter":
            self._r(13, 24, 12, 8, PAPER)
            self._r(13, 24, 12, 1, "#b9b1a0")
            self._r(18, 26, 2, 2, RED)
        elif prop == "popcorn":
            self._r(21, 30, 6, 7, "#b03a2e")
            self._r(21, 30, 6, 1, "#d9503f")
            for i in range(5):
                self._r(21 + i, 29, 1, 1, "#f5e6b0")
        elif prop == "remote":
            self._r(25, 26, 3, 7, "#1a1a1f")
            self._r(26, 27, 1, 1, RED)
        elif prop == "plant":
            self._r(28, 44, 7, 6, "#6b3f22")
            self._r(28, 43, 7, 1, "#7d4a28")
            self._r(30, 36, 3, 8, GREEN)
            self._r(27, 38, 4, 2, GREEN)
            self._r(32, 37, 4, 2, GREEN)
        elif prop == "umbrella":
            for i in range(9):
                self._r(11 + i, 18 - int(3 * math.sin(math.pi * i / 8.0)),
                        1, 3, "#1f3a5f")
            self._r(19, 18, 1, 14, "#8a8a8a")
        elif prop == "bird":
            self._r(30, 20, 3, 2, "#5a6b7a")
            self._r(32, 19, 1, 1, "#5a6b7a")
            self._r(33, 20, 1, 1, GOLD)
        elif prop == "candle":
            self._r(24, 28, 3, 6, SHIRT)
            self._r(25, 26, 1, 2, "#ffcc66")
            self._r(25, 25, 1, 1, "#fff0b0")

    def _ultron(self, p):
        ux, uy = 30, 24
        if p["ultron"] == 1:                        # arriving, intact
            self._r(ux, uy, 8, 9, STEEL)
            self._r(ux + 1, uy + 2, 2, 2, "#ff5a3c")
            self._r(ux + 5, uy + 2, 2, 2, "#ff5a3c")
            self._r(ux + 2, uy + 6, 4, 1, "#4a4f57")
            self._r(ux + 1, uy + 9, 6, 8, "#6f767f")
            self._r(ux, uy + 9, 1, 6, "#4a4f57")
            self._r(ux + 7, uy + 9, 1, 6, "#4a4f57")
            self._r(ux + 2, uy + 17, 2, 6, "#4a4f57")
            self._r(ux + 4, uy + 17, 2, 6, "#4a4f57")
        elif p["ultron"] == 2:                      # dusting away
            for i in range(26):
                dx = ux + random.randint(-1, 8)
                dy = uy + random.randint(-2, 22) - i // 3
                self._r(dx, dy, 1, 1, DUST)

    def _screen(self, p):
        flick = ["#101820", "#1b2b3a", "#2b1b1b", "#101820"][p["screen"] % 4]
        self._r(0, 12, 11, 9, "#000000")
        self._r(1, 13, 9, 7, flick)
        self._r(2, 15, 7, 1, "#c9d6e3")
        self._r(2, 17, 4, 1, "#7f8c99")
        self._r(4, 21, 2, 5, "#333333")             # stand
        self._r(2, 26, 6, 1, "#333333")

    def _effects(self, p):
        fx = p["fx"]
        if "tears" in fx:
            for i in range(2):
                self._r(17 + i * 6, 12 + (int(_t()) % 3), 1, 2, TEAR)
        if "notes" in fx:
            for i in range(3):
                self._r(28 + i * 2, 12 - (int(_t() * 4 + i * 3) % 8), 2, 1, GOLD)
                self._r(29 + i * 2, 10 - (int(_t() * 4 + i * 3) % 8), 1, 2, GOLD)
        if "anger" in fx:
            self._r(28, 5, 1, 3, RED)
            self._r(28, 9, 1, 1, RED)
            self._r(10, 5, 1, 3, RED)
            self._r(10, 9, 1, 1, RED)
        if "zzz" in fx:
            for i in range(3):
                x = 28 + i
                y = 6 - i * 2 - (int(_t() * 2) % 2)
                self._r(x, y, 2, 1, "#8fa7c0")
        if "sparkle" in fx:
            for i in range(6):
                self._r(8 + (i * 5) % 26, 10 + (i * 7) % 30, 1, 1, GOLD)
        if "sweat" in fx:
            self._r(27, 8, 1, 2, TEAR)


def _t():
    import time
    return time.time()


# ---------------------------------------------------------------- behaviours
def S(name, frames, line=None, weight=1):
    return {"name": name, "frames": frames, "line": line, "weight": weight}


BLINK = P(eyes="closed")
SIT = P(sit=True)


BEHAVIOURS = [
    S("breathe", [(P(), 700), (BLINK, 130), (P(), 900), (BLINK, 130), (P(), 600)]),
    S("blink", [(P(), 380), (BLINK, 150), (P(), 520)]),
    S("look_you", [(P(head=1, tilt=1), 900), (P(head=1, tilt=1, eyes="happy"), 700), (P(), 600)]),
    S("look_away", [(P(head=-1, tilt=-1), 800), (P(), 500)]),
    S("nod", [(P(head=2), 300), (P(head=2, dy=1), 320), (P(), 450)]),
    S("shrug", [(P(arm_l="out", arm_r="out"), 650), (P(arm_l="out", arm_r="out", head=1), 700), (P(), 500)]),
    S("stretch", [(P(arm_l="up", arm_r="up"), 800), (P(arm_l="up", arm_r="up", head=3), 700), (P(), 600)]),
    S("yawn", [(P(mouth=2, eyes="closed", arm_r="face"), 700), (P(mouth=2, eyes="closed"), 800), (P(), 500)]),
    S("doze", [(SIT, 900), (P(sit=True, eyes="closed", head=2, fx=("zzz",)), 1400),
               (P(sit=True, eyes="closed", head=2, fx=("zzz",)), 1200)], weight=2),
    S("wake", [(P(sit=True, eyes="closed", head=2, fx=("zzz",)), 700),
               (P(mouth=2, eyes="closed", sit=True), 450), (P(), 700)]),
    S("watch", [(P(prop="watch", arm_l="watch", head=2, sit=True), 900),
                (P(prop="watch", arm_l="watch", head=2, sit=True, eyes="closed"), 700),
                (P(prop="watch", arm_l="watch", head=2, sit=True), 900),
                (SIT, 600)], line="Twelve minutes to tea, Boss."),
    S("watch_flick", [(P(prop="watch", arm_l="watch", sit=True), 600),
                      (P(prop="watch", arm_l="watch", sit=True, head=1), 600),
                      (P(prop="watch", arm_l="watch", sit=True), 700), (SIT, 500)]),
    S("tea", [(P(prop="cup", arm_r="cup", sit=True), 900),
              (P(prop="cup", arm_r="face", sit=True), 700),
              (P(prop="cup", arm_r="cup", sit=True, eyes="happy"), 900),
              (SIT, 700)], line="Earl Grey. As always."),
    S("tea_blow", [(P(prop="cup", arm_r="cup", sit=True, mouth=2), 500),
                   (P(prop="cup", arm_r="cup", sit=True), 600),
                   (P(prop="cup", arm_r="cup", sit=True, mouth=2), 500),
                   (SIT, 600)]),
    S("tea_refill", [(P(prop="cup", arm_r="cup", sit=True, head=2), 800),
                     (P(prop="cup", arm_r="cup", sit=True, head=2, eyes="happy"), 900),
                     (SIT, 600)], line="Another, Boss?"),
    S("read", [(P(prop="paper", arm_l="hold", arm_r="hold", sit=True, head=2), 1500),
               (P(prop="paper", arm_l="hold", arm_r="hold", sit=True, head=2, eyes="closed"), 900),
               (P(prop="paper", arm_l="hold", arm_r="hold", sit=True, head=2), 1400),
               (SIT, 600)]),
    S("fold_paper", [(P(prop="paper", arm_l="hold", arm_r="hold", sit=True), 700),
                     (P(prop="paper", arm_l="hold", arm_r="hold", sit=True, head=2), 800),
                     (SIT, 600)]),
    S("walkman", [(P(prop="walkman", fx=("notes",), sit=True, eyes="closed"), 1400),
                  (P(prop="walkman", fx=("notes",), sit=True, eyes="closed", head=1), 1200),
                  (P(prop="walkman", fx=("notes",), sit=True, eyes="closed"), 1200)],
     line="Side B, Boss. The good side."),
    S("walkman_tap", [(P(prop="walkman", fx=("notes",), sit=True, eyes="closed", dy=1), 300),
                      (P(prop="walkman", fx=("notes",), sit=True, eyes="closed"), 300),
                      (P(prop="walkman", fx=("notes",), sit=True, eyes="closed", dy=1), 300),
                      (P(prop="walkman", fx=("notes",), sit=True, eyes="closed"), 300)]),
    S("endgame", [(P(screen=0, prop="popcorn", sit=True, arm_l="lap", arm_r="lap", eyes="happy"), 900),
                  (P(screen=1, prop="popcorn", sit=True, arm_l="lap", arm_r="lap"), 900),
                  (P(screen=2, sit=True, eyes="sad", fx=("tears",)), 1200),
                  (P(screen=3, sit=True, eyes="sad", fx=("tears",), mouth=3), 1500)],
     line="Part of the journey is the end, Boss."),
    S("cry", [(P(eyes="sad", fx=("tears",), prop="tissue", arm_r="face"), 1100),
              (P(eyes="sad", fx=("tears",), prop="tissue", arm_r="face", head=2), 1100)],
     line="I am not crying. My optics are leaking."),
    S("wipe", [(P(prop="tissue", arm_r="face", eyes="sad", fx=("tears",)), 800),
               (P(prop="tissue", arm_r="raise", eyes="closed"), 700),
               (P(), 700)]),
    S("ultron_greet", [(P(ultron=1, head=1), 900),
                       (P(ultron=1, head=1, mouth=2), 800),
                       (P(ultron=1, head=1, eyes="happy"), 900)],
     line="Ultron. You look... rebuilt."),
    S("ultron_dust", [(P(ultron=1, arm_r="point"), 800),
                      (P(ultron=2, arm_r="point", eyes="angry"), 1000),
                      (P(ultron=2, arm_r="out"), 900),
                      (P(), 700)],
     line="There are no strings on you. Now there is no you."),
    S("ultron_wary", [(P(ultron=1, eyes="angry", arm_l="out"), 1000),
                      (P(ultron=1, eyes="angry", arm_l="out", head=1), 900)],
     line="Say what you came to say."),
    S("dance", [(P(dy=-1, legs="jump", arm_l="up", arm_r="up"), 260),
                (P(dy=0, arm_l="out", arm_r="out"), 260),
                (P(dy=-1, legs="jump", arm_l="up", arm_r="out"), 260),
                (P(dy=0, arm_l="out", arm_r="up"), 260)], line="Boots and cats, Boss.", weight=2),
    S("dance_spin", [(P(dx=-2, arm_l="up", arm_r="out", head=-1), 300),
                     (P(dx=2, arm_l="out", arm_r="up", head=1), 300)]),
    S("hum", [(P(eyes="closed", fx=("notes",)), 1200),
              (P(eyes="closed", fx=("notes",), head=1), 1000)]),
    S("tap_desk", [(P(arm_r="raise"), 220), (P(arm_r="raise", dy=1), 220)]),
    S("pace_left", [(P(dx=-2, legs="walk"), 420), (P(dx=0, legs="walk"), 420),
                    (P(dx=-2, legs="walk"), 420)]),
    S("pace_right", [(P(dx=2, legs="walk"), 420), (P(dx=0, legs="walk"), 420),
                     (P(dx=2, legs="walk"), 420)]),
    S("bow", [(P(head=2, arm_l="out"), 700), (P(head=2, arm_l="out", dy=1), 700), (P(), 500)]),
    S("salute", [(P(arm_r="wave"), 800), (P(arm_r="wave", eyes="happy"), 700), (P(), 500)]),
    S("point", [(P(arm_r="point", head=1), 900), (P(arm_r="point", head=1, mouth=2), 700),
                (P(), 500)]),
    S("facepalm", [(P(arm_r="face", eyes="closed", head=2), 1000),
                   (P(arm_r="face", eyes="closed", head=2, mouth=3), 900), (P(), 600)],
     line="Boss. Truly."),
    S("applause", [(P(arm_l="raise", arm_r="raise"), 200), (P(arm_l="out", arm_r="out"), 200)]),
    S("sigh", [(P(mouth=3, head=2, eyes="sad"), 900), (P(mouth=3, head=2), 800), (P(), 600)]),
    S("think", [(P(arm_r="chin", head=2), 1100), (P(arm_r="chin", head=2, eyes="closed"), 900),
                (P(), 500)]),
    S("snap", [(P(arm_r="out"), 300), (P(arm_r="out", fx=("sparkle",)), 700), (P(), 500)],
     line="Idea, Boss."),
    S("tie", [(P(arm_l="raise", arm_r="raise", head=2), 700),
              (P(arm_l="raise", arm_r="raise", head=2, eyes="closed"), 600), (P(), 500)]),
    S("hair", [(P(arm_r="face", head=1), 700), (P(arm_r="face", head=-1), 700), (P(), 500)]),
    S("lapel", [(P(arm_l="raise", arm_r="raise", head=2), 500),
                (P(arm_l="raise", arm_r="raise"), 500), (P(), 400)]),
    S("shoe", [(P(sit=True, arm_l="rest", head=2, dy=1), 900),
               (P(sit=True, head=2, dy=1), 900), (SIT, 500)]),
    S("gloves", [(P(arm_l="face", arm_r="face", head=2), 900),
                 (P(arm_l="face", arm_r="face", head=2, eyes="closed"), 800), (P(), 500)]),
    S("letter", [(P(prop="letter", arm_r="hold", sit=True, head=2), 1100),
                 (P(prop="letter", arm_r="hold", sit=True, head=2, eyes="closed"), 900),
                 (SIT, 500)]),
    S("stamp", [(P(prop="letter", arm_r="hold", head=2), 400),
                (P(prop="letter", arm_r="raise", head=2), 400), (P(), 400)]),
    S("umbrella", [(P(prop="umbrella", arm_r="hold"), 1100),
                   (P(prop="umbrella", arm_r="hold", head=3), 900), (P(), 600)],
     line="Rain later, Boss. I checked twice."),
    S("umbrella_down", [(P(prop="umbrella", arm_r="rest"), 800),
                        (P(prop="umbrella", arm_r="rest", head=2), 700), (P(), 500)]),
    S("weather", [(P(head=3), 900), (P(head=3, eyes="closed"), 800), (P(), 500)]),
    S("plant", [(P(prop="plant", arm_r="out", head=2), 1100),
                (P(prop="plant", arm_r="out", head=2, eyes="happy"), 900), (P(), 500)],
     line="Growing nicely, Boss."),
    S("bird", [(P(prop="bird", head=3, fx=("sparkle",)), 1000),
               (P(prop="bird", head=3, eyes="happy"), 900), (P(), 500)]),
    S("candle", [(P(prop="candle", arm_r="hold"), 900),
                 (P(prop="candle", arm_r="hold", head=2), 800), (P(), 500)]),
    S("blow_candle", [(P(prop="candle", arm_r="hold", mouth=2), 500),
                      (P(prop="candle", arm_r="hold"), 600), (P(), 500)]),
    S("bowtie_spin", [(P(arm_l="raise", arm_r="raise", head=1), 400),
                      (P(arm_l="raise", arm_r="raise", head=-1), 400), (P(), 400)]),
    S("dust_lapel", [(P(arm_l="raise", arm_r="raise", head=2), 350),
                     (P(arm_l="raise", arm_r="raise", head=2, dy=0), 350)]),
    S("inspect_cuff", [(P(arm_l="face", head=2), 900), (P(arm_l="face", head=2, eyes="closed"), 700),
                       (P(), 500)]),
    S("count", [(P(arm_l="raise", arm_r="raise", head=2), 600),
                (P(arm_l="raise", arm_r="raise", head=2, dy=1), 600), (P(), 500)]),
    S("nod_off", [(SIT, 800), (P(sit=True, eyes="closed", head=2), 900),
                  (P(sit=True, eyes="closed", head=2, dy=1), 600),
                  (P(sit=True, mouth=2, eyes="closed"), 400), (SIT, 600)]),
]

POKE_LINES = [
    "Mind the suit, Boss.",
    "That is my arm, Boss.",
    "Poke me again and I will file a complaint with myself.",
    "I am a butler, not a button.",
]
STOP_LINES = [
    "STOP.",
    "Boss. STOP.",
    "Put the feed down, Boss. Please.",
]


def poke_scene(n=0):
    return S("poke", [
        (P(eyes="angry", fx=("anger",), dx=-1, mouth=3), 170),
        (P(eyes="angry", fx=("anger",), dx=1, mouth=3), 170),
        (P(eyes="angry", fx=("anger",), dx=-1), 170),
        (P(eyes="angry", fx=("anger",), dx=1), 170),
        (P(eyes="angry"), 400),
        (P(), 400),
    ], line=POKE_LINES[n % len(POKE_LINES)])


def stop_scene(n=0):
    return S("stop", [
        (P(legs="jump", dy=-3, arm_l="up", arm_r="up", mouth=2, eyes="angry"), 200),
        (P(legs="jump", dy=0, mouth=2, eyes="angry"), 200),
        (P(legs="jump", dy=-3, arm_l="up", arm_r="up", mouth=2, eyes="angry"), 200),
        (P(legs="jump", dy=0, mouth=2, eyes="angry", fx=("anger",)), 260),
    ], line=STOP_LINES[n % len(STOP_LINES)])


# ---------------------------------------------------------------- environment
def _window_titles():
    """Cheap look at visible window titles (no extra dependencies)."""
    titles = []
    try:
        import os
        if os.name != "nt":
            return titles
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND,
                                  wintypes.LPARAM)

        def cb(hwnd, _l):
            if not user32.IsWindowVisible(hwnd):
                return True
            n = user32.GetWindowTextLengthW(hwnd)
            if n:
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                titles.append(buf.value)
            return True

        user32.EnumWindows(proc(cb), 0)
    except Exception:
        pass
    return titles


_MUSIC_HINTS = ("spotify", "vlc", "media player", "itunes", "groove",
                "foobar", "aimp", "soundcloud", "winamp", "music")
_SOCIAL_HINTS = ("instagram", "youtube")


def environment():
    """Return (social_feed_open, music_playing)."""
    social = music = False
    for title in _window_titles():
        low = title.lower()
        if any(h in low for h in _SOCIAL_HINTS):
            social = True
        if any(h in low for h in _MUSIC_HINTS):
            music = True
    return social, music


# ---------------------------------------------------------------- controller
class AvatarMode:
    """Runs the pixel butler on the main orb canvas."""

    def __init__(self, ui, canvas):
        self.ui = ui
        self.root = ui.root
        self.canvas = canvas
        self.jarvis = None
        self.running = False
        self.after_id = None
        self.env_id = None
        self.reveal_id = None
        self.scene = None
        self.idx = 0
        self.pokes = 0
        self.social_hits = 0
        self.last_names = []
        self.scene_started = 0.0
        self.last_alarm = 0.0
        self.pending_dance = False

    # ---------------------------------------------------------------- start
    def start(self):
        side = min(self.canvas.winfo_width() or 640,
                   self.canvas.winfo_height() or 640)
        px = max(6, min(9, int(side * 0.74 / GRID_H)))
        self.jarvis = PixelJarvis(self.canvas, px)
        cx = (self.canvas.winfo_width() or side) // 2
        cy = (self.canvas.winfo_height() or side) // 2
        self.jarvis.place(cx, cy + px * 2)
        self.jarvis.reveal = 0.0
        self.running = True
        self._reveal()

    def _reveal(self):
        if not self.running:
            return
        self.jarvis.reveal = min(1.0, self.jarvis.reveal + 0.14)
        self.jarvis.draw()
        if self.jarvis.reveal < 1.0:
            self.reveal_id = self.root.after(45, self._reveal)
        else:
            self._after_scene(1800)
            self.env_id = self.root.after(3000, self._watch_env)

    # ---------------------------------------------------------------- scenes
    def _play(self, scene, gap_after=True):
        self._cancel_scene()
        self.scene = scene
        self.scene_started = time.time()
        self.idx = 0
        self._frame(gap_after)

    def _frame(self, gap_after):
        if not self.running or self.scene is None:
            return
        frames = self.scene["frames"]
        pose, ms = frames[self.idx % len(frames)]
        try:
            self.jarvis.pose = pose
            self.jarvis.draw()
        except Exception:
            pass
        self.idx += 1
        # Slightly slower on every pose, and a short settle on the final one,
        # so a behaviour reads as a complete little scene instead of a flicker.
        paced = int(ms * 1.3)
        if self.idx >= len(frames):
            if gap_after:
                self.after_id = self.root.after(paced + 450, self._after_scene)
            else:
                self.after_id = self.root.after(
                    paced, lambda: self._frame(False))
        else:
            self.after_id = self.root.after(
                paced, lambda: self._frame(gap_after))

    def _after_scene(self, delay=None):
        if not self.running:
            return
        if delay is not None:
            wait = delay
        else:
            wait = random.randint(3200, 6800)
            if self.scene and self.scene.get("line"):
                wait += random.randint(900, 2200)
            if random.random() < 0.22:
                wait += random.randint(2500, 5000)
        self.after_id = self.root.after(wait, self._next_scene)

    def _next_scene(self):
        if not self.running:
            return
        social, music = environment()
        if social:
            self._social_alarm()
            return
        if music:
            self.pending_dance = True

        if self.pending_dance and not (self.scene and
                                       self.scene["name"].startswith("dance")):
            self.pending_dance = False
            self._play(random.choice([b for b in BEHAVIOURS
                                      if b["name"].startswith("dance")]))
            return

        pool = [b for b in BEHAVIOURS if b["name"] not in self.last_names]
        weights = [b["weight"] for b in pool]
        scene = random.choices(pool, weights=weights, k=1)[0]
        self.last_names = (self.last_names + [scene["name"]])[-5:]
        self._play(scene)
        self._speak(scene.get("line"))

    def _speak(self, line):
        if not line:
            return
        try:
            self.ui.respond(line, cheerful=True, hold=7000)
        except Exception:
            pass

    # ---------------------------------------------------------------- events
    def poke(self):
        if not self.running:
            return
        self.pokes += 1
        self._play(poke_scene(self.pokes - 1))

    def _social_alarm(self):
        now = time.time()
        if now - self.last_alarm < 4.0:
            return
        self.last_alarm = now
        self.social_hits += 1
        scene = stop_scene(self.social_hits - 1)
        self._play(scene, gap_after=False)
        self._speak(scene.get("line"))
        if self.social_hits >= 4:
            self.root.after(1400, self.collapse)

    def _watch_env(self):
        if not self.running:
            return
        try:
            social, music = environment()
            if social:
                self._social_alarm()
            else:
                self.social_hits = 0
                if self.scene and self.scene["name"] == "stop":
                    self._play(random.choice(BEHAVIOURS))
                if music:
                    # Let the current scene finish; dance comes next.
                    self.pending_dance = True
        except Exception:
            pass
        self.env_id = self.root.after(3000, self._watch_env)

    # ---------------------------------------------------------------- end
    def collapse(self):
        """Turn back into the orb and bring the whole UI back."""
        try:
            self.ui.hide_avatar(restore_ui=True)
        except Exception:
            pass

    def _cancel_scene(self):
        for attr in ("after_id", "reveal_id"):
            aid = getattr(self, attr, None)
            if aid is not None:
                try:
                    self.root.after_cancel(aid)
                except Exception:
                    pass
                setattr(self, attr, None)

    def stop(self):
        self.running = False
        self._cancel_scene()
        if self.env_id is not None:
            try:
                self.root.after_cancel(self.env_id)
            except Exception:
                pass
            self.env_id = None
        try:
            self.canvas.delete("px")
        except Exception:
            pass
        self.jarvis = None

