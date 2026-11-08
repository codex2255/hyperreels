---
name: story-reel
description: Make a narrated "story of a business, venue or event" vertical Reel for a BSL client with this repo, from subject to rendered MP4. Use when asked to make, script, voice, build, render or review a story Reel, or to "do a story reel for <client>".
---

# Story Reel

You are helping a BSL staff member make one story Reel. Work through the steps in order and don't skip a gate. Stop
and ask the staff member whenever a step needs a person: the client's OK, choosing the voice, or media you can't
source with rights. `README.md` is the reference for props and commands.

Pick a slug for the Reel: the subject in lower case with dashes (e.g. `acme-coffee-roasters`). Files:
`props/<slug>.json`, `script/<slug>.evidence.json`, `library/<slug>/` (media, voice and backdrop; git-ignored).

## 1. Subject and the client's OK

- Agree the subject with the staff member: the business, venue or event and the one story worth telling (how it
  started, a turning point, what makes it different).
- The client must OK the subject before work starts. Record who, how and when in `client_ok` in
  `script/<slug>.evidence.json` (copy the shape of `script/example-acme.evidence.json`).
- Ask for the client's logo (PNG, transparent if possible) and any photos or clips they can supply now.

## 2. Research and fact-check

- Use the client's own site and socials, press coverage, and what the client tells you in writing.
- Every script line that states a fact gets at least one entry in `lines[].evidence`: a short **exact quote** and the
  **URL** (or "client email, <date>"). The hook question and CTA can have no evidence. A line with no evidence is cut
  or rewritten.
- **Names**: if a name came from a transcript, a voice note or auto-captions, check its spelling against the person's
  own written source (their site, LinkedIn or the client's email). Note it in `names_checked`. Transcripts often get
  names wrong.
- Don't guess dates, numbers or "firsts". If two sources disagree, use the client's written word or leave it out.

## 3. Script (60-100 words)

- **Hook question** (one line, makes people stay): "Who roasts the coffee in your morning flat white?"
- **Story**: in time order, short sentences, concrete details (years, numbers, places).
- **Payoff**: the reason the story matters now, or a question back to the viewer.
- **CTA**: one clear action: visit, book or order, and where.
- Read it aloud. 60-100 words is about 25-35 s. Keep sentences short, because captions break after every sentence end and comma.
- Respellings for hard names go in `spoken` (`{"Ngaio": "Nye-oh"}`). Only the voice hears them; captions keep the
  real spelling.
- Send the script to the client for approval before voicing it. Record the approval in the evidence file.

## 4. Voice

- The staff member chooses a voice **by ear** in the ElevenLabs Voice Library (in their own account), checks it's
  allowed for commercial use, and adds it to their voices. Don't choose for them, and never clone a real person.
  `npm run voices` lists the voice IDs in their account.
- Generate and time:

      python3 spoken.py props/<slug>.json > script/<slug>.spoken.txt
      npm run voice -- script/<slug>.spoken.txt library/<slug>/voice.mp3 <voiceId>
      python3 time_voice.py library/<slug>/voice.mp3 props/<slug>.json

- Set `"voice": {"engine": "elevenlabs", "voice_id": "<id>", "file": "library/<slug>/voice.mp3"}` in props, and give
  the voice file a `.source.txt` saying "ElevenLabs, voice <name> (<id>), <account owner>, <date>".
- Listen to it. If a word is mispronounced, add a respelling to `spoken`, then regenerate and re-time it. A new voice
  file always needs `time_voice.py` again.

## 5. Media with rights

- In order of preference: **(1)** own or client-supplied media, with the client's OK; **(2)** Creative Commons (or
  similar) that allows commercial use, with the credit; **(3)** nothing else. Never scrape media from websites,
  Instagram, Google Images or anywhere else without the owner's permission.
- Every image and clip in `library/<slug>/` gets `<file>.source.txt`: where it came from, owner, permission or
  licence (with the credit line for CC), and the date. build.py refuses files without one.
- **Never put one person's or brand's photo under another's name.** If you aren't sure a photo shows the right person,
  band or place, don't use it.
- About 12-25 images is plenty, plus short clips if you have them (they play in windows). Pick a wide, bright,
  rights-cleared image or clip for the backdrop.
- Music: a track the staff member is licensed to use in a client's social video, with `<stem>.licence.txt` next to it.

## 6. Build

1. Backdrop: `python3 make_backdrop.py library/<slug>/<source> library/<slug>/backdrop.mp4` (add `--gamma 0.7
   --saturation 1.3` to lift a dull source). It must be bright and moving, but not so busy that the windows are lost.
2. Props: copy `props/example-acme.json` to `props/<slug>.json`. Set `subject`, `media_dir`, `script`, `voice`,
   `backdrop`, `colors` (from the client's brand: `bg` dark, `text` light, `highlight` a bright brand colour that reads
   on the backdrop), `font`, `topics` (one per 2-4 s of narration, starting at word 0), `end` (logo, a short CTA line,
   the client's name or handle as `sub`), `music`, and keep `draft: true`.
3. Run:

       python3 build.py props/<slug>.json
       npx hyperframes lint
       npx hyperframes check
       npx hyperframes render --fps 30 --quality draft -o renders/<slug>_DRAFT.mp4

   Fix every build warning (topic holds outside 1.5-4.5 s) and every lint or check error before rendering.
4. For the final, set `draft: false` and render with `--quality standard -o renders/<slug>.mp4`.

## 7. Self-review before handing over

Make a contact sheet and look at it yourself:

    ffmpeg -v error -y -i renders/<slug>_DRAFT.mp4 -vf "select='isnan(prev_selected_t)+gte(t-prev_selected_t\,2.5)',scale=270:480,tile=6x2" -frames:v 1 renders/<slug>_sheet.jpg

Check, and fix before anyone else sees it:

- Every caption is spelled as in the script, with no word cut off or overlapping the windows.
- Each topic's pictures match what is being said at that moment, and no photo is of the wrong person or place.
- Nothing important in a picture is cropped off (adjust `pos`).
- The end card's logo is sharp and the CTA is correct.
- Watch it once with sound: the highlight follows the voice, the music sits under the voice, and nothing clips.
- Loudness is about -14 LUFS: `ffmpeg -i renders/<slug>.mp4 -af ebur128 -f null - 2>&1 | grep "I:"`.

Hand over the MP4 with the evidence file and the list of media sources (the `.source.txt` notes) for the client's
approval. Don't post anything without the client's approval of that exact video.
