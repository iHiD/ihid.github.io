#!/usr/bin/env python3
"""Split mockups/f-quiet.html into one page per section of the live site.

f-quiet.html stays the single source for the copy and the styling. Each
<section class="panel" id="..."> becomes its own page with a real URL, and the
sidebar marks the current page. The pages are written to the repo root, where
GitHub Pages serves them. Run this after every edit to f-quiet.html:

    python3 mockups/build-quiet.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "f-quiet.html")
SITE = "https://ihid.info/"
OUT = os.path.dirname(HERE)

# Section id -> path below the site root ("" is the home page).
PAGES = {
    "about": "",
    "ai": "ai/",
    "ventures": "ventures/",
    "exercism": "ventures/exercism/",
    "jiki": "ventures/jiki/",
    "kaido": "ventures/kaido/",
    "meducation": "ventures/meducation/",
    "oss": "open-source/",
    "speaking": "speaking/",
    "personal": "personal/",
}
VENTURES = {"exercism", "jiki", "kaido", "meducation"}

src = open(SOURCE, encoding="utf-8").read()

head, rest = src.split("<main>", 1)
main, tail = rest.split("</main>", 1)
tail = re.sub(r'<script id="panels">.*?</script>\s*', "", tail, flags=re.S)
head = head.replace('  <script>document.documentElement.className = "js";</script>\n', "")
head = re.sub(r"    \.js \.panel[^\n]*\n", "", head)

sections = dict(
    (m.group(2), m.group(0))
    for m in re.finditer(r'<section class="panel([^"]*)" id="([^"]+)"[^>]*>.*?</section>', main, re.S)
)
missing = set(PAGES) - set(sections)
if missing:
    raise SystemExit("Sections missing from f-quiet.html: " + ", ".join(sorted(missing)))

title_re = re.compile(r"<title>(.*?)</title>")
site_title = title_re.search(head).group(1)


def page_title(sid, html):
    if sid == "about":
        return site_title
    h2 = re.search(r"<h2>(.*?)</h2>", html).group(1)
    return f"{h2} · {site_title}"


for sid, path in PAGES.items():
    depth = path.count("/")
    root = "../" * depth or "./"
    up = "../" * depth  # from this page back to the repo root

    def link(m):
        target = m.group(1)
        return f'href="{root}{PAGES[target]}"' if target in PAGES else m.group(0)

    html = head + "<main>\n    " + sections[sid].strip() + "\n  </main>" + tail
    title = page_title(sid, sections[sid])
    desc = re.search(r'data-description="([^"]*)"', sections[sid]).group(1)
    html = title_re.sub(f"<title>{title}</title>", html, count=1)
    html = re.sub(r'(<meta (?:name="description"|property="og:description") content=")[^"]*"', lambda m: m.group(1) + desc + '"', html)
    html = re.sub(r'(<meta property="og:title" content=")[^"]*"', lambda m: m.group(1) + title + '"', html)
    html = re.sub(r'(<link rel="canonical" href="|<meta property="og:url" content=")[^"]*"', lambda m: m.group(1) + SITE + path + '"', html)
    html = re.sub(r' data-description="[^"]*"', "", html)
    html = re.sub(r'(src|href)="\.\./', lambda m: f'{m.group(1)}="{up}', html)
    html = re.sub(r'href="#([a-z]+)"', link, html)
    html = html.replace(f'class="panel', 'class="panel on', 1)

    # Mark the current page, and Ventures as the parent of each venture page.
    here = f'href="{root}{path}"'
    html = html.replace(f"<a {here}>", f'<a {here} class="on" aria-current="page">', 1)
    if sid in VENTURES:
        vhref = f'href="{root}{PAGES["ventures"]}"'
        html = html.replace(f"<a {vhref}>", f'<a {vhref} class="parent">', 1)

    dest = os.path.join(OUT, path, "index.html")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w", encoding="utf-8").write(html)
    print("wrote", os.path.relpath(dest, os.path.dirname(HERE)))
