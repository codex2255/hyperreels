#!/usr/bin/env python3
"""Make the placeholder media for the Acme Coffee Roasters example (a fictional business).

  python3 examples/make_acme.py

Writes examples/acme/: labelled colour cards (stand-ins for real photos), one short generated clip, a logo, the
backdrop's source picture and its loop (via make_backdrop.py), a placeholder music bed, and a placeholder "voice"
(a soft tone on every word, at the hand-written timing in props/example-acme.json), so the example builds and
renders without an ElevenLabs key. Every file gets its .source.txt / .licence.txt. Nothing here is real media:
replace all of it for a real Reel.
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(HERE, "acme")
FONT = os.path.join(REPO, "assets", "fonts", "BarlowCondensed-ExtraBold.woff2")
os.makedirs(OUT, exist_ok=True)
NOTE = "generated placeholder (examples/make_acme.py). Not a real photo or clip. Replace with client-supplied or owned media.\n"


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:   # Pillow built without WOFF2 support
        return ImageFont.load_default(size=size)


def card(name, label, sub, c1, c2, size=(1400, 1000)):
    w, h = size
    y = np.linspace(0, 1, h)[:, None, None]
    x = np.linspace(0, 1, w)[None, :, None]
    k = np.clip(0.6 * y + 0.4 * x, 0, 1)
    a, b = np.array(c1, np.float32), np.array(c2, np.float32)
    im = Image.fromarray((a * (1 - k) + b * k).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for i in range(6):   # a few soft rings so the drift and crop are visible
        r = 120 + i * 90
        d.ellipse((w * 0.72 - r, h * 0.3 - r, w * 0.72 + r, h * 0.3 + r), outline=(255, 255, 255), width=3)
    d.text((w / 2, h * 0.46), label, font=font(int(h * 0.15)), fill=(255, 255, 255), anchor="mm", stroke_width=6, stroke_fill=(20, 16, 14))
    d.text((w / 2, h * 0.62), sub, font=font(int(h * 0.06)), fill=(255, 240, 215), anchor="mm")
    d.text((40, h - 40), "PLACEHOLDER", font=font(int(h * 0.04)), fill=(255, 255, 255), anchor="ls")
    p = os.path.join(OUT, name)
    im.convert("RGB").save(p, quality=88)
    open(p + ".source.txt", "w").write(NOTE)


CARDS = [
    ("cup.jpg", "Flat white", "the morning cup", (120, 72, 40), (214, 160, 98)),
    ("cafe.jpg", "Cafe counter", "a local cafe", (40, 90, 110), (110, 170, 160)),
    ("beans.jpg", "Green beans", "before the roast", (70, 110, 50), (170, 190, 90)),
    ("storefront.jpg", "Acme Roasters", "the shopfront", (150, 40, 40), (230, 120, 70)),
    ("garage.jpg", "The garage", "where it started", (60, 60, 80), (140, 130, 150)),
    ("roaster.jpg", "Secondhand roaster", "bought used", (90, 50, 30), (190, 110, 60)),
    ("founders.jpg", "Two friends", "the founders", (30, 80, 140), (120, 160, 220)),
    ("batch.jpg", "Batch 100", "the one that worked", (110, 30, 60), (220, 100, 120)),
    ("roastery.jpg", "The roastery", "six days a week", (50, 50, 50), (160, 120, 80)),
    ("cafes.jpg", "40 cafes", "around town", (20, 100, 90), (120, 200, 160)),
    ("bag.jpg", "Roast date", "stamped on every bag", (140, 100, 30), (240, 200, 110)),
    ("blend-house.jpg", "House", "blend", (120, 60, 30), (200, 120, 60)),
    ("blend-espresso.jpg", "Espresso", "blend", (60, 30, 20), (150, 80, 50)),
    ("blend-filter.jpg", "Filter", "blend", (40, 100, 130), (130, 190, 210)),
    ("blend-decaf.jpg", "Decaf", "blend", (90, 90, 40), (190, 180, 100)),
    ("market.jpg", "Saturday market", "come say hi", (140, 50, 90), (240, 140, 120)),
]


def logo():
    w, h = 1000, 600
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, w - 20, h - 20), radius=60, fill=(250, 240, 222, 255), outline=(40, 24, 16, 255), width=10)
    d.ellipse((70, 170, 330, 430), fill=(120, 66, 34, 255))
    d.line((200, 190, 200, 410), fill=(250, 240, 222, 255), width=14)
    d.text((640, 250), "ACME", font=font(210), fill=(40, 24, 16, 255), anchor="mm")
    d.text((640, 420), "COFFEE ROASTERS", font=font(70), fill=(120, 66, 34, 255), anchor="mm")
    p = os.path.join(OUT, "logo.png")
    im.save(p)
    open(p + ".source.txt", "w").write("generated placeholder logo for a fictional business (examples/make_acme.py). Use the client's own logo file.\n")


def clip():
    """roasting.mp4: 6 s of a turning drum, so the example shows a video window."""
    w, h, n = 1280, 720, 180
    p = os.path.join(OUT, "roasting.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-nostdin", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", "30",
                            "-i", "-", "-c:v", "libx264", "-crf", "24", "-pix_fmt", "yuv420p", p], stdin=subprocess.PIPE)
    f = font(90)
    for i in range(n):
        im = Image.new("RGB", (w, h), (70, 40, 26))
        d = ImageDraw.Draw(im)
        cx, cy, r = 400, 360, 230
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(150, 150, 155), outline=(30, 30, 30), width=8)
        for k in range(6):
            a = i * 0.08 + k * math.pi / 3
            d.line((cx, cy, cx + r * 0.9 * math.cos(a), cy + r * 0.9 * math.sin(a)), fill=(60, 60, 64), width=12)
        d.text((900, 320), "Roasting", font=f, fill=(255, 230, 200), anchor="mm")
        d.text((900, 420), "PLACEHOLDER CLIP", font=font(40), fill=(255, 255, 255), anchor="mm")
        enc.stdin.write(im.tobytes())
    enc.stdin.close()
    enc.wait()
    open(p + ".source.txt", "w").write(NOTE)


def backdrop():
    w, h = 1400, 2400
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = 200 + 55 * np.sin(xx / 170) * np.cos(yy / 230)
    g = 150 + 60 * np.sin((xx + yy) / 260)
    b = 90 + 70 * np.cos(yy / 190)
    im = Image.fromarray(np.dstack([r, g, b]).clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for k in range(40):   # bean-like dots so the motion reads
        x, y = (k * 337) % w, (k * 571) % h
        d.ellipse((x - 46, y - 30, x + 46, y + 30), fill=(110, 60, 30))
        d.line((x - 30, y, x + 30, y), fill=(70, 36, 18), width=6)
    p = os.path.join(OUT, "backdrop-source.png")
    im.save(p)
    open(p + ".source.txt", "w").write(NOTE)
    subprocess.run([sys.executable, os.path.join(REPO, "make_backdrop.py"), p, os.path.join(OUT, "backdrop.mp4"), "--seconds", "16"], check=True)


def write_mp3(path, x, sr=48000):
    """Mono 16-bit PCM piped into ffmpeg and saved as a small mp3 (keeps the repo light)."""
    y = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "-",
                    "-c:a", "libmp3lame", "-b:a", "64k", path], input=y.tobytes(), check=True)


def music(seconds=40, sr=48000):
    t = np.arange(int(seconds * sr)) / sr
    x = np.zeros_like(t)
    chords = [(220.0, 277.18, 329.63), (196.0, 246.94, 293.66), (174.61, 220.0, 261.63), (196.0, 246.94, 329.63)]
    for i, ch in enumerate(chords * 5):   # a soft four-chord pad, 2 s per chord
        a, b = i * 2.0, i * 2.0 + 2.0
        m = (t >= a) & (t < b)
        env = np.sin(np.pi * (t[m] - a) / 2.0) ** 0.5
        for f in ch:
            x[m] += 0.08 * env * np.sin(2 * np.pi * f * t[m])
    beat = (np.sin(2 * np.pi * 2 * t) > 0.95).astype(np.float32) * np.sin(2 * np.pi * 60 * t) * 0.25
    p = os.path.join(OUT, "music-placeholder.mp3")
    write_mp3(p, x + beat)
    open(os.path.join(OUT, "music-placeholder.licence.txt"), "w").write(
        "placeholder, replace. Generated tones (examples/make_acme.py), no third-party audio. A real Reel needs a track "
        "you are licensed to use in a client's social video, with the licence written here.\n")


def voice(sr=48000):
    P = json.load(open(os.path.join(REPO, "props", "example-acme.json")))
    T, TE = P["timing"], P["timing_end"]
    t = np.arange(int((TE[-1] + 0.5) * sr)) / sr
    x = np.zeros_like(t)
    for k, (a, b) in enumerate(zip(T, TE)):   # one soft tone per word, so the karaoke can be checked by ear
        m = (t >= a) & (t < b)
        env = np.sin(np.pi * (t[m] - a) / (b - a))
        x[m] += 0.3 * env * np.sin(2 * np.pi * (330 + 40 * (k % 3)) * t[m])
    p = os.path.join(REPO, P["voice"]["file"])
    write_mp3(p, x)
    open(p + ".source.txt", "w").write("placeholder voice: one tone per script word at the hand-written timing in props/example-acme.json. "
                                       "A real Reel uses eleven_voice.mjs and time_voice.py.\n")


if __name__ == "__main__":
    for c in CARDS:
        card(*c)
    logo()
    clip()
    music()
    voice()
    backdrop()
    print("example media in", os.path.relpath(OUT, REPO))
