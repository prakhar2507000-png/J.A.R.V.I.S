#!/usr/bin/env python3
"""
J.A.R.V.I.S. - readable edition.

This file is the front door, not the whole house. The assistant lives in the
`Dependency/` folder beside it as ordinary, readable Python so that anyone can
open a module, learn from it, and improve it.

    Windows : double-click `1. START ME ONCE FIRST (IF ON WINDOWS).bat`
              (first time), or `JARVIS.py` after that
    macOS   : double-click `2. START ME ONCE FIRST (IF ON MAC).command`
              (first time)
    Any OS  : python JARVIS.py

ID: 504m522o414p43484q522o323032362o4l41525649532o303031
Contact me: prakhar2507000@gmail.com
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DEPENDENCY = os.path.join(BASE, "Dependency")
sys.path.insert(0, DEPENDENCY)
os.chdir(DEPENDENCY)


def main():
    if sys.version_info < (3, 9):
        sys.stderr.write(
            "JARVIS needs Python 3.9 or newer. Install it from python.org.\n")
        raise SystemExit(1)
    from jarvis_main import main as run
    run()


if __name__ == "__main__":
    main()
