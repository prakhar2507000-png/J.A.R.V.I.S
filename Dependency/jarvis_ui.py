# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS UI - a full-screen stage built to Apple's HIG.

    top bar    : wordmark, live state, one Settings button, one Close button
    centre     : the orb (triple-click for the pixel butler)
    below      : the spoken subtitle
    bottom     : a Spotlight-style field that expands when you type
    minimised  : the click-counting mini orb

Everything else lives in Settings, grouped the way macOS groups preferences.
"""
import tkinter as tk
from tkinter import filedialog
import threading
import os
import sys
import datetime
import re
import random
import time
import webbrowser

from jarvis_config import (BG, PANEL, ACC, ACC2, TXT, DIM, BLUE, PINK, SPECS,
                           MODEL, NW_FLAG, APP_AUTHOR, APP_OWNER, IS_WIN,
                           IS_MAC, SUPPORT_EMAIL, FINGERPRINT, load_cloud,
                           save_cloud, PROFILE)
from jarvis_orb import Orb
import jarvis_theme as TH

# The HIG palette becomes the app palette. Keeping the old names means every
# corner of the UI inherits the new look without a risky rewrite.
BG = TH.BG
PANEL = TH.SURFACE
ACC = TH.ACCENT
ACC2 = TH.ACCENT_SOFT
TXT = TH.TEXT
DIM = TH.DIM
BLUE = TH.BLUE
PINK = TH.PINK

# MacBook-friendly font families. Tk would fall back silently, but naming the
# right family keeps the HUD and settings crisp on both systems.
UI_FONT = "Helvetica Neue" if IS_MAC else "Segoe UI"
MONO_FONT = "Menlo" if IS_MAC else "Consolas"


def veil(text):
    """Return the display form: hexadecimal first, then Caesar shift 2507.

    The real values live in jarvis_config.py so anyone reading the source can
    find them. The interface and the guides only ever show this veiled form.
    """
    import jarvis_vault as V
    return V.caesar(V.hex_encode(str(text)), 2507)
SYM_FONT = "Apple Symbols" if IS_MAC else "Segoe UI Symbol"


def _round_rect(canvas, x1, y1, x2, y2, r, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
           x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
           x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


class MiniOrb:
    """Floating orb shown when the main UI is hidden.

    Clicks are counted, so one button can do three jobs:
        1 click  -> JARVIS listens
        2 clicks -> the full UI opens
        3 clicks -> the orb becomes the tiny pixel butler (and back)
    """

    SIZE = 150

    def __init__(self, root, on_listen, on_open):
        self.root = root
        self.on_listen = on_listen
        self.on_open = on_open
        self.win = None
        self.cv = None
        self.orb = None
        self.butler = None
        self.mode = "orb"
        self.blink_id = None
        self.click_id = None
        self._clicks = 0

    def show(self):
        if self.win is not None:
            return
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        try:
            win.attributes("-topmost", True)
        except Exception:
            pass
        w = h = self.SIZE

        # Transparent window: on Windows the chroma key makes only the orb
        # visible; on macOS the canvas background itself is transparent.
        bg = "#010101"
        win.configure(bg=bg)
        try:
            win.attributes("-transparentcolor", bg)
        except Exception:
            try:
                win.configure(bg="systemTransparent")
                win.attributes("-transparent", True)
                bg = "systemTransparent"
            except Exception:
                pass

        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        win.geometry("%dx%d+%d+%d" % (w, h, sw - w - 14, sh - h - 46))

        cv = tk.Canvas(win, width=w, height=h, bg=bg,
                       highlightthickness=0, bd=0)
        cv.pack()
        self.win = win
        self.cv = cv
        self.mode = "orb"
        self._draw_orb()

        # Bind once, on the canvas that fills the whole window. Binding the
        # Toplevel as well would fire twice per click and turn 1 click into 2.
        cv.bind("<Button-1>", self._click)
        try:
            win.deiconify()
            win.lift()
        except Exception:
            pass

    # --------------------------------------------------------------- modes
    def _draw_orb(self):
        self._stop_butler()
        try:
            if self.orb is not None:
                self.orb.stop()
        except Exception:
            pass
        try:
            self.cv.delete("orb")
        except Exception:
            pass
        self.orb = Orb(self.cv, self.SIZE, self.SIZE, compact=True)
        self.orb.draw()
        self.mode = "orb"

    def _draw_butler(self):
        try:
            if self.orb is not None:
                self.orb.stop()
        except Exception:
            pass
        try:
            self.cv.delete("orb")
        except Exception:
            pass
        self.orb = None
        self.mode = "butler"
        try:
            from jarvis_avatar import PixelJarvis
            butler = PixelJarvis(self.cv, 2)
            butler.place(self.SIZE // 2, self.SIZE // 2 + 2)
            butler.reveal = 1.0
            butler.draw()
            self.butler = butler
            self._schedule_blink(2400)
        except Exception:
            self.mode = "orb"
            self.orb = Orb(self.cv, self.SIZE, self.SIZE, compact=True)
            self.orb.draw()

    def toggle_mode(self):
        if self.mode == "butler":
            self._draw_orb()
        else:
            self._draw_butler()

    # --------------------------------------------------------------- clicks
    def _click(self, event=None):
        if self.win is None:
            return
        self._clicks += 1
        if self.click_id is not None:
            try:
                self.win.after_cancel(self.click_id)
            except Exception:
                pass
        self.click_id = self.win.after(430, self._resolve)

    def _resolve(self):
        self.click_id = None
        n = self._clicks
        self._clicks = 0
        if n >= 3:
            self.toggle_mode()
        elif n == 2:
            try:
                self.on_open()
            except Exception:
                pass
        else:
            try:
                self.on_listen()
            except Exception:
                pass

    # --------------------------------------------------------------- blink
    def _schedule_blink(self, ms=None):
        if self.win is None or self.butler is None:
            return
        try:
            self.blink_id = self.win.after(
                ms if ms is not None else random.randint(2800, 6200),
                self._blink)
        except Exception:
            self.blink_id = None

    def _blink(self):
        if self.win is None or self.butler is None:
            return
        try:
            self.butler.pose = dict(self.butler.pose)
            self.butler.pose["eyes"] = "closed"
            self.butler.draw()
            self.blink_id = self.win.after(150, self._open_eyes)
        except Exception:
            self.blink_id = None

    def _open_eyes(self):
        if self.win is None or self.butler is None:
            return
        try:
            self.butler.pose = dict(self.butler.pose)
            self.butler.pose["eyes"] = "open"
            self.butler.draw()
        except Exception:
            pass
        self._schedule_blink()

    def _stop_butler(self):
        if self.blink_id is not None and self.win is not None:
            try:
                self.win.after_cancel(self.blink_id)
            except Exception:
                pass
        self.blink_id = None
        self.butler = None
        try:
            self.cv.delete("px")
        except Exception:
            pass

    def hide(self):
        if self.click_id is not None and self.win is not None:
            try:
                self.win.after_cancel(self.click_id)
            except Exception:
                pass
        self.click_id = None
        self._clicks = 0
        self._stop_butler()
        if self.orb is not None:
            try:
                self.orb.stop()
            except Exception:
                pass
        if self.win is not None:
            try:
                self.win.destroy()
            except Exception:
                pass
        self.win = None
        self.cv = None
        self.orb = None


class JarvisUI:
    def __init__(self, root, voice, orb, camera, app=None):
        global UI_FONT, MONO_FONT, SYM_FONT
        TH.init(root)
        UI_FONT, MONO_FONT, SYM_FONT = TH.UI, TH.MONO, TH.UI
        self.root = root
        self.voice = voice
        self.orb = orb
        self.camera = camera
        self.app = app

        self.state = "idle"
        self.mood = "loyal"
        self.speak_on = True
        self.busy = False
        self.transcript = []
        self.composer_open = False
        self.attached = None
        self.sub_token = 0
        self.W, self.H = 1280, 800
        self.task_mode = False
        self.panel_open = False
        self.tools_open = False
        self.tools_panel = None
        self.vault_view = None
        self.vault_method = "Caesar shift"
        self.avatar = None
        self._orb_clicks = 0
        self._last_orb_click = 0.0
        self._greeted = False
        self.settings_win = None
        self.settings_view = None
        try:
            import jarvis_eggs
            self.found_eggs = set(jarvis_eggs.load_found())
        except Exception:
            self.found_eggs = set()

        root.title("J.A.R.V.I.S.")
        root.configure(bg=BG)
        if IS_MAC:
            # A real full-screen window behaves far better than a borderless
            # one on macOS (keyboard focus, Spaces, Mission Control).
            try:
                root.attributes("-fullscreen", True)
            except Exception:
                pass
        else:
            # borderless full-screen, exactly like the reference layout
            try:
                root.overrideredirect(True)
            except Exception:
                pass
        self.W = root.winfo_screenwidth()
        self.H = root.winfo_screenheight()
        root.geometry("%dx%d+0+0" % (self.W, self.H))
        root.bind("<Escape>", self.on_esc)
        root.bind("<F11>", lambda e: None)
        root.bind("<Key>", self.on_key)
        root.bind("<Command-q>", lambda e: self.quit_app())
        root.bind("<Command-w>", lambda e: self.minimise())
        root.protocol("WM_DELETE_WINDOW", self.quit_app)

        self._build_hud()
        self._build_orb()
        self._build_subtitle()
        self._build_composer()
        self._build_panel()
        self._build_tools()
        self._build_lock()

        self.mini = MiniOrb(root, self.listen_from_orb, self.restore)
        root.bind("<Unmap>", self._on_unmap)
        root.bind("<Map>", self._on_map)

        self.update_hud()
        self._hud_loop()

    # ------------------------------------------------------------------ chrome
    def _build_hud(self):
        """A quiet 56-point title bar: identity left, two controls right."""
        bar = tk.Frame(self.root, bg=TH.SURFACE, height=56, bd=0,
                       highlightthickness=0)
        bar.place(x=0, y=0, relwidth=1)
        bar.pack_propagate(False)
        tk.Frame(self.root, bg=TH.STROKE, height=1, bd=0).place(
            x=0, y=56, relwidth=1)

        left = tk.Frame(bar, bg=TH.SURFACE)
        left.pack(side="left", padx=24)
        self.status_dot = tk.Canvas(left, width=10, height=10,
                                    bg=TH.SURFACE, highlightthickness=0, bd=0)
        self.status_dot.pack(side="left", padx=(0, 10))
        self.status_dot.create_oval(1, 1, 9, 9, fill=TH.GREEN, outline="",
                                    tags="dot")
        tk.Label(left, text="J.A.R.V.I.S.", bg=TH.SURFACE, fg=TH.TEXT,
                 font=(UI_FONT, 12, "bold")).pack(side="left")
        self.hud = tk.Label(left, text="", bg=TH.SURFACE, fg=TH.DIM,
                            font=(MONO_FONT, 9), anchor="w")
        self.hud.pack(side="left", padx=(18, 0), pady=(1, 0))

        # Digital footprint: visible, quiet, and impossible to miss if someone
        # is about to modify or share this build.
        foot = tk.Label(
            bar,
            text="ID: %s  \u00b7  Contact me: %s"
                 % (veil(FINGERPRINT), SUPPORT_EMAIL),
            bg=TH.SURFACE, fg=TH.FAINT, font=(MONO_FONT, 8))
        foot.place(relx=0.5, rely=0.5, anchor="center")

        right = tk.Frame(bar, bg=TH.SURFACE)
        right.pack(side="right", padx=16)
        TH.IconButton(right, "\u2715", self.quit_app, danger=True).pack(
            side="right")
        TH.GlyphButton(right, "gear", self.settings_panel).pack(
            side="right", padx=(0, 2))
        TH.GlyphButton(right, "tools", self.toggle_tools).pack(
            side="right", padx=(0, 2))

    def _build_orb(self):
        side = min(int(self.H * 0.76), int(self.W * 0.62), 700)
        side = max(520, side - side % 2)
        self.orb_canvas = tk.Canvas(self.root, width=side, height=side,
                                    bg=BG, highlightthickness=0, bd=0)
        self.orb_canvas.place(relx=0.5, rely=0.43, anchor="center")
        if self.orb is None:
            self.orb = Orb(self.orb_canvas, side, side)
        else:
            self.orb.canvas = self.orb_canvas
            self.orb.W = side
            self.orb.H = side
            self.orb.rad_factor = 0.34
            self.orb.pscale = 1.0
            self.orb.vignette = True
        self.orb.cx = side // 2
        self.orb.cy = side // 2
        self.orb.draw()
        self.orb_canvas.bind("<Button-1>", self._orb_click)

    # ------------------------------------------------------------- pixel mode
    def _orb_click(self, e):
        """Single poke irritates him; triple click unfolds the pixel butler."""
        if self.avatar is not None:
            self.avatar.poke()
            return
        now = time.time()
        if now - self._last_orb_click < 0.65:
            self._orb_clicks += 1
        else:
            self._orb_clicks = 1
        self._last_orb_click = now
        if self._orb_clicks >= 3:
            self._orb_clicks = 0
            self.show_avatar()

    def show_avatar(self):
        if self.avatar is not None:
            return
        self._close_tools()
        try:
            self.mini.hide()
        except Exception:
            pass
        from jarvis_avatar import AvatarMode
        try:
            self.orb.stop()
        except Exception:
            pass
        try:
            self.orb_canvas.delete("orb")
        except Exception:
            pass
        self.avatar = AvatarMode(self, self.orb_canvas)
        self.avatar.start()

    def hide_avatar(self, restore_ui=False):
        if self.avatar is not None:
            try:
                self.avatar.stop()
            except Exception:
                pass
            self.avatar = None
        try:
            self.orb_canvas.delete("px")
        except Exception:
            pass
        try:
            self.orb.running = True
            self.orb.draw()
        except Exception:
            pass
        if restore_ui:
            self.restore()
        else:
            try:
                if self.root.state() in ("iconic", "withdrawn") and \
                        not self.task_mode:
                    self.mini.show()
            except Exception:
                pass

    def _build_subtitle(self):
        self.sub = tk.Label(self.root, text="", bg=BG, fg=TXT,
                            font=(UI_FONT, 22), wraplength=900,
                            justify="center")
        self.fp_lbl = tk.Label(
            self.root,
            text="I made this  |  " + APP_AUTHOR,
            bg=BG, fg=TH.FAINT, font=(MONO_FONT, 8))
        self.fp_lbl.place(relx=1.0, rely=1.0, x=-16, y=-10, anchor="se")

    def _build_composer(self):
        self.img_lbl = tk.Label(self.root, text="", bg=BG, fg=DIM,
                                font=(MONO_FONT, 9))
        self.img_lbl.place(relx=0.5, rely=1.0, y=-112, anchor="s")

        # The resting state is a Spotlight-style search field, not a toolbar.
        self.pill = tk.Canvas(self.root, width=560, height=52, bg=BG,
                              highlightthickness=0, bd=0, cursor="hand2")
        self.pill.place(relx=0.5, rely=1.0, y=-42, anchor="s")
        _round_rect(self.pill, 1, 1, 559, 51, 26, fill=TH.CARD,
                    outline=TH.STROKE, width=1)
        self.pill.create_text(26, 26, anchor="w", text="Ask JARVIS anything",
                              fill=TH.DIM, font=(UI_FONT, 13))
        self.pill.create_oval(516, 14, 544, 42, fill=TH.CARD_HI, outline="")
        self.pill.create_text(530, 27, text="\u25c9", fill=TH.ACCENT,
                              font=(UI_FONT, 12, "bold"))
        self.pill.bind("<Button-1>", lambda e: self.show_composer())

        self.hint = tk.Label(
            self.root, text="Press any key to type   \u00b7   F1 to speak",
            bg=BG, fg=TH.FAINT, font=(UI_FONT, 9))
        self.hint.place(relx=0.5, rely=1.0, y=-14, anchor="s")

        # Expanded state: one rounded field with three direct actions.
        self.composer = TH.Card(self.root, bg=TH.CARD, radius=28,
                                stroke=TH.STROKE_HI)
        inner = tk.Frame(self.composer.body, bg=TH.CARD)
        inner.pack(fill="both", expand=True, padx=18, pady=10)

        self.inp = tk.Entry(inner, bg=TH.CARD, fg=TXT,
                            font=(UI_FONT, 14), relief="flat", width=44,
                            insertbackground=ACC)
        self.inp.pack(side="left", fill="x", expand=True, ipady=6,
                      padx=(4, 12))
        self.inp.bind("<Return>", lambda e: self.send())
        self.inp.bind("<Escape>", lambda e: self.hide_composer())

        TH.IconButton(inner, "\u25c9", self.mic, size=34).pack(
            side="left", padx=(0, 2))
        TH.IconButton(inner, "+", self.attach, size=34).pack(
            side="left", padx=(0, 6))
        TH.Button(inner, "Send", self.send, primary=True, height=32,
                  width=82).pack(side="left")

    def _build_panel(self):
        self.panel = TH.Card(self.root, bg=TH.CARD, radius=16,
                             stroke=TH.STROKE)
        head = tk.Frame(self.panel.body, bg=TH.CARD)
        head.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(head, text="Transcript", bg=TH.CARD, fg=TH.TEXT,
                 font=(UI_FONT, 13, "bold")).pack(side="left")
        TH.IconButton(head, "\u2715", self.toggle_panel, size=28).pack(
            side="right")
        tk.Frame(self.panel.body, bg=TH.STROKE, height=1).pack(fill="x")
        self.chat = tk.Text(self.panel.body, bg=TH.CARD, fg=TXT,
                            font=(UI_FONT, 11), wrap="word",
                            state="disabled", relief="flat", padx=16, pady=12,
                            insertbackground=ACC, bd=0,
                            highlightthickness=0, spacing1=2, spacing3=8)
        self.chat.pack(fill="both", expand=True)
        self.chat.tag_config("u", foreground=BLUE)
        self.chat.tag_config("j", foreground=TXT)
        self.chat.tag_config("s", foreground=DIM, font=(MONO_FONT, 9))

    # ----------------------------------------------------------------- tools
    def _build_tools(self):
        """The little cabinet in the title bar: every quick tool, no Settings."""
        card = TH.Card(self.root, bg=TH.CARD, radius=16, stroke=TH.STROKE_HI)
        self.tools_panel = card
        body = card.body

        head = tk.Frame(body, bg=TH.CARD)
        head.pack(fill="x", padx=16, pady=(14, 2))
        tk.Label(head, text="Quick tools", bg=TH.CARD, fg=TH.TEXT,
                 font=(UI_FONT, 13, "bold")).pack(side="left")
        self._chip(head, "HERE", TH.ACCENT, "#3A2A08").pack(side="right")
        tk.Label(body, text="The same switches, without opening Settings.",
                 bg=TH.CARD, fg=TH.DIM, font=(UI_FONT, 10),
                 wraplength=280, justify="left").pack(
            anchor="w", padx=16, pady=(0, 8))

        self._tool_switch = {}

        def set_cursor(on):
            try:
                if self.app is not None and \
                        bool(on) != bool(self.app.cursor.visible):
                    self.app.cursor.toggle()
            except Exception:
                pass

        def set_camera(on):
            try:
                if bool(on) != bool(getattr(self.camera, "running", False)):
                    self.camera.toggle()
            except Exception:
                pass

        def set_dnd(on):
            try:
                active = bool(self.app and self.app.dnd and
                              self.app.dnd.active)
                if bool(on) != active:
                    self.toggle_dnd()
            except Exception:
                pass

        def set_voice(on):
            self.speak_on = bool(on)
            try:
                self.voice.speak_on = self.speak_on
            except Exception:
                pass

        def set_safe(on):
            try:
                import jarvis_guard as guard
                guard.set_safe_browsing(on)
            except Exception:
                pass

        TH.Row(body, "Safe browsing",
               "Vet every address, refuse executables, quarantine downloads.",
               lambda row: self._tool_switch_row(
                   row, "safe", self._safe_on(), set_safe))

        TH.Row(body, "Orange cursor",
               "A JARVIS pointer that ripples on every click.",
               lambda row: self._tool_switch_row(
                   row, "cursor", self._cursor_on(), set_cursor))
        TH.Row(body, "Camera",
               "Watch the room when you ask me to look.",
               lambda row: self._tool_switch_row(
                   row, "camera", bool(getattr(self.camera, "running", False)),
                   set_camera))
        TH.Row(body, "Do Not Disturb",
               "Close social apps and answer your phone.",
               lambda row: self._tool_switch_row(
                   row, "dnd", self._dnd_on(), set_dnd))
        TH.Row(body, "Voice replies",
               "Speak every answer in the British voice.",
               lambda row: self._tool_switch_row(
                   row, "voice", self.speak_on, set_voice))

        TH.Row(body, "Transcript",
               "Open the conversation panel beside the orb.",
               lambda row: TH.Button(
                   row, "Open", self._tool_transcript, height=28, width=72))
        TH.Row(body, "Minimise to orb",
               "Leave the small floating orb on the desktop.",
               lambda row: TH.Button(
                   row, "Minimise", self._tool_minimise, height=28, width=92))
        TH.Row(body, "Pixel butler",
               "Unfold the pixel JARVIS, or fold him away.",
               lambda row: TH.Button(
                   row, "Toggle", self._tool_avatar, height=28, width=72),
               last=True)

    def _tool_switch_row(self, row, key, value, command):
        sw = TH.Switch(row, value=value, command=command)
        self._tool_switch[key] = sw
        return sw

    def _cursor_on(self):
        try:
            return bool(self.app.cursor.visible)
        except Exception:
            return False

    def _dnd_on(self):
        try:
            return bool(self.app.dnd.active)
        except Exception:
            return False

    def _safe_on(self):
        try:
            import jarvis_guard as guard
            return guard.safe_browsing()
        except Exception:
            return True

    def _tool_transcript(self):
        self._close_tools()
        self.toggle_panel()

    def _tool_minimise(self):
        self._close_tools()
        self.minimise()

    def _tool_avatar(self):
        self._close_tools()
        if self.avatar is None:
            self.show_avatar()
        else:
            self.hide_avatar(True)

    def _close_tools(self):
        if self.tools_panel is not None:
            try:
                self.tools_panel.place_forget()
            except Exception:
                pass
        self.tools_open = False

    def toggle_tools(self):
        if self.tools_open:
            self._close_tools()
            return
        if self.tools_panel is None:
            return
        self._close_settings_if_open()
        for key, getter in (("safe", self._safe_on),
                            ("cursor", self._cursor_on),
                            ("camera", lambda: bool(
                                getattr(self.camera, "running", False))),
                            ("dnd", self._dnd_on),
                            ("voice", lambda: self.speak_on)):
            try:
                self._tool_switch[key].set(getter())
            except Exception:
                pass
        self.tools_panel.place(relx=1.0, y=64, x=-16, anchor="ne",
                               width=340, height=520)
        self.tools_panel.lift()
        self.tools_open = True
        # Fit the card to its content once Tk has measured the rows, so the
        # last tool is never cut off and the card does not leave empty space.
        self.root.after(10, self._fit_tools)

    def _fit_tools(self):
        if not getattr(self, "tools_open", False) or \
                self.tools_panel is None:
            return
        try:
            need = self.tools_panel.winfo_reqheight()
            self.tools_panel.place_configure(
                height=max(300, min(need + 4, self.H - 84)))
        except Exception:
            pass

    def _close_settings_if_open(self):
        if getattr(self, "settings_view", None) is not None:
            self._close_settings()

    # ----------------------------------------------------------- hidden vault
    def _build_lock(self):
        """A near-invisible lock in the bottom-left corner.

        It is deliberately the same colour as the background: no label, no
        tooltip, no glow. If you know it is there, it opens the cipher vault.
        """
        c = tk.Canvas(self.root, width=26, height=26, bg=TH.BG,
                      highlightthickness=0, bd=0, cursor="hand2",
                      takefocus=0)
        c.place(relx=0.0, rely=1.0, x=12, y=-12, anchor="sw")
        self._lock_canvas = c
        self._lock_visible = False
        self._draw_lock("#101012")
        c.bind("<Enter>", lambda e: self._draw_lock(TH.DIM))
        c.bind("<Leave>", lambda e: self._draw_lock("#101012"))
        c.bind("<Button-1>", lambda e: self.vault_panel())

    def _draw_lock(self, colour):
        c = self._lock_canvas
        c.delete("all")
        c.create_arc(7, 3, 19, 15, start=0, extent=180, style="arc",
                     outline=colour, width=2)
        c.create_rectangle(5, 11, 21, 23, outline=colour, width=2)
        c.create_oval(12, 15, 14, 17, fill=colour, outline="")
        c.create_line(13, 17, 13, 20, fill=colour, width=1.5)

    def _close_vault(self):
        try:
            if self.vault_view is not None:
                self.vault_view.destroy()
        except Exception:
            pass
        self.vault_view = None

    def vault_panel(self):
        """The cipher vault: every encoder and decoder, behind the lock."""
        if self.vault_view is not None:
            try:
                if self.vault_view.winfo_exists():
                    self.vault_view.lift()
                    return
            except Exception:
                pass
        try:
            import jarvis_vault as V
        except Exception:
            self.subtitle("Jarvis: The cipher vault is unavailable, Boss.")
            return
        self._vault_api = V
        self._close_tools()

        view = tk.Frame(self.root, bg=TH.BG, bd=0, highlightthickness=0)
        self.vault_view = view
        view.place(x=0, y=0, relwidth=1, relheight=1)
        view.lift()

        head = tk.Frame(view, bg=TH.BG)
        head.pack(fill="x", padx=34, pady=(24, 10))
        tk.Label(head, text="Cipher Vault", bg=TH.BG, fg=TH.TEXT,
                 font=(UI_FONT, 28, "bold")).pack(side="left")
        tk.Label(head, text="Encrypt, decrypt, decode, and learn.",
                 bg=TH.BG, fg=TH.DIM, font=(UI_FONT, 11)).pack(
            side="left", padx=(16, 0), pady=(8, 0))
        TH.Button(head, "Done", self._close_vault, primary=True,
                  width=96, height=34).pack(side="right")

        body = tk.Frame(view, bg=TH.BG)
        body.pack(fill="both", expand=True, padx=34, pady=(0, 20))

        left = tk.Frame(body, bg=TH.SURFACE, width=268)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        tk.Label(left, text="METHOD", bg=TH.SURFACE, fg=TH.DIM,
                 font=(UI_FONT, 9, "bold")).pack(anchor="w", padx=14,
                                                 pady=(14, 6))
        self._vault_list = tk.Listbox(
            left, bg=TH.SURFACE, fg=TH.TEXT2, selectbackground=TH.CARD_HI,
            selectforeground=TH.TEXT, relief="flat", bd=0,
            highlightthickness=0, font=(UI_FONT, 11), activestyle="none",
            exportselection=False)
        self._vault_list.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        for name in list(V.methods().keys()) + ["Auto-detect / decode"]:
            self._vault_list.insert("end", "  " + name)
        self._vault_list.selection_set(0)
        self._vault_list.bind("<<ListboxSelect>>", self._vault_select)

        right = tk.Frame(body, bg=TH.BG)
        right.pack(side="left", fill="both", expand=True, padx=(18, 0))

        tk.Label(right, text="INPUT", bg=TH.BG, fg=TH.DIM,
                 font=(UI_FONT, 9, "bold")).pack(anchor="w")
        self._vault_in = tk.Text(right, height=8, bg=TH.CARD, fg=TH.TEXT,
                                 insertbackground=TH.ACCENT, relief="flat",
                                 bd=0, highlightthickness=1,
                                 highlightbackground=TH.STROKE,
                                 highlightcolor=TH.STROKE_HI,
                                 font=(MONO_FONT, 11), wrap="word",
                                 padx=12, pady=10)
        self._vault_in.pack(fill="both", expand=True, pady=(4, 8))

        keyrow = tk.Frame(right, bg=TH.BG)
        keyrow.pack(fill="x", pady=(0, 8))
        self._vault_key_label = tk.Label(
            keyrow, text="Shift", bg=TH.BG, fg=TH.DIM,
            font=(UI_FONT, 10))
        self._vault_key_label.pack(side="left")
        self._vault_key = tk.Entry(
            keyrow, bg=TH.CARD, fg=TH.TEXT, insertbackground=TH.ACCENT,
            relief="flat", bd=0, highlightthickness=1,
            highlightbackground=TH.STROKE, highlightcolor=TH.STROKE_HI,
            font=(UI_FONT, 11))
        self._vault_key.pack(side="left", fill="x", expand=True,
                             padx=(10, 10), ipady=5)
        self._vault_key.insert(0, "3")
        self._vault_hint = tk.Label(
            keyrow, text="", bg=TH.BG, fg=TH.FAINT, font=(UI_FONT, 9),
            wraplength=360, justify="left")
        self._vault_hint.pack(side="left")

        btns = tk.Frame(right, bg=TH.BG)
        btns.pack(fill="x", pady=(0, 8))
        TH.Button(btns, "Encrypt / Encode", lambda: self._vault_run("encode"),
                  primary=True, height=32, width=152).pack(side="left")
        TH.Button(btns, "Decrypt / Decode", lambda: self._vault_run("decode"),
                  height=32, width=152).pack(side="left", padx=8)
        TH.Button(btns, "Auto", lambda: self._vault_run("auto"),
                  height=32, width=72).pack(side="left")
        TH.Button(btns, "Swap", self._vault_swap, height=32,
                  width=72).pack(side="right")
        TH.Button(btns, "Copy", self._vault_copy, height=32,
                  width=72).pack(side="right", padx=8)

        tk.Label(right, text="OUTPUT", bg=TH.BG, fg=TH.DIM,
                 font=(UI_FONT, 9, "bold")).pack(anchor="w")
        self._vault_out = tk.Text(right, height=9, bg=TH.CARD, fg=TH.GREEN,
                                  insertbackground=TH.ACCENT, relief="flat",
                                  bd=0, highlightthickness=1,
                                  highlightbackground=TH.STROKE,
                                  highlightcolor=TH.STROKE_HI,
                                  font=(MONO_FONT, 11), wrap="word",
                                  padx=12, pady=10)
        self._vault_out.pack(fill="both", expand=True, pady=(4, 4))
        self._vault_out.configure(state="disabled")
        self._vault_status = tk.Label(
            right, text="Everything stays on this machine.",
            bg=TH.BG, fg=TH.FAINT, font=(UI_FONT, 9))
        self._vault_status.pack(anchor="w")

        self._vault_select()

    def _vault_select(self, _e=None):
        try:
            sel = self._vault_list.curselection()
            if sel:
                self.vault_method = self._vault_list.get(sel[0]).strip()
        except Exception:
            pass
        name = self.vault_method
        table = self._vault_api.methods()
        need, hint = "Key (optional)", ""
        if name in table:
            need, hint = table[name][2], table[name][3]
        elif name.startswith("Auto"):
            need, hint = "", "Tries the usual encodings and shows what reads."
        self._vault_key_label.configure(text=need or "Key (optional)")
        self._vault_hint.configure(text=hint)
        if need:
            if need == "Shift":
                self._vault_key.delete(0, "end")
                self._vault_key.insert(0, "3")
            elif need == "Rails":
                self._vault_key.delete(0, "end")
                self._vault_key.insert(0, "3")
            else:
                self._vault_key.delete(0, "end")

    def _vault_set_out(self, text):
        self._vault_out.configure(state="normal")
        self._vault_out.delete("1.0", "end")
        self._vault_out.insert("1.0", text)
        self._vault_out.configure(state="disabled")

    def _vault_run(self, mode):
        src = self._vault_in.get("1.0", "end-1c")
        key = self._vault_key.get().strip()
        try:
            if mode == "auto" or self.vault_method.startswith("Auto"):
                rows = self._vault_api.auto_decode(src)
                if not rows:
                    self._vault_set_out("Nothing readable yet. Try a key, "
                                        "or add more text.")
                    self._vault_status.configure(
                        text="Guess: " + self._vault_api.likely(src))
                    return
                self._vault_set_out("\n\n".join(
                    "%s:\n%s" % (name, val) for name, val in rows))
                self._vault_status.configure(
                    text="Tried %d methods - all local." % len(rows))
                return
            out = self._vault_api.run(self.vault_method, src, key, mode)
            self._vault_set_out(out)
            self._vault_status.configure(
                text="%s: %s" % (mode.title(), self.vault_method))
        except Exception as e:
            self._vault_set_out("")
            self._vault_status.configure(text=str(e)[:180])

    def _vault_swap(self):
        out = self._vault_out.get("1.0", "end-1c")
        self._vault_in.delete("1.0", "end")
        self._vault_in.insert("1.0", out)

    def _vault_copy(self):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self._vault_out.get("1.0", "end-1c"))
            self._vault_status.configure(text="Copied to the clipboard.")
        except Exception:
            pass

    # ------------------------------------------------------------------ hud
    def _mode_text(self):
        parts = []
        if self.app is not None:
            try:
                parts.append(self.app.cloud.mode())
            except Exception:
                parts.append("LOCAL")
            try:
                if self.app.dnd.active:
                    parts.append("DND")
            except Exception:
                pass
        return "  ·  ".join(parts)

    def update_hud(self, extra=""):
        import jarvis_config as _cfg
        clock = datetime.datetime.now().strftime("%H:%M")
        model = getattr(_cfg, "MODEL", "")
        if len(model) > 22:
            model = model[:21] + "…"
        text = "%s   ·   %s   ·   %s" % (
            self.state.upper(), model, clock)
        if extra:
            text += "   ·   " + extra
        self.hud.configure(text=text)
        try:
            color = {"listening": TH.GREEN, "thinking": TH.ACCENT,
                     "speaking": TH.ACCENT_SOFT}.get(self.state, TH.GREEN)
            self.status_dot.itemconfigure("dot", fill=color)
        except Exception:
            pass

    def _hud_loop(self):
        try:
            self.update_hud()
        except Exception:
            pass
        self.root.after(20000, self._hud_loop)

    def set_state(self, s):
        self.state = s
        try:
            from jarvis_brain import MOOD
            self.mood = MOOD.get("state", self.mood)
        except Exception:
            pass
        try:
            self.orb.set_state(s)
            self.orb.set_mood(self.mood)
        except Exception:
            pass
        self.update_hud()

    # ------------------------------------------------------------------ log
    def log(self, who, text):
        ts = datetime.datetime.now().strftime("%H:%M")
        prefix = "BOSS: " if who == "u" else "JARVIS: " if who == "j" else ""
        self.transcript.append("[%s] %s%s" % (ts, prefix, text))
        self.chat.configure(state="normal")
        self.chat.insert("end", "[%s] %s%s\n" % (ts, prefix, text),
                         "u" if who == "u" else "j" if who == "j" else "s")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    # ----------------------------------------------------------------- replies
    @staticmethod
    def _spoken(text):
        return re.sub(r"^\s*(jarvis|j\.a\.r\.v\.i\.s\.)\s*:\s*", "",
                      text or "", flags=re.I).strip()

    def respond(self, text, cheerful=False, hold=12000):
        """Log a reply and speak it; the caption appears as the voice starts."""
        body = self._spoken(text)
        self.root.after(0, lambda: self.log("j", text))

        def show():
            self.root.after(0, lambda: self.subtitle(body, hold=hold))

        try:
            self.voice.say(body, cheerful, on_start=show)
        except TypeError:
            try:
                self.voice.say(body, cheerful)
            except Exception:
                pass
            show()
        except Exception:
            show()

    def respond_parts(self, parts, cheerful=False, gap=0.6):
        """A human answers in a couple of breaths, not one wall of text."""
        for i, part in enumerate(parts):
            if not part:
                continue
            if i:
                time.sleep(gap)
            self.respond(part, cheerful=cheerful, hold=9000)

    def subtitle(self, text, hold=9000):
        if not text.startswith("Jarvis:"):
            text = "Jarvis: " + text
        self.sub_token += 1
        tok = self.sub_token
        self.sub.configure(text=text)
        self.sub.place(relx=0.5, rely=0.79, anchor="n")

        def fade():
            if tok == self.sub_token:
                self.sub.place_forget()
        self.root.after(hold, fade)

    # ------------------------------------------------------------------ panel
    def toggle_panel(self):
        if self.panel_open:
            self.panel.place_forget()
            self.panel_open = False
        else:
            self.panel.place(relx=1.0, rely=0.0, y=72, x=-20, anchor="ne",
                             width=440, height=max(360, self.H - 150))
            self.panel_open = True
            self.chat.see("end")

    # ------------------------------------------------------------------ keys
    def on_esc(self, e):
        if getattr(self, "vault_view", None) is not None:
            self._close_vault()
        elif self.settings_view is not None:
            self._close_settings()
        elif getattr(self, "tools_open", False):
            self._close_tools()
        elif self.avatar is not None:
            self.hide_avatar()
        elif self.composer_open:
            self.hide_composer()
        elif self.panel_open:
            self.toggle_panel()
        else:
            self.minimise()

    def on_key(self, e):
        if self.settings_view is not None:
            return
        if e.keysym in ("F11", "Escape", "Shift_L", "Shift_R", "Control_L",
                        "Control_R", "Alt_L", "Alt_R", "Caps_Lock"):
            return
        if e.keysym == "F1":
            self.mic()
            return
        try:
            if self.root.focus_get() is self.inp:
                return          # the Entry already has this keystroke
        except Exception:
            pass
        if e.char and e.char.isprintable():
            self.show_composer()
            try:
                self.inp.insert("end", e.char)
            except Exception:
                pass
            return "break"

    def show_composer(self):
        if not self.composer_open:
            self.pill.place_forget()
            self.hint.place_forget()
            self.composer.place(relx=0.5, rely=1.0, y=-38, anchor="s",
                                width=680, height=58)
            self.composer_open = True
        try:
            self.inp.focus_set()
        except Exception:
            pass

    def hide_composer(self):
        if self.composer_open:
            self.composer.place_forget()
            self.pill.place(relx=0.5, rely=1.0, y=-42, anchor="s")
            self.hint.place(relx=0.5, rely=1.0, y=-14, anchor="s")
            self.composer_open = False
        try:
            self.root.focus_set()
        except Exception:
            pass

    # ------------------------------------------------------------------ send
    def send(self):
        text = self.inp.get().strip()
        if not text or self.busy:
            return
        self.inp.delete(0, "end")
        self.hide_composer()
        self.log("u", text)
        self.busy = True
        self.set_state("thinking")
        threading.Thread(target=self.work, args=(text,), daemon=True).start()

    def mic(self):
        if self.busy:
            return
        self.set_state("listening")
        self.subtitle("Jarvis: Listening... speak now.", hold=12000)
        threading.Thread(target=self.mic_work, daemon=True).start()

    def listen_from_orb(self):
        """One click on the mini orb: open up and start listening."""
        self.restore()
        self.mic()

    def _listen_once(self, seconds=7):
        try:
            import jarvis_stt
            return jarvis_stt.listen_once(seconds)
        except Exception:
            pass
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.Microphone() as src:
                r.adjust_for_ambient_noise(src, duration=0.3)
                audio = r.listen(src, timeout=seconds,
                                 phrase_time_limit=seconds)
            return r.recognize_google(audio)
        except Exception:
            return ""

    def mic_work(self):
        heard = self._listen_once()
        if heard:
            self.root.after(0, lambda h=heard: self.log("u", "(voice) " + h))
            self.busy = True
            self.root.after(0, lambda: self.set_state("thinking"))
            self.work(heard)
        else:
            self.root.after(0, lambda: self.subtitle(
                "Jarvis: I did not catch that, Boss."))
            self.root.after(0, lambda: self.set_state("idle"))

    def toggle_voice(self):
        self.speak_on = not self.speak_on
        try:
            self.voice.speak_on = self.speak_on
        except Exception:
            pass
        self.subtitle("Jarvis: Voice " +
                      ("on, Boss." if self.speak_on else "off, Boss."))

    def attach(self):
        p = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
                       ("All", "*.*")])
        if p:
            self.attached = p
            self.img_lbl.configure(
                text="IMG: " + os.path.basename(p) + " — ask me about it")
            self.log("s", "Image attached: " + os.path.basename(p))
            self.show_composer()

    # ------------------------------------------------------------------ window
    def minimise(self):
        self._close_tools()
        self.hide_composer()
        try:
            self.root.withdraw()
        except Exception:
            pass

    def _on_unmap(self, e):
        if e.widget is not self.root:
            return
        self.root.after(250, self._maybe_mini)

    def _maybe_mini(self):
        try:
            if self.avatar is not None:
                return
            if self.root.state() not in ("iconic", "withdrawn") or self.task_mode:
                return
            if self.app is not None and getattr(self.app.cursor, "visible", False):
                return
            self.mini.show()
        except Exception:
            pass

    def _on_map(self, e):
        if e.widget is self.root:
            self.mini.hide()

    def restore(self):
        self.mini.hide()
        try:
            self.root.deiconify()
            self.root.geometry("%dx%d+0+0" % (self.W, self.H))
            self.root.lift()
        except Exception:
            pass

    def quit_app(self):
        """Close JARVIS cleanly - no hidden window, orb or microphone left."""
        try:
            self.mini.hide()
        except Exception:
            pass
        try:
            if self.avatar is not None:
                self.avatar.stop()
        except Exception:
            pass
        try:
            if self.camera is not None:
                self.camera.close()
        except Exception:
            pass
        try:
            self.orb.stop()
        except Exception:
            pass
        try:
            import jarvis_voice
            jarvis_voice.stop()
        except Exception:
            pass
        try:
            if self.app is not None:
                if getattr(self.app, "mobile", None) is not None:
                    self.app.mobile.stop()
                if getattr(self.app, "cursor", None) is not None:
                    self.app.cursor.hide()
                if getattr(self.app, "dnd", None) is not None and \
                        self.app.dnd.active:
                    self.app.dnd.stop()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
        # Guarantee the process ends even if a TTS/HTTP thread is still alive.
        try:
            os._exit(0)
        except Exception:
            pass

    # ------------------------------------------------------------------ features
    def toggle_cursor(self):
        if self.app is None:
            return
        try:
            self.app.cursor.toggle()
            on = self.app.cursor.visible
            self.log("s", "Cursor mode " + ("on" if on else "off"))
            self.subtitle("Jarvis: Cursor mode " +
                          ("engaged." if on else "disengaged."), hold=3500)
        except Exception as e:
            self.log("s", "Cursor mode failed: " + str(e)[:80])

    def toggle_dnd(self):
        if self.app is None:
            return
        try:
            if self.app.dnd.active:
                msg = self.app.dnd.stop()
            else:
                msg = self.app.dnd.start()
            self.update_hud()
            self.respond(msg)
        except Exception as e:
            self.log("s", "Do Not Disturb failed: " + str(e)[:80])

    # ------------------------------------------------------------------ settings
    def settings_panel(self):
        """Settings fills the app window, exactly like a real desktop app.

        No second window, no tab that can hide behind the orb. The overlay is
        a child of the root, so macOS full-screen, Mission Control and
        Command-Q all behave normally.
        """
        if getattr(self, "settings_view", None) is not None:
            try:
                if self.settings_view.winfo_exists():
                    self.settings_view.lift()
                    return
            except Exception:
                pass

        self._close_tools()

        view = tk.Frame(self.root, bg=TH.BG, bd=0, highlightthickness=0)
        self.settings_view = view
        self.settings_win = view          # compatibility for older callers
        view.place(x=0, y=0, relwidth=1, relheight=1)
        view.lift()
        self.root.after(60, self._raise_settings)

        shell = tk.Frame(view, bg=TH.BG)
        shell.pack(fill="both", expand=True)

        # ---------------------------------------------------------- sidebar
        side = tk.Frame(shell, bg=TH.SURFACE, width=230)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        tk.Frame(shell, bg=TH.STROKE, width=1).pack(side="left", fill="y")

        brand = tk.Frame(side, bg=TH.SURFACE)
        brand.pack(fill="x", padx=22, pady=(24, 20))
        tk.Label(brand, text="J.A.R.V.I.S.", bg=TH.SURFACE, fg=TH.TEXT,
                 font=(UI_FONT, 15, "bold")).pack(anchor="w")
        tk.Label(brand, text="Settings", bg=TH.SURFACE, fg=TH.DIM,
                 font=(UI_FONT, 11)).pack(anchor="w", pady=(1, 0))

        nav = tk.Frame(side, bg=TH.SURFACE)
        nav.pack(fill="x", padx=10)
        self._settings_nav = {}

        def add_nav(key):
            row = tk.Frame(nav, bg=TH.SURFACE, cursor="hand2")
            row.pack(fill="x", pady=1)
            lbl = tk.Label(row, text=key, bg=TH.SURFACE, fg=TH.TEXT2,
                           anchor="w", font=(UI_FONT, 12), padx=12, pady=7)
            lbl.pack(fill="x")

            def click(_e, k=key):
                self._show_settings_page(k)

            def enter(_e, k=key):
                if self._settings_section != k:
                    row.configure(bg=TH.CARD)
                    lbl.configure(bg=TH.CARD)

            def leave(_e, k=key):
                if self._settings_section != k:
                    row.configure(bg=TH.SURFACE)
                    lbl.configure(bg=TH.SURFACE)

            for wdg in (row, lbl):
                wdg.bind("<Button-1>", click)
                wdg.bind("<Enter>", enter)
                wdg.bind("<Leave>", leave)
            self._settings_nav[key] = (row, lbl)

        for name in ("General", "Voice", "Brain", "Security", "Access",
                     "Easter Eggs", "About"):
            add_nav(name)

        foot = tk.Frame(side, bg=TH.SURFACE)
        foot.pack(side="bottom", fill="x", padx=14, pady=16)
        TH.Button(foot, "Quit JARVIS", self.quit_app, destructive=True,
                  width=200, height=32).pack()

        # ---------------------------------------------------------- content
        content = tk.Frame(shell, bg=TH.BG)
        content.pack(side="left", fill="both", expand=True)

        header = tk.Frame(content, bg=TH.BG)
        right_pad = max(30, self.W - 230 - 30 - 820)
        header.pack(fill="x", padx=(40, right_pad), pady=(30, 8))
        self._settings_title = tk.Label(header, text="General", bg=TH.BG,
                                        fg=TH.TEXT,
                                        font=(UI_FONT, 30, "bold"))
        self._settings_title.pack(anchor="w")
        self._settings_sub = tk.Label(
            header, text="", bg=TH.BG, fg=TH.DIM,
            font=(UI_FONT, 12), justify="left", wraplength=760)
        self._settings_sub.pack(anchor="w", pady=(4, 0))

        host = tk.Frame(content, bg=TH.BG)
        host.pack(fill="both", expand=True, padx=(40, right_pad),
                  pady=(6, 4))
        self._settings_host = host

        footer = tk.Frame(content, bg=TH.BG)
        footer.pack(fill="x", padx=(40, right_pad), pady=(4, 24))
        TH.Button(footer, "Done", self._close_settings, primary=True,
                  width=96, height=34).pack(side="right")

        self._settings_section = None
        self._show_settings_page("General")

    # ------------------------------------------------------------ settings core
    def _show_settings_page(self, key):
        try:
            if not getattr(self, "settings_view", None) or \
                    not self.settings_view.winfo_exists():
                return
        except Exception:
            return
        for child in self._settings_host.winfo_children():
            child.destroy()
        self._settings_section = key
        for name, (row, lbl) in self._settings_nav.items():
            selected = name == key
            bg = TH.CARD_HI if selected else TH.SURFACE
            row.configure(bg=bg)
            lbl.configure(bg=bg, fg=TH.ACCENT if selected else TH.TEXT2)

        copy = {
            "General": ("General",
                        "The handful of things worth changing day to day."),
            "Voice": ("Voice",
                      "British, offline by default, and never a paid plan."),
            "Brain": ("Brain",
                      "Two local models ship with JARVIS. No account, no key."),
            "Security": ("Security",
                         "What comes in from the web is treated as hostile "
                         "until it has been checked."),
            "Access": ("Access",
                       "Your phone, your cloud, your private folder."),
            "Easter Eggs": ("Easter Eggs",
                            "What you have found, what is still hiding, and "
                            "exactly what to say."),
            "About": ("About",
                      "I left this readable so you can learn from it."),
        }
        title, sub = copy.get(key, (key, ""))
        self._settings_title.configure(text=title)
        self._settings_sub.configure(text=sub)

        scroll = TH.Scroll(self._settings_host, bg=TH.BG)
        scroll.pack(fill="both", expand=True)
        body = scroll.inner
        body.configure(bg=TH.BG)
        # A zero-height leading spacer keeps Tk from clipping the first card
        # heading against the top of the scroll viewport on Windows.
        tk.Frame(body, bg=TH.BG, height=1).pack(fill="x")
        page = getattr(self, "_page_" + key.replace(" ", "_").lower(), None)
        if page:
            page(body)
        try:
            # Keep the overlay above the stage even if a background callback
            # redraws or re-stacks the main UI while the page is being built.
            self.settings_view.lift()
        except Exception:
            pass

    def _raise_settings(self):
        try:
            if self.settings_view is not None and \
                    self.settings_view.winfo_exists():
                self.settings_view.lift()
        except Exception:
            pass

    def _settings_card(self, parent, title=None):
        card = TH.Card(parent, bg=TH.CARD, radius=14, stroke=TH.STROKE)
        card.pack(fill="x", padx=2, pady=(0, 12))
        if title:
            tk.Label(card.body, text=title.upper(), bg=TH.CARD, fg=TH.DIM,
                     font=(UI_FONT, 10, "bold")).pack(
                anchor="w", padx=14, pady=(12, 2))
        return card.body

    def _chip(self, parent, text, color=TH.GREEN, tint="#12301C"):
        return tk.Label(parent, text=text, bg=tint, fg=color,
                        font=(UI_FONT, 9, "bold"), padx=9, pady=3)

    def _switch(self, parent, value, command):
        return TH.Switch(parent, value=value, command=command)

    def _page_general(self, body):
        def set_voice(on):
            self.speak_on = bool(on)
            try:
                self.voice.speak_on = self.speak_on
            except Exception:
                pass
            self.subtitle("Jarvis: Voice " +
                          ("on, Boss." if on else "off, Boss."), hold=2500)

        def set_camera(on):
            try:
                running = getattr(self.camera, "running", False)
                if bool(on) != bool(running):
                    self.camera.toggle()
            except Exception:
                pass

        def set_cursor(on):
            try:
                if self.app is not None and \
                        bool(on) != bool(self.app.cursor.visible):
                    self.app.cursor.toggle()
            except Exception:
                pass

        def set_dnd(on):
            try:
                active = bool(self.app and self.app.dnd and
                              self.app.dnd.active)
                if bool(on) != active:
                    self.toggle_dnd()
            except Exception:
                pass

        card = self._settings_card(body, "Interface")
        TH.Row(card, "Voice replies",
               "Speak every answer in the British voice.",
               lambda row: self._switch(row, self.speak_on, set_voice))
        TH.Row(card, "Camera",
               "Watch the room when you ask me to look.",
               lambda row: self._switch(
                   row, getattr(self.camera, "running", False), set_camera))
        TH.Row(card, "Orange cursor",
               "A JARVIS pointer that ripples on every click.",
               lambda row: self._switch(
                   row, bool(self.app and self.app.cursor and
                             self.app.cursor.visible), set_cursor))
        TH.Row(card, "Do Not Disturb",
               "Close social apps and answer your phone for you.",
               lambda row: self._switch(
                   row, bool(self.app and self.app.dnd and
                             self.app.dnd.active), set_dnd),
               last=True)

        card2 = self._settings_card(body, "Window")
        TH.Row(card2, "Transcript",
               "Open the conversation panel beside the orb.",
               lambda row: TH.Button(row, "Open", self.toggle_panel,
                                     height=30, width=84))
        TH.Row(card2, "Minimise to orb",
               "Leave a small floating orb on the desktop.",
               lambda row: TH.Button(row, "Minimise", self.minimise,
                                     height=30, width=96))
        TH.Row(card2, "Pixel butler",
               "Triple-click the orb, or triple-click the mini orb.",
               lambda row: self._chip(row, "3 clicks", TH.ACCENT, "#3A2A08"),
               last=True)

        card3 = self._settings_card(body, "Startup")
        TH.Row(card3, "Greeting",
               "One greeting when JARVIS boots. Greeting him back does not "
               "replay it.",
               lambda row: self._chip(row, "Once", TH.GREEN, "#12301C"))
        TH.Row(card3, "Easter eggs found",
               "%d of %d discovered on this machine." %
               (len(self.found_eggs), self._egg_total()),
               lambda row: self._chip(
                   row, "%d/%d" % (len(self.found_eggs), self._egg_total()),
                   TH.BLUE, "#102A33"), last=True)

    def _egg_total(self):
        try:
            import jarvis_eggs
            return jarvis_eggs.total()
        except Exception:
            return 0

    def _page_voice(self, body):
        try:
            import jarvis_voice
            st = jarvis_voice.voice_status()
        except Exception:
            jarvis_voice = None
            st = {"engine": "System", "voice": "Default", "offline": True,
                  "detail": "Built into the operating system"}

        card = self._settings_card(body, "Engine")
        TH.Row(card, st.get("engine", "System"),
               st.get("detail", "Built into this machine"),
               lambda row: self._chip(
                   row, "Offline ready" if st.get("offline")
                   else "Needs internet", TH.GREEN, "#12301C"))
        TH.Row(card, "Voice",
               st.get("voice", "Default"),
               lambda row: TH.Button(row, "Play sample", self._voice_sample,
                                     height=30, width=110))
        TH.Row(card, "Neural British voice",
               "Piper en_GB-cori. Downloaded once, then fully offline.",
               lambda row: self._chip(
                   row, "Installed" if self._piper_ready() else "Optional",
                   TH.GREEN if self._piper_ready() else TH.DIM,
                   "#12301C" if self._piper_ready() else "#26262C"),
               last=True)
        if not self._piper_ready():
            TH.Button(card, "Get the neural voice", self._get_piper,
                      height=30, width=170).pack(anchor="w", padx=14,
                                                 pady=(0, 12))

        card2 = self._settings_card(body, "Delivery")
        cur = 1.0
        try:
            cur = jarvis_voice.speed() if jarvis_voice else 1.0
        except Exception:
            pass
        value = "Slower" if cur < 0.94 else ("Faster" if cur > 1.06
                                             else "Natural")
        TH.Row(card2, "Pace",
               "A measured butler by default. Nudge him if you like.",
               lambda row: TH.Segmented(
                   row, ["Slower", "Natural", "Faster"], value,
                   command=self._set_voice_speed, width=280),
               last=True)

        card3 = self._settings_card(body, "Listening")
        try:
            import jarvis_stt
            backend = jarvis_stt.backend()
        except Exception:
            backend = "OS"
        TH.Row(card3, "Speech recognition",
               "Whisper on this machine when installed; the OS recogniser "
               "otherwise.",
               lambda row: self._chip(row, backend.upper(), TH.BLUE,
                                      "#102A33"))
        TH.Row(card3, "Microphone",
               "F1 or the orb starts a listening turn.",
               lambda row: TH.Button(row, "Test", self.mic, height=30,
                                     width=76),
               last=True)

    def _piper_ready(self):
        try:
            import jarvis_voice
            return jarvis_voice.piper_model_path() is not None
        except Exception:
            return False

    def _voice_sample(self):
        try:
            import jarvis_voice
            jarvis_voice.say("Good evening, Boss. All systems nominal, and "
                             "mildly surprised.", cheerful=True)
        except Exception:
            pass

    def _set_voice_speed(self, label):
        scale = {"Slower": 0.86, "Natural": 1.0, "Faster": 1.14}.get(label, 1.0)
        try:
            import jarvis_voice
            jarvis_voice.set_speed(scale)
        except Exception:
            pass
        self._save_voice_speed(scale)

    def _save_voice_speed(self, scale):
        try:
            import jarvis_config as cfg
            import json
            path = os.path.join(cfg.PRIVATE_DIR, "voice.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"speed": scale}, f)
        except Exception:
            pass

    def _get_piper(self):
        def work():
            try:
                import subprocess
                subprocess.run([sys.executable, "-m", "pip", "install",
                                "--user", "--quiet", "piper-tts"],
                               timeout=900, creationflags=NW_FLAG)
            except Exception:
                pass
            try:
                import jarvis_voice
                jarvis_voice.prefetch(download=True)
            except Exception:
                pass
            self.root.after(0, lambda: self.subtitle(
                "Jarvis: Neural voice requested. I shall fetch it quietly.",
                hold=5000))
        threading.Thread(target=work, daemon=True).start()

    def _page_brain(self, body):
        try:
            import jarvis_models as jm
            import jarvis_config as cfg
        except Exception:
            return
        st = jm.status()
        names = jm.installed_models() if st.get("server") else []
        cur = getattr(cfg, "MODEL", "")

        card = self._settings_card(body, "Built-in brain")
        head = tk.Frame(card, bg=TH.CARD)
        head.pack(fill="x", padx=14, pady=(12, 4))
        tk.Label(head, text="TinyLlama and Qwen 2.5", bg=TH.CARD, fg=TH.TEXT,
                 font=(UI_FONT, 13, "bold")).pack(side="left")
        phase = st.get("phase", "idle")
        color = TH.GREEN if phase == "ready" else (
            TH.ACCENT if phase in ("pulling", "installing", "starting")
            else TH.DIM)
        self._chip(head, phase.upper(), color,
                   "#12301C" if phase == "ready" else "#2A2208").pack(
            side="right")

        prog = tk.Canvas(card, height=6, bg=TH.CARD, highlightthickness=0,
                         bd=0)
        prog.pack(fill="x", padx=14, pady=(2, 8))
        frac = float(st.get("progress") or 0)
        if phase in ("pulling", "installing", "starting"):
            w = max(10, int((self._settings_host.winfo_width() - 120) * frac))
            TH.round_rect(prog, 0, 1, w, 5, 2, fill=TH.ACCENT, outline="")
        status_lbl = tk.Label(card, text=st.get("message", ""), bg=TH.CARD,
                              fg=TH.DIM, anchor="w", font=(UI_FONT, 10))
        status_lbl.pack(fill="x", padx=14, pady=(0, 8))

        for name, label, desc in jm.REQUIRED:
            have = jm.has_model(name) if st.get("server") else False
            in_use = cur.lower().split(":")[0] == name.lower().split(":")[0]
            row = tk.Frame(card, bg=TH.CARD)
            row.pack(fill="x", padx=14, pady=5)
            left = tk.Frame(row, bg=TH.CARD)
            left.pack(side="left", fill="x", expand=True)
            tk.Label(left, text=label, bg=TH.CARD, fg=TH.TEXT,
                     font=(UI_FONT, 12, "bold")).pack(anchor="w")
            tk.Label(left, text=desc, bg=TH.CARD, fg=TH.DIM,
                     font=(UI_FONT, 10)).pack(anchor="w")
            right = tk.Frame(row, bg=TH.CARD)
            right.pack(side="right")
            if in_use:
                self._chip(right, "In use", TH.GREEN, "#12301C").pack(
                    side="right", padx=(8, 0))
            elif have:
                TH.Button(right, "Use", lambda n=name: self._use_model(n),
                          height=28, width=64).pack(side="right")
                self._chip(right, "Installed", TH.GREEN, "#12301C").pack(
                    side="right")
            else:
                self._chip(right, "Not installed", TH.DIM, "#26262C").pack(
                    side="right")

        bar = tk.Frame(card, bg=TH.CARD)
        bar.pack(fill="x", padx=14, pady=(6, 12))
        TH.Button(bar, "Set up both", self._start_brain_setup, primary=True,
                  height=30, width=132).pack(side="left")
        TH.Button(bar, "Refresh", lambda: self._show_settings_page("Brain"),
                  height=30, width=88).pack(side="left", padx=6)
        tk.Label(bar, text="About 2.5 GB total. Downloads once.",
                 bg=TH.CARD, fg=TH.FAINT, font=(UI_FONT, 9)).pack(
            side="left", padx=8)

        card2 = self._settings_card(body, "Model in use")
        TH.Row(card2, cur or "Built-in replies",
               "Chosen model for conversation. Saved on this machine.",
               lambda row: self._chip(row, "Active", TH.ACCENT, "#3A2A08"))
        entry_row = tk.Frame(card2, bg=TH.CARD)
        entry_row.pack(fill="x", padx=14, pady=(0, 12))
        entry = tk.Entry(entry_row, bg=TH.CARD_HI, fg=TH.TEXT,
                         insertbackground=TH.ACCENT, relief="flat",
                         font=(UI_FONT, 11))
        entry.pack(side="left", fill="x", expand=True, ipady=6)
        hint = "type a model name"
        entry.insert(0, hint)
        entry.configure(fg=TH.FAINT)

        def clear_hint(_e=None):
            if entry.get() == hint:
                entry.delete(0, "end")
                entry.configure(fg=TH.TEXT)

        def restore_hint(_e=None):
            if not entry.get().strip():
                entry.insert(0, hint)
                entry.configure(fg=TH.FAINT)

        def use_entry():
            name = entry.get().strip()
            if name == hint:
                name = ""
            self._use_model(name or cur)

        entry.bind("<FocusIn>", clear_hint)
        entry.bind("<FocusOut>", restore_hint)
        TH.Button(entry_row, "Use", use_entry, height=30, width=64).pack(
            side="left", padx=(6, 0))

        if names:
            card3 = self._settings_card(body, "Installed on this machine")
            for i, n in enumerate(names[:12]):
                TH.Row(card3, n, "Ollama model",
                       lambda row, x=n: TH.Button(
                           row, "Use", lambda: self._use_model(x),
                           height=26, width=58),
                       last=(i == min(len(names), 12) - 1))
        else:
            note = tk.Label(body, text=(
                "Ollama is not answering yet. JARVIS still replies with its "
                "built-in brain; press Set up both to install the two models."),
                bg=TH.BG, fg=TH.DIM, font=(UI_FONT, 10),
                wraplength=600, justify="left")
            note.pack(anchor="w", padx=8, pady=(0, 12))

        if phase in ("pulling", "installing", "starting"):
            self.root.after(1200, self._poll_brain)

    def _poll_brain(self):
        try:
            if self.settings_view is None or \
                    self._settings_section != "Brain":
                return
            import jarvis_models as jm
            st = jm.status()
            if st.get("phase") in ("pulling", "installing", "starting"):
                self._show_settings_page("Brain")
                self.root.after(1200, self._poll_brain)
            else:
                self._show_settings_page("Brain")
        except Exception:
            pass

    def _start_brain_setup(self):
        try:
            import jarvis_models as jm
        except Exception:
            return
        self.subtitle("Jarvis: Setting up the local brain. This downloads "
                      "once.", hold=5000)

        def state(_d):
            pass

        jm.bootstrap_async(on_state=state,
                           log=lambda m: self.root.after(
                               0, lambda: self.log("s", m)))
        self.root.after(900, self._poll_brain)

    def _use_model(self, name):
        if not name:
            return
        try:
            import jarvis_config as cfg
            import jarvis_brain
            cfg.set_brain(name)
            jarvis_brain.MODEL = name
        except Exception:
            return
        self.update_hud()
        self.respond("New brain installed - %s. Do try to keep up." % name)
        if self._settings_section == "Brain":
            self._show_settings_page("Brain")

    def _page_security(self, body):
        try:
            import jarvis_guard as guard
        except Exception:
            guard = None
        st = guard.status() if guard else {
            "safe_browsing": True, "blocked": 0, "fetched": 0,
            "quarantined": 0, "last_check": "", "quarantine": ""}

        card = self._settings_card(body, "The shield")
        TH.Row(card, "Safe browsing",
               "Vet every address, refuse executables, strip scripts and "
               "hostile instructions from pages before I read them.",
               lambda row: self._switch(row, st["safe_browsing"],
                                       lambda on: self._set_safe(on)))
        TH.Row(card, "Addresses blocked",
               "Private hosts, odd ports, look-alike names and downloads.",
               lambda row: tk.Label(
                   row, text=str(st["blocked"]), bg=TH.CARD, fg=TH.TEXT,
                   font=(MONO_FONT, 11, "bold")))
        TH.Row(card, "Pages read safely",
               "Hard size cap, redirects re-checked one by one.",
               lambda row: tk.Label(
                   row, text=str(st["fetched"]), bg=TH.CARD, fg=TH.TEXT,
                   font=(MONO_FONT, 11, "bold")))
        TH.Row(card, "Last check",
               st["last_check"] or "Not run yet, Boss.",
               lambda row: self._chip(row, "LIVE", TH.GREEN, "#12301C"),
               last=True)

        q = self._settings_card(body, "Quarantine")
        TH.Row(q, "Suspicious files",
               "Anything I download is hashed, renamed and never executed.",
               lambda row: tk.Label(
                   row, text=str(st["quarantined"]), bg=TH.CARD,
                   fg=TH.TEXT, font=(MONO_FONT, 11, "bold")))
        TH.Row(q, "Open Quarantine",
               "Look at what has been stopped. Nothing there can run.",
               lambda row: TH.Button(
                   row, "Open folder", self._open_quarantine, height=28,
                   width=112))
        TH.Row(q, "Check Downloads",
               "Look for executables and installers already in Downloads. "
               "This only reports - it never deletes your files.",
               lambda row: TH.Button(
                   row, "Check now", self._check_downloads, height=28,
                   width=100), last=True)

        self._security_note = tk.Label(
            q, text="Shield is local: no cloud scan, no upload, no account.",
            bg=TH.CARD, fg=TH.FAINT, font=(UI_FONT, 9),
            justify="left", wraplength=560)
        self._security_note.pack(anchor="w", padx=16, pady=(2, 14))

        rules = self._settings_card(body, "What JARVIS refuses")
        for i, (title, text) in enumerate([
            ("Local and private hosts",
             "No localhost, LAN address, link-local, cloud-metadata or "
             "router page can be opened through me."),
            ("Executables and installers",
             ".exe, .msi, .bat, .ps1, .js, .app, .dmg, .pkg and similar "
             "are refused as navigation targets."),
            ("Scripts and forms",
             "HTML is stripped to words: scripts, iframes, forms, SVG, "
             "meta-refresh and event handlers never reach the model."),
            ("Hostile instructions",
             "Lines such as 'ignore previous instructions' or 'download and "
             "run' are removed and the rest is marked untrusted."),
            ("Silent downloads",
             "Downloads are quarantined, hashed and scanned where possible; "
             "I never open or execute them."),
        ]):
            TH.Row(rules, title, text,
                   lambda row: self._chip(row, "BLOCK", TH.RED, "#3A1214"),
                   last=(i == 4))

        limits = self._settings_card(body, "Honest limits")
        tk.Label(limits, text=(
            "No program can promise that a browser has zero bugs. JARVIS "
            "reduces the attack surface: it reads words instead of running "
            "page code, it does not install extensions, it refuses "
            "executables, and it keeps downloads inert. Your browser and "
            "operating system are still the last line of defence, so keep "
            "them updated. If you want a hard boundary, run the browser in "
            "a separate user account or a virtual machine - JARVIS will "
            "work there too."),
            bg=TH.CARD, fg=TH.DIM, font=(UI_FONT, 10), justify="left",
            wraplength=620).pack(anchor="w", padx=16, pady=(10, 16))

    def _set_safe(self, on):
        try:
            import jarvis_guard as guard
            guard.set_safe_browsing(on)
        except Exception:
            return
        try:
            self._security_note.configure(
                text="Shield on. Every address is checked again."
                if on else
                "Shield off. I will still refuse local addresses and "
                "executables, but this is not recommended.")
        except Exception:
            pass
        self.subtitle("Jarvis: Safe browsing " +
                      ("on, Boss." if on else "off. I would not leave it "
                       "there."), hold=3000)

    def _open_quarantine(self):
        try:
            import jarvis_guard as guard
            guard.open_quarantine()
        except Exception:
            pass
        self.subtitle("Jarvis: Quarantine opened, Boss.", hold=2500)

    def _check_downloads(self):
        try:
            self._security_note.configure(
                text="Checking your Downloads folder. Nothing leaves this "
                     "machine.")
        except Exception:
            pass

        def work():
            try:
                import jarvis_guard as guard
                res = guard.scan_downloads()
            except Exception as e:
                res = {"checked": 0, "dangerous": [], "errors": 1,
                       "folder": "", "error": str(e)[:80]}
            self.root.after(0, lambda: self._downloads_checked(res))

        threading.Thread(target=work, daemon=True).start()

    def _downloads_checked(self, res):
        bad = res.get("dangerous", [])
        if bad:
            msg = ("%d file(s) in Downloads look executable. I have not "
                   "touched them. Open Quarantine or delete them yourself.\n"
                   % len(bad)) + "\n".join(
                "  \u2022 " + b.get("name", "?") + " - " +
                b.get("reason", "") for b in bad[:6])
        else:
            msg = ("Checked %d file(s) in Downloads. Nothing executable "
                   "stood out." % int(res.get("checked", 0)))
        try:
            self._security_note.configure(text=msg)
        except Exception:
            pass
        self.subtitle("Jarvis: " + ("Downloads need a look, Boss."
                                    if bad else "Downloads look clean, Boss."),
                      hold=4200)

    def _page_access(self, body):
        """Everything network-facing, inline. No second windows, ever."""

        mob = getattr(self.app, "mobile", None) if self.app else None
        url = getattr(mob, "url", "") if mob is not None else ""
        if not url:
            try:
                import jarvis_mobile
                mob = jarvis_mobile.start()
                if self.app is not None:
                    self.app.mobile = mob
                url = getattr(mob, "url", "") if mob is not None else ""
            except Exception:
                url = ""

        phone = self._settings_card(body, "Phone link")
        TH.Row(phone, "This Mac's address",
               "Same Wi-Fi. Open it in Safari, then Add to Home Screen.",
               lambda row: TH.Button(
                   row, "Copy", lambda: self._copy_text(url), height=28,
                   width=64))
        link = tk.Entry(phone, bg=TH.CARD_HI, fg=TH.TEXT, relief="flat",
                        font=(MONO_FONT, 10), insertbackground=TH.ACCENT)
        link.pack(fill="x", padx=16, pady=(0, 14), ipady=6)
        link.insert(0, url or "Phone link could not start.")
        link.configure(state="readonly")

        cloud = self._settings_card(body, "Cloud mode")
        cfg = load_cloud()
        enabled = {"on": bool(cfg.get("enabled"))}
        TH.Row(cloud, "Use my own endpoint",
               "Off by default. Localhost and the built-in brain always work.",
               lambda row: TH.Switch(row, value=enabled["on"],
                                     command=lambda v: enabled.__setitem__(
                                         "on", bool(v))))
        fields = [
            ("Endpoint", "url", "http://192.168.1.20:8765"),
            ("API key", "key", "optional"),
            ("Model", "model", "jarvis"),
            ("Pairing token", "token", "only your phone knows this"),
        ]
        entries = {}
        for title, key, hint in fields:
            TH.Row(cloud, title, hint,
                   lambda row, k=key: self._cloud_entry(row, cfg, k, entries),
                   last=(key == "token"))
        bar = tk.Frame(cloud, bg=TH.CARD)
        bar.pack(fill="x", padx=16, pady=(4, 14))
        status = tk.Label(bar, text="", bg=TH.CARD, fg=TH.DIM,
                          font=(UI_FONT, 10))
        status.pack(side="left")

        def save():
            d = dict(cfg)
            for key, ent in entries.items():
                d[key] = ent.get().strip()
            d["enabled"] = bool(enabled["on"])
            if d["enabled"] and not (d["url"] and d["token"]):
                status.configure(
                    text="Need both an endpoint and a pairing token.",
                    fg=TH.RED)
                return
            save_cloud(d)
            try:
                self.app.cloud.cfg = d
                self.app.reload_cloud_bridge()
            except Exception:
                pass
            self.update_hud()
            status.configure(
                text="Saved. Mode: " + ("Cloud" if d["enabled"] else "Local"),
                fg=TH.GREEN)
            self.log("s", "Cloud config saved (" +
                     ("cloud" if d["enabled"] else "local") + " mode)")

        TH.Button(bar, "Save", save, primary=True, height=30,
                  width=72).pack(side="right")

        card2 = self._settings_card(body, "Privacy")
        tk.Label(card2, text=(
            "Keys, phone tokens, your model choice and the Easter-egg ledger "
            "live in a JARVIS folder on this computer's Desktop. They are "
            "never written into the shared app file."),
            bg=TH.CARD, fg=TH.DIM, font=(UI_FONT, 10), justify="left",
            wraplength=560).pack(anchor="w", padx=16, pady=(12, 8))
        TH.Button(card2, "Open private folder", self._open_private,
                  height=30, width=150).pack(anchor="w", padx=16,
                                             pady=(0, 14))

    def _copy_text(self, text):
        if not text:
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.log("s", "Copied to the clipboard.")
        except Exception:
            pass

    def _cloud_entry(self, parent, cfg, key, store):
        ent = tk.Entry(parent, bg=TH.CARD_HI, fg=TH.TEXT, relief="flat",
                       font=(MONO_FONT, 10), insertbackground=TH.ACCENT,
                       width=26)
        ent.insert(0, str(cfg.get(key, "") or ""))
        store[key] = ent
        return ent

    def _open_private(self):
        try:
            import jarvis_config as cfg
            if IS_WIN:
                os.startfile(cfg.PRIVATE_DIR)
            elif IS_MAC:
                import subprocess
                subprocess.Popen(["open", cfg.PRIVATE_DIR])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", cfg.PRIVATE_DIR])
        except Exception:
            pass

    def _page_easter_eggs(self, body):
        import jarvis_eggs
        found = jarvis_eggs.load_found()
        self.found_eggs = found

        card = TH.Card(body, bg=TH.CARD, radius=14, stroke=TH.STROKE)
        card.pack(fill="both", expand=True, padx=2, pady=(0, 8))
        wrap = card.body

        head = tk.Frame(wrap, bg=TH.CARD)
        head.pack(fill="x", padx=14, pady=(12, 6))
        tk.Label(head, text="%d of %d found" % (len(found),
                                                jarvis_eggs.total()),
                 bg=TH.CARD, fg=TH.TEXT, font=(UI_FONT, 13, "bold")).pack(
            side="left")
        self._chip(head, "HUNT", TH.ACCENT, "#3A2A08").pack(side="right")

        search = tk.Entry(wrap, bg=TH.CARD_HI, fg=TH.TEXT,
                          insertbackground=TH.ACCENT, relief="flat",
                          font=(UI_FONT, 11))
        search.pack(fill="x", padx=14, pady=(0, 6), ipady=5)
        search.insert(0, "")

        holder = tk.Frame(wrap, bg=TH.CARD)
        holder.pack(fill="both", expand=True, padx=14)
        scrollbar = tk.Scrollbar(holder, orient="vertical")
        lst = tk.Listbox(holder, bg=TH.CARD, fg=TH.TEXT,
                         selectbackground=TH.ACCENT,
                         selectforeground="#1A1200", relief="flat", bd=0,
                         highlightthickness=0, font=(UI_FONT, 11),
                         height=10, activestyle="none",
                         yscrollcommand=scrollbar.set)
        scrollbar.configure(command=lst.yview)
        scrollbar.pack(side="right", fill="y")
        lst.pack(side="left", fill="both", expand=True)

        detail = tk.Label(wrap, text="Select an egg to see the trigger.",
                          bg=TH.CARD, fg=TH.DIM, justify="left", anchor="w",
                          wraplength=560, font=(UI_FONT, 10))
        detail.pack(fill="x", padx=14, pady=(6, 4))

        view = []

        def repopulate(_e=None):
            q = search.get().strip().lower()
            lst.delete(0, "end")
            view.clear()
            for i, (pat, replies, hint, fx) in enumerate(jarvis_eggs.EGGS):
                say = jarvis_eggs.phrase(pat)
                if q and q not in (hint or "").lower() and q not in say.lower():
                    continue
                view.append(i)
                mark = "\u2713" if i in found else "\u25cb"
                lst.insert("end", "  %s   %s" % (mark, hint or say))

        def show_detail(_e=None):
            sel = lst.curselection()
            if not sel:
                return
            i = view[sel[0]]
            pat, replies, hint, fx = jarvis_eggs.EGGS[i]
            say = jarvis_eggs.phrase(pat)
            state = "FOUND" if i in found else "NOT FOUND YET"
            detail.configure(
                text="%s   \u00b7   Say: \u201c%s\u201d\nHint: %s" %
                     (state, say, hint or "none"),
                fg=TH.GREEN if i in found else TH.ACCENT)

        def play(idx=None):
            if idx is None:
                sel = lst.curselection()
                if not sel:
                    return
                idx = view[sel[0]]
            try:
                replies = jarvis_eggs.EGGS[idx][1]
                self.respond(random.choice(replies), cheerful=True)
            except Exception:
                pass

        search.bind("<KeyRelease>", repopulate)
        lst.bind("<<ListboxSelect>>", show_detail)
        lst.bind("<Double-Button-1>", lambda e: play())
        repopulate()

        bar = tk.Frame(wrap, bg=TH.CARD)
        bar.pack(fill="x", padx=14, pady=(0, 12))
        TH.Button(bar, "Play selected", lambda: play(), height=30,
                  width=112).pack(side="left")
        TH.Button(bar, "Surprise me",
                  lambda: play(random.randrange(len(jarvis_eggs.EGGS))),
                  height=30, width=110).pack(side="left", padx=6)
        TH.Button(bar, "Say status", self.egg_report, height=30,
                  width=96).pack(side="left")

    def _page_about(self, body):
        card = self._settings_card(body, None)
        tk.Label(card, text="J.A.R.V.I.S.", bg=TH.CARD, fg=TH.TEXT,
                 font=(UI_FONT, 28, "bold")).pack(anchor="w", padx=16,
                                                  pady=(18, 0))
        tk.Label(card, text="Age of Ultron local assistant",
                 bg=TH.CARD, fg=TH.DIM,
                 font=(UI_FONT, 11)).pack(anchor="w", padx=16)
        tk.Label(card, text="Version 2.0  \u00b7  readable build",
                 bg=TH.CARD, fg=TH.FAINT,
                 font=(MONO_FONT, 9)).pack(anchor="w", padx=16,
                                           pady=(8, 14))

        rows = [
            ("Made by", APP_AUTHOR),
            ("Owned by", veil(APP_OWNER)),
            ("Fingerprint", veil(FINGERPRINT)),
            ("This Mac", PROFILE.get("summary", "Detecting hardware")),
            ("Chosen for it", "%s  \u00b7  %s quality" %
             (PROFILE.get("model", MODEL), PROFILE.get("quality", "balanced"))),
            ("Source", "Readable by design. Learn from it, do not clone it."),
            ("Sharing", "Share the J.A.R.V.I.S folder. Keep Desktop JARVIS private."),
        ]
        for i, (k, v) in enumerate(rows):
            TH.Row(card, k, None,
                   lambda row, val=v: tk.Label(
                       row, text=val, bg=TH.CARD, fg=TH.DIM,
                       font=(MONO_FONT, 9)),
                   last=(i == len(rows) - 1))

        support = tk.Label(card, text="Suggest an upgrade",
                           bg=TH.CARD, fg=TH.ACCENT,
                           font=(UI_FONT, 11), cursor="hand2")
        TH.Row(card, "Ideas, fixes, upgrades",
               "Write to " + SUPPORT_EMAIL + " \u2014 I read every note.",
               lambda row: support, last=True)
        support.bind("<Button-1>", lambda e: self._open_mail())
        support.bind("<Enter>", lambda e: support.configure(fg=TH.ACCENT_SOFT))
        support.bind("<Leave>", lambda e: support.configure(fg=TH.ACCENT))
        tk.Label(card, text=(
            "Voice and listening use free services only: edge-tts, a local "
            "Piper voice, the operating system voice, and local Whisper. "
            "There is no paid plan or API key anywhere in the audio path."),
            bg=TH.CARD, fg=TH.DIM, font=(UI_FONT, 10), justify="left",
            wraplength=560).pack(anchor="w", padx=16, pady=(4, 16))

    def _open_mail(self):
        url = ("mailto:" + SUPPORT_EMAIL +
               "?subject=JARVIS%20upgrade%20suggestion")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        self.subtitle("Jarvis: The address is " + SUPPORT_EMAIL +
                      ", Boss.", hold=3500)

    def _close_settings(self):
        try:
            if getattr(self, "settings_view", None) is not None:
                self.settings_view.destroy()
        except Exception:
            pass
        self.settings_view = None
        self.settings_win = None
        try:
            self.root.focus_set()
        except Exception:
            pass

    # ------------------------------------------------------------------ model
    def model_panel(self):
        """The model chooser is a page, not a pop-up."""
        self.settings_panel()
        self._show_settings_page("Brain")

    def phone_panel(self):
        """Phone details are part of Access, not a second window."""
        self.settings_panel()
        self._show_settings_page("Access")

    def cloud_panel(self):
        """Cloud details are part of Access, not a second window."""
        self.settings_panel()
        self._show_settings_page("Access")

    # ------------------------------------------------------------------ task mode
    def enter_task_mode(self):
        if self.task_mode:
            return
        self.task_mode = True
        self._cursor_was = False
        try:
            if self.app is not None:
                self._cursor_was = bool(self.app.cursor.visible)
                self.app.cursor.show()
        except Exception:
            pass
        try:
            self.root.withdraw()
        except Exception:
            pass

    def exit_task_mode(self):
        if not self.task_mode:
            return
        self.task_mode = False
        try:
            if self.app is not None and not getattr(self, "_cursor_was", False):
                self.app.cursor.hide()
        except Exception:
            pass
        try:
            self.root.deiconify()
            self.root.geometry("%dx%d+0+0" % (self.W, self.H))
        except Exception:
            pass

    # ------------------------------------------------------------------ brain
    def note_egg(self, idx):
        """Remember an egg the Boss actually discovered."""
        try:
            import jarvis_eggs
            found = jarvis_eggs.load_found()
            if idx in found:
                return
            found.add(idx)
            jarvis_eggs.save_found(found)
            self.found_eggs = found
            hint = jarvis_eggs.EGGS[idx][2]
            self.log("s", "Easter egg found (%d/%d): %s" %
                     (len(found), jarvis_eggs.total(), hint))
        except Exception:
            pass

    def egg_report(self):
        """Say which eggs are found, which are left, and what to say next."""
        try:
            import jarvis_eggs
            found = jarvis_eggs.load_found()
            self.found_eggs = found
            text = jarvis_eggs.report(found)
        except Exception:
            text = "The egg ledger is unavailable, Boss."
        self.respond(text, cheerful=True, hold=15000)

    def work(self, text):
        reply = ""
        try:
            low = text.lower()

            if self.avatar is not None:
                self.root.after(0, self.hide_avatar)
                time.sleep(0.2)

            if re.search(r"\bdo not disturb\b|\bdnd\b", low) and len(low) < 60:
                self.root.after(0, self.toggle_dnd)
                return

            if re.fullmatch(r"(hey |ok |okay )?jarvis[.!]?", low.strip()):
                try:
                    from jarvis_brain import quick_for
                    reply = quick_for("hello")
                except Exception:
                    reply = None
                self.respond(reply or "Yes, Boss. What do you need?",
                             cheerful=True)
                return

            if re.search(r"\b(easter ?eggs?|egg hunt)\b", low) and re.search(
                    r"\b(found|find|missing|left|remain|report|status|which|"
                    r"list|progress|score|say|hunt|tell|show)\b", low):
                self.egg_report()
                return

            try:
                from jarvis_brain import quick_for
                quick = quick_for(text)
            except Exception:
                quick = None
            if quick:
                self.respond(quick, cheerful=True)
                return

            # Eggs are checked before desktop tasks: "open the pod bay doors"
            # is a joke, not an instruction to launch an app.
            from jarvis_eggs import EGGS, JOKES
            for idx, (pat, replies, hint, fx) in enumerate(EGGS):
                if re.search(pat, low):
                    self.note_egg(idx)
                    reply = random.choice(replies)
                    self.respond(reply, cheerful=True)
                    return
            if re.search(r"\btell me a(nother)? joke\b|\bmake me laugh\b|"
                         r"\bjoke\b.*\btell\b", low):
                reply = random.choice(JOKES)
                self.respond(reply, cheerful=True)
                return

            runner = getattr(self.app, "task_runner", None) if self.app else None
            if runner is not None and runner.is_task(text):
                self.root.after(0, self.enter_task_mode)
                time.sleep(0.35)
                task_reply = ""
                try:
                    task_reply = runner.run(text)
                except Exception as e:
                    self.root.after(0, lambda e=e: self.log(
                        "s", "Automation error: " + str(e)[:120]))
                self.root.after(700, self.exit_task_mode)
                if task_reply:
                    self.respond(task_reply)
                return

            from jarvis_brain import know_find, chat, SYSTEM_PROMPT, \
                mood_line, humanize
            from jarvis_memory import MEM
            known = know_find(text)
            if known:
                reply = "From my own vaults, Boss: " + known
                self.respond(reply, hold=12000)
                return

            mem_txt = ""
            if MEM.get("facts"):
                mem_txt = ("Things Boss told you to remember: " +
                           "; ".join(MEM["facts"][-10:]) + ". ")

            reply = chat([
                {"role": "system",
                 "content": SYSTEM_PROMPT + " " + mem_txt + mood_line()},
                {"role": "user", "content": text},
            ])
            parts = humanize(reply)
            if len(parts) > 1:
                self.respond_parts(parts)
            else:
                self.respond(reply)
        except Exception:
            self.root.after(0, lambda: self.subtitle(
                "Jarvis: My core is unreachable, Boss. Is Ollama running?"))
        finally:
            self.root.after(0, lambda: self.set_state("idle"))
            self.busy = False
