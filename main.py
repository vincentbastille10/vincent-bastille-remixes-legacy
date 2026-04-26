import json
import html
import logging
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from itertools import product as iterproduct

import requests

# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

log = logging.getLogger(__name__)

# =============================================================================
# CONFIG
# =============================================================================

BASE_URL = "https://remixes.vincentbastille.online"

OUTPUT_DIR = Path("seo-pages")
SEO_DIRS = [Path("SEO"), Path("seo-pages")]

JSON_PATH = Path("bandcamp_full.json")
SITEMAP_PATH = Path("sitemap.xml")
STATE_FILE = Path(".seo_state.json")

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

MAX_PAGES_PER_RUN = 300
MIN_WORDS = 500
TARGET_WORDS_MIN = 800
TARGET_WORDS_MAX = 1200

INTERNAL_LINKS_PER_PAGE = 12
DELAY_BETWEEN_PAGES = 0.3

# =============================================================================
# KEYWORD SYSTEM — MASS GENERATION ENGINE
# =============================================================================

SEED_KEYWORDS = [
    "deep house remix",
    "house remix",
    "afro house remix",
    "vocal house remix",
    "french house remix",
    "underground house edit",
    "melodic house remix",
    "night electronic remix",
    "club house remix",
    "tech house remix",
    "tribal house remix",
    "soulful house remix",
    "progressive house remix",
    "organic house remix",
    "minimal house remix",
    "chicago house remix",
    "garage house remix",
    "nu disco remix",
    "funky house remix",
    "latin house remix",
]

MODIFIERS = [
    "2026",
    "for DJs",
    "listening session",
    "guide",
    "124 bpm",
    "126 bpm",
    "128 bpm",
    "club perspective",
    "late night",
    "warm up set",
    "peak hour",
    "hypnotic session",
    "emotional guide",
    "sound design notes",
    "archive entry",
    "b-ready deep dive",
    "club ready",
    "summer",
    "winter",
    "best of",
]

ARTIST_TERMS = [
    "vincent bastille",
    "producer perspective",
    "bandcamp exclusive",
    "independent release",
]

GENRE_COMBOS = [
    "house soul",
    "house funk",
    "house jazz",
    "house electronic",
    "house tribal",
    "house ambient",
]

LOCATION_MODIFIERS = [
    "paris",
    "ibiza",
    "berlin",
    "london",
    "new york",
    "chicago",
    "detroit",
]

def build_keyword_pool():
    pool = set()

    # Seed + modifier combos
    for seed in SEED_KEYWORDS:
        pool.add(seed)
        for mod in MODIFIERS:
            pool.add(f"{seed} {mod}")
        for loc in LOCATION_MODIFIERS:
            pool.add(f"{seed} {loc}")

    # Best/top prefix
    for seed in SEED_KEYWORDS:
        pool.add(f"best {seed}")
        pool.add(f"top {seed} 2026")

    # Genre combos
    for gc in GENRE_COMBOS:
        pool.add(f"{gc} remix")
        pool.add(f"{gc} remix 2026")
        pool.add(f"best {gc} remix")

    # Artist + seed
    for seed in SEED_KEYWORDS[:10]:
        pool.add(f"{seed} vincent bastille")
        pool.add(f"vincent bastille {seed}")

    # BPM-specific
    for bpm in ["120", "122", "124", "126", "128", "130"]:
        for seed in SEED_KEYWORDS[:8]:
            pool.add(f"{seed} {bpm} bpm")

    return list(pool)

# =============================================================================
# SECONDARY KEYWORD CLUSTERS
# =============================================================================

SECONDARY_KEYWORD_CLUSTERS = {
    "deep house": [
        "deep house music", "deep house DJs", "deep house production",
        "deep grooves", "four on the floor", "soulful deep house",
        "deep house listening", "late night deep house", "deep house 2026",
        "underground deep house"
    ],
    "afro house": [
        "afro house rhythms", "afro beats remix", "african house music",
        "afro house DJs", "percussion house", "tribal afro house",
        "afro house 2026", "south african house", "afro tech",
        "spiritual house music"
    ],
    "vocal house": [
        "vocal house tracks", "house music vocals", "soulful vocals",
        "house diva", "vocal remix", "house singing", "emotional house music",
        "gospel house", "vocal deep house", "house vocals 2026"
    ],
    "french house": [
        "french touch music", "paris house music", "french electronic",
        "daft punk influence", "french groove", "filter house",
        "french house DJs", "french disco house", "french touch 2026",
        "parisian house music"
    ],
    "tech house": [
        "tech house beats", "techno house fusion", "tech house DJs",
        "underground tech house", "minimal tech house", "driving beats",
        "club tech house", "tech house 2026", "warehouse tech house",
        "tech house production"
    ],
    "general": [
        "house music remix", "electronic dance music", "DJ tools",
        "remix production", "club music", "dance floor anthems",
        "house music 2026", "house music listening", "best remixes",
        "remix guide"
    ]
}

def get_secondary_keywords(keyword):
    """Select 5-10 relevant secondary keywords for a given primary keyword."""
    cluster_key = "general"
    for k in SECONDARY_KEYWORD_CLUSTERS:
        if k in keyword.lower():
            cluster_key = k
            break
    cluster = SECONDARY_KEYWORD_CLUSTERS[cluster_key]
    general = SECONDARY_KEYWORD_CLUSTERS["general"]
    combined = list(set(cluster + general))
    return random.sample(combined, min(8, len(combined)))

# =============================================================================
# HELPERS
# =============================================================================

def slugify(text):
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.strip("-")[:80]

def safe_text(t):
    return html.escape(t)

def word_count(text):
    return len(text.split())

def load_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"generated_slugs": [], "generated_keywords": []}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

# =============================================================================
# CONTENT ANGLES — ensure each page has a different structural angle
# =============================================================================

CONTENT_ANGLES = [
    "dj_tool",
    "production_guide",
    "listening_journey",
    "history_culture",
    "track_analysis",
    "scene_overview",
    "emotional_impact",
    "technical_breakdown",
    "artist_spotlight",
    "beginner_intro",
]

def get_angle(i):
    return CONTENT_ANGLES[i % len(CONTENT_ANGLES)]

ANGLE_PROMPTS = {
    "dj_tool": "Focus on how DJs use this in their sets. Include mixing tips, BPM considerations, energy flow, and when in a set to drop it.",
    "production_guide": "Explain the production elements: drum patterns, basslines, synth layers, how Vincent Bastille approaches these in remixes.",
    "listening_journey": "Write as if guiding the listener through an emotional listening experience. Describe feelings, moods, textures.",
    "history_culture": "Explore the cultural roots and history behind this style. Reference Chicago, Detroit, Paris, UK garage as relevant.",
    "track_analysis": "Analyze specific sonic elements: groove, tension, release, transitions, and what makes a great remix in this style.",
    "scene_overview": "Overview the current state of this sound in 2026. Who's making it, where it's played, what's trending.",
    "emotional_impact": "Focus on the emotional and physical effect of this music on the dancefloor and listener at home.",
    "technical_breakdown": "Technical deep-dive: time signatures, key signatures, arrangement structures, typical track length and breakdown points.",
    "artist_spotlight": "Vincent Bastille's personal approach to this style, his influences, what makes his remixes distinctive.",
    "beginner_intro": "Written for someone discovering this style for the first time. Explain what it is, why it matters, how to start exploring.",
}

# =============================================================================
# META DESCRIPTION TEMPLATES — CTR optimized
# =============================================================================

META_TEMPLATES = [
    "Discover how {primary} transforms dancefloors in 2026 — the complete guide for DJs and music lovers who want deeper understanding.",
    "Why is {primary} taking over underground clubs? Explore the sounds, culture, and production secrets behind this essential style.",
    "Everything you need to know about {primary}: from BPM selection to emotional impact. A definitive guide by Vincent Bastille.",
    "The hidden language of {primary} decoded — how top DJs use it to move crowds, and why it resonates so deeply.",
    "Looking for the best {primary} experience? This guide breaks down the sounds, feelings, and culture behind the style.",
    "Explore {primary} from dancefloor to studio: production insights, DJ techniques, and the artists who define the sound in 2026.",
    "From late-night clubs to bedroom listening sessions — how {primary} creates unforgettable musical moments.",
    "The complete {primary} deep dive: history, production, DJ application, and why it matters more than ever in 2026.",
]

def build_meta_description(keyword):
    template = random.choice(META_TEMPLATES)
    return template.format(primary=keyword.title())

# =============================================================================
# OLLAMA LLM
# =============================================================================

def llm_generate(keyword, secondary_keywords, angle, angle_hint):
    sec_kw_str = ", ".join(secondary_keywords)

    prompt = f"""You are a knowledgeable music journalist and house music expert writing for an educated audience of DJs, producers, and music enthusiasts.

Write a high-quality SEO article about: "{keyword}"

WRITING ANGLE: {angle_hint}

STRUCTURE REQUIRED:
1. An engaging introduction paragraph (2-3 sentences, hooks the reader, includes the primary keyword naturally)
2. Section with H2: explore the sound and culture (use markdown ## for H2)
3. Section with H2: practical applications for DJs and listeners
4. Section with H2: production and sonic characteristics
5. A conclusion paragraph (wrap up, forward-looking, mention Vincent Bastille naturally)

KEYWORDS TO EMBED NATURALLY (do not list them, weave them into the text):
Primary: {keyword}
Secondary: {sec_kw_str}

RULES:
- Write 900 to 1100 words total
- Natural, human writing — NOT robotic or repetitive
- No bullet points anywhere
- No markdown except ## for H2 headers
- Include "Vincent Bastille" mentioned 2-3 times naturally as an artist/producer in this space
- Include specific sonic details: BPM ranges, instrument descriptions, mood descriptors
- Vary sentence length. Mix short punchy sentences with longer flowing ones.
- Do NOT keyword stuff. Density should feel natural.
- Write with genuine enthusiasm and expertise
- Avoid generic filler phrases like "in conclusion" or "in today's world"

Begin writing now:"""

    try:
        res = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.72,
                    "top_p": 0.9,
                    "num_predict": 1400,
                    "repeat_penalty": 1.1,
                }
            },
            timeout=120
        )

        data = res.json()
        text = data.get("response", "").strip()

        if not text or word_count(text) < MIN_WORDS:
            raise Exception(f"Content too short: {word_count(text)} words")

        return text

    except Exception as e:
        log.warning(f"Ollama primary generation failed: {e}")
        return None

def llm_enrich(existing_text, keyword):
    """Append enrichment content if word count is too low."""
    prompt = f"""Continue this article about "{keyword}" with 2 more paragraphs. 
Write naturally, no headers, no bullet points, 150-200 words per paragraph.
Match the existing tone. Mention "Vincent Bastille" once naturally.

Existing text ends with: ...{existing_text[-300:]}

Continue:"""

    try:
        res = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.68,
                    "top_p": 0.9,
                    "num_predict": 500,
                }
            },
            timeout=60
        )
        data = res.json()
        return data.get("response", "").strip()
    except Exception as e:
        log.warning(f"Enrichment failed: {e}")
        return ""

def fallback_content(keyword, secondary_keywords):
    """Generate minimal fallback content if Ollama fails entirely."""
    sec = ", ".join(secondary_keywords[:3])
    return f"""The world of {keyword} is as rich and layered as the music itself. Few styles in electronic music capture the intersection of groove, emotion, and technical mastery quite like this one. Vincent Bastille has spent years exploring this territory, and the results speak for themselves across his Bandcamp catalog.

## The Sound and What Makes It Move

At its core, {keyword} is built on a foundation of rhythmic precision and emotional depth. The grooves roll forward with intention, never rushed, never stagnant. Producers working in this space understand that a great remix isn't just about changing a track — it's about reimagining it entirely, finding the hidden emotional core and amplifying it through sound design, arrangement, and feel. The best examples in this genre share a common thread: they make you feel something specific, whether that's the weight of late night, the release of a dancefloor moment, or the quiet intimacy of a home listening session. {sec} all play a role in shaping how this music lands.

## How DJs Apply This Sound

Professional DJs working with {keyword} understand its specific energy requirements. It sits best in certain moments of a set — transitional spaces, building zones, or as a peak tool depending on the exact tempo and mood. Vincent Bastille's approach to {keyword} has always been informed by real dancefloor experience: knowing when a crowd needs to be lifted versus when they need to settle into a groove. The BPM range matters, the key matters, and so does the emotional arc of each individual track within the context of a longer set. Smart DJs use these tools strategically.

## The Cultural Roots Run Deep

Electronic music doesn't emerge from nowhere. {keyword} carries the DNA of decades of club culture: the warehouse raves of Chicago and Detroit, the underground parties of Paris and Berlin, the sweaty basement clubs of London. Each regional scene contributed something essential — rhythmic innovations, new sonic palettes, different attitudes toward tempo and space. Vincent Bastille's work in this space explicitly acknowledges these roots while pushing forward. The best remix isn't a museum piece — it's a living document that bridges past and present.

## Why It Resonates in 2026

The landscape of electronic music in 2026 is both crowded and thrilling. Yet {keyword} continues to carve out real space because it serves a genuine human need: the desire to feel music physically and emotionally at the same time. It moves the body and occupies the mind. For listeners, for DJs, for producers like Vincent Bastille — this balance is the whole game. The production continues to evolve, the sounds change, but the core proposition remains the same. Find the groove. Hold it. Let it breathe."""

# =============================================================================
# PARSE CONTENT INTO STRUCTURED HTML
# =============================================================================

def parse_content_to_html(raw_text, secondary_keywords, all_page_slugs):
    """Convert raw LLM output into structured HTML with internal links."""
    lines = raw_text.strip().split("\n")
    html_parts = []
    current_paragraph = []
    h2_count = 0

    def flush_paragraph():
        if current_paragraph:
            para = " ".join(current_paragraph).strip()
            if para:
                # Occasionally embed a contextual internal link in paragraphs
                if all_page_slugs and random.random() < 0.25:
                    target = random.choice(all_page_slugs)
                    anchor = target.replace("-", " ").title()
                    link = f'<a href="{target}.html">{anchor}</a>'
                    # Insert link at a natural point
                    words = para.split()
                    if len(words) > 20:
                        insert_at = random.randint(15, len(words) - 5)
                        words.insert(insert_at, link)
                        para = " ".join(words)
                html_parts.append(f"<p>{safe_text(para) if '<a href' not in para else para}</p>")
            current_paragraph.clear()

    for line in lines:
        line = line.strip()
        if not line:
            flush_paragraph()
        elif line.startswith("## "):
            flush_paragraph()
            h2_text = line[3:].strip()
            h2_count += 1
            html_parts.append(f"<h2>{safe_text(h2_text)}</h2>")
        elif line.startswith("# "):
            flush_paragraph()
            h1_text = line[2:].strip()
            html_parts.append(f"<h2>{safe_text(h1_text)}</h2>")
        else:
            current_paragraph.append(line)

    flush_paragraph()
    return "\n".join(html_parts)

# =============================================================================
# INTERNAL LINKING SECTION
# =============================================================================

def build_related_links(current_slug, all_slugs, count=INTERNAL_LINKS_PER_PAGE):
    """Build a 'related pages' section with human-readable anchor text."""
    candidates = [s for s in all_slugs if s != current_slug]
    selected = random.sample(candidates, min(count, len(candidates)))

    links_html = []
    for slug in selected:
        anchor = slug.replace("-", " ").title()
        # Clean up anchor: remove trailing numbers that look like dedup suffixes
        anchor = re.sub(r"\s+\d+$", "", anchor)
        links_html.append(f'<li><a href="{slug}.html">{anchor}</a></li>')

    return "\n".join(links_html)

# =============================================================================
# PAGE BUILDER
# =============================================================================

def build_page(keyword, secondary_keywords, angle_index, all_slugs, date_str):
    slug = slugify(keyword)
    title = keyword.title()
    angle = get_angle(angle_index)
    angle_hint = ANGLE_PROMPTS[angle]

    meta_desc = build_meta_description(keyword)

    # Build OpenGraph title variation
    og_title_templates = [
        f"{title} — Complete Guide 2026",
        f"The Best {title}: DJ & Listener Guide",
        f"{title}: Culture, Sound & Production",
        f"Understanding {title} — Vincent Bastille",
        f"{title} Deep Dive | House Music Guide",
    ]
    og_title = random.choice(og_title_templates)

    # Generate content
    raw_content = llm_generate(keyword, secondary_keywords, angle, angle_hint)

    if raw_content is None:
        log.warning(f"Using fallback content for: {keyword}")
        raw_content = fallback_content(keyword, secondary_keywords)

    # Enrich if too short
    wc = word_count(raw_content)
    if wc < TARGET_WORDS_MIN:
        log.info(f"Content short ({wc} words), enriching...")
        enrichment = llm_enrich(raw_content, keyword)
        if enrichment:
            raw_content += "\n\n" + enrichment
        wc = word_count(raw_content)
        log.info(f"After enrichment: {wc} words")

    # Parse to HTML
    body_html = parse_content_to_html(raw_content, secondary_keywords, all_slugs)

    # Internal related links
    related_links_html = ""
    if len(all_slugs) > 1:
        related_links_html = build_related_links(slug, all_slugs)
        related_section = f"""
<section class="related-pages">
  <h2>Related Remix Pages</h2>
  <ul>
    {related_links_html}
  </ul>
</section>"""
    else:
        related_section = ""

    # Breadcrumb
    breadcrumb = f'<nav class="breadcrumb"><a href="../index.html">Home</a> &rsaquo; {safe_text(title)}</nav>'

    # Page HTML
    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_text(og_title)}</title>
  <meta name="description" content="{safe_text(meta_desc)}">
  <meta name="keywords" content="{safe_text(keyword)}, {safe_text(', '.join(secondary_keywords[:5]))}">
  <link rel="canonical" href="{BASE_URL}/seo-pages/{slug}.html">
  <meta property="og:title" content="{safe_text(og_title)}">
  <meta property="og:description" content="{safe_text(meta_desc)}">
  <meta property="og:url" content="{BASE_URL}/seo-pages/{slug}.html">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Vincent Bastille Remixes">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{safe_text(og_title)}">
  <meta name="twitter:description" content="{safe_text(meta_desc)}">
  <style>
    body {{ font-family: Georgia, serif; max-width: 860px; margin: 0 auto; padding: 20px 24px; color: #1a1a1a; line-height: 1.75; background: #fff; }}
    h1 {{ font-size: 2em; margin-bottom: 0.4em; color: #111; }}
    h2 {{ font-size: 1.35em; margin-top: 2em; color: #222; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }}
    p {{ margin: 1.1em 0; font-size: 1.05em; }}
    a {{ color: #0057b7; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .breadcrumb {{ font-size: 0.9em; color: #666; margin-bottom: 1.5em; }}
    .meta {{ font-size: 0.85em; color: #888; margin-bottom: 2em; }}
    .related-pages {{ background: #f8f8f8; border: 1px solid #e0e0e0; border-radius: 6px; padding: 20px 24px; margin-top: 3em; }}
    .related-pages h2 {{ border: none; font-size: 1.1em; margin-top: 0; }}
    .related-pages ul {{ columns: 2; column-gap: 2em; padding: 0; margin: 0; list-style: none; }}
    .related-pages li {{ margin-bottom: 0.5em; font-size: 0.92em; break-inside: avoid; }}
    .site-nav {{ background: #111; color: #fff; padding: 12px 16px; margin-bottom: 2em; font-size: 0.9em; }}
    .site-nav a {{ color: #aad4ff; margin-right: 1em; }}
    footer {{ margin-top: 4em; padding-top: 2em; border-top: 1px solid #eee; font-size: 0.85em; color: #999; }}
  </style>
</head>
<body>

<div class="site-nav">
  <a href="../index.html">&#8592; All Remix Guides</a>
  <a href="{BASE_URL}">Vincent Bastille</a>
</div>

{breadcrumb}

<article>
  <h1>{safe_text(title)}</h1>
  <div class="meta">Published: {date_str} &nbsp;|&nbsp; House Music &amp; Remix Culture &nbsp;|&nbsp; Vincent Bastille</div>

  {body_html}
</article>

{related_section}

<footer>
  <p>&copy; {datetime.now().year} Vincent Bastille Remixes. Explore <a href="../index.html">all remix guides</a>.</p>
</footer>

</body>
</html>
"""

    return slug, html_doc

# =============================================================================
# INDEX PAGE
# =============================================================================

THEME_PATTERNS = {
    "Deep House": ["deep house"],
    "Afro House": ["afro house", "african house", "tribal"],
    "French House": ["french house", "french touch", "parisian"],
    "Vocal House": ["vocal house", "gospel house", "soul"],
    "Tech House": ["tech house", "minimal tech"],
    "Underground & Club": ["underground", "club house", "garage house", "chicago", "detroit"],
    "Melodic & Organic": ["melodic", "organic", "progressive", "ambient"],
    "Nu Disco & Funk": ["nu disco", "funky", "funk", "disco"],
    "Artist Focus": ["vincent bastille"],
    "Other Styles": [],
}

def classify_page(slug):
    for theme, patterns in THEME_PATTERNS.items():
        if theme == "Other Styles":
            continue
        for pattern in patterns:
            if pattern in slug:
                return theme
    return "Other Styles"

def build_index(all_slugs, all_keywords, date_str):
    # Group pages by theme
    groups = {theme: [] for theme in THEME_PATTERNS}

    for slug, kw in zip(all_slugs, all_keywords):
        theme = classify_page(slug)
        anchor = kw.title()
        groups[theme].append((slug, anchor))

    sections_html = ""
    for theme, pages in groups.items():
        if not pages:
            continue
        items = "\n".join(
            f'<li><a href="seo-pages/{slug}.html">{safe_text(anchor)}</a></li>'
            for slug, anchor in sorted(pages, key=lambda x: x[1])
        )
        sections_html += f"""
<section class="theme-group">
  <h2>{safe_text(theme)}</h2>
  <ul class="page-list">
    {items}
  </ul>
</section>
"""

    total = len(all_slugs)

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>House Music Remix Guides 2026 | Vincent Bastille</title>
  <meta name="description" content="Explore {total} in-depth house music remix guides covering deep house, afro house, vocal house, French house, and more. Curated by Vincent Bastille.">
  <link rel="canonical" href="{BASE_URL}/index.html">
  <meta property="og:title" content="House Music Remix Guides 2026 | Vincent Bastille">
  <meta property="og:description" content="The complete house music guide: {total} pages covering every style, BPM, mood, and DJ technique.">
  <meta property="og:url" content="{BASE_URL}/index.html">
  <meta property="og:type" content="website">
  <style>
    body {{ font-family: Georgia, serif; max-width: 1000px; margin: 0 auto; padding: 20px 24px; color: #1a1a1a; line-height: 1.7; background: #fff; }}
    h1 {{ font-size: 2.2em; color: #111; margin-bottom: 0.3em; }}
    h2 {{ font-size: 1.25em; color: #222; border-bottom: 2px solid #111; padding-bottom: 0.3em; margin-top: 2.5em; }}
    .subtitle {{ font-size: 1.1em; color: #555; margin-bottom: 2em; }}
    .theme-group {{ margin-bottom: 2em; }}
    .page-list {{ columns: 3; column-gap: 2em; padding: 0; margin: 0.8em 0 0; list-style: none; }}
    .page-list li {{ break-inside: avoid; margin-bottom: 0.45em; font-size: 0.93em; }}
    a {{ color: #0057b7; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .site-header {{ background: #111; color: #fff; padding: 16px 20px; margin-bottom: 2em; display: flex; align-items: center; justify-content: space-between; }}
    .site-header a {{ color: #aad4ff; font-size: 0.9em; }}
    .stats {{ background: #f0f4f8; border-left: 4px solid #0057b7; padding: 12px 20px; margin-bottom: 2em; font-size: 0.95em; }}
    footer {{ margin-top: 4em; padding-top: 2em; border-top: 1px solid #eee; font-size: 0.85em; color: #999; }}
    @media (max-width: 600px) {{ .page-list {{ columns: 1; }} }}
  </style>
</head>
<body>

<div class="site-header">
  <strong style="color:#fff;">Vincent Bastille — Remix Guides</strong>
  <a href="{BASE_URL}">Visit Main Site</a>
</div>

<h1>House Music Remix Guides 2026</h1>
<p class="subtitle">The definitive resource for DJs, producers, and music lovers exploring house music, remixes, and electronic dance culture — curated by producer Vincent Bastille.</p>

<div class="stats">
  <strong>{total} guides</strong> covering deep house, afro house, vocal house, French house, tech house, nu disco, and more.
  Updated: {date_str}
</div>

{sections_html}

<footer>
  <p>&copy; {datetime.now().year} Vincent Bastille. House music made with love in Paris.</p>
  <p><a href="sitemap.xml">Sitemap</a></p>
</footer>

</body>
</html>
"""

    return html_doc

# =============================================================================
# SITEMAP
# =============================================================================

def collect_urls():
    urls = []
    for folder in SEO_DIRS:
        if not folder.exists():
            continue
        for p in folder.rglob("*.html"):
            urls.append("/" + str(p).replace("\\", "/"))
    # Add index
    index_path = Path("index.html")
    if index_path.exists():
        urls.append("/index.html")
    return list(set(urls))

def write_sitemap(date_str):
    urls = collect_urls()
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for u in urls:
        priority = "1.0" if u == "/index.html" else "0.8"
        lines.append(f"""  <url>
    <loc>{BASE_URL}{u}</loc>
    <lastmod>{date_str}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>{priority}</priority>
  </url>""")
    lines.append("</urlset>")
    SITEMAP_PATH.write_text("\n".join(lines), encoding="utf-8")
    log.info(f"Sitemap written: {len(urls)} URLs")

# =============================================================================
# MAIN
# =============================================================================

def main():
    log.info("=== SEO SYSTEM START ===")

    OUTPUT_DIR.mkdir(exist_ok=True)

    date_str = datetime.now().date().isoformat()

    # Load resume state
    state = load_state()
    already_done_slugs = set(state.get("generated_slugs", []))
    already_done_keywords = set(state.get("generated_keywords", []))
    log.info(f"Already generated: {len(already_done_slugs)} pages (resume mode)")

    # Build full keyword pool
    keyword_pool = build_keyword_pool()
    random.shuffle(keyword_pool)
    log.info(f"Total keyword pool: {len(keyword_pool)} keywords")

    # Filter out already-done
    pending = [kw for kw in keyword_pool if kw not in already_done_keywords]
    to_generate = pending[:MAX_PAGES_PER_RUN]
    log.info(f"Generating {len(to_generate)} new pages this run")

    # Collect all existing slugs (for internal linking)
    existing_slugs = list(already_done_slugs)
    new_slugs = [slugify(kw) for kw in to_generate]
    all_slugs_pool = list(set(existing_slugs + new_slugs))

    all_generated_slugs = list(already_done_slugs)
    all_generated_keywords = list(already_done_keywords)

    for i, keyword in enumerate(to_generate):
        slug = slugify(keyword)

        # Dedup check
        if slug in already_done_slugs:
            log.info(f"Skip (dup slug): {keyword}")
            continue

        log.info(f"[{i+1}/{len(to_generate)}] Generating: {keyword} (angle: {get_angle(i)})")

        secondary_kw = get_secondary_keywords(keyword)

        try:
            slug, html_doc = build_page(
                keyword=keyword,
                secondary_keywords=secondary_kw,
                angle_index=i,
                all_slugs=all_slugs_pool,
                date_str=date_str
            )

            out_path = OUTPUT_DIR / f"{slug}.html"
            out_path.write_text(html_doc, encoding="utf-8")

            all_generated_slugs.append(slug)
            all_generated_keywords.append(keyword)
            already_done_slugs.add(slug)

            wc = word_count(html_doc)
            log.info(f"  Saved: {out_path} (~{wc} words in HTML)")

            # Save state every 10 pages for resume capability
            if (i + 1) % 10 == 0:
                save_state({
                    "generated_slugs": all_generated_slugs,
                    "generated_keywords": all_generated_keywords
                })
                log.info("State saved (checkpoint)")

        except Exception as e:
            log.error(f"Failed to generate page for '{keyword}': {e}")

        time.sleep(DELAY_BETWEEN_PAGES)

    # Save final state
    save_state({
        "generated_slugs": all_generated_slugs,
        "generated_keywords": all_generated_keywords
    })

    # Build index page
    log.info("Building index.html...")
    index_html = build_index(all_generated_slugs, all_generated_keywords, date_str)
    Path("index.html").write_text(index_html, encoding="utf-8")
    log.info("index.html written")

    # Write sitemap
    write_sitemap(date_str)

    log.info(f"=== DONE: {len(all_generated_slugs)} total pages across all runs ===")

# =============================================================================

if __name__ == "__main__":
    main()