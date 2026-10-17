"""Build index.html from site/data/poems.json.

Standard library only. Run from anywhere:  python site/build.py
"""
import base64
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from themes import tags, THEMES  # noqa: E402

MRD = {"nam": "रामनामाचा जप आणि स्मरण", "sam": "शांती आणि समाधान", "guru": "सद्गुरू आणि संत",
       "man": "चंचल मन", "jiv": "रोजचे जगणे", "swar": "स्वर आणि संगीत", "nis": "निसर्ग आणि छोट्या गोष्टी"}
ORDER = ["nam", "sam", "guru", "man", "jiv", "swar", "nis", "hin", "eng"]


def read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read()


def js_json(o):
    # Safe inside <script type="application/json">: no "<" can close the tag.
    return json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def build():
    with open(os.path.join(HERE, "data", "poems.json"), encoding="utf-8") as f:
        poems = json.load(f)
    with open(os.path.join(ROOT, "makarand.png"), "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    data = []
    for p in poems:
        text = " ".join(line for st in p["s"] for line in st)
        data.append(dict(p, t=tags(text)))

    meta = [{"k": k, "mr": mr, "en": en, "mrd": MRD[k]} for k, mr, en, _, _ in THEMES]
    meta += [{"k": "hin", "mr": "हिंदी", "en": "Hindi verses", "mrd": "हिंदीतील रचना"},
             {"k": "eng", "mr": "इंग्रजी शब्द", "en": "Marathi with English words", "mrd": "मराठी-इंग्रजी मिश्र रचना"}]
    meta.sort(key=lambda t: ORDER.index(t["k"]))

    n = len(data)
    years = sorted({p["d"][:4] for p in data})
    css, js = read("style.css"), read("app.js")

    body = f"""<div class="topline wide">
  <div class="seg lang" role="group" aria-label="भाषा / Language">
    <button type="button" data-l="mr" aria-pressed="true"><span class="deva">मराठी</span></button>
    <button type="button" data-l="mx" aria-pressed="false"><span class="deva">मराठी</span> + English</button>
  </div>
</div>
<header class="hero wide">
  <canvas id="motes" aria-hidden="true"></canvas>
  <div class="id">
    <div class="halo"><img class="portrait" src="data:image/png;base64,{b64}" alt="मकरंद जोशी" width="132" height="132"></div>
    <div>
      <p class="inv-top">श्रीराम जयराम जयजयराम</p>
      <h1>भावछंद</h1>
      <p class="by"><span data-t="name">मकरंद जोशी</span> <span class="pen">· घेई छंद मकरंद</span></p>
    </div>
  </div>
  <figure class="feature">
    <p class="lbl" id="featLbl">आजचे कडवे</p>
    <blockquote id="feat"></blockquote>
    <div class="acts">
      <button class="pill solid" id="readit" type="button" data-t="read">संपूर्ण कविता वाचा</button>
      <button class="pill" id="another" type="button" data-t="another">दुसरे कडवे</button>
    </div>
  </figure>
</header>

<main class="explore wide" id="explore">
  <div class="tools">
    <div class="seg view" role="group" data-ta="browse" aria-label="कविता कशा पाहायच्या">
      <button type="button" data-v="topic" aria-pressed="true" data-t="byTopic">विषयानुसार</button>
      <button type="button" data-v="date" aria-pressed="false" data-t="byDate">तारखेनुसार</button>
    </div>
    <input class="search" id="q" type="search" placeholder="शब्द किंवा ओळ शोधा" data-tp="search" data-ta="searchLbl" aria-label="कविता शोधा" autocomplete="off">
    <span class="count" id="count"></span>
  </div>
  <div class="topics" id="topics"></div>
  <div class="rhythm" id="rhythm" hidden></div>
  <div class="split">
    <div class="list" id="list" data-ta="list" aria-label="कवितांची यादी"></div>
    <article class="reader" id="reader" aria-live="polite"></article>
  </div>
  <noscript><p>कविता पाहण्यासाठी JavaScript सुरू करा.</p></noscript>
</main>

<footer class="wide">
  <p class="deva">भावछंद · घेई छंद मकरंद</p>
</footer>
<script type="application/json" id="themes">{js_json(meta)}</script>
<script type="application/json" id="data">{js_json(data)}</script>
<script>
{js}</script>
"""
    page = ("<!doctype html>\n<html lang=\"mr\">\n<head>\n<meta charset=\"utf-8\">\n"
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            "<title>भावछंद · घेई छंद मकरंद</title>\n"
            f'<meta name="description" content="भावछंद, poems by Makarand Joshi (घेई छंद मकरंद). {n} poems, {years[0]}–{years[-1]}.">\n'
            '<meta name="color-scheme" content="light dark">\n'
            "<style>\n" + css + "</style>\n</head>\n<body>\n" + body + "</body>\n</html>\n")
    out = os.path.join(ROOT, "index.html")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print(f"built index.html: {n} poems")


if __name__ == "__main__":
    build()
