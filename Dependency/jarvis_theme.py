# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS Theme - Apple Human Interface Guidelines, translated to Tk.

The HIG principles used here:

* Clarity    - one job per screen, a readable type scale, generous spacing.
* Deference  - the interface recedes; the orb, the avatar and Boss's words
               are the content, not the chrome.
* Depth      - layered surfaces (background, card, raised control) with soft
               hairline strokes instead of loud borders, plus short motion.
* Familiarity- switches look like switches, segmented controls segment,
               the primary action is the only filled button on a page.
* Flexibility- every control is reachable from one Settings window with a
               sidebar, so nothing is hidden in a corner icon.
* Craft      - an 8-point spacing grid, aligned edges, consistent radii.

Everything is drawn with plain Tk canvases: no images, no extra packages.
"""
import sys
import math

import tkinter as tk
import tkinter.font as tkfont

# ---------------------------------------------------------------- palette
# A cool near-black canvas with warm JARVIS amber as the single accent. This is
# deliberately restrained: Apple interfaces use colour to mean something, not
# to decorate every edge.
BG = "#0A0A0C"
SURFACE = "#121215"
CARD = "#1A1A1F"
CARD_HI = "#222228"
STROKE = "#2C2C33"
STROKE_HI = "#3A3A43"
TEXT = "#F2F2F7"
TEXT2 = "#C7C7CE"
DIM = "#8E8E96"
FAINT = "#5A5A63"
ACCENT = "#FF9F0A"
ACCENT_SOFT = "#FFD60A"
ACCENT_DIM = "#7A4E08"
GREEN = "#30D158"
RED = "#FF453A"
BLUE = "#64D2FF"
PINK = "#FF375F"

RADIUS = 14
PAD = 16
GAP = 8

IS_MAC = sys.platform == "darwin"

_ready = False
UI = "Segoe UI"
DISPLAY = "Segoe UI"
MONO = "Consolas"
SMALL_CAPS = "Segoe UI"


def init(root=None):
    """Pick the best system families once, the way the OS would."""
    global _ready, UI, DISPLAY, MONO, SMALL_CAPS
    if _ready:
        return
    try:
        fams = set(tkfont.families(root))
    except Exception:
        fams = set()
    if IS_MAC:
        for name in ("SF Pro Text", "SF Pro Display", "Helvetica Neue",
                     "Helvetica"):
            if name in fams:
                UI = DISPLAY = name
                break
        for name in ("SF Mono", "Menlo", "Monaco"):
            if name in fams:
                MONO = name
                break
    else:
        for name in ("Segoe UI Variable Text", "Segoe UI"):
            if name in fams:
                UI = DISPLAY = name
                break
        for name in ("Segoe UI Variable Display", "Segoe UI"):
            if name in fams:
                DISPLAY = name
                break
        for name in ("Cascadia Mono", "Consolas"):
            if name in fams:
                MONO = name
                break
    SMALL_CAPS = UI
    _ready = True


def f(size, weight="normal", mono=False, display=False):
    try:
        size = int(round(float(size)))
    except Exception:
        size = 11
    fam = MONO if mono else (DISPLAY if display else UI)
    return (fam, size, weight) if weight != "normal" else (fam, size)


# ---------------------------------------------------------------- drawing
def round_rect(canvas, x1, y1, x2, y2, r, **kw):
    """A smooth rounded rectangle that survives Tk's polygon smoothing."""
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


def hairline(parent, color=STROKE, pady=(0, 0)):
    line = tk.Frame(parent, bg=color, height=1, bd=0, highlightthickness=0)
    line.pack(fill="x", pady=pady)
    return line


def label(parent, text="", size=13, weight="normal", fg=TEXT, bg=None,
          anchor="w", justify="left", mono=False, display=False, **kw):
    return tk.Label(parent, text=text, bg=bg or parent["bg"], fg=fg,
                    font=f(size, weight, mono=mono, display=display),
                    anchor=anchor, justify=justify, **kw)


# ---------------------------------------------------------------- card
class Card(tk.Frame):
    """A rounded surface. `body` is the frame to put content in."""

    def __init__(self, parent, bg=CARD, radius=RADIUS, stroke=STROKE,
                 pad=0, **kw):
        outer_bg = parent["bg"] if "bg" in parent.keys() else BG
        super().__init__(parent, bg=outer_bg, bd=0, highlightthickness=0, **kw)
        self._bg = bg
        self._stroke = stroke
        self._radius = radius
        self._pad = pad
        self.canvas = tk.Canvas(self, bg=outer_bg, highlightthickness=0,
                                bd=0, takefocus=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        # The body is inset just far enough that its square corners never
        # reach the rounded edge of the card. A full-bleed child frame paints
        # over the radius and makes every card look like a plain rectangle,
        # which is the biggest visual difference between a real Mac window and
        # a Tk imitation.
        inset = min(radius, max(5, radius // 2))
        self.body = tk.Frame(self, bg=bg, bd=0, highlightthickness=0)
        self.body.pack(fill="both", expand=True, padx=inset, pady=inset)
        self.bind("<Configure>", self._redraw)

    def _redraw(self, _e=None):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4 or h < 4:
            return
        self.canvas.delete("card")
        if self._stroke:
            round_rect(self.canvas, 0.5, 0.5, w - 0.5, h - 0.5,
                       self._radius, fill=self._stroke, outline="",
                       tags="card")
            inset = 1
            round_rect(self.canvas, inset + 0.5, inset + 0.5,
                       w - inset - 0.5, h - inset - 0.5,
                       self._radius - inset, fill=self._bg, outline="",
                       tags="card")
        else:
            round_rect(self.canvas, 0.5, 0.5, w - 0.5, h - 0.5,
                       self._radius, fill=self._bg, outline="", tags="card")
        self.canvas.tag_lower("card")


# ---------------------------------------------------------------- switch
class Switch(tk.Canvas):
    """iOS/macOS switch: 44 x 26, animated knob, keyboard accessible."""

    def __init__(self, parent, value=False, command=None, bg=None):
        self._parent_bg = bg or (parent["bg"] if "bg" in parent.keys() else BG)
        super().__init__(parent, width=46, height=28, bg=self._parent_bg,
                         highlightthickness=0, bd=0, cursor="hand2",
                         takefocus=1)
        self.value = bool(value)
        self.command = command
        self._pos = 1.0 if self.value else 0.0
        self.bind("<Button-1>", self._toggle)
        self.bind("<space>", self._toggle)
        self.bind("<Return>", self._toggle)
        self._draw()

    def _toggle(self, _e=None):
        self.value = not self.value
        self._animate()
        if self.command:
            self.command(self.value)
        return "break"

    def set(self, value, fire=False):
        value = bool(value)
        if value == self.value:
            self._draw()
            return
        self.value = value
        self._animate()
        if fire and self.command:
            self.command(self.value)

    def _animate(self, step=0):
        target = 1.0 if self.value else 0.0
        self._pos += (target - self._pos) * 0.45
        if abs(target - self._pos) < 0.04:
            self._pos = target
        self._draw()
        if self._pos != target:
            self.after(16, lambda: self._animate(step + 1))

    def _draw(self):
        self.delete("all")
        w, h = 46, 28
        p = self._pos
        track = _mix("#3A3A40", ACCENT, p)
        round_rect(self, 2, 3, w - 2, h - 3, 11, fill=track, outline="")
        kx = 12 + p * (w - 24)
        self.create_oval(kx - 8, h / 2 - 8, kx + 8, h / 2 + 8,
                         fill="#FFFFFF", outline="")


def _mix(a, b, t):
    try:
        a = a.lstrip("#")
        b = b.lstrip("#")
        ar, ag, ab = int(a[0:2], 16), int(a[2:4], 16), int(a[4:6], 16)
        br, bg, bb = int(b[0:2], 16), int(b[2:4], 16), int(b[4:6], 16)
        return "#%02x%02x%02x" % (round(ar + (br - ar) * t),
                                  round(ag + (bg - ag) * t),
                                  round(ab + (bb - ab) * t))
    except Exception:
        return b


# ---------------------------------------------------------------- segmented
class Segmented(tk.Canvas):
    """A two-or-three option picker, exactly like the macOS segmented control."""

    def __init__(self, parent, options, value=None, command=None,
                 width=220, height=30):
        bg = parent["bg"] if "bg" in parent.keys() else BG
        super().__init__(parent, width=width, height=height, bg=bg,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.options = list(options)
        self.value = value if value in options else self.options[0]
        self.command = command
        self._cw, self._ch = width, height
        self.bind("<Button-1>", self._click)
        self._draw()

    def _click(self, e):
        i = max(0, min(len(self.options) - 1,
                       int(e.x / (self._cw / len(self.options)))))
        self.set(self.options[i], fire=True)

    def set(self, value, fire=False):
        if value not in self.options:
            return
        self.value = value
        self._draw()
        if fire and self.command:
            self.command(value)

    def _draw(self):
        self.delete("all")
        w, h = self._cw, self._ch
        round_rect(self, 1, 1, w - 1, h - 1, h / 2 - 1,
                   fill="#26262C", outline="")
        n = len(self.options)
        seg = w / n
        i = self.options.index(self.value)
        pad = 2
        round_rect(self, pad + i * seg, pad, pad + (i + 1) * seg, h - pad,
                   h / 2 - 2, fill="#48484F", outline="")
        for j, opt in enumerate(self.options):
            self.create_text(seg * (j + 0.5), h / 2, text=opt,
                             fill=TEXT if j == i else DIM,
                             font=f(11, "bold" if j == i else "normal"))


# ---------------------------------------------------------------- button
class Button(tk.Canvas):
    """A pill button. `primary=True` is the single filled action on a page."""

    def __init__(self, parent, text, command=None, primary=False,
                 destructive=False, width=None, height=34, glyph=None):
        bg = parent["bg"] if "bg" in parent.keys() else BG
        self._text = text
        self._glyph = glyph
        self._primary = primary
        self._destructive = destructive
        self._hover = False
        self._enabled = True
        fnt = f(12, "bold" if primary else "normal")
        try:
            tw = tkfont.Font(font=fnt).measure(text)
        except Exception:
            tw = len(text) * 7
        w = width or max(76, tw + (54 if glyph else 32))
        super().__init__(parent, width=w, height=height, bg=bg,
                         highlightthickness=0, bd=0, cursor="hand2",
                         takefocus=1)
        self._cw, self._ch = w, height
        self.command = command
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<Return>", self._click)
        self.bind("<space>", self._click)
        self._draw()

    def _set_hover(self, on):
        self._hover = on
        self._draw()

    def _click(self, _e=None):
        if self._enabled and self.command:
            self.command()
        return "break"

    def set_text(self, text):
        self._text = text
        self._draw()

    def set_enabled(self, on):
        self._enabled = bool(on)
        self.configure(cursor="hand2" if on else "arrow")
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self._cw, self._ch
        if self._primary:
            fill = _mix(ACCENT, "#FFFFFF", 0.16 if self._hover else 0.0)
            fg = "#1A1200"
        elif self._destructive:
            fill = "#3A1A1A" if not self._hover else "#4A2020"
            fg = "#FF8A80"
        else:
            fill = "#2A2A31" if not self._hover else "#34343C"
            fg = TEXT
        if not self._enabled:
            fill, fg = "#222227", FAINT
        round_rect(self, 1, 1, w - 1, h - 1, (h - 2) / 2,
                   fill=fill, outline="")
        tx = w / 2 + (8 if self._glyph else 0)
        if self._glyph:
            self.create_text(20, h / 2, text=self._glyph, fill=fg,
                             font=f(13, "bold"))
        self.create_text(tx, h / 2, text=self._text, fill=fg,
                         font=f(12, "bold" if self._primary else "normal"))


class IconButton(tk.Canvas):

    def __init__(self, parent, glyph, command=None, size=34, danger=False):
        bg = parent["bg"] if "bg" in parent.keys() else BG
        super().__init__(parent, width=size, height=size, bg=bg,
                         highlightthickness=0, bd=0, cursor="hand2",
                         takefocus=1)
        self.glyph = glyph
        self.command = command
        self.danger = danger
        self._hover = False
        self._size = size
        self.bind("<Button-1>", lambda e: command() if command else None)
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self._draw()

    def _enter(self, _e):
        self._hover = True
        self._draw()

    def _leave(self, _e):
        self._hover = False
        self._draw()

    def _draw(self):
        self.delete("all")
        s = self._size
        if self._hover:
            self.create_oval(1, 1, s - 1, s - 1,
                             fill="#3A1A1A" if self.danger else "#26262C",
                             outline="")
        self.create_text(s / 2, s / 2 - 1,
                         text=self.glyph,
                         fill=(RED if self.danger else TEXT2),
                         font=f(15))


class GlyphButton(tk.Canvas):
    """A chrome button drawn with lines, not a font symbol.

    System font glyphs for a gear differ wildly between machines (on some
    Windows builds U+2699 renders as a flower). Drawing the shape keeps the
    Settings icon and the Tools cabinet identical everywhere.
    """

    def __init__(self, parent, kind, command=None, size=34):
        bg = parent["bg"] if "bg" in parent.keys() else SURFACE
        super().__init__(parent, width=size, height=size, bg=bg,
                         highlightthickness=0, bd=0, cursor="hand2",
                         takefocus=1)
        self.kind = kind
        self.command = command
        self._hover = False
        self._size = size
        self.bind("<Button-1>", lambda e: command() if command else None)
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Return>", lambda e: command() if command else None)
        self._draw()

    def _enter(self, _e):
        self._hover = True
        self._draw()

    def _leave(self, _e):
        self._hover = False
        self._draw()

    def _draw(self):
        self.delete("all")
        s = self._size
        cx = cy = s / 2.0
        if self._hover:
            self.create_oval(1, 1, s - 1, s - 1, fill="#26262C", outline="")
        c = TEXT if self._hover else TEXT2
        if self.kind == "gear":
            for i in range(8):
                a = i * math.pi / 4.0
                x1 = cx + math.cos(a) * 7.2
                y1 = cy + math.sin(a) * 7.2
                x2 = cx + math.cos(a) * 10.6
                y2 = cy + math.sin(a) * 10.6
                self.create_line(x1, y1, x2, y2, fill=c, width=2.4)
            self.create_oval(cx - 7.2, cy - 7.2, cx + 7.2, cy + 7.2,
                             outline=c, width=2)
            self.create_oval(cx - 2.4, cy - 2.4, cx + 2.4, cy + 2.4,
                             fill=c, outline="")
        else:
            # A little cabinet / closet: three drawers with handles.
            self.create_rectangle(8.5, 7.5, s - 8.5, s - 7.5,
                                  outline=c, width=2)
            for y in (12.5, 17.0, 21.5):
                self.create_line(8.5, y, s - 8.5, y, fill=c, width=1.4)
            for y in (10.0, 14.8, 19.6):
                self.create_line(cx - 3.5, y, cx + 3.5, y, fill=c, width=1.8)


# ---------------------------------------------------------------- scroll
class Scroll(tk.Frame):
    """A clean vertical scroller with an optional hairline indicator."""

    def __init__(self, parent, bg=BG):
        super().__init__(parent, bg=bg, bd=0, highlightthickness=0)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.bar = tk.Canvas(self, width=8, bg=bg, highlightthickness=0, bd=0)
        self.bar.pack(side="right", fill="y")
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window((0, 0), window=self.inner,
                                              anchor="nw")
        self.inner.bind("<Configure>", self._on_inner)
        self.canvas.bind("<Configure>", self._on_canvas)
        self.canvas.bind_all("<MouseWheel>", self._wheel, add="+")
        self.canvas.bind_all("<Button-4>", lambda e: self._scroll(-1), add="+")
        self.canvas.bind_all("<Button-5>", lambda e: self._scroll(1), add="+")
        self._draw_bar()

    def _on_inner(self, _e=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._draw_bar()

    def _on_canvas(self, _e=None):
        self.canvas.itemconfigure(self._win, width=self.canvas.winfo_width())
        self._draw_bar()

    def _wheel(self, e):
        try:
            if not self.winfo_ismapped():
                return
            # only scroll when the pointer is over this scroller
            x, y = self.winfo_pointerxy()
            w = self.winfo_containing(x, y)
            while w is not None:
                if w is self:
                    break
                w = getattr(w, "master", None)
            if w is not self:
                return
            delta = -1 if getattr(e, "delta", 0) > 0 else 1
            self.canvas.yview_scroll(delta * 3, "units")
        except Exception:
            pass

    def _scroll(self, direction):
        self.canvas.yview_scroll(direction * 3, "units")

    def _draw_bar(self):
        self.bar.delete("all")
        try:
            lo, hi = self.canvas.yview()
        except Exception:
            return
        h = self.bar.winfo_height()
        if hi - lo >= 0.999 or h < 20:
            return
        y1, y2 = lo * h, hi * h
        self.bar.create_oval(2, y1, 6, y2, fill=STROKE_HI, outline="")


# ---------------------------------------------------------------- rows
class Row(tk.Frame):
    """A settings row: description on the left, control on the right.

    The row itself spans the card so the separator can run edge to edge, the
    way macOS System Settings does. Only the content is inset.
    """

    def __init__(self, parent, title, subtitle=None, control=None,
                 bg=CARD, padx=16, pady=10, last=False):
        super().__init__(parent, bg=bg)
        self.pack(fill="x")
        inner = tk.Frame(self, bg=bg)
        inner.pack(fill="x", padx=padx, pady=(pady, pady))
        left = tk.Frame(inner, bg=bg)
        left.pack(side="left", fill="x", expand=True)
        label(left, title, 13, "bold", TEXT, bg).pack(anchor="w")
        if subtitle:
            label(left, subtitle, 10.5, fg=DIM, bg=bg, wraplength=430,
                  justify="left").pack(anchor="w", pady=(1, 0))
        if callable(control):
            control = control(inner)
        if control is not None:
            control.pack(side="right", padx=(12, 0))
        if not last:
            tk.Frame(self, bg=STROKE, height=1).pack(fill="x")


def pill_text(parent, text, color=ACCENT, bg=CARD, size=10):
    lbl = tk.Label(parent, text=text, bg=bg, fg=color,
                   font=f(size, "bold"), padx=8, pady=2)
    return lbl
