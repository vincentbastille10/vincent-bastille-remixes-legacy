"""
Vincent Bastille — MAX SEO enrichment
Safe to run multiple times.
Uses bandcamp_full.json as the only source of truth.
Enriches HTML pages in /SEO and /seo-pages.
"""

import json
import re
import html
import random
from pathlib import Path
from difflib import SequenceMatcher

try:
    from rapidfuzz import fuzz, process as rfprocess
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False


JSON_PATH = Path("bandcamp_full.json")
HTML_DIRS = [Path("SEO"), Path("seo-pages")]
SENTINEL = "<!-- SEO-ENRICHED-VB-MAX -->"
INSERT_BEFORE = "</body>"

MIN_MATCH_SCORE = 42
RELATED_LINKS_COUNT = 5

GENERIC_TAGS = {
    "electronic",
    "remix",
    "remixes",
    "house",
    "techno",
    "ambiant",
    "ambient",
    "le mans",
}


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def slugify(text: str) -> str:
    return normalize(text).replace(" ", "-")


def clean_tags(tags):
    seen = set()
    result = []
    for tag in tags or []:
        t = str(tag).strip()
        key = t.lower()
        if t and key not in seen:
            seen.add(key)
            result.append(t)
    return result


def strong_tags(tags):
    tags = clean_tags(tags)
    selected = [t for t in tags if t.lower() not in GENERIC_TAGS]
    return selected[:6] if selected else tags[:6]


def extract_artists(title: str):
    title = title.strip()

    if " - " in title:
        left = title.split(" - ", 1)[0].strip()
    else:
        left = title

    left = re.sub(r"\(.*?\)", "", left).strip()
    left = left.replace("Vincent Bastille remix", "").strip()
    left = left.replace("Vincent Bastille Remix", "").strip()

    if not left or left.lower().startswith("vincent bastille"):
        return ["Vincent Bastille"]

    parts = re.split(r",|/| feat\. | ft\. | and | & ", left, flags=re.I)
    artists = [p.strip() for p in parts if p.strip()]

    if "Vincent Bastille" not in artists:
        artists.append("Vincent Bastille")

    return artists[:8]


def page_title_from_path(path: Path):
    return path.stem.replace("-", " ").replace("_", " ").title()


def album_key(album):
    text = " ".join([
        album.get("title", ""),
        " ".join(album.get("tags", [])),
        " ".join(album.get("tracks", [])[:4]),
    ])
    return normalize(text)


def best_album_for_file(path: Path, albums):
    needle = normalize(path.stem)
    keys = [album_key(a) for a in albums]

    if HAS_RAPIDFUZZ:
        match = rfprocess.extractOne(needle, keys, scorer=fuzz.token_set_ratio)
        if match and match[1] >= MIN_MATCH_SCORE:
            return albums[match[2]], match[1]

    best_i = 0
    best_score = 0
    for i, key in enumerate(keys):
        score = SequenceMatcher(None, needle, key).ratio() * 100
        words_a = set(needle.split())
        words_b = set(key.split())
        if words_a and words_b:
            jaccard = len(words_a & words_b) / len(words_a | words_b) * 100
            score = max(score, jaccard)
        if score > best_score:
            best_score = score
            best_i = i

    if best_score >= MIN_MATCH_SCORE:
        return albums[best_i], round(best_score, 1)

    return None, round(best_score, 1)


def collect_html_files():
    files = []
    for folder in HTML_DIRS:
        if folder.exists():
            files.extend(sorted(folder.rglob("*.html")))
    return files


def build_page_index(files):
    index = []
    for path in files:
        rel = "/" + str(path).replace("\\", "/")
        label = page_title_from_path(path)
        index.append({"path": rel, "label": label, "stem": path.stem})
    return index


def related_links(current_path, page_index, album):
    current = "/" + str(current_path).replace("\\", "/")
    tags = set(normalize(" ".join(album.get("tags", []))).split())

    scored = []
    for item in page_index:
        if item["path"] == current:
            continue
        stem_words = set(normalize(item["stem"]).split())
        score = len(tags & stem_words)
        scored.append((score, item))

    scored.sort(key=lambda x: (-x[0], x[1]["label"]))

    chosen = [item for _, item in scored[:RELATED_LINKS_COUNT]]
    if len(chosen) < RELATED_LINKS_COUNT:
        pool = [i for i in page_index if i["path"] != current and i not in chosen]
        chosen.extend(pool[: RELATED_LINKS_COUNT - len(chosen)])

    items = "\n".join(
        f'      <li><a href="{html.escape(i["path"])}">{html.escape(i["label"])}</a></li>'
        for i in chosen
    )

    return f"""
    <section class="vb-related-remixes">
      <h2>Related remixes</h2>
      <ul>
{items}
      </ul>
    </section>
"""


def schema_json(album, path):
    title = album.get("title", "")
    tags = clean_tags(album.get("tags", []))
    tracks = album.get("tracks", [])

    data = {
        "@context": "https://schema.org",
        "@type": "MusicAlbum",
        "name": title,
        "byArtist": {
            "@type": "MusicGroup",
            "name": "Vincent Bastille"
        },
        "genre": tags,
        "url": "https://remixes.vincentbastille.online/" + str(path).replace("\\", "/"),
        "track": [
            {
                "@type": "MusicRecording",
                "name": track
            }
            for track in tracks
        ]
    }

    return json.dumps(data, ensure_ascii=False, indent=2)


def build_description(album):
    title = album.get("title", "").strip()
    tags = clean_tags(album.get("tags", []))
    tracks = album.get("tracks", [])
    artists = extract_artists(title)
    main_artist = artists[0] if artists else "the original artist"

    tag_focus = strong_tags(tags)
    genre_sentence = ", ".join(tag_focus[:5]) if tag_focus else "house and electronic music"

    track_examples = ", ".join(tracks[:4]) if tracks else title

    return f"""
      <p>
        <strong>{html.escape(title)}</strong> is presented here as part of Vincent Bastille’s extended remix universe,
        built around {html.escape(genre_sentence)} and a strong sense of electronic arrangement.
        Rather than treating the material as a simple edit, this page frames the release as a complete
        <strong>Vincent Bastille remix</strong>: a piece designed for listening, discovery, DJ selection and long-term archive value.
      </p>

      <p>
        The musical identity comes from the contrast between familiar song references and a more personal production language:
        rhythmic pressure, atmospheric detail, club structure, and a cinematic sense of progression.
        For listeners searching for a <strong>house remix</strong>, an <strong>electronic remix</strong>, or a more underground
        reinterpretation of pop, soul, disco or cinematic material, this release gives clear context around the sound,
        the tags, and the tracks connected to it.
      </p>

      <p>
        The release connects Vincent Bastille with {html.escape(main_artist)} and related material such as
        {html.escape(track_examples)}. Its tags — {html.escape(", ".join(tags[:10]))} — help describe the musical zone:
        dancefloor energy, remix culture, electronic production, and the French independent music scene around Le Mans.
        This added context is meant to make the page useful both for human listeners and for search engines trying to understand
        what the music is, who it relates to, and why it belongs in a remix catalogue.
      </p>
"""


def build_seo_block(album, path, page_index, score):
    title = album.get("title", "").strip()
    tags = clean_tags(album.get("tags", []))
    tracks = album.get("tracks", [])
    artists = extract_artists(title)

    genre_text = ", ".join(tags) if tags else "house, electronic remix"
    artist_text = ", ".join(artists)

    track_items = "\n".join(
        f"        <li>{html.escape(track)}</li>" for track in tracks
    ) or "        <li>Vincent Bastille remix</li>"

    tag_items = "\n".join(
        f"        <li>{html.escape(tag)}</li>" for tag in tags
    )

    return f"""
{SENTINEL}
<section class="vb-seo-block" aria-label="Detailed remix information">
  <style>
    .vb-seo-block {{
      max-width: 980px;
      margin: 80px auto;
      padding: 40px;
      border: 1px solid rgba(255,255,255,.14);
      border-radius: 24px;
      background: rgba(255,255,255,.035);
      color: inherit;
    }}
    .vb-seo-block h2 {{
      margin-top: 32px;
      margin-bottom: 14px;
      font-size: clamp(28px, 4vw, 48px);
      line-height: 1.05;
    }}
    .vb-seo-block p {{
      margin: 0 0 18px;
      line-height: 1.8;
      opacity: .92;
    }}
    .vb-seo-block ul {{
      margin: 0;
      padding-left: 22px;
      line-height: 1.8;
    }}
    .vb-seo-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 22px;
      margin-top: 24px;
    }}
    .vb-seo-card {{
      padding: 22px;
      border: 1px solid rgba(255,255,255,.12);
      border-radius: 18px;
      background: rgba(0,0,0,.16);
    }}
    .vb-related-remixes a {{
      color: inherit;
      text-decoration: underline;
      text-underline-offset: 4px;
    }}
    .vb-seo-small {{
      font-size: 13px;
      opacity: .55;
      margin-top: 28px;
    }}
  </style>

  <h2>About this remix</h2>
{build_description(album)}

  <div class="vb-seo-grid">
    <div class="vb-seo-card">
      <h2>Genres</h2>
      <p>{html.escape(genre_text)}</p>
      <ul>
{tag_items}
      </ul>
    </div>

    <div class="vb-seo-card">
      <h2>Artists</h2>
      <p>{html.escape(artist_text)}</p>
      <p>Vincent Bastille appears here as producer, remixer and curator of this electronic remix catalogue.</p>
    </div>
  </div>

  <h2>Tracklist</h2>
  <ul>
{track_items}
  </ul>

{related_links(path, page_index, album)}

  <script type="application/ld+json">
{schema_json(album, path)}
  </script>

  <p class="vb-seo-small">SEO match confidence: {score}% — generated from Bandcamp archive data.</p>
</section>
"""


def enrich_file(path, albums, page_index):
    content = path.read_text(encoding="utf-8", errors="replace")

    if SENTINEL in content:
        return "skipped", None, None

    album, score = best_album_for_file(path, albums)
    if not album:
        return "no_match", None, score

    block = build_seo_block(album, path, page_index, score)

    if INSERT_BEFORE in content:
        content = content.replace(INSERT_BEFORE, block + "\n" + INSERT_BEFORE, 1)
    elif INSERT_BEFORE.upper() in content:
        content = content.replace(INSERT_BEFORE.upper(), block + "\n" + INSERT_BEFORE.upper(), 1)
    else:
        content += "\n" + block

    path.write_text(content, encoding="utf-8")
    return "enriched", album.get("title"), score


def main():
    if not JSON_PATH.exists():
        raise FileNotFoundError("bandcamp_full.json not found at repo root")

    albums = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    html_files = collect_html_files()
    page_index = build_page_index(html_files)

    random.seed(42)

    stats = {
        "scanned": len(html_files),
        "enriched": 0,
        "skipped": 0,
        "no_match": 0,
        "errors": 0,
    }

    print("Vincent Bastille — MAX SEO enrichment")
    print(f"Albums loaded: {len(albums)}")
    print(f"HTML files found: {len(html_files)}")

    for path in html_files:
        try:
            status, title, score = enrich_file(path, albums, page_index)
            stats[status] += 1

            if status == "enriched":
                print(f"[OK] {path} → {title} ({score}%)")
            elif status == "skipped":
                print(f"[SKIP] {path}")
            elif status == "no_match":
                print(f"[NO MATCH] {path} ({score}%)")

        except Exception as e:
            stats["errors"] += 1
            print(f"[ERROR] {path}: {e}")

    print("\nSUMMARY")
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
