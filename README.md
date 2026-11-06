<<<<<<< HEAD
# J.A.R.V.I.S. - readable edition

**ID: `504m522o414p43484q522o323032362o4l41525649532o303031`**
**Contact me: `prakhar2507000@gmail.com`**

This is the readable build I am sharing. Open the source, learn from it,
and build your own.

---

## Start here

| Your computer | Do this |
|---|---|
| **Windows** | Double-click `1. START ME ONCE FIRST (IF ON WINDOWS).bat` |
| **macOS** | Right-click `2. START ME ONCE FIRST (IF ON MAC).command` > Open |
| Any OS with Python 3.9+ | `python JARVIS.py` |

There are exactly three numbered files, and you only follow the one for your
computer:

1. `1. START ME ONCE FIRST (IF ON WINDOWS).bat` - Windows: creates the files
   and starts JARVIS.
2. `2. START ME ONCE FIRST (IF ON MAC).command` - macOS: the same, one click.
3. `3. READ ME FIRST.txt` - the plain-English guide.

On iPhone or iPad there is nothing to double-click: iOS cannot run Python or
Tkinter, so JARVIS serves the phone web app described below instead.

`jarvis_setup.py` is the script those launchers call; you never need to open
it yourself.

The first run creates your private settings folder, installs the optional
extras one at a time, and opens JARVIS. Nothing needs an account, an API key
or a payment.

After the first run you can simply double-click `JARVIS.py`.

---

## What is inside

```
J.A.R.V.I.S/
  1. START ME ONCE FIRST (IF ON WINDOWS).bat
                                  Windows one-click setup + start
  2. START ME ONCE FIRST (IF ON MAC).command
                                  macOS one-click setup + start
  3. READ ME FIRST.txt            plain-English start guide
  jarvis_setup.py                 the setup script the launchers call
  JARVIS.py                       readable front door
  FINGERPRINT.txt                 ownership record
  requirements.txt                optional extras
  Dependency/                     23 readable Python modules
```

### The modules

| Module | What it does |
|---|---|
| `jarvis_main.py` | orchestrator: UI, voice, camera, models, phone bridge |
| `jarvis_ui.py` | full-screen HUD, Settings, Quick Tools, Cipher Vault, mini-orb |
| `jarvis_theme.py` | Apple-HIG-style palette, cards, switches, glyphs |
| `jarvis_orb.py` | plasma orb with the lub-dub heartbeat at rest |
| `jarvis_avatar.py` | pixel butler, 58 behaviours, environment watcher |
| `jarvis_brain.py` | local Ollama chat, cloud chat, knowledge, mood |
| `jarvis_models.py` | Ollama detection, trusted download, model provisioning |
| `jarvis_voice.py` | free British TTS: edge-tts -> Piper -> OS voice |
| `jarvis_stt.py` | free local speech-to-text (Whisper when present) |
| `jarvis_camera.py` | webcam view and permission flow |
| `jarvis_automation.py` | cursor, guarded browser tasks, DND, wake word |
| `jarvis_control.py` | whitelisted app launching and safe site opening |
| `jarvis_autoreply.py` | exact auto-reply wording and phone bridge |
| `jarvis_mobile.py` | iPhone / iPad / Android web app on port 8765 |
| `jarvis_guard.py` | web shield: URL vetting, sanitising, quarantine, audit |
| `jarvis_vault.py` | Caesar to hexadecimal: every encoder and decoder |
| `jarvis_web.py` | guarded search, fetch, Wikipedia, weather, headlines |
| `jarvis_eggs.py` | 75 Easter eggs, hints and the found ledger |
| `jarvis_knowledge.py` | 120-entry built-in knowledge vault |
| `jarvis_memory.py` | chat and fact memory |
| `jarvis_config.py` | hardware profile, palette, private paths |
| `jarvis_loader.py` | loads a tool from readable source |
| `jarvis_video.py` | video tool placeholder (disabled) |

---

## The voice

There is one voice: the light British greeting voice.

> "Systems online. I am Jarvis, at your service, Boss."

The old deep male register is gone. Every engine now aims at the same light
sound:

1. **edge-tts** `en-GB-SoniaNeural` - free public endpoint, needs internet.
2. **Piper** `en_GB-cori-high` - local neural voice, downloaded once, offline.
3. **Windows SAPI** - prefers Hazel / Zira / female names; deep male names last.
4. **macOS `say`** - prefers Kate / Serena / Samantha; Daniel and friends last.

All of it is free. No account, no key, no subscription.

---

## What JARVIS can do

- **Talk and listen** - type, speak, or use the wake phrase "Hey Jarvis".
- **See** - open the camera from Quick Tools.
- **Drive the desktop** - an orange JARVIS cursor that really moves, clicks,
  searches and runs whitelisted browser flows.
- **Do Not Disturb** - closes social apps and tabs, shows a banner, and
  auto-replies with the exact wording in `jarvis_autoreply.py`.
- **Switch brains** - pick an installed Ollama model in Settings > Brain, or
  type any model name; it applies immediately.
- **Easter eggs** - 75 of them, each with a hint and a found/not-found ledger.
- **Phone companion** - a real PWA for iOS and Android (see below).
- **Cipher Vault** - a hidden lock in the bottom-left corner opens every
  encoder and decoder from Caesar shift to hex, base64, Morse, XOR and
  ChaCha20 + HMAC.

---

## Security: what JARVIS refuses

Web content is treated as hostile until it has been checked. `jarvis_guard.py`
does the work:

- public `http(s)` only; `localhost`, LAN, link-local, cloud-metadata and
  router addresses are refused,
- redirects are re-checked one hop at a time,
- hard size caps before anything is read,
- HTML is stripped to words: scripts, iframes, forms, SVG, meta-refresh and
  event handlers never reach the model,
- prompt-injection lines ("ignore previous instructions", "download and run")
  are removed and the rest is marked untrusted,
- executables and installers (`.exe`, `.msi`, `.bat`, `.ps1`, `.app`, `.dmg`,
  `.pkg` and similar) are refused as navigation targets,
- downloads are hashed, renamed and quarantined; JARVIS never runs them,
- Ollama installers are accepted only from the official host and are scanned
  with Windows Defender where available,
- Chrome is launched with a hardened flag set, and every action is written to
  `security.log` in your private folder.

**Honest limit:** no program can promise a browser has zero bugs. JARVIS
shrinks the attack surface; your browser and operating system are still the
last line of defence. Keep them updated. For a hard boundary, run the browser
in a separate user account or a virtual machine - JARVIS works there too.

See **Settings > Security** for live counters, the quarantine folder, and a
Downloads check.

---

## iPhone, iPad and Android

Python and Tkinter cannot run natively on iOS, so JARVIS does the honest
thing: the desktop app hosts a small web app on your Wi-Fi.

1. Start JARVIS on the computer.
2. **Settings > Phone Link** - copy the `http://<ip>:8765/?k=...` link.
3. Open it in Safari, then **Share > Add to Home Screen**.

What the phone gets:

- a full-screen, dark, standalone layout with safe-area support,
- text chat and the same British voice (the PC renders the audio),
- dictation through Safari's recogniser where available,
- a real PNG home-screen icon and a web-app manifest,
- security headers and a CSP on every page,
- a token on every `/api/*` request, so other devices on the Wi-Fi are out.

The shell page itself is public so the home-screen icon can reopen after
Safari forgets the query string. It contains no data and no token.

No cloud, no account, no port forwarding.

---

## Windows and macOS

Both are supported in code. Windows is the tested, primary platform. macOS
paths exist for hardware detection, `say`, `afplay`, `open`, camera
permissions and the `.command` launcher, but this build was written on
Windows, so treat macOS as code-reviewed rather than hardware-tested.

**Windows camera:** Settings > Privacy & Camera > turn on *Camera access* and
*Let desktop apps access your camera*. There is no runtime popup for desktop
apps.

**macOS permissions:** allow microphone and camera once. If you denied them
earlier, enable Python/Terminal in System Settings > Privacy & Security, then
press RETRY in JARVIS.

---

## Hardware and models

JARVIS reads RAM, GPU and - on Apple Silicon - unified memory, then picks a
model and quality profile. Tiers are **OPTIMAL**, **RISKY** and
**IMPOSSIBLE**. The built-in knowledge brain answers immediately while the
local models download in the background.

Optional extras are listed in `requirements.txt`. Each one degrades
gracefully if absent: no camera package means no camera, no Whisper means
typing only, no Piper means the OS voice.

---

## Private settings

Your settings never live in this folder. They live on **your** Desktop under
`JARVIS/`:

| File | What it holds |
|---|---|
| `cloud.json` | cloud endpoint, optional API key, model, token |
| `phone.json` | phone automation settings |
| `dnd.json` | Do Not Disturb state |
| `brain.json` | the model you picked |
| `eggs.json` | which Easter eggs you have found |
| `security.json` + `security.log` | shield state and audit trail |
| `Quarantine/` | files JARVIS refused to run |

Sharing this folder can never ship my keys or yours, because neither set
lives in it.

---

## Share / do not share

**Share:** the whole `J.A.R.V.I.S` folder. That is the copy I made for you.

**Please never share:**

- your Desktop `JARVIS` folder (settings, tokens, quarantine),
- my `do not share` folder (sealed backup, build key, screenshots, debug),
- any file containing an API key, password or pairing token.

Before uploading, run the scrub check described in `FINGERPRINT.txt`.

---

## Cipher Vault

There is a lock in the bottom-left corner of the main screen. It is the same
colour as the background on purpose: no label, no tooltip, no glow. If you
know it is there, hover and click.

Inside: Caesar, ROT13, Atbash, Vigenere, A1Z26, Bacon, rail fence, reverse,
Morse, Base64 / Base32 / Base85, hexadecimal, binary, octal, decimal, URL,
HTML, Unicode, XOR, ChaCha20 + HMAC, SHA-256 / SHA-1 / MD5 / BLAKE2b, and an
auto-detect mode. Everything runs locally.

---

## Credit and contact

I am **Prakhar Srivastava**. I built this.

ID: `504m522o414p43484q522o323032362o4l41525649532o303031`
Contact me: **prakhar2507000@gmail.com**

Ideas, fixes and upgrade suggestions are welcome.
=======
# J.A.R.V.I.S
a vibe cosed jarvis
>>>>>>> 734044d3fae312bd0bcc0fd47be957a77404a10d
