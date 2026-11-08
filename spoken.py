"""The script as the voice should say it. Used by time_voice.py, and run directly to make the text for the voice:

  python3 spoken.py props/<slug>.json > script/<slug>.spoken.txt

props["spoken"] maps a script word to a respelling that only the voice sees ("Ngaio": "Nye-oh"). Captions
always use the script's own spelling. Matching ignores case and punctuation; the word's punctuation stays.
"""
import json, re, sys


def core(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())


def respell(word, table):
    """The spoken form of one script word, punctuation kept ("Ngaio," -> "Nye-oh,")."""
    t = {core(k): v for k, v in (table or {}).items()}
    m = re.match(r"^(\W*)(.*?)(\W*)$", word)
    pre, body, post = m.groups()
    sub = t.get(core(body))
    return pre + sub + post if sub else word


def spoken_per_word(props):
    """One spoken string per script word (it may be several words, e.g. "Acme" -> "Ack me")."""
    return [respell(w, props.get("spoken")) for w in props["script"].split()]


def spoken_text(props):
    return " ".join(spoken_per_word(props))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    print(spoken_text(json.load(open(sys.argv[1]))))
