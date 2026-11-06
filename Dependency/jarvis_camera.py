# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS Camera - cross-platform webcam view with a real permission flow.

Why JARVIS never showed the "allow camera?" box:
    Browsers ask because they are sandboxed apps. A desktop program is not.
    On Windows, camera access for desktop apps is a Settings toggle, not a
    popup - there is nothing to click at runtime. On macOS, the system DOES
    ask the first time, once per host app (python / Terminal / the .app).

So this module:
    * tries every backend and camera index before giving up
    * if access is refused, explains exactly what to switch on and opens the
      right settings page for the OS
    * keeps a Retry button, so once you grant it the feed starts immediately
"""
import tkinter as tk
from tkinter import messagebox
import threading
import time
import base64

from jarvis_config import IS_WIN, IS_MAC

try:
    import cv2
    HAS_CV2 = True
except Exception:
    HAS_CV2 = False


def _backends():
    if not HAS_CV2:
        return []
    out = []
    for name in ("CAP_DSHOW", "CAP_MSMF", "CAP_AVFOUNDATION", "CAP_V4L2"):
        if hasattr(cv2, name):
            out.append(getattr(cv2, name))
    out.append(0)
    return out


def open_camera():
    """Return an opened VideoCapture or None. Tries backends and indexes."""
    if not HAS_CV2:
        return None
    for be in _backends():
        for idx in (0, 1, 2):
            try:
                cap = cv2.VideoCapture(idx, be) if be else cv2.VideoCapture(idx)
            except Exception:
                continue
            if cap is not None and cap.isOpened():
                ok, _ = cap.read()
                if ok:
                    return cap
            try:
                cap.release()
            except Exception:
                pass
    return None


def permission_target():
    """OS settings page that controls camera access."""
    if IS_WIN:
        return "ms-settings:privacy-webcam"
    if IS_MAC:
        return ("x-apple.systempreferences:com.apple.preference.security"
                "?Privacy_Camera")
    return ""


def permission_help():
    if IS_WIN:
        return ("Windows controls camera access per app, in Settings - not with "
                "a popup. I opened Settings > Privacy > Camera.\n\n"
                "Turn ON 'Camera access' and 'Let desktop apps access your camera', "
                "then press Retry.")
    if IS_MAC:
        return ("macOS asks once, the first time a program uses the camera.\n\n"
                "I opened System Settings > Privacy & Security > Camera. "
                "Tick the app running JARVIS (Python, Terminal or iTerm), "
                "then press Retry. If you never saw the prompt, that means "
                "the app was previously denied - untick and re-tick it.")
    return "Allow camera access for this program in your system privacy settings."


class CameraView:
    def __init__(self, parent, width=380, height=430):
        self.parent = parent
        self.W = width
        self.H = height
        self.window = None
        self.label = None
        self.info = None
        self.retry_btn = None
        self.cap = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        self.frame_data = None
        self.cam_info = {"status": "idle"}

    # ------------------------------------------------------------------ public
    def toggle(self):
        if self.window is not None:
            self.close()
            return
        if not HAS_CV2:
            messagebox.showerror(
                "Missing library",
                "Install opencv-python to use the camera:\n\npip install opencv-python")
            return
        self.open()

    def open(self):
        if self.window is not None:
            return
        self.window = tk.Toplevel(self.parent)
        self.window.title("JARVIS Vision")
        self.window.configure(bg="#000000")
        self.window.geometry("%dx%d" % (self.W, self.H))
        self.window.attributes("-topmost", True)

        tk.Label(self.window, text="WHAT I SEE", bg="#000000", fg="#ff8c00",
                 font=("Consolas", 11, "bold")).pack(pady=(10, 2))

        self.label = tk.Label(self.window, bg="#000000", width=320, height=240)
        self.label.pack()

        self.info = tk.Label(self.window, text="starting camera...",
                             bg="#000000", fg="#ffd9a0",
                             font=("Consolas", 10), justify="left",
                             wraplength=self.W - 30)
        self.info.pack(pady=8, padx=12, anchor="w")

        self.retry_btn = tk.Button(self.window, text="RETRY", command=self._retry,
                                   bg="#150d03", fg="#ffc14d", relief="flat",
                                   font=("Segoe UI", 9, "bold"), padx=16, pady=6,
                                   highlightbackground="#3d2810", highlightthickness=1)
        self.retry_btn.pack(pady=(0, 10))

        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.running = True
        self._start_thread()
        self._refresh()

    def close(self):
        self.running = False
        if self.thread:
            try:
                self.thread.join(timeout=2)
            except Exception:
                pass
        try:
            if self.cap is not None:
                self.cap.release()
        except Exception:
            pass
        self.cap = None
        if self.window is not None:
            try:
                self.window.destroy()
            except Exception:
                pass
        self.window = None
        self.label = None
        self.info = None
        self.retry_btn = None

    # ----------------------------------------------------------------- internals
    def _start_thread(self):
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _retry(self):
        try:
            if self.cap is not None:
                self.cap.release()
        except Exception:
            pass
        self.cap = None
        with self.lock:
            self.frame_data = None
            self.cam_info = {"status": "starting"}
        self._start_thread()

    def _loop(self):
        cap = open_camera()
        if cap is None:
            with self.lock:
                self.cam_info = {"status": "blocked"}
            if self.parent:
                self.parent.after(0, self._show_permission)
            return

        self.cap = cap
        with self.lock:
            self.cam_info = {"status": "live", "w": 320, "h": 240}

        while self.running and self.cap is not None:
            try:
                ok, frame = self.cap.read()
            except Exception:
                ok, frame = False, None
            if not ok or frame is None:
                time.sleep(0.15)
                continue
            try:
                small = cv2.resize(frame, (320, 240))
                rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
                with self.lock:
                    self.frame_data = rgb.tobytes()
                    self.cam_info = {"status": "live", "w": 320, "h": 240}
            except Exception:
                pass
            time.sleep(0.04)

    def _show_permission(self):
        if self.window is None:
            return
        self.info.configure(text=permission_help(), fg="#ffb43c")
        target = permission_target()
        if target:
            try:
                if IS_WIN:
                    import os
                    os.startfile(target)
                elif IS_MAC:
                    import subprocess
                    subprocess.Popen(["open", target])
            except Exception:
                pass

    def _refresh(self):
        if not self.running or self.window is None:
            return
        try:
            with self.lock:
                frame = self.frame_data
                info = dict(self.cam_info)

            if frame:
                w, h = info.get("w", 320), info.get("h", 240)
                ppm = ("P6\n%d %d\n255\n" % (w, h)).encode() + frame
                img = tk.PhotoImage(data=base64.b64encode(ppm).decode(), format="PPM")
                self.label.configure(image=img)
                self.label.image = img
                if info.get("status") == "live":
                    self.info.configure(
                        text="status: live   %dx%d" % (w, h), fg="#4cd97b")
            elif info.get("status") == "blocked":
                self.info.configure(text=permission_help(), fg="#ffb43c")
        except Exception:
            pass
        try:
            self.window.after(120, self._refresh)
        except Exception:
            pass
