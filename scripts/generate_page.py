#!/usr/bin/env python3
from __future__ import annotations
import argparse
import os
from pathlib import Path
import re

try:
    import requests
except Exception:
    requests = None

ROOT = Path(__file__).resolve().parents[1]

LANDING = "https://remixes.vincentbastille.online"
SPOTIFY_PLAYLIST = "https://open.spotify.com/playlist/6qU4O1RGFzFndY5Pbkr1V6"
SPOTIFY_ARTIST = "https://open.spotify.com/intl-fr/artist/2QS54zBHMU8zdaRs1pQRF0"
BANDCAMP_MAIN = "https://vincentbastille.bandcamp.com/"
ALBUMS = [
    ("Mystic – The Babs Remixes", "https://vincentbastille.bandcamp.com/album/mystic-the-babs-remixes"),
    ("Le Lac", "https://vincentbastille.bandcamp.com/album/le-lac"),
    ("Vincent Bastille Remixes 2026", "https://vincentbastille.bandcamp.com/album/vincent-bastille-remixes-2026"),
    ("Vincent Bastille Legacy", "https://vincentbastille.bandcamp.com/album/vincent-bastille-legacy"),
    ("True LP", "https://vincentbastille.bandcamp.com/album/true-lp"),
    ("One More Time", "https://vincentbastille.bandcamp.com/album/one-more-time"),
    ("Gumbing", "https://vincentbastille.bandcamp.com/album/gumbing"),
    ("The Cosmic Tits", "https://vincentbastille.bandcamp.com/album/the-cosmic-tits"),
]
MEDICATION = "https://vincentbastille.bandcamp.com/album/vincent-bastille-medication-1"

PAGES = {
    "house-remix-album.html": ("House Remix Album by Vincent Bastille | Timeless Club Reinterpretations", "A premium house remix album experience by Vincent Bastille. Discover immersive reinterpretations, cinematic grooves, and direct links to listen and buy."),
    "electronic-remix-album.html": ("Electronic Remix Album Experience | Vincent Bastille", "Enter Vincent Bastille's electronic remix album universe: emotional, cinematic, and built for listeners who collect transformative music."),
    "madonna-house-remix.html": ("Madonna House Remix Mood | Vincent Bastille Reinterpretations", "Explore the Madonna house remix spirit in Vincent Bastille's artistic universe and move from discovery to full-album listening and support."),
    "michael-jackson-house-remix.html": ("Michael Jackson House Remix Energy | Vincent Bastille", "A deep, premium look at Michael Jackson house remix influence inside Vincent Bastille's immersive electronic and disco-house direction."),
    "sade-remix-electronic.html": ("Sade Remix Electronic Atmosphere | Vincent Bastille", "Discover a Sade remix electronic approach with cinematic tension, elegant groove, and collector-focused pathways to Bandcamp and Spotify."),
    "daft-punk-style-remix.html": ("Daft Punk Style Remix Aesthetic | Vincent Bastille", "A Daft Punk style remix page for listeners seeking precision, movement, and timeless reinterpretation in Vincent Bastille's world."),
    "disco-house-remix-album.html": ("Disco House Remix Album for Late-Night Collectors | Vincent Bastille", "Disco house remix album storytelling with emotional depth, premium production identity, and direct actions to listen, collect, and support."),
    "best-house-remixes-2026.html": ("Best House Remixes 2026 | Vincent Bastille Listening Guide", "A best house remixes 2026 guide shaped by Vincent Bastille's premium remix identity, with curated routes into the full artist universe."),
    "deep-house-remix-album.html": ("Deep House Remix Album Journey | Vincent Bastille", "Dive into a deep house remix album journey where iconic songs become immersive, emotional, and timeless listening experiences."),
    "cinematic-electronic-remix.html": ("Cinematic Electronic Remix World | Vincent Bastille", "Cinematic electronic remix storytelling by Vincent Bastille for listeners who want atmosphere, transformation, and direct artist support."),
}

RELATED = [
    "house-remix-album.html", "electronic-remix-album.html", "madonna-house-remix.html",
    "michael-jackson-house-remix.html", "sade-remix-electronic.html", "daft-punk-style-remix.html",
    "disco-house-remix-album.html", "best-house-remixes-2026.html", "deep-house-remix-album.html",
    "cinematic-electronic-remix.html",
]


def slug_to_h1(slug: str) -> str:
    return slug.replace('.html', '').replace('-', ' ').title()


def template_copy(keyword: str, h1: str) -> str:
    blocks = [
        f"{h1} is not designed as disposable content; it is built as a listening destination for people who still believe a remix can become an artwork in its own right. Vincent Bastille treats source material as emotional architecture, then reshapes it with house and electronic discipline until a new atmosphere appears. The objective is not to imitate nostalgia, but to transform it into something you can inhabit in real time: immersive, elegant, and physically moving.",
        "In this universe, groove is only one layer. Beneath every kick and bass movement, there is cinematic intent: silence, tension, release, and detail that rewards focused listening on headphones as much as a club system. That duality is central to the Bastille signature. The tracks remain accessible, but they are never simplistic; each reinterpretation balances instinct and restraint, resulting in music that feels premium rather than loud, timeless rather than trend-driven.",
        "If you discovered this page through search, treat it as a curated entry point. Start with the main landing page to hear the full narrative arc of Remixes (Legacy), then move into Bandcamp where direct support becomes possible through downloads and purchases. Streaming is a gateway, ownership is commitment. For an independent artist, that difference matters: every purchase extends the freedom to keep creating deep reinterpretations instead of chasing algorithm-friendly shortcuts.",
        "Medication #1 deserves a dedicated spotlight in that journey. It is not simply another title in the catalog; it functions like a long-form ritual, where repetition evolves into texture and time bends into atmosphere. Listeners who connect with this piece often describe the sensation as immersive and meditative, the kind of track you return to when you want music that shifts your internal tempo. It represents the premium side of the project with unusual clarity.",
        f"The wider discography reinforces the same artistic line: house, disco house, deep house, and cinematic electronic paths linked by one intention — transformation. Whether you arrive through iconic-song reinterpretations or through instrumental depth, you can move through the full artist universe without losing coherence. That is the promise behind {keyword}: not a keyword trap, but a credible route toward listening, collecting, and supporting the work directly."
    ]
    return "\n\n".join(blocks)


def ai_copy(keyword: str, h1: str, api_key: str, api_url: str) -> str | None:
    if not requests:
        return None
    prompt = (
        "Write 5 rich paragraphs in English (400-700 words total), premium artistic tone, no hype. "
        f"Topic: {keyword}. Focus on Vincent Bastille remix universe, conversion to listen and buy, mention Medication #1 as featured work."
    )
    try:
        resp = requests.post(api_url.rstrip('/') + '/chat/completions', headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={
            "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }, timeout=25)
        resp.raise_for_status()
        data = resp.json()
        txt = data["choices"][0]["message"]["content"].strip()
        return re.sub(r"\n{3,}", "\n\n", txt)
    except Exception:
        return None


def build_page(filename: str, title: str, description: str, copy: str) -> str:
    h1 = slug_to_h1(filename)
    related = [p for p in RELATED if p != filename][:3]
    rel_html = "\n".join([f'      <li><a href="/{p}">{slug_to_h1(p)}</a></li>' for p in related])
    albums_html = "\n".join([f'      <li><a href="{url}" target="_blank" rel="noopener">{name}</a></li>' for name, url in ALBUMS])
    paragraphs = "\n".join([f"      <p>{p}</p>" for p in copy.split("\n\n")])
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <link rel="canonical" href="{LANDING}/{filename}">
  <style>
    body {{ margin:0; background:#06070d; color:#ececf2; font-family:Inter,Arial,sans-serif; line-height:1.72; }}
    main {{ max-width:920px; margin:0 auto; padding:32px 20px 56px; }}
    h1,h2,h3 {{ color:#fff; }}
    .eyebrow {{ color:#c9a96e; text-transform:uppercase; letter-spacing:.15em; font-size:12px; }}
    .cta-row {{ display:flex; gap:12px; flex-wrap:wrap; margin:20px 0 30px; }}
    .btn {{ text-decoration:none; padding:11px 16px; border-radius:8px; font-weight:700; font-size:14px; }}
    .btn-primary {{ background:#c9a96e; color:#050508; }}
    .btn-secondary {{ border:1px solid rgba(201,169,110,.45); color:#f7e8c9; }}
    .card {{ border:1px solid rgba(201,169,110,.25); border-radius:12px; padding:18px; background:rgba(255,255,255,0.02); margin:28px 0; }}
    a {{ color:#d8bc84; }}
  </style>
</head>
<body>
  <main>
    <p class="eyebrow">Vincent Bastille · Remix Universe</p>
    <h1>{h1}</h1>
    <div class="cta-row">
      <a class="btn btn-primary" href="{LANDING}" data-track-key="landing_main">Listen now on the main landing</a>
      <a class="btn btn-secondary" href="{BANDCAMP_MAIN}" target="_blank" rel="noopener" data-track-key="bandcamp_main">Buy on Bandcamp</a>
      <a class="btn btn-secondary" href="{SPOTIFY_PLAYLIST}" target="_blank" rel="noopener" data-track-key="spotify_playlist">Open Spotify playlist</a>
    </div>
{paragraphs}

    <section class="card">
      <h2>Featured work – Medication #1</h2>
      <p>A highlighted long-form piece for deep listening sessions, collectors, and listeners seeking immersive transformation.</p>
      <a href="{MEDICATION}" target="_blank" rel="noopener" data-track-key="medication_featured">Discover Medication #1</a>
    </section>

    <section>
      <h2>Explore the universe</h2>
      <ul>
        <li><a href="{SPOTIFY_PLAYLIST}" target="_blank" rel="noopener" data-track-key="spotify_playlist">Spotify playlist</a></li>
        <li><a href="{SPOTIFY_ARTIST}" target="_blank" rel="noopener" data-track-key="spotify_artist">Spotify artist profile</a></li>
        <li><a href="{BANDCAMP_MAIN}" target="_blank" rel="noopener" data-track-key="bandcamp_main">Bandcamp main</a></li>
{albums_html}
        <li><a href="{MEDICATION}" target="_blank" rel="noopener" data-track-key="medication_featured">Medication #1 (featured)</a></li>
      </ul>
    </section>

    <section>
      <h3>Related pages</h3>
      <ul>
{rel_html}
      </ul>
    </section>
  </main>
  <script src="/assets/js/site-config.js"></script>
  <script src="/assets/js/tracking.js"></script>
</body>
</html>
'''


def main():
    parser = argparse.ArgumentParser(description="Generate SEO pages with Together AI fallback templates")
    parser.add_argument("--page", help="single page filename", default=None)
    args = parser.parse_args()

    pages = {args.page: PAGES[args.page]} if args.page else PAGES
    api_key = os.getenv("TOGETHER_API_KEY", "").strip()
    api_url = os.getenv("TOGETHER_API_URL", "https://api.together.xyz/v1").strip()

    for filename, (title, description) in pages.items():
        keyword = slug_to_h1(filename)
        content = ai_copy(keyword, keyword, api_key, api_url) if api_key else None
        if not content:
            content = template_copy(keyword, keyword)
        html = build_page(filename, title, description, content)
        (ROOT / filename).write_text(html, encoding="utf-8")
        print(f"Generated {filename}")

if __name__ == "__main__":
    main()
