import os
import json
import logging
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
#
# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("seo_generator.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

BASE_URL          = "https://remixes.vincentbastille.online"
OUTPUT_DIR        = Path("seo-pages")
JSON_PATH         = Path("bandcamp_full.json")
SITEMAP_PATH      = Path("sitemap.xml")
STATE_PATH        = Path(".seo_state.json")   # tracks already-generated slugs

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

MODEL             = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"

LLM_TIMEOUT       = 30          # seconds per attempt
LLM_RETRIES       = 3
LLM_RETRY_DELAY   = 5           # seconds between retries
MIN_CONTENT_WORDS = 500         # enforce minimum length

BATCH_PAUSE       = 0.5         # seconds between pages (be kind to the API)

# ─────────────────────────────────────────────────────────────────────────────
# KEYWORD SEEDS — natural variation base
# ─────────────────────────────────────────────────────────────────────────────

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

# Suffix pool — prevents duplicate keyword strings across iterations
SUFFIX_POOL = [
    "vol {n}", "edition {n}", "part {n}", "mix {n}", "session {n}",
    "series {n}", "chapter {n}", "release {n}", "drop {n}", "cut {n}",
]

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:120]   # cap slug length


def word_count(text: str) -> int:
    return len(text.split())


def load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"generated": []}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def unique_keyword(seed: str, n: int) -> str:
    suffix = random.choice(SUFFIX_POOL).format(n=n)
    return f"{seed} {suffix}"


# ─────────────────────────────────────────────────────────────────────────────
# LLM CALL WITH RETRY + FALLBACK
# ─────────────────────────────────────────────────────────────────────────────

_FALLBACK_PARAGRAPHS = [
    (
        "House music has always been a space where originals are reborn. A well-crafted remix "
        "doesn't just extend a track's life — it opens a second conversation with the listener, "
        "one built on familiarity and surprise in equal measure."
    ),
    (
        "In the world of electronic production, the remix is both a technical exercise and a "
        "creative statement. Producers who excel at it understand the geometry of a track: "
        "where the tension lives, where the release arrives, and how to reshape both without "
        "losing the original's soul."
    ),
    (
        "A house remix at 124 BPM is a precise thing. The kick must anchor, the hi-hats must "
        "breathe, and the harmonic content must remain coherent across filters, pitched loops, "
        "and added layers. When it works, the floor responds before the brain catches up."
    ),
    (
        "Remix culture in France has a distinct character. Influenced by the early Daft Punk "
        "era, the filtered-disco school, and the deeper underground strands of Chicago and "
        "Detroit, French producers bring a particular sensitivity to texture and space."
    ),
    (
        "Listening to a great house remix at the end of a long drive or on headphones late at "
        "night reveals details that a club mix would hide. The reverb tails, the side-chain "
        "breathe, the small edits that reward close attention. That depth is what separates "
        "craft from commodity."
    ),
    (
        "The best electronic remixes age well. What sounds fresh in 2026 often carries echoes "
        "of 1989 Chicago or 1994 London — production philosophies that understood rhythm as "
        "architecture, not decoration."
    ),
    (
        "Building a remix around a vocal requires restraint. The temptation is to bury the "
        "original under new production. The discipline is knowing which elements to keep "
        "exposed so the listener's connection to the source remains intact."
    ),
]


def llm_generate(keyword: str, album_context: list[dict]) -> str:
    import requests

    album_titles = ", ".join(a["title"] for a in album_context[:5])

    prompt = f"""
Write a 600 word SEO article about: {keyword}

Context:
Vincent Bastille is an electronic music producer focused on house remixes.

Albums:
{album_titles}

Requirements:
- Natural human writing
- No repetition
- No bullet points
- Strong emotional + musical tone
- Unique content
- At least 600 words
"""

    url = "https://api.together.xyz/v1/completions"

    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.2",
        "prompt": prompt,
        "max_tokens": 900,
        "temperature": 0.9
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["text"]

    except Exception as e:
        print("LLM ERROR:", e)

        return f"""
{keyword} is a central theme in modern electronic music culture.

Vincent Bastille explores remix structures through rhythm, emotion, and sound design.
Each track reflects a balance between club energy and personal listening experience.

House music continues to evolve, and remixes remain a key format for reinterpretation.
"""


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL LINK BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def _anchor_text(slug: str) -> str:
    """Convert slug to readable anchor text — no raw slug dumps."""
    words = slug.replace("-", " ").split()
    # Capitalise first word only
    return " ".join([words[0].capitalize()] + words[1:]) if words else slug


def build_internal_links(current_slug: str, all_slugs: list[str], max_links: int = 5) -> str:
    candidates = [s for s in all_slugs if s != current_slug]
    if not candidates:
        return ""
    picks = random.sample(candidates, min(max_links, len(candidates)))
    items = "\n        ".join(
        f'<li><a href="{BASE_URL}/{s}.html">{_anchor_text(s)}</a></li>'
        for s in picks
    )
    return items


# ─────────────────────────────────────────────────────────────────────────────
# ALBUM LINK BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def build_album_links(albums: list[dict], max_links: int = 5) -> str:
    picks = random.sample(albums, min(max_links, len(albums)))
    items = "\n        ".join(
        f'<li><a href="{a["url"]}" rel="noopener">{a["title"]}</a></li>'
        for a in picks
    )
    return items


# ─────────────────────────────────────────────────────────────────────────────
# HTML PAGE BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def build_page(
    keyword: str,
    albums: list[dict],
    all_slugs: list[str],
    date_str: str,
) -> tuple[str, str]:
    slug    = slugify(keyword)
    title   = keyword.title()
    content = llm_generate(keyword, random.sample(albums, min(6, len(albums))))

    # Split content into paragraphs for semantic HTML structure
    raw_paras = [p.strip() for p in content.split("\n\n") if p.strip()]
    if not raw_paras:
        raw_paras = [content]

    # First paragraph is the lede; rest form the body sections
    lede  = raw_paras[0]
    body  = raw_paras[1:]

    # Build paragraph HTML
    lede_html = f"<p class=\"lede\">{lede}</p>"
    body_html = "\n\n    ".join(f"<p>{p}</p>" for p in body) if body else ""

    # Section midpoint — insert an H2 halfway through if enough paragraphs
    mid_section = ""
    if len(body) >= 4:
        half      = len(body) // 2
        first_half = "\n\n    ".join(f"<p>{p}</p>" for p in body[:half])
        sec_label  = f"Producing a {title}"
        second_half = "\n\n    ".join(f"<p>{p}</p>" for p in body[half:])
        body_html  = (
            f"{first_half}\n\n"
            f"    <h2>{sec_label}</h2>\n\n"
            f"    {second_half}"
        )

    internal_items = build_internal_links(slug, all_slugs)
    album_items    = build_album_links(albums)

    description_meta = (
        f"{title} — Explore Vincent Bastille's take on {keyword.lower()}. "
        "House remixes, electronic edits and production insight."
    )[:160]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | Vincent Bastille</title>
  <meta name="description" content="{description_meta}">
  <meta name="robots" content="index, follow">
  <meta property="og:title" content="{title} | Vincent Bastille">
  <meta property="og:description" content="{description_meta}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{BASE_URL}/{slug}.html">
  <link rel="canonical" href="{BASE_URL}/{slug}.html">
  <style>
    body {{ font-family: Georgia, serif; max-width: 800px; margin: 0 auto; padding: 2rem 1rem; color: #111; line-height: 1.75; }}
    h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
    h2 {{ font-size: 1.4rem; margin-top: 2.5rem; margin-bottom: 0.75rem; }}
    p.lede {{ font-size: 1.1rem; font-weight: 500; }}
    nav.related ul, section.listen ul {{ list-style: none; padding: 0; }}
    nav.related li, section.listen li {{ margin: 0.4rem 0; }}
    a {{ color: #333; }}
    footer {{ margin-top: 3rem; font-size: 0.85rem; color: #777; border-top: 1px solid #ddd; padding-top: 1rem; }}
  </style>
</head>
<body>

<article>
  <header>
    <h1>{title}</h1>
  </header>

  <section class="content">
    {lede_html}

    <h2>Inside the Remix</h2>

    {body_html}
  </section>

  <section class="listen">
    <h2>Listen to Related Work</h2>
    <ul>
        {album_items}
    </ul>
    <p><a href="https://vincentbastille.bandcamp.com" rel="noopener">Full discography on Bandcamp →</a></p>
  </section>

  <nav class="related" aria-label="Related pages">
    <h2>Explore More</h2>
    <ul>
        {internal_items}
    </ul>
  </nav>
</article>

<footer>
  <p>Published {date_str} · <a href="{BASE_URL}/sitemap.xml">Sitemap</a></p>
</footer>

</body>
</html>
"""
    return slug, html


# ─────────────────────────────────────────────────────────────────────────────
# SITEMAP
# ─────────────────────────────────────────────────────────────────────────────

def write_sitemap(slugs: list[str], date_str: str) -> None:
    urls = "\n  ".join(
        f"<url>"
        f"<loc>{BASE_URL}/{s}.html</loc>"
        f"<lastmod>{date_str}</lastmod>"
        f"<changefreq>monthly</changefreq>"
        f"<priority>0.7</priority>"
        f"</url>"
        for s in slugs
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  {urls}\n"
        "</urlset>\n"
    )
    SITEMAP_PATH.write_text(xml, encoding="utf-8")
    log.info("Sitemap written: %d URLs → %s", len(slugs), SITEMAP_PATH)


# ─────────────────────────────────────────────────────────────────────────────
# GOOGLE PING
# ─────────────────────────────────────────────────────────────────────────────

def ping_google() -> None:
    sitemap_url = f"{BASE_URL}/sitemap.xml"
    ping_url    = f"https://www.google.com/ping?sitemap={sitemap_url}"
    try:
        r = requests.get(ping_url, timeout=10)
        if r.status_code == 200:
            log.info("Google sitemap ping OK (HTTP 200).")
        else:
            log.warning("Google ping returned HTTP %d.", r.status_code)
    except requests.exceptions.Timeout:
        log.warning("Google ping timed out — sitemap still valid.")
    except Exception as exc:
        log.warning("Google ping failed: %s", exc)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    log.info("SEO GENERATOR START")

    # ── Validate config ──────────────────────────────────────────────────────
    if TOGETHER_API_KEY == "TA_CLE_ICI":
        log.error("TOGETHER_API_KEY is not set. Edit the CONFIG section and rerun.")
        sys.exit(1)

    if not JSON_PATH.exists():
        log.error("JSON file not found: %s", JSON_PATH)
        sys.exit(1)

    # ── Load data ────────────────────────────────────────────────────────────
    albums: list[dict] = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    log.info("Loaded %d albums from %s", len(albums), JSON_PATH)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    state    = load_state()
    existing = set(state["generated"])
    date_str = datetime.now().date().isoformat()

    # ── Build keyword list — 20 iterations × len(KEYWORD_SEEDS) ─────────────
    all_keywords: list[str] = []
    for n in range(1, 3):
        for seed in KEYWORD_SEEDS:
            kw = unique_keyword(seed, n)
            if slugify(kw) not in existing:
                all_keywords.append(kw)

    total_planned = len(all_keywords)
    log.info("Pages to generate this run: %d", total_planned)

    # all_slugs includes previously generated ones for internal linking
    all_slugs: list[str] = list(existing)
    newly_generated: list[str] = []
    errors = 0

    for idx, keyword in enumerate(all_keywords, 1):
        slug = slugify(keyword)

        # Guard: slug collision (e.g. two keywords that normalise identically)
        if slug in existing or slug in newly_generated:
            log.debug("Skipping duplicate slug: %s", slug)
            continue

        log.info("[%d/%d] Generating: %s", idx, total_planned, keyword)

        try:
            slug, html = build_page(keyword, albums, all_slugs, date_str)
            out_path = OUTPUT_DIR / f"{slug}.html"
            out_path.write_text(html, encoding="utf-8")

            newly_generated.append(slug)
            all_slugs.append(slug)

            # Persist state after every page — safe against mid-run crashes
            state["generated"] = list(set(state["generated"]) | set(newly_generated))
            save_state(state)

        except Exception as exc:
            errors += 1
            log.error("Failed to generate '%s': %s", keyword, exc)

        time.sleep(BATCH_PAUSE)

    # ── Sitemap ───────────────────────────────────────────────────────────────
    all_known_slugs = list(set(state["generated"]))
    write_sitemap(all_known_slugs, date_str)

    # ── Google ping ───────────────────────────────────────────────────────────
    ping_google()

    # ── Summary ───────────────────────────────────────────────────────────────
    log.info("─" * 50)
    log.info("DONE")
    log.info("  Pages planned   : %d", total_planned)
    log.info("  Pages generated : %d", len(newly_generated))
    log.info("  Errors          : %d", errors)
    log.info("  Total in state  : %d", len(all_known_slugs))
    log.info("─" * 50)


if __name__ == "__main__":
    main()
