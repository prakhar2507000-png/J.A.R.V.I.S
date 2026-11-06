# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS Main - orchestrator. Double-click launch_jarvis.py to start everything.

Wires the UI to the automation tools, the camera,
cloud mode, wake word and Do Not Disturb.
"""
import tkinter as tk
import sys
import os
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jarvis_config import MODEL, load_cloud
from jarvis_voice import say as tts_say
from jarvis_camera import CameraView
from jarvis_ui import JarvisUI
import jarvis_loader


class JarvisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("J.A.R.V.I.S.")
        self.root.configure(bg="#000000")

        self.camera = CameraView(root)
        self.busy = False
        self.speak_on = True
        self.state = "idle"
        self._bridge = None
        self._greeted = False

        # ---- tools loaded from readable source (or a sealed copy if present)
        self.auto = None
        self.autoreply = None
        self.cursor = None
        self.task_runner = None
        self.dnd = None
        self.cloud = None
        self.wake = None
        try:
            self.auto = jarvis_loader.load_automation()
        except Exception as e:
            print("automation unavailable:", e)
        try:
            self.autoreply = jarvis_loader.load_autoreply()
        except Exception as e:
            print("auto-reply unavailable:", e)

        if self.auto is not None:
            self.cursor = self.auto.CursorMode(root)
            self.task_runner = self.auto.TaskRunner(
                cursor=self.cursor, log=self._auto_log)
            self.dnd = self.auto.DoNotDisturb(root)
            self.cloud = self.auto.CloudToggle()

        self.ui = JarvisUI(root, self, None, self.camera, self)
        self.orb = self.ui.orb

        self.mobile = None
        try:
            import jarvis_mobile
            self.mobile = jarvis_mobile.start()
            if self.mobile is not None:
                self.ui.log("s", "Phone / iOS: " + self.mobile.url)
        except Exception as e:
            self.ui.log("s", "Phone link unavailable: " + str(e)[:80])
        try:
            from jarvis_config import PRIVATE_DIR
            self.ui.log("s", "Private keys live in " + PRIVATE_DIR)
        except Exception:
            pass

        self.reload_cloud_bridge()
        threading.Thread(target=self._bridge_loop, daemon=True).start()
        try:
            import jarvis_stt
            jarvis_stt.warmup()
        except Exception:
            pass
        self.root.after(1200, self._start_wake)
        self.root.after(1000, self.boot)
        self.root.after(1500, self._hide_shell_windows)
        self.root.after(3200, self._bootstrap_models)

    # ------------------------------------------------------------------ voice
    def say(self, text, cheerful=False, on_start=None):
        if self.speak_on:
            tts_say(text, cheerful, on_start=on_start)
        elif on_start is not None:
            try:
                on_start()
            except Exception:
                pass

    def _auto_log(self, msg):
        try:
            self.root.after(0, lambda: self.ui.log("s", msg))
        except Exception:
            pass

    # ------------------------------------------------------------------ boot
    def boot(self):
        if self._greeted:
            return
        self._greeted = True
        self.ui.respond(
            "Systems online. I am Jarvis, at your service, Boss.",
            cheerful=True, hold=9000)
        try:
            import jarvis_voice
            jarvis_voice.warm()
        except Exception:
            pass
        self.ui.set_state("idle")
        mode = "cloud" if (self.cloud and self.cloud.usable()) else "local"
        self.ui.log("s", "Core: %s  ·  brain: %s" % (mode, MODEL))
        if self.dnd is not None:
            self.ui.log(
                "s", "Wake word armed: \"Hey Jarvis\"  ·  "
                     "say \"Do Not Disturb\" to arm auto-reply.")

    def _hide_shell_windows(self):
        if self.auto is not None:
            try:
                self.auto.minimize_terminal_and_explorer()
            except Exception:
                pass

    # ------------------------------------------------------------------ brain
    def _bootstrap_models(self):
        """Provision TinyLlama and Qwen once, quietly, in the background.

        The app never blocks on this. If the Mac is offline, or Ollama cannot
        be installed, the built-in brain keeps answering and the Brain page
        explains what happened. Set JARVIS_NO_MODEL_SETUP=1 to skip it.
        """
        if os.environ.get("JARVIS_NO_MODEL_SETUP"):
            return
        try:
            import jarvis_models as jm
        except Exception:
            return
        try:
            st = jm.status()
            if st.get("phase") in ("installing", "starting", "pulling"):
                return
            if st.get("server") and all(jm.has_model(n) for n, _l, _d
                                        in jm.REQUIRED):
                self.ui.log("s", "Local brain ready: TinyLlama + Qwen 2.5.")
                return
        except Exception:
            return

        def log(msg):
            try:
                self.root.after(0, lambda: self.ui.log("s", msg))
            except Exception:
                pass

        def state(d):
            pass

        try:
            jm.bootstrap_async(log=log, on_state=state)
            self.ui.log("s", "Setting up the two local models in the "
                             "background. Settings > Brain shows progress.")
        except Exception:
            pass

    # ------------------------------------------------------------------ wake
    def _start_wake(self):
        if self.auto is None:
            return
        try:
            self.wake = self.auto.WakeWord(
                on_wake=self.on_wake, on_dnd=self.on_dnd)
            self.wake.start()
        except Exception as e:
            self.ui.log("s", "Wake word unavailable: " + str(e)[:80])

    def on_wake(self):
        def _do():
            try:
                self.root.deiconify()
                self.root.attributes("-fullscreen", True)
                self.ui.respond("Yes, Boss?", hold=5000)
                self.ui.mic()
            except Exception:
                pass
        try:
            self.root.after(0, _do)
        except Exception:
            pass

    def on_dnd(self):
        try:
            self.root.after(0, self.ui.toggle_dnd)
        except Exception:
            pass

    # ------------------------------------------------------------------ cloud
    def _make_bridge(self):
        try:
            return self.autoreply.CloudBridge(load_cloud())
        except Exception:
            return None

    def reload_cloud_bridge(self):
        """Point the bridge at the freshly saved phone endpoint."""
        self._bridge = self._make_bridge()

    def _bridge_loop(self):
        """Poll Boss's own phone; answer only while Do Not Disturb is on."""
        counts = {}
        while True:
            bridge = self._bridge
            try:
                if bridge is not None and bridge.enabled and \
                        self.dnd is not None and self.dnd.active:
                    for m in bridge.pending():
                        text = m.get("text", "")
                        who = m.get("from", "")
                        counts[who] = counts.get(who, 0) + 1
                        out = self.autoreply.reply_for(text, counts[who])
                        bridge.send(who, out)
                        bridge.ack(m.get("id"))
                        self._auto_log("Auto-reply -> %s: %s" %
                                       (who or "?", out))
            except Exception:
                pass
            time.sleep(4)


def main():
    # fold the console and any File Explorer window away before the UI appears
    try:
        import jarvis_loader as _l
        _l.load_automation().minimize_terminal_and_explorer()
    except Exception:
        pass

    root = tk.Tk()
    JarvisApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
