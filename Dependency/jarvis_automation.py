# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS Automation - readable source module.

Contains:
    CursorMode   : the floating orange "Jarvis" cursor that drives the real mouse
    TaskRunner   : opens Chrome, searches, types, clicks, adds to cart
    DoNotDisturb : blocks social apps/sites and warns on screen
    WakeWord     : listens for "Hey Jarvis" / "Do Not Disturb"
    CloudToggle  : local Ollama <-> cloud endpoint, falls back to local offline
    startup_cleanup : minimises the terminal and File Explorer at launch

Decrypted in memory by jarvis_loader.py. Nothing is written to disk.
"""
import os
import sys
import time
import math
import re
import threading
import subprocess
import webbrowser
import urllib.parse

from jarvis_config import (IS_WIN, IS_MAC, IS_LINUX, NW_FLAG,
                           load_cloud, save_cloud, online)

# --------------------------------------------------------------------- helpers
def _pyautogui():
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.05
        return pyautogui
    except Exception:
        return None


def _have(cmd):
    try:
        return subprocess.call(["which", cmd], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL) == 0
    except Exception:
        return False


# ------------------------------------------------------------ startup cleanup
def minimize_terminal_and_explorer():
    """Hide the console window and File Explorer windows that opened with us."""
    try:
        if IS_WIN:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            SW_MINIMIZE = 6

            # the console that launched us
            hwnd = kernel32.GetConsoleWindow()
            if hwnd:
                user32.ShowWindow(hwnd, SW_MINIMIZE)

            # every Explorer window
            EnumWindows = user32.EnumWindows
            GetClassNameW = user32.GetClassNameW
            GetWindowTextW = user32.GetWindowTextW
            IsWindowVisible = user32.IsWindowVisible
            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND,
                                             wintypes.LPARAM)

            def _cb(h, l):
                if not IsWindowVisible(h):
                    return True
                buf = ctypes.create_unicode_buffer(256)
                GetClassNameW(h, buf, 256)
                if buf.value == "CabinetWClass":
                    user32.ShowWindow(h, SW_MINIMIZE)
                return True

            EnumWindows(WNDENUMPROC(_cb), 0)
            return True

        if IS_MAC:
            subprocess.run(
                ["osascript", "-e",
                 'tell application "Terminal" to set visible of every window to false'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            subprocess.run(
                ["osascript", "-e",
                 'tell application "Finder" to set collapsed of every window to true'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            return True
    except Exception:
        pass
    return False


# ------------------------------------------------------------------ cursor
class CursorMode:
    """
    An independent orange cursor.

    While it is active the real OS arrow is hidden, so this is the only pointer
    you see: it moves with you, click-throughs to whatever is underneath, and
    ripples on every click. During a task the automation moves the real pointer,
    so the chip travels with it and appears to be doing the clicking itself.
    """

    ARROW_W = 12
    ARROW_H = 18
    PLATE_H = 18

    def __init__(self, root):
        self.root = root
        self.window = None
        self.canvas = None
        self.running = False
        self.visible = False
        self.after_id = None
        self.W, self.H = 90, 22
        self._plate_w = 56
        self._os_hidden = False
        self._was_down = False
        self._ripple_step = None

    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show()

    # ---------------------------------------------------------- os cursor
    def _os_hide(self):
        try:
            import ctypes
            u = ctypes.windll.user32
            for _ in range(24):
                if u.ShowCursor(False) < 0:
                    break
            self._os_hidden = True
        except Exception:
            self._os_hidden = False

    def _os_show(self):
        if not self._os_hidden:
            return
        try:
            import ctypes
            u = ctypes.windll.user32
            for _ in range(24):
                if u.ShowCursor(True) >= 0:
                    break
        except Exception:
            pass
        self._os_hidden = False

    def _click_through(self):
        """Never steal a click from the app underneath."""
        try:
            import ctypes
            u = ctypes.windll.user32
            hwnd = self.window.winfo_id()
            parent = u.GetParent(hwnd) or hwnd
            GWL_EXSTYLE = -20
            style = u.GetWindowLongW(parent, GWL_EXSTYLE)
            style |= 0x00000020      # WS_EX_TRANSPARENT
            style |= 0x08000000      # WS_EX_NOACTIVATE
            style |= 0x00000080      # WS_EX_TOOLWINDOW
            u.SetWindowLongW(parent, GWL_EXSTYLE, style)
        except Exception:
            pass

    def show(self):
        if self.visible:
            return
        import tkinter as tk
        import tkinter.font as tkfont

        font = tkfont.Font(family="Segoe UI", size=9, weight="bold")
        self._plate_w = font.measure("Jarvis") + 12
        self.W = self.ARROW_W + 2 + self._plate_w
        self.H = self.PLATE_H + 4

        self.window = tk.Toplevel(self.root)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        try:
            self.window.attributes("-transparentcolor", "#010101")
        except Exception:
            pass
        try:
            self.window.attributes("-transparent", True)
        except Exception:
            pass
        bg = "#010101"
        self.window.configure(bg=bg)
        self.window.geometry("%dx%d+0+0" % (self.W, self.H))

        self.canvas = tk.Canvas(self.window, width=self.W, height=self.H,
                                bg=bg, highlightthickness=0, bd=0)
        self.canvas.pack()

        # compact black chip, just wide enough for the word
        self._round_rect(self.ARROW_W + 1, 2,
                         self.ARROW_W + 1 + self._plate_w, 2 + self.PLATE_H,
                         6, fill="#000000", outline="#ff8c00", width=1)
        self.canvas.create_text(
            self.ARROW_W + 1 + self._plate_w / 2, 2 + self.PLATE_H / 2,
            text="Jarvis", fill="#ff3b30", font=("Segoe UI", 9, "bold"))

        self._arrow()

        self.visible = True
        self.running = True
        self._click_through()
        self._os_hide()
        import atexit
        try:
            atexit.register(self._os_show)
        except Exception:
            pass
        self._follow()

    def _round_rect(self, x1, y1, x2, y2, r, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
               x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
               x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        self.canvas.create_polygon(pts, smooth=True, **kw)

    def _arrow(self):
        """Normal-size cursor arrow: orange body, black edge, white glint."""
        body = [0, 0, 0, 17, 4.6, 12.6, 7.2, 18, 9.4, 17,
                6.8, 11.8, 12, 11.8]
        self.canvas.create_polygon(body, fill="#ff8c00", outline="#000000",
                                   width=1, joinstyle="miter")
        # pixel glint so it reads like a real pointer at a glance
        self.canvas.create_polygon([2, 2, 2, 7, 3.6, 5.4, 5.4, 5.4],
                                   fill="#ffd9a0", outline="")

    def _ripple(self, fresh=False):
        if self.canvas is None:
            return
        if fresh:
            self._ripple_step = 0
        if self._ripple_step is None:
            return
        self.canvas.delete("ripple")
        step = self._ripple_step
        if step > 5:
            self._ripple_step = None
            return
        r = 3 + step * 2.2
        color = ["#ffd27a", "#ffb347", "#ff8c00", "#c96a00",
                 "#8a4a00", "#3a2000"][min(step, 5)]
        self.canvas.create_oval(-r, -r, r, r, outline=color,
                                width=max(1, 2 - step // 3), tags="ripple")
        self._ripple_step = step + 1

    def hide(self):
        self.running = False
        self.visible = False
        if self.after_id is not None:
            try:
                self.root.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None
        if self.window is not None:
            try:
                self.window.destroy()
            except Exception:
                pass
        self.window = None
        self._os_show()

    def _mouse_down(self):
        try:
            import ctypes
            return bool(ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000)
        except Exception:
            return False

    def _follow(self):
        """Main-thread loop: Tk must never be driven from a worker thread."""
        if not self.running or self.window is None:
            return
        try:
            x = self.window.winfo_pointerx()
            y = self.window.winfo_pointery()
            sw = self.window.winfo_screenwidth()
            sh = self.window.winfo_screenheight()
            # arrow tip exactly on the pointer, chip to its right
            wx = min(max(0, x), sw - self.W - 2)
            wy = min(max(0, y), sh - self.H - 2)
            self.window.geometry("+%d+%d" % (wx, wy))
            down = self._mouse_down()
            if down and not self._was_down:
                self._ripple(True)
            elif self._ripple_step is not None:
                self._ripple()
            self._was_down = down
        except Exception:
            pass
        try:
            self.after_id = self.root.after(16, self._follow)
        except Exception:
            self.after_id = None


# ------------------------------------------------------------------ task runner
class TaskRunner:
    """
    Turns a spoken/typed instruction into real desktop actions.

    Real mouse movement comes from pyautogui, so the CursorMode plate follows
    it. Browser work uses Selenium when it is installed (reliable clicking on
    Amazon), and falls back to opening the search URL in the default browser.
    """

    def __init__(self, cursor=None, log=None):
        self.cursor = cursor
        self.log = log or (lambda m: None)
        self.stop_flag = False
        self.driver = None

    # -- basic actions -----------------------------------------------------
    def move_to(self, x, y, duration=0.6):
        g = _pyautogui()
        if g:
            try:
                g.moveTo(int(x), int(y), duration=duration)
                return True
            except Exception:
                pass
        return False

    def click(self):
        g = _pyautogui()
        if g:
            try:
                g.click()
                return True
            except Exception:
                pass
        return False

    def type_text(self, text, interval=0.02):
        g = _pyautogui()
        if g:
            try:
                g.write(text, interval=interval)
                return True
            except Exception:
                pass
        return False

    def press(self, key):
        g = _pyautogui()
        if g:
            try:
                g.press(key)
                return True
            except Exception:
                pass
        return False

    def open_chrome(self, url):
        """Open a vetted address only. JARVIS never follows a raw URL."""
        try:
            import jarvis_guard as guard
            ok, clean, reason = guard.check_url(url)
            if not ok:
                guard.record_block(reason, url)
                self.log("Blocked unsafe address: %s" % reason)
                return False
            url = clean
        except Exception:
            pass
        if IS_WIN:
            for path in (
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            ):
                if os.path.exists(path):
                    try:
                        import jarvis_guard as guard
                        subprocess.Popen([path] + guard.chrome_args() + [url],
                                         creationflags=NW_FLAG)
                    except Exception:
                        subprocess.Popen([path, url], creationflags=NW_FLAG)
                    return True
            try:
                os.startfile(url)
                return True
            except Exception:
                pass
        elif IS_MAC:
            if os.path.exists("/Applications/Google Chrome.app"):
                try:
                    import jarvis_guard as guard
                    subprocess.Popen(["open", "-a", "Google Chrome"] +
                                     guard.chrome_args() + [url])
                except Exception:
                    subprocess.Popen(["open", "-a", "Google Chrome", url])
                return True
        else:
            if _have("google-chrome"):
                try:
                    import jarvis_guard as guard
                    subprocess.Popen(["google-chrome"] +
                                     guard.chrome_args() + [url])
                except Exception:
                    subprocess.Popen(["google-chrome", url])
                return True
        webbrowser.open(url)
        return True

    # -- task parsing ------------------------------------------------------
    def run(self, text):
        t = (text or "").strip()
        low = t.lower()

        if not t:
            return "I need an instruction, Boss."

        if "amazon" in low and any(w in low for w in
                                   ("find", "search", "buy", "add", "cart", "hot wheel", "hot wheels")):
            return self.amazon_task(t)

        if low.startswith("open "):
            target = t[5:].strip()
            if target.startswith("http"):
                if not self.open_chrome(target):
                    return ("I will not open that address, Boss. It is not a "
                            "public web page.")
                return "Opening %s, Boss." % target
            host = target.replace(" ", "")
            url = "https://" + host
            if "." not in host:
                url = "https://www." + host + ".com"
            if not self.open_chrome(url):
                return ("I will not open that address, Boss. It is not a "
                        "public web page.")
            return "Opening %s, Boss." % target

        if "search" in low and " on " in low:
            try:
                q = low.split("search", 1)[1].split(" on ", 1)[0].strip()
                site = low.split(" on ", 1)[1].strip().split()[0]
                site = re.sub(r"[^a-z0-9.-]", "", site)[:60]
                url = "https://www.%s.com/search?q=%s" % (
                    site, urllib.parse.quote_plus(q))
                if not self.open_chrome(url):
                    return ("I will not search that site, Boss. The address "
                            "did not pass the safety check.")
                return "Searching %s for %s, Boss." % (site, q)
            except Exception:
                pass

        if low.startswith("type "):
            self.type_text(t[5:])
            return "Typed it, Boss."

        if "google" in low:
            q = low.replace("google", "").replace("search", "").strip(" for")
            url = ("https://www.google.com/search?q=" +
                   urllib.parse.quote_plus(q))
            if not self.open_chrome(url):
                return ("I will not run that search, Boss. The address did "
                        "not pass the safety check.")
            return "Searching the web for %s, Boss." % q

        return ""

    # -- quick classification ---------------------------------------------
    def is_task(self, text):
        """True when this is a real desktop action, not conversation."""
        low = (text or "").strip().lower()
        if not low:
            return False
        if "amazon" in low and any(w in low for w in
                                   ("find", "search", "buy", "add", "cart",
                                    "hot wheel", "hot wheels")):
            return True
        if low.startswith("open ") or low.startswith("type "):
            return True
        if "search" in low and " on " in low:
            return True
        if "google" in low:
            return True
        return False

    # -- amazon ------------------------------------------------------------
    def amazon_task(self, text):
        low = text.lower()
        query = "hot wheels"
        for marker in ("find me", "find", "search for", "search", "buy me", "buy"):
            if marker in low:
                part = low.split(marker, 1)[1]
                part = part.split(" on amazon")[0]
                part = part.replace("a good", "").replace("some", "").strip(" ,.")
                if part:
                    query = part
                break
        self.log("Amazon: looking for %s" % query)

        # 1. real automation when Selenium is available
        try:
            return self._amazon_selenium(query)
        except Exception as e:
            self.log("Selenium unavailable (%s) - opening the search instead." %
                     str(e)[:60])

        url = "https://www.amazon.in/s?k=" + query.replace(" ", "+")
        self.open_chrome(url)
        return ("I opened Amazon and searched %s, Boss. Selenium is not "
                "installed, so I cannot click the cart for you yet." % query)

    def _amazon_selenium(self, query):
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.action_chains import ActionChains

        opts = Options()
        opts.add_experimental_option("detach", True)
        try:
            import jarvis_guard as guard
            guard.harden_selenium(opts)
        except Exception:
            pass
        driver = webdriver.Chrome(options=opts)
        self.driver = driver
        driver.maximize_window()

        driver.get("https://www.amazon.in/s?k=" + query.replace(" ", "+"))
        time.sleep(3)

        results = driver.find_elements(
            By.CSS_SELECTOR, 'div[data-component-type="s-search-result"] h2 a')
        if not results:
            return "Amazon showed no results for %s, Boss." % query

        first = results[0]
        title = (first.text or query)[:60]
        self._glide_to(first)
        first.click()
        time.sleep(3)

        # add to cart
        for sel in ("add-to-cart-button", "addToCart_feature_div input",
                    "input[name='submit.add-to-cart']"):
            try:
                if sel.startswith("add-to-cart"):
                    btn = driver.find_element(By.ID, sel)
                else:
                    btn = driver.find_element(By.CSS_SELECTOR, sel)
                self._glide_to(btn)
                btn.click()
                time.sleep(1.5)
                return "Added %s to your cart, Boss." % title
            except Exception:
                continue

        return "Opened %s, but I could not find the cart button, Boss." % title

    def _glide_to(self, element):
        """Move the visible cursor to a browser element before clicking."""
        g = _pyautogui()
        if not g:
            return
        try:
            pos = self.driver.get_window_position()
            loc = element.location
            size = element.size
            # rough browser chrome offset so the plate lands near the target
            x = pos["x"] + loc["x"] + size["width"] / 2
            y = pos["y"] + loc["y"] + size["height"] / 2 + 90
            g.moveTo(int(x), int(y), duration=0.8)
            time.sleep(0.2)
        except Exception:
            pass

    def close(self):
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass
        self.driver = None


# ------------------------------------------------------------------ DND
SOCIAL_PROCESSES = {
    "win": ["Instagram.exe", "TikTok.exe", "Snapchat.exe", "Discord.exe",
            "Facebook.exe", "Twitter.exe", "X.exe", "YouTube.exe"],
    "mac": ["Instagram", "TikTok", "Snapchat", "Discord", "Facebook",
            "Twitter", "X", "YouTube"],
}

SOCIAL_DOMAINS = ["instagram.com", "www.instagram.com", "tiktok.com",
                  "www.tiktok.com", "facebook.com", "www.facebook.com",
                  "x.com", "twitter.com", "snapchat.com", "youtube.com",
                  "www.youtube.com", "reddit.com", "www.reddit.com"]


SOCIAL_KEYWORDS = ["instagram", "tiktok", "facebook", "twitter", "x.com",
                   "snapchat", "youtube", "reddit", "reels", "shorts"]


def _foreground_title():
    """Title of the window in front, used to catch social sites in a browser."""
    try:
        if IS_WIN:
            import ctypes
            u = ctypes.windll.user32
            h = u.GetForegroundWindow()
            n = u.GetWindowTextLengthW(h)
            buf = ctypes.create_unicode_buffer(n + 1)
            u.GetWindowTextW(h, buf, n + 1)
            return buf.value or ""
        if IS_MAC:
            out = subprocess.check_output(
                ["osascript", "-e",
                 'tell application "System Events" to get name of front window '
                 'of (first process whose frontmost is true)'],
                text=True, stderr=subprocess.DEVNULL, timeout=3)
            return out.strip()
    except Exception:
        pass
    return ""


class DoNotDisturb:
    """Blocks social apps, warns on screen, and drives the auto-reply."""

    def __init__(self, root=None, on_reply=None):
        self.root = root
        self.on_reply = on_reply
        self.active = False
        self.thread = None
        self.overlay = None
        self.blocked = []
        self.message_count = 0

    def start(self):
        if self.active:
            return "Do Not Disturb is already on, Boss."
        self.active = True
        self.blocked = []
        self.thread = threading.Thread(target=self._watch, daemon=True)
        self.thread.start()
        self._show_overlay()
        return "Do Not Disturb on. Social apps and short video are blocked, Boss."

    def stop(self):
        self.active = False
        self._hide_overlay()
        return "Do Not Disturb off. Welcome back, Boss."

    # -- app blocking ------------------------------------------------------
    def _watch(self):
        while self.active:
            try:
                if IS_WIN:
                    for proc in SOCIAL_PROCESSES["win"]:
                        if subprocess.call(
                                ["taskkill", "/F", "/IM", proc],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                creationflags=NW_FLAG) == 0:
                            if proc not in self.blocked:
                                self.blocked.append(proc)
                elif IS_MAC:
                    for app in SOCIAL_PROCESSES["mac"]:
                        if subprocess.call(
                                ["osascript", "-e",
                                 'tell application "%s" to quit' % app],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL) == 0:
                            if app not in self.blocked:
                                self.blocked.append(app)
                self._block_sites()
            except Exception:
                pass
            time.sleep(4)

    def _block_sites(self):
        """Close a browser tab that is sitting on a blocked site."""
        title = _foreground_title().lower()
        if not title:
            return
        if not any(k in title for k in SOCIAL_KEYWORDS):
            return
        g = _pyautogui()
        if not g:
            return
        try:
            g.hotkey("command" if IS_MAC else "ctrl", "w")
            if title not in self.blocked:
                self.blocked.append(title)
        except Exception:
            pass

    # -- overlay -----------------------------------------------------------
    def _show_overlay(self):
        if self.root is None:
            return
        try:
            import tkinter as tk
            self.overlay = tk.Toplevel(self.root)
            self.overlay.overrideredirect(True)
            self.overlay.attributes("-topmost", True)
            self.overlay.configure(bg="#1a0d00")
            w, h = 460, 64
            sw = self.overlay.winfo_screenwidth()
            self.overlay.geometry("%dx%d+%d+%d" % (w, h, sw - w - 24, 24))
            tk.Label(self.overlay,
                     text="Do Not Disturb  ·  best avoided unless necessary",
                     bg="#1a0d00", fg="#ff8c00",
                     font=("Segoe UI", 11, "bold")).pack(expand=True)
        except Exception:
            self.overlay = None

    def _hide_overlay(self):
        try:
            if self.overlay is not None:
                self.overlay.destroy()
        except Exception:
            pass
        self.overlay = None

    # -- auto reply --------------------------------------------------------
    def handle_message(self, text):
        """Return the reply Jarvis would send, per the agreed wording."""
        self.message_count += 1
        try:
            from jarvis_loader import load_autoreply
            return load_autoreply().reply_for(text, self.message_count)
        except Exception as e:
            return "Jarvis; I have recorded your message (%s)." % str(e)[:40]


# ------------------------------------------------------------------ wake word
class WakeWord:
    """Listens for 'Hey Jarvis' and for 'Do Not Disturb'."""

    def __init__(self, on_wake=None, on_dnd=None):
        self.on_wake = on_wake
        self.on_dnd = on_dnd
        self.running = False
        self.thread = None
        self._last = 0.0

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    # -- phrase routing ----------------------------------------------------
    def _handle_text(self, text):
        low = (text or "").lower()
        now = time.time()
        if now - self._last < 1.5:
            return
        if "do not disturb" in low or re.search(r"\bdnd\b", low):
            self._last = now
            if self.on_dnd:
                self.on_dnd()
        elif "hey jarvis" in low or "jarvis" in low:
            self._last = now
            if self.on_wake:
                self.on_wake()

    # -- backend 1: speech_recognition (needs pyaudio) ---------------------
    def _sr_loop(self):
        try:
            import speech_recognition as sr
            mic = sr.Microphone()
        except Exception:
            return False
        r = sr.Recognizer()
        r.dynamic_energy_threshold = True
        while self.running:
            try:
                with mic as source:
                    audio = r.listen(source, timeout=2, phrase_time_limit=4)
                self._handle_text(r.recognize_google(audio))
            except Exception:
                time.sleep(0.3)
        return True

    # -- backend 2: Windows SAPI, no pyaudio needed ------------------------
    def _sapi_loop(self):
        ps = (
            "$ErrorActionPreference='SilentlyContinue';"
            "Add-Type -AssemblyName System.Speech;"
            "$r=New-Object System.Speech.Recognition.SpeechRecognitionEngine;"
            "$r.SetInputToDefaultAudioDevice();"
            "$r.LoadGrammar((New-Object System.Speech.Recognition."
            "DictationGrammar));"
            "while($true){"
            " try{$res=$r.Recognize([TimeSpan]::FromSeconds(3));"
            " if($res){[Console]::Out.WriteLine($res.Text);"
            "[Console]::Out.Flush()}}"
            " catch{Start-Sleep -Milliseconds 300}"
            "}"
        )
        try:
            proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", ps],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, creationflags=NW_FLAG)
        except Exception:
            return False
        try:
            while self.running:
                line = proc.stdout.readline()
                if not line:
                    if proc.poll() is not None:
                        break
                    time.sleep(0.1)
                    continue
                self._handle_text(line.strip())
        finally:
            try:
                proc.kill()
            except Exception:
                pass
        return True

    def _loop(self):
        if self._sr_loop():
            return
        if IS_WIN:
            self._sapi_loop()


# ------------------------------------------------------------------ cloud
class CloudToggle:
    """Local Ollama by default; cloud endpoint when enabled and reachable."""

    def __init__(self):
        self.cfg = load_cloud()

    @property
    def enabled(self):
        return bool(self.cfg.get("enabled"))

    def is_on(self):
        return self.enabled

    def toggle(self):
        self.cfg["enabled"] = not self.cfg.get("enabled", False)
        save_cloud(self.cfg)
        return self.cfg["enabled"]

    def set_config(self, url="", key="", model="", token=""):
        self.cfg.update({"url": url, "key": key, "model": model, "token": token})
        save_cloud(self.cfg)
        return self.cfg

    def get_config(self):
        return dict(self.cfg)

    def usable(self):
        """Cloud only if switched on, online, and configured."""
        return bool(self.cfg.get("enabled") and self.cfg.get("url") and online())

    def mode(self):
        return "CLOUD" if self.usable() else "LOCAL"
