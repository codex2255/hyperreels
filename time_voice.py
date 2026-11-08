#!/usr/bin/env python3
"""Time a narration against its script, offline.

  time_voice.py <voice.mp3|wav> <props.json> [--timing-out <file.json>]

The voice was made from the approved script (eleven_voice.mjs), so the words are already known. whisper-cli
(whisper.cpp, offline, large-v3-turbo by default; set WHISPER_MODEL to use another) only supplies WHEN each word is said. The voice read the *spoken* text (the script with
props["spoken"] respellings, e.g. "Ngaio" -> "Nye-oh"), so the heard words are aligned against that, with
difflib, and the times are mapped back to the original script words: captions keep the script's spelling.
Script words whose respelling whisper heard as something else (or not at all) take the span of the unmatched heard
words between their matched neighbours, spread by length, so the output has exactly one {text,start,end} per
script word.

Writes <voice>.timing.json next to the voice (or --timing-out), and copies the word starts into the props
file (`timing`, `timing_end`), which is what build.py reads. Deterministic: same voice, same numbers.
"""
import difflib, json, os, re, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spoken  # noqa: E402

MODEL = os.path.expanduser(os.environ.get("WHISPER_MODEL", "~/.cache/whisper-models/ggml-large-v3-turbo.bin"))


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower().replace("-", ""))


def heard(wav):
    """[(text, start, end)] one entry per word whisper heard."""
    with tempfile.TemporaryDirectory() as tmp:
        pcm = os.path.join(tmp, "v.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-ar", "16000", "-ac", "1", pcm], check=True)
        base = os.path.join(tmp, "out")
        subprocess.run(["whisper-cli", "-m", MODEL, "-f", pcm, "-ml", "1", "-sow", "-oj", "-of", base, "-l", "en"],
                       check=True, capture_output=True)
        data = json.load(open(base + ".json"))
    out = []
    for seg in data["transcription"]:
        t = seg["text"].strip()
        if norm(t):
            out.append((t, seg["offsets"]["from"] / 1000, seg["offsets"]["to"] / 1000))
    return out


def align(spoken_words, hw):
    """spoken_words: one spoken string per script word. Returns (starts, ends) per script word."""
    toks, owner = [], []
    for i, s in enumerate(spoken_words):
        for t in s.split():
            if norm(t):
                toks.append(norm(t))
                owner.append(i)
    b = [norm(t) for t, _, _ in hw]
    sm = difflib.SequenceMatcher(a=toks, b=b, autojunk=False)
    n = len(spoken_words)
    start, end = [None] * n, [None] * n
    used = set()
    for i, j, size in sm.get_matching_blocks():
        for k in range(size):
            w = owner[i + k]
            used.add(j + k)
            s, e = hw[j + k][1], hw[j + k][2]
            start[w] = s if start[w] is None else min(start[w], s)
            end[w] = e if end[w] is None else max(end[w], e)
    total_end = hw[-1][2]
    i = 0
    while i < n:
        if start[i] is not None:
            i += 1
            continue
        j = i
        while j < n and start[j] is None:
            j += 1
        lo = end[i - 1] if i > 0 else 0.0
        hi = start[j] if j < n else total_end
        free = [hw[k] for k in range(len(hw)) if k not in used and hw[k][1] >= lo - 0.02 and hw[k][2] <= hi + 0.02]
        if free:
            lo, hi = free[0][1], free[-1][2]
        weights = [len(norm(spoken_words[k])) + 1 for k in range(i, j)]
        t = lo
        for k, wt in zip(range(i, j), weights):
            d = max(hi - lo, 0) * wt / sum(weights)
            start[k], end[k] = round(t, 2), round(t + d, 2)
            t += d
        i = j
    for k in range(n):
        if k and start[k] < end[k - 1] - 1e-6:
            start[k] = end[k - 1]
        end[k] = max(end[k], start[k])
    return [round(x, 2) for x in start], [round(x, 2) for x in end]


def main():
    args = list(sys.argv[1:])
    out = None
    if "--timing-out" in args:
        i = args.index("--timing-out")
        out = args[i + 1]
        del args[i:i + 2]
    if len(args) != 2:
        raise SystemExit(__doc__)
    wav, props_path = args
    props = json.load(open(props_path))
    words = props["script"].split()
    hw = heard(wav)
    start, end = align(spoken.spoken_per_word(props), hw)
    out = out or re.sub(r"\.\w+$", "", wav) + ".timing.json"
    v = props.get("voice")
    json.dump({"audio": wav, "voice": v if isinstance(v, dict) else str(v), "words": [{"text": w, "start": s, "end": e} for w, s, e in zip(words, start, end)]},
              open(out, "w"), indent=1)
    props["timing"], props["timing_end"] = start, end
    json.dump(props, open(props_path, "w"), indent=1, ensure_ascii=False)
    print(f"{len(words)} script words, {len(hw)} heard, last word ends {end[-1]}s -> {out}, and written into {props_path}")


if __name__ == "__main__":
    main()
