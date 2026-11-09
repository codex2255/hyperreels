# Story Reels

An open-source kit for making narrated "story of a business, venue or event" vertical Reels (1080x1920, 30 fps),
built on [HyperFrames](https://www.npmjs.com/package/hyperframes) and made by Blank Software Limited. Each Reel has:

- a hook question, the story, the payoff, then a call to action
- two-word karaoke captions, with the spoken word highlighted
- the subject's photos and clips in a set of desktop-style windows (one big, two small, or a grid) that pops in per topic
- a bright, always-moving backdrop
- an end card with the client's logo and a CTA line

One props file per Reel. HyperFrames renders the HTML page to MP4.

The guided way to make one is the Claude Code skill in `.claude/skills/story-reel/SKILL.md` (ask Claude to "make a
story reel"). This README is the reference.

## Install

```bash
git clone https://github.com/codex2255/hyperreels.git
cd story-reels
npm i                                  # HyperFrames, GSAP and the ElevenLabs SDK, pinned
pip3 install numpy pillow
brew install ffmpeg whisper-cpp        # macOS; on Linux use your package manager
mkdir -p ~/.cache/whisper-models && curl -L -o ~/.cache/whisper-models/ggml-large-v3-turbo.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin
cp .env.example .env.local             # add your own ElevenLabs API key (only needed for real voices)
python3 build.py props/example-acme.json && npx hyperframes render --fps 30 --quality draft -o renders/example-acme.mp4
```

If `npm i` warns that esbuild's install script was not approved, rendering still works; run `npm approve-builds` if you want to silence it.

Requirements: Node 22.18+, Python 3.10+, ffmpeg, whisper.cpp (`whisper-cli`). Claude Code is optional: the guided skill in
`.claude/skills/story-reel/` walks you through a Reel step by step.

## Setup (once), in detail

1. **Node 22.18+**, **Python 3.10+** with `numpy` and `Pillow` (`pip3 install numpy pillow`), and **ffmpeg** (`brew install ffmpeg`).
2. **whisper-cli** (whisper.cpp) and a model, for timing the voice offline:
   `brew install whisper-cpp`, then download `ggml-large-v3-turbo.bin` from the whisper.cpp models page into
   `~/.cache/whisper-models/` (or set `WHISPER_MODEL` to another model file).
3. `npm i` in this folder (installs HyperFrames and the ElevenLabs SDK at pinned versions).
4. `cp .env.example .env.local` and put **your own** ElevenLabs API key in it. Never share it or commit it (`.env*` is ignored).
5. Check everything works with the example (no key or real media needed):

       python3 build.py props/example-acme.json
       npx hyperframes lint && npx hyperframes check
       npx hyperframes render --fps 30 --quality draft -o renders/example-acme.mp4

   `python3 examples/make_acme.py` regenerates the example's placeholder media if you ever need it.

## Workflow

| Step | What | Command / file |
|---|---|---|
| 1 | Subject agreed with the client, in writing | note it in `script/<slug>.evidence.json` (`client_ok`) |
| 2 | Research and fact-check: a quote and URL for every line | `script/<slug>.evidence.json` |
| 3 | Script, 60-100 words: hook question, story, payoff, CTA | `script` in `props/<slug>.json` |
| 4 | Voice: choose by ear, generate, time | `python3 spoken.py props/<slug>.json > script/<slug>.spoken.txt`<br>`npm run voice -- script/<slug>.spoken.txt library/<slug>/voice.mp3 <voiceId>`<br>`python3 time_voice.py library/<slug>/voice.mp3 props/<slug>.json` |
| 5 | Media with rights, each with `.source.txt` | `library/<slug>/` |
| 6 | Backdrop, build, lint, check, render | `python3 make_backdrop.py <img or video> library/<slug>/backdrop.mp4`<br>`python3 build.py props/<slug>.json`<br>`npx hyperframes lint` / `check` / `render` |
| 7 | Self-review a contact sheet before handing over | see the skill |

`library/` and `renders/` are git-ignored: client media and finished videos stay on your machine or in the client's
shared drive, never in this repo. Commit only props and scripts you have the client's OK to keep.

## Props reference

```jsonc
{
  "subject": "Acme Coffee Roasters",          // slug = lower-case, dashes ("acme-coffee-roasters")
  "media_dir": "library/acme-coffee-roasters", // optional; default library/<slug>
  "script": "Who roasts the coffee ...",       // the exact words; captions show these
  "spoken": {"Acme": "Ack-mee"},               // optional respellings the VOICE says; captions never use them
  "voice": {"engine": "elevenlabs", "voice_id": "<id>", "file": "library/<slug>/voice.mp3"},
  "timing": [0.25, ...], "timing_end": [...],  // one start/end second per script word; written by time_voice.py
  "backdrop": "library/<slug>/backdrop.mp4",   // optional; from make_backdrop.py. Without it: flat colors.bg
  "backdrop_start": 0,
  "colors": {"bg": "#1A120D", "text": "#FFFFFF", "highlight": "#FFC94A"},   // #RRGGBB; highlight = spoken word, window dot, sub line
  "font": "barlow",                            // "barlow" | "barlow-black" | "inter" | {"file", "family", "weight", "width"}
  "topics": [
    {"from_word": 0, "big": "cup.jpg", "small": ["cafe.jpg", "beans.jpg"]},
    {"from_word": 9, "big": {"file": "storefront.jpg", "pos": "50% 50%"}},
    {"from_word": 28, "big": {"clip": "roasting.mp4", "start": 0}, "small": ["batch.jpg"]},
    {"from_word": 67, "grid": ["a.jpg", "b.jpg", "c.jpg", "d.jpg"]}
  ],
  "end": {"from_word": 72, "logo": "logo.png", "line": "Taste it this Saturday", "sub": "Acme Coffee Roasters", "hold": 1.6},
  "music": "library/music/track.mp3", "music_start": 0,
  "music_db": -20, "voice_db": 0, "music_fade_out": 1.4,
  "duck": {"ratio": 2, "threshold": 0.1, "attack": 20, "release": 260},
  "pop_gap": 0.2, "bob": 2,
  "draft": true
}
```

- **Words** are counted by splitting `script` on spaces, from 0. `from_word` is the index of a topic's first word.
- **Topics**: one window set per topic, held while it is narrated. Aim for 2-4 s each; build.py warns outside
  1.5-4.5 s. `{from_word, big, small: [a, b]}` (small is optional, up to two) or `{from_word, grid: [4-8 entries]}`.
  The motion comes from the backdrop and the pops, so don't change topic every second.
- **Window entries**: a file name, `{file, pos}` (CSS object-position, default `50% 22%`), or a video
  `{clip, start, pos}`. A clip is cut from `start` for the window's on-screen time, muted, cropped to fit; build.py stops
  if the clip is too short. Files live in `media_dir` (subfolders work).
- **End card**: `logo` (a file in `media_dir`, PNG with transparency is best), `line` (the CTA, short), `sub`
  (smaller, in the highlight colour). It appears at `end.from_word` (the windows give way while the CTA is spoken) or,
  without it, just after the last word. It holds `hold` seconds after the last word. Captions keep running over it.
- **Paths**: window media and the logo resolve inside `media_dir`. `voice.file`, `music` and `backdrop` resolve from
  the repo root.
- **Sound**: the voice goes to -14 LUFS and the music sits `music_db` under it. The voice ducks the music gently
  (sidechain, about 3 dB), and the whole mix is brought to -14 LUFS. No voice (or `--no-voice`) means music only.
- **Safe zone**: captions stay in y 290-430 and x 96-926; the end card's text sits in y 500-1240. Windows may pass x 926.
- `draft: true` shows a DRAFT badge. Remove it for the final render (`--quality standard`).

## Rights rules (build.py enforces the files; you are responsible for what's in them)

- **Every image and clip** (including the backdrop source and the logo) needs `<file>.source.txt` next to it with:
  where it came from (URL or "supplied by <client contact>"), who owns it, the permission or licence, and the date.
  build.py and make_backdrop.py refuse a file without one.
- **Order of preference**: (1) our own or client-supplied media, with their OK in writing; (2) Creative Commons or
  similar open licences that allow commercial use, with the credit written in `.source.txt` (and in the post caption
  if the licence asks); (3) nothing else. Never take photos from websites, social media or Google Images without the
  owner's permission.
- **Never put one person's or brand's photo under another's name.** If a picture of a person, band or venue is not
  certainly them, don't use it.
- **Music** needs `<track stem>.licence.txt` next to it: the source and the licence that covers use in a client's
  social video. No licence, no build.
- **Voice**: ElevenLabs under your own account and its terms. Pick a voice from the library you are allowed to use
  commercially. Don't clone a real person's voice.
- **Facts**: every line of the script has a quote and URL in `script/<slug>.evidence.json`, and spoken names are checked
  against the person's or business's own spelling.

## Files

- `build.py`: props to `index.html`, `assets/clips/` and `assets/music/mix.wav` (all rebuilt each time, git-ignored)
- `page.tpl`: the page template (not `.html`, so lint sees one composition)
- `make_backdrop.py`: any image or video to a 1080x1920 moving loop
- `eleven_voice.mjs`: ElevenLabs narration, with your key and a voice ID you choose
- `spoken.py`: the text the voice reads, with respellings
- `time_voice.py`: offline whisper alignment that writes `timing` into the props
- `props/example-acme.json`, `examples/acme/` and `script/example-acme.evidence.json`: the fictional worked example
- `assets/fonts/`: Barlow Condensed and Inter (SIL OFL)
- `lib/vendor/gsap.min.js`: the animation library

See `LICENSE` (MIT) and `NOTICE` (third-party credits).
