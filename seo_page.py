import os
import json
import html
import logging
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("seo_generator.log", encoding="utf-8"),
    ],
)

log = logging.getLogger(__name__)


# =============================================================================
# CONFIG
# =============================================================================

BASE_URL = "https://remixes.vincentbastille.online"

ROOT_DIR = Path(".")
OUTPUT_DIR = Path("seo-pages")
SEO_DIRS = [Path("SEO"), Path("seo-pages")]

JSON_PATH = Path("bandcamp_full.json")
SITEMAP_PATH = Path("sitemap.xml")
STATE_PATH = Path(".seo_state.json")

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "").strip()

PRIMARY_CHAT_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct-Turbo"
FALLBACK_CHAT_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct-Turbo"

CHAT_URL = "https://api.together.xyz/v1/chat/completions"

REQUEST_TIMEOUT = 40
RETRIES = 2
RETRY_DELAY = 4

# Important :
# 40 pages par run = raisonnable pour GitHub Actions + API.
# Si tu veux plus, tu peux mettre un secret/variable GitHub MAX_PAGES_PER_RUN=100.
MAX_PAGES_PER_RUN = int(os.getenv("MAX_PAGES_PER_RUN", "40"))

BATCH_PAUSE = 0.4

MIN_WORDS = 450

RANDOM_SEED = 42
random.seed(RANDOM_SEED)


# =============================================================================
# KEYWORDS
# =============================================================================

KEYWORD_SEEDS = [
    "best house remixes 2026",
    "deep house remix 124 bpm",
    "madonna house remix",
    "sade remix electronic",
    "afterparty house remix",
    "night drive electronic remix",
    "french house remix",
    "ibiza sunset house remix",
    "disco house remix classics",
    "underground house edit 2026",
    "late night electronic remix",
    "dancefloor house remix 128 bpm",
    "vocal house remix 2026",
    "lo-fi house edit",
    "summer house remix playlist",
    "chill electronic remix session",
    "organic house remix 2026",
    "afro house remix edit",
    "melodic house remix 2026",
    "progressive house remix 2026",
]

SUFFIX_POOL = [
    "guide",
    "selection",
    "listening notes",
    "producer analysis",
    "club perspective",
    "archive entry",
    "deep dive",
    "session",
    "mix culture",
    "sound design notes",
]

ANGLE_POOL = [
    "club DJ usage and how the track could work in a set",
    "emotional listening experience and late-night replay value",
    "production techniques, sound design, rhythm and arrangement",
    "remix history, French touch influence and electronic culture",
    "modern streaming behavior and why listeners search for remixes",
    "the link between cinematic music, house music and personal storytelling",
    "how classic artists can be reframed through modern electronic production",
    "why house remixes remain useful for DJs, collectors and close listeners",
]

MOOD_POOL = [
    "cinematic",
    "late-night",
    "deep",
    "club-ready",
    "emotional",
    "textural",
    "hypnotic",
    "French electronic",
    "warm",
    "underground",
]


# =============================================================================
# FALLBACK CONTENT
# =============================================================================

FALLBACK_PARAGRAPHS = [
    (
        "House music has always been a space where originals are reborn. "
        "A well-crafted remix does not simply extend the life of a track; it opens a second conversation with the listener, "
        "one built on familiarity and surprise in equal measure."
    ),
    (
        "In electronic production, the remix is both a technical exercise and a creative statement. "
        "The producer has to understand where the tension lives, where the release arrives, and how to reshape both without removing the soul of the original idea."
    ),
    (
        "A house remix around 124 BPM depends on balance. The kick must anchor the body, the percussion must breathe, "
        "and the harmonic material has to remain clear enough to carry emotion through a club system or a pair of headphones."
    ),
    (
        "French electronic music has a recognizable relationship with texture and repetition. "
        "From filtered disco to deeper underground forms, the best productions often use restraint rather than excess to create momentum."
    ),
    (
        "Listening to a remix late at night reveals decisions that can disappear on first contact: the tail of a reverb, a small filter movement, "
        "a bass note that arrives half a second later than expected. Those details separate craft from simple edit culture."
    ),
    (
        "A strong remix becomes useful because it offers more than novelty. It gives DJs a bridge, gives listeners a new emotional angle, "
        "and gives the original song another possible life."
    ),
    (
        "Vincent Bastille's catalogue sits in that zone between archive, club tool and personal production diary. "
        "The music points toward house, electronic remix culture, cinematic atmosphere and independent release energy."
    ),
]


# =============================================================================
# BASIC HELPERS
# =============================================================================

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(r"[^\w\s-]", " ", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:120]


def safe_text(value: Any) -> str:
    return html.escape(str(value or "").strip())


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"generated": []}

    try:
        data = load_json(STATE_PATH)
        if "generated" not in data or not isinstance(data["generated"], list):
            return {"generated": []}
        return data
    except Exception:
        return {"generated": []}


def save_state(state: dict) -> None:
    write_json(STATE_PATH, state)


def clean_tags(tags: list[str]) -> list[str]:
    seen = set()
    cleaned = []

    for tag in tags or []:
        t = str(tag).strip()
        key = t.lower()

        if not t:
            continue

        if key in seen:
            continue

        seen.add(key)
        cleaned.append(t)

    return cleaned


def extract_artist_from_title(title: str) -> str:
    title = title.strip()

    if " - " in title:
        artist = title.split(" - ", 1)[0].strip()
    else:
        artist = title

    artist = re.sub(r"\(.*?\)", "", artist).strip()

    if not artist:
        return "Vincent Bastille"

    return artist


def make_keyword(seed: str, n: int) -> str:
    suffix = random.choice(SUFFIX_POOL)
    mood = random.choice(MOOD_POOL)

    if n == 1:
        return f"{seed} {suffix}"

    return f"{seed} {mood} {suffix} {n}"


def build_keyword_plan() -> list[str]:
    keywords = []

    for n in range(1, 50):
        for seed in KEYWORD_SEEDS:
            kw = make_keyword(seed, n)
            keywords.append(kw)

    deduped = []
    seen = set()

    for kw in keywords:
        slug = slugify(kw)
        if slug in seen:
            continue
        seen.add(slug)
        deduped.append(kw)

    return deduped


def existing_page_is_valid(path: Path) -> bool:
    if not path.exists():
        return False

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False

    if "LLM ERROR" in content:
        return False

    if "is part of modern house remix culture" in content:
        return False

    if word_count(content) < 350:
        return False

    return True


# =============================================================================
# ALBUM CONTEXT
# =============================================================================

def pick_album_context(albums: list[dict], count: int = 6) -> list[dict]:
    if not albums:
        return []

    return random.sample(albums, min(count, len(albums)))


def album_context_text(albums: list[dict]) -> str:
    lines = []

    for album in albums[:6]:
        title = album.get("title", "Unknown release")
        tags = ", ".join(clean_tags(album.get("tags", []))[:8])
        tracks = ", ".join(album.get("tracks", [])[:5])
        url = album.get("url", "")

        lines.append(
            f"- Title: {title}\n"
            f"  Tags: {tags}\n"
            f"  Tracks: {tracks}\n"
            f"  URL: {url}"
        )

    return "\n".join(lines)


def build_album_links(albums: list[dict], max_links: int = 5) -> str:
    if not albums:
        return ""

    picks = random.sample(albums, min(max_links, len(albums)))

    items = []
    for album in picks:
        title = safe_text(album.get("title", "Vincent Bastille release"))
        url = safe_text(album.get("url", "https://vincentbastille.bandcamp.com"))
        items.append(f'<li><a href="{url}" rel="noopener" target="_blank">{title}</a></li>')

    return "\n        ".join(items)


# =============================================================================
# TOGETHER API
# =============================================================================

def headers() -> dict:
    return {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json",
    }


def parse_chat_response(data: dict) -> str:
    try:
        choice = data["choices"][0]

        if "message" in choice and "content" in choice["message"]:
            return str(choice["message"]["content"]).strip()

        if "text" in choice:
            return str(choice["text"]).strip()

    except Exception:
        return ""

    return ""




def build_prompt(keyword: str, album_context: list[dict]) -> str:
    angle = random.choice(ANGLE_POOL)
    albums_txt = album_context_text(album_context)

    return (
        f"Write a unique long-form SEO article in natural English.\n\n"
        f"Topic:\n{keyword}\n\n"
        f"Angle:\n{angle}\n\n"
        f"Context:\n"
        f"This page is for remixes.vincentbastille.online, a site about Vincent Bastille's electronic music, "
        f"house remixes, remix culture, Bandcamp catalogue, club listening, and cinematic production.\n\n"
        f"Real album data to use as source material:\n{albums_txt}\n\n"
        f"Strict requirements:\n"
        f"- 550 to 750 words.\n"
        f"- Plain paragraphs only.\n"
        f"- No bullet points.\n"
        f"- No markdown.\n"
        f"- No fake facts.\n"
        f"- Do not claim official collaborations.\n"
        f"- Mention Vincent Bastille naturally.\n"
        f"- Mention house remix, electronic remix, Bandcamp, listening context, production craft.\n"
        f"- Every paragraph must bring a new idea.\n"
        f"- Avoid generic filler.\n"
        f"- Do not repeat the same sentence structure.\n"
        f"- Write like a real music writer, not like a robot."
    )


def fallback_content(keyword: str, album_context: list[dict]) -> str:
    paragraphs = list(FALLBACK_PARAGRAPHS)
    random.shuffle(paragraphs)

    album_titles = ", ".join(
        album.get("title", "Vincent Bastille release")
        for album in album_context[:4]
    )

    intro = (
        f"{keyword} connects directly with the way Vincent Bastille treats remix culture: "
        f"not as a shortcut, but as a way to rebuild atmosphere, rhythm and emotional movement. "
        f"The surrounding catalogue includes releases such as {album_titles}, giving the subject "
        f"a real musical context rather than a generic search phrase."
    )

    return intro + "\n\n" + "\n\n".join(paragraphs[:6])


def llm_generate(keyword: str, album_context: list[dict]) -> str:
    print("🔥 VERSION V2 ACTIVE 🔥")
    if not TOGETHER_API_KEY:
        log.error("Missing API key")
        return fallback_content(keyword, album_context)

    prompt = build_prompt(keyword, album_context)

    payload = {
        "model": PRIMARY_CHAT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a professional music writer. Write natural English. No bullet points. No markdown."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 800,
        "temperature": 0.7
    }

    try:
        response = requests.post(
            CHAT_URL,
            headers=headers(),
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

        log.info(f"STATUS: {response.status_code}")
        log.info(f"BODY: {response.text[:300]}")

        response.raise_for_status()

        data = response.json()

        # ✅ parsing correct
        text = data["choices"][0]["message"]["content"]

        if not text or word_count(text) < 100:
            return fallback_content(keyword, album_context)

        return text.strip()

    except Exception as e:
        log.error(f"LLM ERROR: {e}")
        return fallback_content(keyword, album_context)


def paragraphize(text: str) -> list[str]:
    text = text.replace("\r\n", "\n")
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    if len(parts) <= 1:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        chunks = []
        buf = []

        for sentence in sentences:
            buf.append(sentence)
            if len(" ".join(buf).split()) >= 90:
                chunks.append(" ".join(buf))
                buf = []

        if buf:
            chunks.append(" ".join(buf))

        parts = chunks

    cleaned = []
    for part in parts:
        part = re.sub(r"^#+\s*", "", part.strip())
        if part:
            cleaned.append(part)

    return cleaned
def build_internal_links(current_slug: str, all_slugs: list[str], max_links: int = 8) -> str:
    candidates = [s for s in all_slugs if s != current_slug]

    if not candidates:
        return ""

    picks = random.sample(candidates, min(max_links, len(candidates)))

    items = []
    for slug in picks:
        label = slug.replace("-", " ").capitalize()
        items.append(f'<li><a href="/seo-pages/{safe_text(slug)}.html">{safe_text(label)}</a></li>')

    return "\n        ".join(items)


def schema_article(title: str, description: str, slug: str, date_str: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "url": f"{BASE_URL}/seo-pages/{slug}.html",
        "datePublished": date_str,
        "dateModified": date_str,
        "author": {
            "@type": "Person",
            "name": "Vincent Bastille",
        },
        "publisher": {
            "@type": "Organization",
            "name": "Vincent Bastille Remixes",
        },
        "about": [
            "house remix",
            "electronic remix",
            "Vincent Bastille",
            "remix culture",
            "Bandcamp",
        ],
    }

    return json.dumps(data, ensure_ascii=False, indent=2)


def build_page(keyword: str, albums: list[dict], all_slugs: list[str], date_str: str) -> tuple[str, str]:
    slug = slugify(keyword)
    title = keyword.title()
    album_context = pick_album_context(albums, 6)

    content = llm_generate(keyword, album_context)
    paragraphs = paragraphize(content)

    if not paragraphs:
        paragraphs = paragraphize(fallback_content(keyword, album_context))

    lede = paragraphs[0]
    rest = paragraphs[1:]

    if not rest:
        rest = paragraphs

    midpoint = max(1, len(rest) // 2)
    first_half = rest[:midpoint]
    second_half = rest[midpoint:]

    meta_description = (
        f"{title} — a Vincent Bastille guide to house remix culture, electronic remix production, Bandcamp listening and club-focused reinterpretation."
    )[:155]

    album_items = build_album_links(album_context, 6)
    internal_items = build_internal_links(slug, all_slugs, 8)
    schema = schema_article(title, meta_description, slug, date_str)

    first_html = "\n      ".join(f"<p>{safe_text(p)}</p>" for p in first_half)
    second_html = "\n      ".join(f"<p>{safe_text(p)}</p>" for p in second_half)

    if not internal_items:
        internal_items = '<li><a href="/">Main Vincent Bastille remix catalogue</a></li>'

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_text(title)} | Vincent Bastille Remixes</title>
  <meta name="description" content="{safe_text(meta_description)}">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="{BASE_URL}/seo-pages/{safe_text(slug)}.html">

  <meta property="og:type" content="article">
  <meta property="og:title" content="{safe_text(title)} | Vincent Bastille Remixes">
  <meta property="og:description" content="{safe_text(meta_description)}">
  <meta property="og:url" content="{BASE_URL}/seo-pages/{safe_text(slug)}.html">

  <script type="application/ld+json">
{schema}
  </script>

  <style>
    body {{
      font-family: Georgia, serif;
      max-width: 880px;
      margin: 0 auto;
      padding: 2rem 1rem;
      color: #111;
      line-height: 1.75;
      background: #fff;
    }}
    header {{
      margin-bottom: 2rem;
      border-bottom: 1px solid #ddd;
      padding-bottom: 1.5rem;
    }}
    h1 {{
      font-size: clamp(2rem, 5vw, 3.4rem);
      line-height: 1.05;
      margin-bottom: 1rem;
    }}
    h2 {{
      font-size: 1.55rem;
      margin-top: 2.6rem;
      margin-bottom: 0.8rem;
    }}
    p {{
      font-size: 1.05rem;
      margin-bottom: 1.15rem;
    }}
    p.lede {{
      font-size: 1.18rem;
      font-weight: 500;
    }}
    a {{
      color: #111;
      text-decoration-thickness: 1px;
      text-underline-offset: 3px;
    }}
    nav ul, section.listen ul {{
      padding-left: 1.2rem;
    }}
    li {{
      margin: 0.4rem 0;
    }}
    .meta {{
      color: #777;
      font-size: 0.9rem;
    }}
    .cta {{
      margin: 2rem 0;
      padding: 1.25rem;
      border: 1px solid #ddd;
      background: #fafafa;
    }}
    footer {{
      margin-top: 3rem;
      border-top: 1px solid #ddd;
      padding-top: 1rem;
      color: #777;
      font-size: 0.9rem;
    }}
  </style>
</head>
<body>

<article>
  <header>
    <p class="meta">Vincent Bastille Remixes · Published {safe_text(date_str)}</p>
    <h1>{safe_text(title)}</h1>
    <p class="lede">{safe_text(lede)}</p>
  </header>

  <section>
    <h2>{safe_text(title)}: Remix Context</h2>
      {first_html}
  </section>

  <section>
    <h2>Production, Listening And Club Energy</h2>
      {second_html}
  </section>

  <section class="cta">
    <h2>Listen To Vincent Bastille On Bandcamp</h2>
    <p>Explore the full Vincent Bastille catalogue, including house remixes, electronic releases, cinematic material and independent Bandcamp releases.</p>
    <p><a href="https://vincentbastille.bandcamp.com" target="_blank" rel="noopener">Open Vincent Bastille Bandcamp →</a></p>
  </section>

  <section class="listen">
    <h2>Related Bandcamp Releases</h2>
    <ul>
        {album_items}
    </ul>
  </section>

  <nav aria-label="Related remix pages">
    <h2>Explore More Remix Pages</h2>
    <ul>
        {internal_items}
    </ul>
  </nav>
</article>

<footer>
  <p><a href="/">Back to main remix catalogue</a> · <a href="/sitemap.xml">Sitemap</a></p>
</footer>

</body>
</html>
"""

    return slug, html_doc


# =============================================================================
# SITEMAP
# =============================================================================

def collect_all_html_urls() -> list[str]:
    urls = ["/"]

    for folder in SEO_DIRS:
        if not folder.exists():
            continue

        for path in sorted(folder.rglob("*.html")):
            if path.name.lower().startswith("google"):
                continue

            rel = "/" + str(path).replace("\\", "/")
            urls.append(rel)

    deduped = []
    seen = set()

    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        deduped.append(url)

    return deduped


def write_sitemap(date_str: str) -> None:
    urls = collect_all_html_urls()

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for rel_url in urls:
        priority = "1.0" if rel_url == "/" else "0.8"
        changefreq = "daily" if rel_url == "/" else "weekly"

        lines.append("  <url>")
        lines.append(f"    <loc>{BASE_URL}{safe_text(rel_url)}</loc>")
        lines.append(f"    <lastmod>{safe_text(date_str)}</lastmod>")
        lines.append(f"    <changefreq>{changefreq}</changefreq>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")

    lines.append("</urlset>")

    SITEMAP_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info("Sitemap written: %d URLs → %s", len(urls), SITEMAP_PATH)


def ping_google() -> None:
    sitemap_url = f"{BASE_URL}/sitemap.xml"
    ping_url = f"https://www.google.com/ping?sitemap={sitemap_url}"

    try:
        response = requests.get(ping_url, timeout=10)
        log.info("Google ping response: HTTP %s", response.status_code)

    except Exception as exc:
        log.warning("Google ping failed: %s", exc)


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    log.info("SEO GENERATOR START")

    if not TOGETHER_API_KEY:
        log.error("Missing TOGETHER_API_KEY. Add it in GitHub Secrets → Actions.")
        sys.exit(1)

    if not JSON_PATH.exists():
        log.error("Missing bandcamp_full.json at repo root.")
        sys.exit(1)

    albums = load_json(JSON_PATH)

    if not isinstance(albums, list) or not albums:
        log.error("bandcamp_full.json must contain a non-empty list.")
        sys.exit(1)

    log.info("Loaded %d albums from %s", len(albums), JSON_PATH)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    state = load_state()
    generated = set(state.get("generated", []))
    date_str = datetime.now().date().isoformat()

    keyword_plan = build_keyword_plan()
    selected_keywords = []

    for keyword in keyword_plan:
        slug = slugify(keyword)
        out_path = OUTPUT_DIR / f"{slug}.html"

        if slug in generated and existing_page_is_valid(out_path):
            continue

        selected_keywords.append(keyword)

        if len(selected_keywords) >= MAX_PAGES_PER_RUN:
            break

    log.info("Pages to generate this run: %d", len(selected_keywords))

    all_existing_slugs = []
    for path in OUTPUT_DIR.glob("*.html"):
        all_existing_slugs.append(path.stem)

    newly_generated = []
    errors = 0

    for index, keyword in enumerate(selected_keywords, start=1):
        slug = slugify(keyword)
        out_path = OUTPUT_DIR / f"{slug}.html"

        log.info("[%d/%d] Generating: %s", index, len(selected_keywords), keyword)

        try:
            current_link_pool = list(set(all_existing_slugs + newly_generated))
            slug, page_html = build_page(keyword, albums, current_link_pool, date_str)

            out_path.write_text(page_html, encoding="utf-8")

            generated.add(slug)
            newly_generated.append(slug)

            state["generated"] = sorted(generated)
            save_state(state)

            log.info("Written: %s", out_path)

        except Exception as exc:
            errors += 1
            log.error("Failed generating %s: %s", keyword, exc)

        time.sleep(BATCH_PAUSE)

    write_sitemap(date_str)
    ping_google()

    log.info("─" * 60)
    log.info("DONE")
    log.info("Generated this run: %d", len(newly_generated))
    log.info("Errors: %d", errors)
    log.info("Total generated in state: %d", len(generated))
    log.info("─" * 60)


if __name__ == "__main__":
    main()
