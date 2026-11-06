# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS PC Control — open apps, volume, brightness, etc.
NO code execution allowed.
"""
import subprocess, os, re, datetime, ctypes, webbrowser
from jarvis_config import NW_FLAG, popen_hidden, SPECS

def run(cmd, timeout=10):
    try:
        return subprocess.check_output(cmd, shell=True, text=True,
            stderr=subprocess.STDOUT, timeout=timeout,
            creationflags=NW_FLAG).strip()
    except Exception as e:
        return str(e)

MAPPING = {
    "notepad": "notepad.exe", "calculator": "calc.exe", "calc": "calc.exe",
    "chrome": "chrome.exe", "edge": "msedge.exe", "explorer": "explorer.exe",
    "files": "explorer.exe", "spotify": "spotify.exe", "cmd": "cmd.exe",
    "terminal": "wt.exe", "settings": "ms-settings:",
    "task manager": "taskmgr.exe", "taskmgr": "taskmgr.exe",
    "paint": "mspaint.exe", "word": "winword.exe", "excel": "excel.exe",
    "vscode": "code", "code": "code",
    "camera": "microsoft.windows.camera:", "store": "ms-windows-store:",
}

SITES = {"youtube": "https://www.youtube.com",
         "gmail": "https://mail.google.com", "github": "https://github.com",
         "netflix": "https://www.netflix.com",
         "maps": "https://maps.google.com",
         "drive": "https://drive.google.com",
         "chatgpt": "https://chatgpt.com", "claude": "https://claude.ai"}

def _guard():
    try:
        import jarvis_guard
        return jarvis_guard
    except Exception:
        return None


def do_pc_action(a):
    op = a.get("op", "")
    t = str(a.get("target", "")).lower().strip()

    if op == "open":
        if t in SITES:
            g = _guard()
            if g is not None:
                ok, msg = g.web_open(SITES[t])
                return msg
            webbrowser.open(SITES[t])
            return t + " opened in your browser."
        # Only the named, safe apps. A model cannot ask for arbitrary code.
        if t not in MAPPING:
            return ("I will not open that, Boss. It is not on my allowed "
                    "application list.")
        exe = MAPPING[t]
        try:
            os.startfile(exe)
        except Exception:
            popen_hidden(exe, shell=True)
        return t + " opened."
    if op == "close":
        name = re.sub(r"[^a-z0-9 ._-]", "", t)[:40]
        if not name:
            return "I need a name to close, Boss."
        run("taskkill /IM " + name + ".exe /F")
        return t + " closed."
    if op == "volume":
        if t == "mute":
            run('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"')
        elif t == "up":
            run('powershell -c "$o=New-Object -ComObject WScript.Shell; 1..5 | %{$o.SendKeys([char]175)}"')
        else:
            run('powershell -c "$o=New-Object -ComObject WScript.Shell; 1..5 | %{$o.SendKeys([char]174)}"')
        return "Volume " + t + "."
    if op == "media":
        keys = {"play": 179, "pause": 179, "next": 176, "prev": 177,
                "previous": 177, "stop": 178}
        run('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]%d)"' % keys.get(t, 179))
        return "Media " + t + "."
    if op == "brightness":
        try:
            if t in ("up", "+"):
                run('powershell -c "$m=Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods; $b=Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness; $m.WmiSetBrightness(1, [Math]::Min(100, $b.CurrentBrightness+10))"')
            elif t in ("down", "-"):
                run('powershell -c "$m=Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods; $b=Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness; $m.WmiSetBrightness(1, [Math]::Max(10, $b.CurrentBrightness-10))"')
            else:
                n = max(10, min(100, int(re.sub(r"\D", "", t) or 50)))
                run('powershell -c "$m=Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods; $m.WmiSetBrightness(1, %d)"' % n)
            return "Brightness " + t + "."
        except Exception as e:
            return str(e)[:150]
    if op == "time":
        return datetime.datetime.now().strftime("It is %I:%M %p, sir.")
    if op == "date":
        return datetime.datetime.now().strftime("Today is %A, %B %d, %Y.")
    if op == "spec":
        return f"Intel {SPECS['cpu']}, {SPECS['ram_gb']} gigabytes RAM, {SPECS['gpu']}. Running {MODEL}."
    if op == "stats":
        try:
            return run('powershell -NoProfile -Command "Get-Process | Sort-Object WS -Descending | Select-Object -First 5 Name, @{n=\'MB\';e={[int]($_.WS/1MB)}} | Format-Table -HideTableHeaders | Out-String"', timeout=20)
        except Exception as e:
            return str(e)[:150]
    if op == "procs":
        return run('powershell -NoProfile -Command "Get-Process | Sort-Object CPU -Descending | Select-Object -First 8 Name"', timeout=20)[:600]
    if op == "kill":
        run("taskkill /IM " + re.sub(r"[^a-z0-9._ ]", "", t) + ".exe /F")
        return t + " terminated."
    if op == "lock":
        ctypes.windll.user32.LockWorkStation()
        return "Workstation locked."
    if op == "shutdown":
        popen_hidden("shutdown /s /t 10", shell=True)
        return "Shutdown in 10 seconds."
    if op == "restart":
        popen_hidden("shutdown /r /t 10", shell=True)
        return "Restart in 10 seconds."
    if op == "list":
        try:
            p = t if t and t != "files" else os.path.expanduser("~\\Desktop")
            return "Files: " + ", ".join(os.listdir(p)[:30])
        except Exception as e:
            return str(e)
    if op == "ip":
        return run("ipconfig | findstr IPv4")
    if op == "screenshot":
        p = os.path.expanduser("~\\Desktop\\jarvis_shot.png")
        ps = ("Add-Type -AssemblyName System.Windows.Forms; $b=New-Object Drawing.Bitmap([System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width,[System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height); $g=[Drawing.Graphics]::FromImage($b); $g.CopyFromScreen(0,0,0,0,$b.Size); $b.Save('" + p + "')")
        run('powershell -c "' + ps + '"')
        return "Screenshot saved to Desktop."
    if op == "sense":
        return "Camera feed opened in vision window."
    if op == "video":
        return "video_op"
    if op == "calc":
        import ast, operator as op_mod
        ops = {ast.Add: op_mod.add, ast.Sub: op_mod.sub, ast.Mult: op_mod.mul,
               ast.Div: op_mod.truediv, ast.Pow: op_mod.pow, ast.USub: op_mod.neg}
        allowed = {"pi": 3.14159, "e": 2.71828}
        try:
            tree = ast.parse(a.get("text", t)[:100], mode="eval")
            def ev(n):
                if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
                    return n.value
                if isinstance(n, ast.BinOp) and type(n.op) in ops:
                    return ops[type(n.op)](ev(n.left), ev(n.right))
                if isinstance(n, ast.UnaryOp) and type(n.op) in ops:
                    return ops[type(n.op)](ev(n.operand))
                if isinstance(n, ast.Name) and n.id in allowed:
                    return allowed[n.id]
                raise ValueError("nope")
            return str(round(ev(tree.body), 6))
        except Exception:
            return "That sum defeated me, Boss."
    if op == "clipboard":
        try:
            if t in ("read", "get", "show", ""):
                out = run("powershell -NoProfile -Command Get-Clipboard", timeout=15)[:500]
                return "Clipboard holds: " + (out.strip() if out.strip() else "nothing at all, Boss.")
            run('powershell -NoProfile -Command Set-Clipboard -Value \'' + a.get("text", t)[:500].replace("'", "") + "'")
            return "Copied to clipboard."
        except Exception as e:
            return str(e)[:150]
    if op == "noteadd":
        from jarvis_memory import MEM, save_mem
        MEM.setdefault("facts", [])
        MEM["facts"].append(a.get("text", "")[:200])
        MEM["facts"] = MEM["facts"][-50:]
        save_mem(MEM)
        return "Committed to memory, Boss."
    if op == "notelist":
        from jarvis_memory import MEM
        items = MEM.get("facts", [])
        if not items:
            return "Memory is empty, Boss."
        return "Memory: " + "; ".join(items[-10:])
    if op == "noteclear":
        from jarvis_memory import MEM, save_mem
        MEM["facts"] = []
        save_mem(MEM)
        return "Memory wiped clean, Boss."
    if op == "remind":
        secs = max(5, min(86400, int(a.get("seconds", 60))))
        import threading
        def fire():
            import jarvis_voice as v
            v.say("Boss — " + a.get("text", "something"))
        threading.Timer(secs, fire).start()
        return f"Reminder set for {secs} seconds, Boss."
    return "Done."

MODEL = None
