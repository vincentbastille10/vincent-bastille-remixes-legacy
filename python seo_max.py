"""
Vincent Bastille — SEO MAX SCRIPT
✔ Remplacement des [[PLACEHOLDERS]]
✔ Enrichissement SEO automatique
✔ Idempotent (safe)
✔ Compatible sans dépendances
"""

import json
import re
import random
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

JSON_PATH = Path("bandcamp_full.json")
HTML_DIRS = [Path("SEO"), Path("seo-pages")]

SENTINEL = "<!-- SEO-ENRICHED-VB -->"
INSERT_BEFORE = "</body>"

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def slugify(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.strip("-")

def best_album(name, albums):
    name = name.lower()
    for a in albums:
        if slugify(a["title"]) in name:
            return a
    return random.choice(albums)

# ─────────────────────────────────────────────
# PLACEHOLDER REPLACEMENT
# ─────────────────────────────────────────────

def replace_vars(content, album):
    title = album.get("title", "Vincent Bastille Remix")
    slug  = slugify(title)
    tags  = album.get("tags", ["house", "remix"])
    tracks = album.get("tracks", [])

    def get(i, default):
        return tags[i] if len(tags) > i else default

    mapping = {
        "[[PAGE_TITLE]]": title,
        "[[SLUG]]": slug,
        "[[META_DESCRIPTION_150CHARS]]": f"{title} — Vincent Bastille remix. Deep house, cinematic electronic production.",
        "[[KEYWORD_1]]": get(0, "house remix"),
        "[[KEYWORD_2]]": get(1, "deep house"),
        "[[KEYWORD_3]]": get(2, "electronic remix"),
        "[[ALBUM_NAME]]": title,
        "[[ALBUM_BC_SLUG]]": slug,
        "[[BREADCRUMB_CAT]]": "Remixes",
        "[[CAT_SLUG]]": "remixes",
        "[[GENRE_TAG]]": get(0, "HOUSE").upper(),
        "[[YEAR_TAG]]": "2026",
        "[[TRACK_COUNT]]": str(len(tracks)),
        "[[HERO_SUBTITLE_ITALIC]]": "A cinematic house reinterpretation",
        "[[HERO_DESCRIPTION_2_3_SENTENCES]]": "A deep house remix crafted for club systems and immersive listening.",
        "[[FAQ_Q1]]": "What makes this remix unique?",
        "[[FAQ_A1]]": "It blends cinematic storytelling with club-ready structure.",
        "[[FAQ_Q2]]": "Is this track DJ friendly?",
        "[[FAQ_A2]]": "Yes, it is designed for seamless mixing.",
        "[[FAQ_Q_CUSTOM]]": "Who is Vincent Bastille?",
        "[[FAQ_A_CUSTOM]]": "A French electronic producer specializing in house remixes.",
    }

    for k, v in mapping.items():
        content = content.replace(k, v)

    return content

# ─────────────────────────────────────────────
# SEO BLOCK
# ─────────────────────────────────────────────

def seo_block(album, all_albums):
    title = album["title"]
    tags = album.get("tags", [])
    tracks = album.get("tracks", [])

    related = random.sample(all_albums, min(3, len(all_albums)))
    links = "\n".join(
        f'<li><a href="/seo-pages/{slugify(a["title"])}.html">{a["title"]}</a></li>'
        for a in related if a["title"] != title
    )

    track_html = ""
    if tracks:
        items = "\n".join(f"<li>{t}</li>" for t in tracks[:10])
        track_html = f"<ul>{items}</ul>"

    return f"""
{SENTINEL}
<section>
<h2>{title}</h2>
<p>This Vincent Bastille remix explores {", ".join(tags[:3])} with a cinematic house approach designed for both club systems and immersive listening.</p>
{track_html}
<ul>{links}</ul>
</section>
"""

# ─────────────────────────────────────────────
# PROCESS FILE
# ─────────────────────────────────────────────

def process_file(path, albums):
    content = path.read_text(encoding="utf-8", errors="ignore")

    album = best_album(path.stem, albums)

    # 1️⃣ replace placeholders
    content = replace_vars(content, album)

    # 2️⃣ add SEO block if not already
    if SENTINEL not in content:
        block = seo_block(album, albums)
        if INSERT_BEFORE in content:
            content = content.replace(INSERT_BEFORE, block + INSERT_BEFORE)
        else:
            content += block

    path.write_text(content, encoding="utf-8")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print("=== SEO MAX SCRIPT ===")

    if not JSON_PATH.exists():
        print("❌ JSON manquant")
        return

    albums = json.loads(JSON_PATH.read_text(encoding="utf-8"))

    files = []
    for d in HTML_DIRS:
        if d.exists():
            files += list(d.rglob("*.html"))

    print(f"{len(files)} fichiers trouvés")

    for f in files:
        process_file(f, albums)
        print(f"✔ {f}")

    print("DONE")

if __name__ == "__main__":
    main()
