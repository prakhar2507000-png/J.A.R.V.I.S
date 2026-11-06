# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS Cipher Vault - a pocket codebook of encoders and decoders.

Everything here is standard library only, so the same code runs on Windows,
macOS and any laptop a learner opens it on. It is a teaching toolbox: Caesar,
Vigenere, Atbash, Bacon, rail fence, Morse, bases, XOR, ChaCha20+HMAC, and the
common one-way hashes. Nothing is sent anywhere.
"""
import base64
import binascii
import hashlib
import hmac
import html
import os
import re
import struct
import urllib.parse

# ------------------------------------------------------------------ classical
def caesar(text, shift=3, decrypt=False):
    n = int(shift or 0) * (-1 if decrypt else 1)
    out = []
    for ch in str(text):
        if "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 + n) % 26 + 97))
        elif "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 + n) % 26 + 65))
        else:
            out.append(ch)
    return "".join(out)


def rot13(text):
    return caesar(text, 13)


def atbash(text):
    out = []
    for ch in str(text):
        if "a" <= ch <= "z":
            out.append(chr(219 - ord(ch)))
        elif "A" <= ch <= "Z":
            out.append(chr(155 - ord(ch)))
        else:
            out.append(ch)
    return "".join(out)


def _key_stream(key, n):
    k = re.sub(r"[^a-z]", "", str(key or "").lower())
    if not k:
        raise ValueError("a key of letters is required")
    return [ord(c) - 97 for c in (k * (n // len(k) + 1))[:n]]


def vigenere(text, key, decrypt=False):
    ks = _key_stream(key, len(str(text)))
    out, i = [], 0
    for ch in str(text):
        if ch.isalpha():
            base = 97 if ch.islower() else 65
            k = ks[i]
            i += 1
            if decrypt:
                k = -k
            out.append(chr((ord(ch) - base + k) % 26 + base))
        else:
            out.append(ch)
    return "".join(out)


def a1z26(text, decrypt=False):
    if decrypt:
        nums = re.findall(r"\d+", str(text))
        return "".join(chr(int(n) + 96) if 1 <= int(n) <= 26 else "?"
                       for n in nums)
    return " ".join(str(ord(c) - 96) for c in str(text).lower()
                    if "a" <= c <= "z")


_BACON = {i: format(i, "05b").replace("0", "A").replace("1", "B")
          for i in range(26)}


def bacon(text, decrypt=False):
    if decrypt:
        bits = re.sub(r"[^ABab]", "", str(text)).upper()
        out = []
        for i in range(0, len(bits) - 4, 5):
            out.append(chr(int(bits[i:i + 5].replace("A", "0")
                               .replace("B", "1"), 2) + 97))
        return "".join(out)
    return " ".join(_BACON[ord(c) - 97] for c in str(text).lower()
                    if "a" <= c <= "z")


def rail_fence(text, rails=3, decrypt=False):
    s = str(text)
    r = max(2, int(rails or 3))
    if decrypt:
        pattern = list(range(r)) + list(range(r - 2, 0, -1))
        order = [pattern[i % len(pattern)] for i in range(len(s))]
        counts = [order.count(x) for x in range(r)]
        chunks, pos = [], 0
        for c in counts:
            chunks.append(list(s[pos:pos + c]))
            pos += c
        out = []
        for row in order:
            if chunks[row]:
                out.append(chunks[row].pop(0))
        return "".join(out)
    rows = [[] for _ in range(r)]
    pattern = list(range(r)) + list(range(r - 2, 0, -1))
    for i, ch in enumerate(s):
        rows[pattern[i % len(pattern)]].append(ch)
    return "".join("".join(row) for row in rows)


def reverse(text):
    return str(text)[::-1]


_MORSE = {
    "a": ".-", "b": "-...", "c": "-.-.", "d": "-..", "e": ".", "f": "..-.",
    "g": "--.", "h": "....", "i": "..", "j": ".---", "k": "-.-", "l": ".-..",
    "m": "--", "n": "-.", "o": "---", "p": ".--.", "q": "--.-", "r": ".-.",
    "s": "...", "t": "-", "u": "..-", "v": "...-", "w": ".--", "x": "-..-",
    "y": "-.--", "z": "--..", "0": "-----", "1": ".----", "2": "..---",
    "3": "...--", "4": "....-", "5": ".....", "6": "-....", "7": "--...",
    "8": "---..", "9": "----.", ".": ".-.-.-", ",": "--..--", "?": "..--..",
    "'": ".----.", "!": "-.-.--", "/": "-..-.", "(": "-.--.", ")": "-.--.-",
    "&": ".-...", ":": "---...", ";": "-.-.-.", "=": "-...-", "+": ".-.-.",
    "-": "-....-", "_": "..--.-", '"': ".-..-.", "$": "...-..-", "@": ".--.-.",
}
_MORSE_REV = {v: k for k, v in _MORSE.items()}


def morse(text, decrypt=False):
    if decrypt:
        out = []
        for token in str(text).strip().split(" "):
            if not token:
                out.append(" ")
            elif token == "/":
                out.append(" ")
            else:
                out.append(_MORSE_REV.get(token, "?"))
        return "".join(out)
    return " ".join(_MORSE.get(c, "") for c in str(text).lower()
                    if c in _MORSE or c == " ").replace("  ", " / ")


# ------------------------------------------------------------------- encodings
def b64_encode(text):
    return base64.b64encode(str(text).encode("utf-8")).decode("ascii")


def b64_decode(text):
    s = re.sub(r"\s+", "", str(text))
    s += "=" * (-len(s) % 4)
    return base64.b64decode(s).decode("utf-8", "replace")


def b32_encode(text):
    return base64.b32encode(str(text).encode("utf-8")).decode("ascii")


def b32_decode(text):
    s = re.sub(r"\s+", "", str(text)).upper()
    s += "=" * (-len(s) % 8)
    return base64.b32decode(s).decode("utf-8", "replace")


def b85_encode(text):
    return base64.b85encode(str(text).encode("utf-8")).decode("ascii")


def b85_decode(text):
    return base64.b85decode(str(text)).decode("utf-8", "replace")


def hex_encode(text):
    return str(text).encode("utf-8").hex()


def hex_decode(text):
    s = re.sub(r"0x|[\s:,-]", "", str(text))
    return bytes.fromhex(s).decode("utf-8", "replace")


def binary_encode(text):
    return " ".join(format(b, "08b")
                    for b in str(text).encode("utf-8"))


def binary_decode(text):
    bits = re.sub(r"[^01]", "", str(text))
    data = bytes(int(bits[i:i + 8], 2)
                 for i in range(0, len(bits) - 7, 8))
    return data.decode("utf-8", "replace")


def octal_encode(text):
    return " ".join(format(b, "03o") for b in str(text).encode("utf-8"))


def octal_decode(text):
    data = bytes(int(t, 8) for t in re.findall(r"[0-7]+", str(text)))
    return data.decode("utf-8", "replace")


def decimal_encode(text):
    return " ".join(str(b) for b in str(text).encode("utf-8"))


def decimal_decode(text):
    data = bytes(int(t) for t in re.findall(r"\d+", str(text)))
    return data.decode("utf-8", "replace")


def url_encode(text):
    return urllib.parse.quote(str(text), safe="")


def url_decode(text):
    return urllib.parse.unquote(str(text))


def html_encode(text):
    return html.escape(str(text), quote=True)


def html_decode(text):
    return html.unescape(str(text))


def unicode_encode(text):
    return str(text).encode("unicode_escape").decode("ascii")


def unicode_decode(text):
    return re.sub(r"\\u([0-9a-fA-F]{4})|\\x([0-9a-fA-F]{2})|\\U([0-9a-fA-F]{8})",
                  lambda m: chr(int(next(g for g in m.groups() if g), 16)),
                  str(text))


# ---------------------------------------------------------------------- modern
def xor_cipher(text, key="jarvis"):
    k = str(key or "").encode("utf-8") or b"jarvis"
    data = str(text).encode("utf-8")
    out = bytes(b ^ k[i % len(k)] for i, b in enumerate(data))
    return out.hex()


def xor_decrypt(text, key="jarvis"):
    k = str(key or "").encode("utf-8") or b"jarvis"
    data = bytes.fromhex(re.sub(r"[^0-9a-fA-F]", "", str(text)))
    return bytes(b ^ k[i % len(k)] for i, b in enumerate(data)) \
        .decode("utf-8", "replace")


_M = 0xFFFFFFFF


def _rotl(v, n):
    return ((v << n) & _M) | (v >> (32 - n))


def _qr(s, a, b, c, d):
    s[a] = (s[a] + s[b]) & _M
    s[d] = _rotl(s[d] ^ s[a], 16)
    s[c] = (s[c] + s[d]) & _M
    s[b] = _rotl(s[b] ^ s[c], 12)
    s[a] = (s[a] + s[b]) & _M
    s[d] = _rotl(s[d] ^ s[a], 8)
    s[c] = (s[c] + s[d]) & _M
    s[b] = _rotl(s[b] ^ s[c], 7)


def _block(key, counter, nonce):
    st = (list(struct.unpack("<4I", b"expand 32-byte k")) +
          list(struct.unpack("<8I", key)) +
          [counter & _M] + list(struct.unpack("<3I", nonce)))
    w = st[:]
    for _ in range(10):
        _qr(w, 0, 4, 8, 12)
        _qr(w, 1, 5, 9, 13)
        _qr(w, 2, 6, 10, 14)
        _qr(w, 3, 7, 11, 15)
        _qr(w, 0, 5, 10, 15)
        _qr(w, 1, 6, 11, 12)
        _qr(w, 2, 7, 8, 13)
        _qr(w, 3, 4, 9, 14)
    return struct.pack("<16I", *[(w[i] + st[i]) & _M for i in range(16)])


def _chacha(key, nonce, data, counter=1):
    out = bytearray()
    for off in range(0, len(data), 64):
        stream = _block(key, counter, nonce)
        out.extend(a ^ b for a, b in zip(data[off:off + 64], stream))
        counter += 1
    return bytes(out)


def _derive(passphrase, salt):
    return hashlib.pbkdf2_hmac("sha256", str(passphrase).encode("utf-8"),
                               salt, 200_000, dklen=32)


def _mac(key, nonce, cipher):
    return hmac.new(key, b"jarvis-vault-v1" + nonce + cipher,
                    hashlib.sha256).digest()


def chacha_encrypt(text, passphrase):
    if not passphrase:
        raise ValueError("a passphrase is required")
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = _derive(passphrase, salt)
    cipher = _chacha(key, nonce, str(text).encode("utf-8"))
    tag = _mac(key, nonce, cipher)
    blob = base64.b64encode(salt + nonce + tag + cipher).decode("ascii")
    return "JVAULT1." + blob


def chacha_decrypt(token, passphrase):
    s = str(token).strip()
    if s.startswith("JVAULT1."):
        s = s[8:]
    raw = base64.b64decode(re.sub(r"\s+", "", s))
    salt, nonce, tag, cipher = raw[:16], raw[16:28], raw[28:60], raw[60:]
    key = _derive(passphrase, salt)
    if not hmac.compare_digest(_mac(key, nonce, cipher), tag):
        raise ValueError("wrong passphrase or damaged text")
    return _chacha(key, nonce, cipher).decode("utf-8", "replace")


# ------------------------------------------------------------------------ hash
def hash_text(text, algo="sha256"):
    data = str(text).encode("utf-8")
    return hashlib.new(algo, data).hexdigest()


# ------------------------------------------------------------------ auto tools
def likely(text):
    """A short, honest guess about what a blob probably is."""
    s = str(text or "").strip()
    if not s:
        return "empty"
    if s.startswith("JVAULT1."):
        return "JARVIS ChaCha20 vault text"
    if re.fullmatch(r"[0-9a-fA-F\s:]+", s) and len(re.sub(r"\s", "", s)) % 2 == 0:
        return "hexadecimal"
    if re.fullmatch(r"[01\s]+", s):
        return "binary"
    if re.fullmatch(r"[0-7\s]+", s) and "8" not in s and "9" not in s:
        return "octal"
    if re.fullmatch(r"[A-Za-z0-9+/=\s]+", s) and len(s) % 4 == 0:
        return "base64"
    if re.fullmatch(r"[A-Z2-7=\s]+", s.upper()) and len(s) % 8 == 0:
        return "base32"
    if re.fullmatch(r"[.\-/ \s]+", s):
        return "Morse"
    if re.fullmatch(r"[ABab\s]+", s) and len(re.sub(r"\s", "", s)) % 5 == 0:
        return "Bacon"
    if re.fullmatch(r"\d+(?:\s+\d+)+", s):
        return "decimal or a1z26"
    if re.fullmatch(r"\S+", s) and all(c.isalpha() for c in s):
        return "text (try Caesar, Atbash or Vigenere)"
    return "unknown"


def auto_decode(text):
    """Try the common transforms and return readable candidates."""
    s = str(text or "").strip()
    trials = [
        ("Base64", lambda: b64_decode(s)),
        ("Base32", lambda: b32_decode(s)),
        ("Hex", lambda: hex_decode(s)),
        ("Binary", lambda: binary_decode(s)),
        ("Octal", lambda: octal_decode(s)),
        ("Decimal", lambda: decimal_decode(s)),
        ("URL", lambda: url_decode(s)),
        ("HTML", lambda: html_decode(s)),
        ("Unicode", lambda: unicode_decode(s)),
        ("ROT13", lambda: rot13(s)),
        ("Atbash", lambda: atbash(s)),
        ("Reverse", lambda: reverse(s)),
        ("Morse", lambda: morse(s, True)),
        ("Bacon", lambda: bacon(s, True)),
        ("a1z26", lambda: a1z26(s, True)),
    ]
    out = []
    for name, fn in trials:
        try:
            val = fn()
            if val and val.strip() and val != s:
                out.append((name, val[:400]))
        except Exception:
            continue
    return out


# --------------------------------------------------------------------- methods
# name -> (encode, decode | None, needs, hint)
def methods():
    return {
        "Caesar shift": (lambda t, k: caesar(t, _num(k, 3), False),
                         lambda t, k: caesar(t, _num(k, 3), True),
                         "Shift", "1-25. The oldest trick in the book."),
        "ROT13": (rot13, rot13, "", "Caesar with shift 13. Encodes and decodes."),
        "Atbash": (atbash, atbash, "", "A<->Z, B<->Y. Mirror alphabet."),
        "Vigenere": (lambda t, k: vigenere(t, k, False),
                     lambda t, k: vigenere(t, k, True),
                     "Key", "Letters only. The unbreakable cipher of 1553."),
        "A1Z26": (lambda t, k: a1z26(t, False),
                  lambda t, k: a1z26(t, True),
                  "", "Letters to 1-26 numbers."),
        "Bacon": (lambda t, k: bacon(t, False),
                  lambda t, k: bacon(t, True),
                  "", "Five A/B symbols per letter."),
        "Rail fence": (lambda t, k: rail_fence(t, _num(k, 3), False),
                       lambda t, k: rail_fence(t, _num(k, 3), True),
                       "Rails", "Writes zig-zag rows, then reads them flat."),
        "Reverse": (reverse, reverse, "", "Reads the text backwards."),
        "Morse": (lambda t, k: morse(t, False),
                  lambda t, k: morse(t, True),
                  "", "Dots, dashes, and / between words."),
        "Base64": (b64_encode, b64_decode, "", "The internet's default packing."),
        "Base32": (b32_encode, b32_decode, "", "A-Z and 2-7. No ambiguity."),
        "Base85": (b85_encode, b85_decode, "", "Denser than Base64."),
        "Hexadecimal": (hex_encode, hex_decode, "", "Two hex digits per byte."),
        "Binary": (binary_encode, binary_decode, "", "Eight bits per byte."),
        "Octal": (octal_encode, octal_decode, "", "Three octal digits per byte."),
        "Decimal ASCII": (decimal_encode, decimal_decode, "",
                          "Byte values as ordinary numbers."),
        "URL encode": (url_encode, url_decode, "",
                       "Percent-escapes for addresses and forms."),
        "HTML entities": (html_encode, html_decode, "",
                          "&lt; &gt; &amp; and friends."),
        "Unicode escape": (unicode_encode, unicode_decode, "",
                           "\\uXXXX code points."),
        "XOR": (lambda t, k: xor_cipher(t, k),
                lambda t, k: xor_decrypt(t, k),
                "Key", "Repeating-key XOR, shown as hex."),
        "ChaCha20 + HMAC": (lambda t, k: chacha_encrypt(t, k),
                            lambda t, k: chacha_decrypt(t, k),
                            "Passphrase",
                            "PBKDF2-SHA256, 200k rounds, authenticated."),
        "SHA-256": (lambda t, k: hash_text(t, "sha256"), None, "",
                    "One-way fingerprint. Cannot be decoded."),
        "SHA-1": (lambda t, k: hash_text(t, "sha1"), None, "",
                  "Old one-way hash. Fine for learning, not for security."),
        "MD5": (lambda t, k: hash_text(t, "md5"), None, "",
                "Checksum only. Never for passwords."),
        "BLAKE2b": (lambda t, k: hash_text(t, "blake2b"), None, "",
                    "Modern, fast one-way hash."),
    }


def _num(value, fallback):
    try:
        return int(str(value).strip())
    except Exception:
        return fallback


def run(method, text, key="", mode="encode"):
    table = methods()
    if method not in table:
        raise ValueError("unknown method")
    enc, dec, _needs, _hint = table[method]
    fn = dec if mode == "decode" else enc
    if fn is None:
        raise ValueError("that one is one-way; it cannot be decoded")
    try:
        return fn(text, key)
    except TypeError:
        # Simple encoders take only the text; keyed ones take both.
        return fn(text)
