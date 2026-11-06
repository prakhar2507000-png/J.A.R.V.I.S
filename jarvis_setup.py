#!/usr/bin/env python3
"""
J.A.R.V.I.S. - first-run bootstrapper.

Run this once. It:

    1. checks that Python and Tk are present,
    2. creates the private settings folder on this user's Desktop,
    3. installs the optional extras one by one (each is optional),
    4. starts JARVIS.

Nothing here needs an account, a key or a payment. Set JARVIS_SKIP_PIP=1 to
skip the optional downloads entirely.

ID: 504m522o414p43484q522o323032362o4l41525649532o303031
Contact me: prakhar2507000@gmail.com
"""
import os
import subprocess
import sys
import json

BASE = os.path.dirname(os.path.abspath(__file__))
DEPENDENCY = os.path.join(BASE, "Dependency")
LAUNCHER = os.path.join(BASE, "JARVIS.py")
FINGERPRINT = "504m522o414p43484q522o323032362o4l41525649532o303031"

BANNER = r"""
  J.A.R.V.I.S.  -  first run
  ---------------------------------------------
  One click. All required files are created for you.
"""

OPTIONAL = [
    ("pillow", "image handling for the camera and screenshots"),
    ("edge-tts", "extra-polished free British voice"),
    ("numpy", "faster audio shaping"),
    ("sounddevice", "microphone input"),
    ("opencv-python", "camera view"),
    ("pyautogui", "cursor automation"),
    ("selenium", "reliable browser flows"),
    ("faster-whisper", "offline speech-to-text"),
    ("piper-tts", "offline neural British voice"),
    ("onnxruntime", "runs the Piper voice"),
]


def desktop_folder():
    home = os.path.expanduser("~")
    for cand in (os.path.join(home, "Desktop"),
                 os.path.join(home, "OneDrive", "Desktop"),
                 os.path.join(home, "OneDrive - Personal", "Desktop")):
        if os.path.isdir(cand):
            return cand
    return home


def create_private_files():
    """Create the Desktop/JARVIS folder and any missing default files."""
    folder = os.path.join(desktop_folder(), "JARVIS")
    os.makedirs(folder, exist_ok=True)
    os.makedirs(os.path.join(folder, "Quarantine"), exist_ok=True)
    defaults = {
        "brain.json": {},
        "cloud.json": {"enabled": False, "url": "", "key": "",
                       "model": "", "token": ""},
        "dnd.json": {"active": False},
        "phone.json": {},
        "eggs.json": [],
    }
    for name, value in defaults.items():
        path = os.path.join(folder, name)
        if not os.path.exists(path):
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(value, f, indent=1)
            except Exception:
                pass
    note = os.path.join(folder, "READ ME - PRIVATE.txt")
    if not os.path.exists(note):
        try:
            with open(note, "w", encoding="utf-8") as f:
                f.write(
                    "I made this folder for you. It holds your settings,\n"
                    "your keys and your phone token.\n"
                    "Please never share it. Sharing J.A.R.V.I.S does not share it.\n"
                    "ID: " + FINGERPRINT + "\n"
                    "Contact me: prakhar2507000@gmail.com\n")
        except Exception:
            pass
    return folder


def pip(pkg, label):
    print("  - %-16s %s" % (pkg, label))
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q",
             "--disable-pip-version-check", pkg],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=240)
    except Exception:
        print("      (skipped - JARVIS will still run without it)")


def main():
    print(BANNER)
    if sys.version_info < (3, 9):
        print("  Python 3.9 or newer is required.")
        print("  Install it from https://www.python.org/downloads/ and "
              "run this again.")
        input("  Press Return to close.")
        return 1
    try:
        import tkinter  # noqa: F401
    except Exception:
        print("  This Python has no Tk support, so the window cannot open.")
        print("  Install the official Python from python.org (it includes "
              "Tk), then run this again.")
        input("  Press Return to close.")
        return 1

    if not os.path.isdir(DEPENDENCY):
        print("  The Dependency folder is missing.")
        print("  Share the whole J.A.R.V.I.S folder, not this file alone.")
        input("  Press Return to close.")
        return 1

    print("  Creating your private settings folder...")
    folder = create_private_files()
    print("    " + folder)

    if os.environ.get("JARVIS_SKIP_PIP") == "1":
        print("  Skipping optional packages (JARVIS_SKIP_PIP=1).")
    elif os.path.exists(os.path.join(folder, ".setup-done")):
        print("  Optional extras were already checked on this machine.")
        print("  Delete Desktop/JARVIS/.setup-done to check them again.")
    else:
        print("  Checking optional extras (this can take a few minutes)...")
        for pkg, label in OPTIONAL:
            pip(pkg, label)
        try:
            with open(os.path.join(folder, ".setup-done"), "w",
                      encoding="utf-8") as f:
                f.write(FINGERPRINT + "\n")
        except Exception:
            pass

    print()
    print("  Everything is ready. Starting JARVIS...")
    print()
    os.chdir(DEPENDENCY)
    sys.path.insert(0, DEPENDENCY)
    try:
        import runpy
        runpy.run_path(LAUNCHER, run_name="__main__")
    except Exception as exc:
        print("  JARVIS could not start: %s" % exc)
        input("  Press Return to close.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
