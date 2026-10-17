"""Import new poems from the Google Sheet into site/data/poems.json.

The Sheet is published to the web as CSV (File > Share > Publish to web > CSV).
Its address is read from the SHEET_CSV_URL environment variable.

  python site/sheet_import.py               # fetch SHEET_CSV_URL
  python site/sheet_import.py --file x.csv  # read a local CSV instead (for testing)

Rules
- A poem already on the site (same words) is skipped, so re-running is safe.
- A poem whose opening and most of its text match an existing one is treated as a
  revision: it becomes the main version and the old text moves to "earlier versions".
- Anything else is added as a new poem.
Standard library only. Exits non-zero, without writing anything, on any error.
"""
import argparse
import csv
import datetime
import difflib
import io
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "poems.json")

ALLOWED_HOSTS = ("docs.google.com",)
ALLOWED_FINAL = ("docs.google.com", ".googleusercontent.com")
MAX_BYTES = 5_000_000
MAX_POEM_CHARS = 6000
MAX_LINES = 120
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# "[17/10/26, 7:14 am] Makarand Joshi: "  or  "17/10/26, 7:14 am - Makarand Joshi: "
PREFIX = re.compile(
    r"^\[?\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}(?::\d{2})?\s*(?:[ap]\.?\s?m\.?)?\]?\s*(?:-\s*)?[^:\n]{1,40}:\s*",
    re.I)
DROP = set(" \t।॥.,;:!?-–—'\"()*_~/")


# ---------- text ----------
def clean_line(line):
    s = line.replace("‎", "").replace("‏", "").replace(" ", " ").replace(" ", " ").strip()
    s = s.replace("24*7", "\x00")      # literal "24*7" is content, not bold markup
    s = s.replace("*", "")             # WhatsApp bold markers
    s = s.replace("\x00", "24*7")
    return re.sub(r"[ \t]{2,}", " ", s).strip()


def parse_poem(text):
    """Return (invocation, stanzas, signature) or None if there is no verse."""
    if not text or len(text) > MAX_POEM_CHARS:
        return None
    text = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    text = text.replace(" ", " ").replace(" ", " ")
    text = PREFIX.sub("", text.lstrip(), count=1)
    lines = [clean_line(l) for l in text.split("\n")]
    if len(lines) > MAX_LINES:
        return None
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    inv = lines.pop(0) if lines and "श्रीराम" in lines[0] and len(lines[0]) <= 60 else ""
    sig = lines.pop() if lines and "भावछंद" in lines[-1] else ""
    stanzas, cur = [], []
    for l in lines:
        if l:
            cur.append(l)
        elif cur:
            stanzas.append(cur)
            cur = []
    if cur:
        stanzas.append(cur)
    if not stanzas:
        return None
    return inv, stanzas, sig


def body(stanzas):
    return " ".join(l for st in stanzas for l in st)


def key(stanzas):
    return "".join(ch for ch in unicodedata.normalize("NFC", "".join(l for st in stanzas for l in st)) if ch not in DROP)


def opening(stanzas):
    return re.sub(r"[\s।॥.,;:!?'\"()*_~/-]+", "", stanzas[0][0])[:14]


# ---------- dates ----------
def parse_date(s, order="DMY"):
    """Google Form timestamps follow the Sheet's locale: 17/10/2026 (India) or 10/17/2026 (US)."""
    s = (s or "").strip()
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        y, mo, d = map(int, m.groups())
    else:
        m = re.match(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})", s)
        if not m:
            return None
        a, b, y = map(int, m.groups())
        if y < 100:
            y += 2000
        if a > 12:
            d, mo = a, b
        elif b > 12:
            mo, d = a, b
        elif order == "MDY":
            mo, d = a, b
        else:
            d, mo = a, b
    try:
        return datetime.date(y, mo, d).isoformat()
    except ValueError:
        return None


# ---------- sheet ----------
def check_url(url):
    u = urllib.parse.urlparse(url)
    if u.scheme != "https" or u.hostname not in ALLOWED_HOSTS or not u.path.startswith("/spreadsheets/"):
        raise ValueError("SHEET_CSV_URL must be a https://docs.google.com/spreadsheets/... address")
    return url


def fetch(url):
    check_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": "bhavchhand-site-import"})
    with urllib.request.urlopen(req, timeout=30) as r:
        final = urllib.parse.urlparse(r.geturl()).hostname or ""
        if not (final == ALLOWED_FINAL[0] or final.endswith(ALLOWED_FINAL[1])):
            raise ValueError("the Sheet address redirected somewhere unexpected")
        raw = r.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("the Sheet is larger than expected")
    text = raw.decode("utf-8-sig")
    if text.lstrip().startswith("<"):
        raise ValueError("got a web page, not CSV: is the Sheet published to the web as CSV?")
    return text


def rows_from_csv(text, order="DMY"):
    """Yield (iso_date or None, poem_text) for each non-empty row."""
    rows = [r for r in csv.reader(io.StringIO(text)) if any(c.strip() for c in r)]
    if not rows:
        return []
    head = [c.strip().lower() for c in rows[0]]
    date_col = next((i for i, h in enumerate(head) if any(w in h for w in ("timestamp", "date", "तारीख"))), None)
    poem_col = next((i for i, h in enumerate(head) if any(w in h for w in ("poem", "कविता", "text", "message"))), None)
    has_header = date_col is not None or poem_col is not None
    data = rows[1:] if has_header else rows
    if poem_col is None:  # fall back to the column holding the longest text
        width = max(len(r) for r in data) if data else 0
        poem_col = max(range(width), key=lambda i: sum(len(r[i]) for r in data if i < len(r)), default=0)
    out = []
    for r in data:
        poem = r[poem_col] if poem_col < len(r) else ""
        if not poem.strip():
            continue
        d = parse_date(r[date_col], order) if date_col is not None and date_col < len(r) else None
        out.append((d, poem))
    return out


# ---------- merge ----------
def merge(poems, rows, today):
    added = revised = skipped = 0
    known = set()
    for p in poems:
        known.add(key(p["s"]))
        for e in p["e"]:
            known.add(key(e["s"]))
    for d, text in sorted(rows, key=lambda r: r[0] or today):
        parsed = parse_poem(text)
        if not parsed:
            skipped += 1
            continue
        inv, stanzas, sig = parsed
        k = key(stanzas)
        if k in known:
            skipped += 1
            continue
        d = d or today
        op, txt = opening(stanzas), body(stanzas)
        best, best_r = None, 0.0
        for p in poems:
            if opening(p["s"]) == op:
                r = difflib.SequenceMatcher(None, body(p["s"]), txt, autojunk=False).ratio()
                if r > best_r:
                    best, best_r = p, r
        if best is not None and best_r >= 0.8:
            best["e"].append({"d": best["r"] or best["d"], "s": best["s"]})
            best["s"] = stanzas
            best["inv"] = inv or best["inv"]
            best["g"] = sig or best["g"]
            best["r"] = d if d != best["d"] else ""
            revised += 1
        else:
            poems.append({"n": max((p["n"] for p in poems), default=0) + 1, "d": d, "r": "",
                          "inv": inv, "s": stanzas, "g": sig, "e": []})
            added += 1
        known.add(k)
    return added, revised, skipped


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="read this local CSV instead of SHEET_CSV_URL")
    ap.add_argument("--data", default=DATA)
    args = ap.parse_args(argv)
    order = os.environ.get("SHEET_DATE_ORDER", "DMY").upper()
    try:
        if args.file:
            with open(args.file, encoding="utf-8-sig") as f:
                text = f.read(MAX_BYTES + 1)
        else:
            url = os.environ.get("SHEET_CSV_URL", "").strip()
            if not url:
                print("SHEET_CSV_URL is not set; nothing to import.")
                return 0
            text = fetch(url)
        rows = rows_from_csv(text, order)
        with open(args.data, encoding="utf-8") as f:
            poems = json.load(f)
        added, revised, skipped = merge(poems, rows, datetime.datetime.now(IST).date().isoformat())
    except (OSError, ValueError, csv.Error, json.JSONDecodeError) as e:
        print(f"import failed: {e}", file=sys.stderr)
        return 1
    print(f"sheet rows: {len(rows)}  added: {added}  revised: {revised}  already on site / empty: {skipped}")
    if added or revised:
        tmp = args.data + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(poems, f, ensure_ascii=False, indent=1)
        os.replace(tmp, args.data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
