#!/bin/bash
# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
# J.A.R.V.I.S. - first run on macOS.
# Right-click this file and choose Open the first time (macOS blocks unsigned
# scripts), or run:  chmod +x "2. START ME ONCE FIRST (IF ON MAC).command"

cd "$(dirname "$0")" || exit 1
clear
echo "J.A.R.V.I.S. - first run"
echo

PY=""
for candidate in python3 python3.13 python3.12 python3.11 python3.10 python3.9; do
    if command -v "$candidate" >/dev/null 2>&1; then
        if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
            PY="$candidate"
            break
        fi
    fi
done

if [ -z "$PY" ]; then
    echo "Python 3.9 or newer is required."
    echo "Install it once from https://www.python.org/downloads/ and run this again."
    echo
    read -r -p "Press Return to close."
    exit 1
fi

if ! "$PY" -c 'import tkinter' >/dev/null 2>&1; then
    echo "This Python has no Tk window support."
    echo "Install the official Python 3 from python.org, then run this again."
    echo
    read -r -p "Press Return to close."
    exit 1
fi

"$PY" "jarvis_setup.py"
