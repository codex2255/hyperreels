#!/usr/bin/env python3
"""Story Reel: a narrated story of a business, venue or event, as a 1080x1920 vertical video.

Two-word karaoke captions synced to the voice, the subject's images in a fixed set of desktop-style windows (one big,
two small, or a grid) that pops in per topic, over a bright moving backdrop, ending on the client's end card
(logo, CTA line, sub line). One props file per Reel, nothing else to edit.

  python3 build.py props/<slug>.json [--no-voice]

Writes index.html (from page.tpl), assets/clips/ (images, window clips, the backdrop) and assets/music/mix.wav.
Source media is only read. Then: npx hyperframes lint, npx hyperframes check, npx hyperframes render.

Paths in props:
  - window images and clips (`topics`) and the end card logo are file names inside `media_dir`
    (default library/<slug>/); subpaths such as footage/x.mp4 work.
  - `voice.file`, `music` and `backdrop` are relative to this folder (the repo root).
Every image and clip needs a `<file>.source.txt` next to it, and the music a `<file stem>.licence.txt`.
See README.md for the full props reference.
"""
import html as H, json, math, os, re, shutil, subprocess, sys

# GSAP comes from npm (node_modules/gsap), copied next to the page at build time; it is not redistributed in this repo.
import shutil as _sh
_g = os.path.join(os.path.dirname(os.path.abspath(__file__)), "node_modules", "gsap", "dist", "gsap.min.js")
if not os.path.exists(_g):
    sys.exit("GSAP missing: run `npm i` first")
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib", "vendor"), exist_ok=True)
_sh.copyfile(_g, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib", "vendor", "gsap.min.js"))

HERE = os.path.dirname(os.path.abspath(__file__))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
if not args:
    raise SystemExit(__doc__)
props_path = os.path.abspath(args[0])
os.chdir(HERE)
NO_VOICE = "--no-voice" in sys.argv
P = json.load(open(props_path))
FPS = 30
MAX_HOLD = 4.5   # a topic's window set holds 2-4 s while it is narrated
MIN_HOLD = 1.5
POP_GAP = P.get("pop_gap", 0.2)   # the big window first, then each small one this far apart

FONTS = {   # bundled, SIL Open Font License (assets/fonts/OFL-*.txt). width = average glyph width per em, for fitting
    "barlow": {"family": "Barlow Condensed", "file": "assets/fonts/BarlowCondensed-ExtraBold.woff2", "weight": 800, "width": 0.5},
    "barlow-black": {"family": "Barlow Condensed", "file": "assets/fonts/BarlowCondensed-Black.woff2", "weight": 900, "width": 0.51},
    "inter": {"family": "Inter", "file": "assets/fonts/Inter-Bold.woff2", "weight": 700, "width": 0.6},
}
COLORS = {"bg": "#0B0B10", "text": "#FFFFFF", "highlight": "#FFD23F", **P.get("colors", {})}


def die(msg):
    raise SystemExit("story build: " + msg)


def run(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode:
        die(r.stderr[-1500:])


# ---- inputs and the rules about them -------------------------------------------------------------------------
words = P["script"].split()
T = P["timing"]
TE = P.get("timing_end") or T[1:] + [T[-1] + 0.6]
if len(T) != len(words) or len(TE) != len(words):
    die(f"timing has {len(T)} starts and {len(TE)} ends for {len(words)} script words (run time_voice.py)")
if any(b < a for a, b in zip(T, T[1:])):
    die("timing runs backwards")
slug = re.sub(r"[^a-z0-9]+", "-", P["subject"].lower()).strip("-")
MEDIA = os.path.join(HERE, P.get("media_dir", f"library/{slug}"))
for c in ("bg", "text", "highlight"):
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", COLORS[c]):
        die(f"colors.{c} must be a #RRGGBB hex colour, got {COLORS[c]!r}")


def sourced(p, what="image or clip"):
    if not os.path.isfile(p):
        die(f"missing {what} {os.path.relpath(p, HERE)}")
    if not os.path.isfile(p + ".source.txt"):
        die(f"{os.path.relpath(p, HERE)} has no .source.txt next to it (where it came from, who owns it, the permission "
            f"or licence, and the date). Every image and clip needs one.")
    return p


def media(name):
    return sourced(os.path.join(MEDIA, name))


def repo_file(rel):
    p = os.path.join(HERE, rel)
    if not os.path.isfile(p):
        die(f"not found: {rel}")
    return p


V = P.get("voice")
voice = None
if V and not NO_VOICE:
    voice = repo_file(V["file"] if isinstance(V, dict) else V)
music = None
if P.get("music"):
    music = repo_file(P["music"])
    lic = os.path.splitext(music)[0] + ".licence.txt"
    if not os.path.isfile(lic):
        die(f"no {os.path.relpath(lic, HERE)} next to the music: say where the track is from and the licence that "
            f"covers its use in a client Reel")

# ---- timeline ------------------------------------------------------------------------------------------------
E = P.get("end") or {}
if not E.get("logo") and not E.get("line"):
    die("props need an `end` card: {logo, line, sub}")
last_end = TE[-1]
END_FROM = round(max(T[E["from_word"]] - 0.15, 0) if "from_word" in E else last_end + 0.2, 3)
DUR = round(max(last_end, END_FROM) + E.get("hold", 1.6), 2)

topics = P["topics"]
if any(tp["from_word"] >= E.get("from_word", len(words)) for tp in topics):
    die("every topic must start before end.from_word")
tfrom = [0.0] + [T[s["from_word"]] for s in topics[1:]]
tto = tfrom[1:] + [END_FROM]
for s, a, b in zip(topics, tfrom, tto):
    if b - a > MAX_HOLD + 0.001 or b - a < MIN_HOLD - 0.001:
        print(f"WARNING: topic at word {s['from_word']} holds {b - a:.2f}s (aim for {MIN_HOLD}-{MAX_HOLD}s)")

# ---- images ----------------------------------------------------------------------------------------------------
for d in ("assets/clips", "assets/music"):
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
made = {}


def prep(path, out, long=1400):
    if out in made:
        return
    run("ffmpeg", "-v", "error", "-nostdin", "-y", "-i", path, "-vf", f"scale='min({long},iw)':'min({long},ih)':force_original_aspect_ratio=decrease", "-q:v", "3", "-update", "1", "-frames:v", "1", out)
    made[out] = True


def stem(n):
    return re.sub(r"[^a-z0-9]+", "-", os.path.splitext(n)[0].lower()).strip("-")


# The fixed window set on 1080x1920 (windows may pass x 926; text never does). The big window is ~90% wide, the
# two small ones ~44% wide under it, the right one higher so the big window's lower-right corner sits over it.
BIG = (54, 500, 972, 620)
SMALL = [(54, 1134, 475, 392), (551, 1110, 475, 392)]


def grid(n):
    cols = 4 if n > 6 else 3 if n > 4 else 2
    rows = math.ceil(n / cols)
    g = 18
    w = (972 - g * (cols - 1)) // cols
    h = (980 - g * (rows - 1)) // rows
    return [(54 + (k % cols) * (w + g), 500 + (k // cols) * (h + g), w, h) for k in range(n)]


def pos_frac(pos):
    """CSS object-position (percent or keyword pairs) -> (x, y) fractions for a crop."""
    kw = {"left": 0, "top": 0, "center": 0.5, "right": 1, "bottom": 1}
    parts = pos.split()
    if len(parts) == 1:
        parts.append("center")
    out = []
    for p in parts[:2]:
        out.append(float(p[:-1]) / 100 if p.endswith("%") else kw[p] if p in kw else die(f"bad pos {pos!r}"))
    return out


def probe_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def window(wid, kind, box, im, ti, wi, at, to):
    im = {"file": im} if isinstance(im, str) else im
    l, t, w, h = box
    style = f"left:{l}px;top:{t}px;width:{w}px;height:{h}px"
    head = f'      <div id="{wid}" class="win {kind}" style="{style}"><div class="bob"><div class="bar"><i></i><i></i><i></i><b></b></div>'
    if "clip" in im:
        # A video window: cut to the on-screen time from `start`, muted, centre-cropped (honouring pos) to the picture
        # area (window minus the 2 px border and the title bar), so there is no letterboxing.
        src = media(im["clip"])
        start = float(im.get("start", 0))
        dur = round(max(to - at, 0.3), 3)
        if probe_dur(src) < start + dur:
            die(f"clip {im['clip']} is {probe_dur(src):.2f}s; window {wid} needs {dur:.2f}s from {start}s")
        cw, ch = w - 4, h - 4 - (36 if kind in ("small", "cell") else 44)
        cw, ch = cw - cw % 2, ch - ch % 2
        px, py = pos_frac(im.get("pos", "50% 50%"))
        out = f"assets/clips/win_{ti}_{wi}_{stem(os.path.basename(im['clip']))}.mp4"
        run("ffmpeg", "-v", "error", "-nostdin", "-y", "-ss", str(start), "-t", str(dur + 0.05), "-i", src, "-an",
            "-vf", f"scale={cw}:{ch}:force_original_aspect_ratio=increase:flags=lanczos,crop={cw}:{ch}:'(iw-{cw})*{px}':'(ih-{ch})*{py}',fps={FPS},format=yuv420p",
            "-c:v", "libx264", "-profile:v", "high", "-crf", "18", "-preset", "medium", "-g", "15", "-movflags", "+faststart", out)
        return (head + f'<div class="pic" data-layout-allow-overflow><video id="{wid}v" class="clip" src="{out}" muted playsinline '
                f'data-start="{at:.3f}" data-duration="{dur:.3f}" data-track-index="{2 + wi}"></video></div></div></div>')
    base = f"assets/clips/{stem(im['file'])}.jpg"
    prep(media(im["file"]), base)
    out = f"assets/clips/{stem(im['file'])}_{ti}_{wi}.jpg"   # one file per window, so lint sees no duplicated media
    shutil.copyfile(base, out)
    pos = im.get("pos", "50% 12%" if kind == "cell" else "50% 22%")
    return head + f'<div class="pic" data-layout-allow-overflow><img src="{out}" alt="" style="object-position:{pos}" /></div></div></div>'


win_html, topic_wins = [], []
for ti, tp in enumerate(topics):
    if "grid" in tp:
        if not 4 <= len(tp["grid"]) <= 8:
            die(f"topic {ti}: a grid takes 4-8 entries")
        items = [("cell", box, im, k * 0.06) for k, (box, im) in enumerate(zip(grid(len(tp["grid"])), tp["grid"]))]
    else:
        items = [("big", BIG, tp["big"], 0.0)] + [("small", box, im, (k + 1) * POP_GAP) for k, (box, im) in enumerate(zip(SMALL, tp.get("small", [])))]
    ids = []
    for wi, (kind, box, im, delay) in enumerate(items):
        wid = f"w{ti}_{wi}"
        at = 0.0 if ti == 0 else round(tfrom[ti] + delay, 3)
        win_html.append(window(wid, kind, box, im, ti, wi, at, tto[ti]))
        ids.append([wid, round(delay, 3)])
    topic_wins.append([round(tfrom[ti], 3), round(tto[ti], 3), ids])

# ---- the backdrop: a bright moving loop (make_backdrop.py), looped to length; a flat colour if none is given --------
bg_html = []
if P.get("backdrop"):
    bd = sourced(repo_file(P["backdrop"]), "backdrop")
    out = "assets/clips/backdrop.mp4"
    run("ffmpeg", "-v", "error", "-nostdin", "-y", "-stream_loop", "-1", "-ss", str(P.get("backdrop_start", 0)), "-i", bd, "-t", str(DUR), "-an",
        "-vf", f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps={FPS},format=yuv420p",
        "-c:v", "libx264", "-profile:v", "high", "-crf", "17", "-preset", "fast", "-g", "15", "-movflags", "+faststart", out)
    bg_html.append(f'      <div id="bgw0" class="bgwrap"><video id="bgv0" class="clip" src="{out}" muted playsinline data-start="0" data-duration="{DUR:.3f}" data-track-index="1"></video></div>')
else:
    print("WARNING: no backdrop; the film sits on colors.bg (make one with make_backdrop.py)")

# ---- the end card: the client's logo, a CTA line and a sub line -------------------------------------------------
end_html = ['      <div id="end"><div id="endcard">']
if E.get("logo"):
    logo = f"assets/clips/logo{os.path.splitext(E['logo'])[1].lower()}"
    shutil.copyfile(media(E["logo"]), logo)
    end_html.append(f'        <img id="logo" src="{logo}" alt="" />')
if E.get("line"):
    end_html.append(f'        <div id="endline">{H.escape(E["line"])}</div>')
if E.get("sub"):
    end_html.append(f'        <div id="endsub">{H.escape(E["sub"])}</div>')
end_html.append("      </div></div>")

# ---- captions: karaoke pairs. Two words at a time, broken after a sentence end or comma and where the end card
# starts; each word is highlighted while it is said. One line, sized to fit x 96-926. ---------------------------------
font = P.get("font", "barlow")
F = FONTS.get(font) if isinstance(font, str) else {"family": font.get("family", "Story Custom"), "file": font["file"], "weight": font.get("weight", 700), "width": font.get("width", 0.55)}
if not F:
    die(f"font {font!r}: use one of {sorted(FONTS)} or {{file, family?, weight?, width?}}")
repo_file(F["file"])
end_word = E.get("from_word", -1)
groups, i = [], 0
while i < len(words):
    j = i + 1
    if j < len(words) and not re.search(r"[.,?!;:]$", words[i]) and j != end_word:
        j += 1
    groups.append((i, j))
    i = j
gstart = []   # a pair is on screen at least 0.4 s, even where whisper gives several words one start
for a, _ in groups:
    gstart.append(0.0 if not gstart else min(max(T[a], gstart[-1] + 0.4), DUR - 0.4))
cap_html, cap_times = [], []
for gi, (a, b) in enumerate(groups):
    ws = words[a:b]
    size = max(76, min(128, int(780 / (len(" ".join(ws)) * F["width"] + 0.24 * len(ws)))))
    spans = "".join(f'<span id="c{gi}_{k}" class="w">{H.escape(w)}</span>' for k, w in enumerate(ws))
    t0 = gstart[gi]
    t1 = gstart[gi + 1] if gi + 1 < len(groups) else min(TE[-1] + 0.6, DUR - 0.05)
    on = [t0]   # whisper sometimes gives two words one start; each still gets 0.15 s of highlight
    for k in range(1, len(ws)):
        on.append(min(max(T[a + k], on[-1] + 0.15), t1 - 0.05))
    wt = [[f"c{gi}_{k}", round(on[k], 3), round(on[k + 1] if k + 1 < len(ws) else t1, 3)] for k in range(len(ws))]
    cap_html.append(f'        <div id="c{gi}" class="cap" style="font-size:{size}px">{spans}</div>')
    cap_times.append([f"c{gi}", round(t0, 3), round(t1, 3), wt])

# ---- sound: the voice at -14 LUFS, the music under it, gently ducked by the voice, the whole mix at -14 LUFS ----------
mstart = P.get("music_start", 0)
FADE_OUT = P.get("music_fade_out", 1.4)
fade = f"afade=in:d=0.5,afade=out:st={max(DUR - FADE_OUT, 0)}:d={FADE_OUT}"
MUSIC_DB = P.get("music_db", -20)   # the music's level under the voice
VOICE_DB = P.get("voice_db", 0)     # a trim on the voice before the whole mix is brought to -14 LUFS
D = {"ratio": 2, "threshold": 0.1, "attack": 20, "release": 260, **P.get("duck", {})}
m = f"[0:a]atrim={mstart}:{mstart + DUR + 1},asetpts=PTS-STARTPTS,aresample=48000,loudnorm=I=-14:LRA=9:TP=-1.5,aresample=48000"
tail = f"apad=whole_dur={DUR + 0.5},loudnorm=I=-14:LRA=9:TP=-1.5,aresample=48000,asetpts=N/SR/TB,apad=whole_dur={DUR},atrim=0:{DUR}"   # loudnorm shifts timestamps; restamp and cut by samples
vgain = f",volume={VOICE_DB:g}dB" if VOICE_DB else ""
if voice and music:
    graph = (f"{m},volume={MUSIC_DB + VOICE_DB:g}dB,{fade}[m];[1:a]aresample=48000,loudnorm=I=-14:LRA=7:TP=-1.5,aresample=48000{vgain},asplit[v][vk];"
             f"[m][vk]sidechaincompress=threshold={D['threshold']}:ratio={D['ratio']}:attack={D['attack']}:release={D['release']}:makeup=1[md];"
             f"[md][v]amix=inputs=2:normalize=0:duration=longest,{tail}")
    ins = ["-i", music, "-i", voice]
elif voice:
    graph = f"[0:a]aresample=48000{vgain},{tail}"
    ins = ["-i", voice]
elif music:
    graph = f"{m},{fade},asetpts=N/SR/TB,apad=whole_dur={DUR},atrim=0:{DUR}"
    ins = ["-i", music]
else:
    graph = f"anullsrc=r=48000:cl=stereo,atrim=0:{DUR}"
    ins = []
run("ffmpeg", "-v", "error", "-nostdin", "-y", *ins, *(["-filter_complex", graph] if ins else ["-f", "lavfi", "-i", graph]),
    "-t", f"{DUR}", "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", "assets/music/mix.wav")

# ---- the page ------------------------------------------------------------------------------------------------------
page = open("page.tpl").read().replace("__DUR__", str(DUR))


def block(name, lines):
    global page
    page = re.sub(rf"<!-- {name} -->.*?<!-- /{name} -->", lambda _: f"<!-- {name} -->\n" + "\n".join(lines) + f"\n      <!-- /{name} -->", page, flags=re.S)


theme = (f'@font-face {{ font-family: "{F["family"]}"; font-weight: {F["weight"]}; src: url("{F["file"]}") format("{"woff2" if F["file"].endswith(".woff2") else "truetype"}"); }}\n'
         f'      :root {{ --bg: {COLORS["bg"]}; --text: {COLORS["text"]}; --highlight: {COLORS["highlight"]}; '
         f'--font: "{F["family"]}", sans-serif; --weight: {F["weight"]}; }}')
block("theme", ["      <style>", "      " + theme, "      </style>"])
block("bgs", bg_html)
block("caps", ['      <div id="caps" data-layout-allow-overflow>'] + cap_html + ["      </div>"])
block("wins", win_html)
block("end", end_html)
block("draft", ['      <div id="draft">DRAFT</div>'] if P.get("draft") else [])
for name, val in (("GROUPS", cap_times), ("TOPICS", topic_wins)):
    page = re.sub(rf"const {name} = \[\];", lambda _: f"const {name} = {json.dumps(val)};", page, count=1)
page = re.sub(r"const LOOK = \{\};", lambda _: "const LOOK = " + json.dumps({"bob": P.get("bob", 2), "end_from": END_FROM, "has_bg": bool(bg_html)}) + ";", page, count=1)
open("index.html", "w").write(page)
print(f"{DUR}s, {len(words)} words, {len(topics)} topics -> index.html")
