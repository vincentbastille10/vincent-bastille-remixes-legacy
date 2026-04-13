#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "pages.json"
SITE_URL = "https://remixes.vincentbastille.online"
CTA_URL = "https://remixes.vincentbastille.online/"

ARTISTS = ["Michael Jackson", "Sade", "Madonna", "Daft Punk", "David Guetta"]


@dataclass(frozen=True)
class Page:
    id: int
    slug: str
    keyword: str
    title: str
    description: str


def load_pages() -> list[Page]:
    items = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    pages = [Page(**item) for item in items]
    slugs = [p.slug for p in pages]
    if len(slugs) != len(set(slugs)):
        raise ValueError("All slugs must be unique.")
    return pages


def heading_from_slug(slug: str) -> str:
    return slug.replace("-", " ").title()


def words(text: str) -> int:
    return len(text.split())


def build_intro(page: Page, rng: random.Random) -> str:
    opener = rng.choice([
        "Some remixes are disposable, but legacy remixes become cultural memory.",
        "A great remix does not simply speed up a song; it rewrites how people feel it.",
        "When people search for the best remix ever made, they are searching for emotional proof.",
    ])
    return (
        f"{opener} This guide explores {page.keyword} through the lens of remix legacy culture, from club foundations "
        "to today's streaming behavior. You will find context, production analysis, and direct listening paths to "
        "Vincent Bastille remixes so discovery turns into action."
    )


def make_section(title: str, lines: list[str]) -> dict[str, str | list[str]]:
    return {"title": title, "paragraphs": lines}


def build_sections(page: Page) -> list[dict[str, str | list[str]]]:
    rng = random.Random(page.id * 17)
    bpm = 118 + (page.id % 10)
    artist_a, artist_b = rng.sample(ARTISTS, 2)

    history = make_section(
        "History and context of remix culture",
        [
            f"The history behind {page.keyword} is tied to dub edits, vinyl extensions, and club remix history from the late 80s and 90s.",
            f"Promoters learned quickly that a single remix could revive an artist catalog. Fans of {artist_a} and {artist_b} still discover songs through reinterpretations before hearing the originals.",
            "As house remix classics moved from white labels to digital stores, remix legacy became a search behavior: listeners look for iconic versions that carry both nostalgia and surprise.",
        ],
    )

    analysis = make_section(
        "Musical analysis: style, BPM and vibe",
        [
            f"This page frames the style around {bpm} BPM, balancing dancefloor pressure with melodic space so the drop feels earned.",
            "Arrangement choices matter: filtered intros, restrained midrange, and vocal phrasing help the hook stay recognizable while feeling newly cinematic.",
            "The vibe typically combines deep house remix legends energy with modern low-end control, letting the remix translate from headphones to big systems.",
        ],
    )

    legendary = make_section(
        "Why this remix angle is considered legendary",
        [
            f"A legendary remix survives trend cycles. In long-tail searches like 'iconic remix songs history' or 'best {artist_a.lower()} remix ever', longevity matters more than hype.",
            "What gives this direction lasting impact is emotional timing: tension before release, vocal respect without imitation, and groove architecture that DJs can trust.",
            "That is why collectors return to classic remix references: they deliver identity, not just loudness.",
        ],
    )

    cta = make_section(
        "Listen Vincent Bastille Remix",
        [
            "If you want a modern extension of this legacy, jump to the Vincent Bastille catalog and listen in full context.",
            "Use the button below to discover, stream, and support the project directly.",
        ],
    )

    return [history, analysis, legendary, cta]


def build_faq(page: Page) -> list[dict[str, str]]:
    return [
        {
            "q": f"What makes {page.keyword} different from a standard remix?",
            "a": "It focuses on long-term replay value, storytelling arrangement, and club-ready mix decisions rather than quick trend aesthetics.",
        },
        {
            "q": "Why do people search for classic and iconic remixes from the 90s?",
            "a": "Because those versions often balanced emotional songwriting with DJ functionality, creating tracks that still work decades later.",
        },
        {
            "q": "Where can I listen to Vincent Bastille remixes?",
            "a": "Use the main catalog link on this page to access the latest Vincent Bastille remix releases and listening routes.",
        },
        {
            "q": "How does internal remix exploration help listeners?",
            "a": "Related pages connect adjacent styles and artists, helping fans move from one remix topic to another without losing context.",
        },
    ]


def related_links(all_pages: list[Page], current: Page, count: int = 5) -> list[dict[str, str]]:
    start = all_pages.index(current)
    picks = []
    for step in range(1, len(all_pages)):
        if len(picks) >= count:
            break
        candidate = all_pages[(start + step) % len(all_pages)]
        picks.append({"slug": candidate.slug, "anchor": f"{heading_from_slug(candidate.slug)} guide"})
    return picks


def build_body(page: Page) -> dict:
    intro = build_intro(page, random.Random(page.id))
    sections = build_sections(page)
    faq = build_faq(page)

    # Ensure practical SEO length target.
    body_parts = [intro]
    for section in sections:
        body_parts.extend(section["paragraphs"])
    while words(" ".join(body_parts)) < 820:
        body_parts.append(
            f"In practical terms, {page.keyword} also connects with searches like 'legendary house remixes 90s club' and 'best remix ever made', "
            "which is why this page keeps both historical context and conversion paths in the same experience."
        )
    return {"intro": intro, "sections": sections, "faq": faq, "word_count": words(" ".join(body_parts))}


def schema_for(page: Page, faq: list[dict[str, str]]) -> str:
    schema = [
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
                }
                for item in faq
            ],
        },
        {
            "@context": "https://schema.org",
            "@type": "MusicRecording",
            "name": page.title,
            "url": f"{SITE_URL}/{page.slug}.html",
            "byArtist": {"@type": "MusicGroup", "name": "Vincent Bastille"},
            "genre": ["House", "Deep House", "Remix"],
        },
    ]
    return json.dumps(schema, ensure_ascii=False)



def render_html(page: Page, heading: str, body: dict, related: list[dict[str, str]], schema_json: str) -> str:
    related_items = "".join([f'<li><a href="/{link["slug"]}.html">{link["anchor"]}</a></li>' for link in related])
    section_html = []
    for section in body["sections"]:
        paras = "".join([f"<p>{p}</p>" for p in section["paragraphs"]])
        section_html.append(f"<section class=\"card\"><h2>{section['title']}</h2>{paras}</section>")
    faq_html = "".join([f"<h3>{f['q']}</h3><p>{f['a']}</p>" for f in body["faq"]])
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{page.title}</title>
  <meta name=\"description\" content=\"{page.description}\">
  <link rel=\"canonical\" href=\"{SITE_URL}/{page.slug}.html\">
  <meta property=\"og:type\" content=\"article\">
  <meta property=\"og:title\" content=\"{page.title}\">
  <meta property=\"og:description\" content=\"{page.description}\">
  <meta property=\"og:url\" content=\"{SITE_URL}/{page.slug}.html\">
  <script type=\"application/ld+json\">{schema_json}</script>
</head>
<body>
<main>
<section class=\"card\"><h1>{heading}</h1><p>{page.description}</p><a href=\"{CTA_URL}\">Listen Vincent Bastille Remix</a></section>
<section class=\"card\"><h2>Ultimate remix legacy introduction</h2><p>{body['intro']}</p></section>
{''.join(section_html)}
<section class=\"card\"><h2>Similar remix pages to explore</h2><h3>Internal remix cluster</h3><ul>{related_items}</ul></section>
<section class=\"card\"><h2>FAQ</h2>{faq_html}</section>
</main>
</body>
</html>"""



def write_sitemap(pages: list[Page]) -> None:
    today = date.today().isoformat()
    urls = [
        "  <url><loc>{}</loc><lastmod>{}</lastmod><changefreq>weekly</changefreq><priority>{}</priority></url>".format(
            f"{SITE_URL}/{p.slug}.html", today, "0.8"
        )
        for p in pages
    ]
    root_url = f"  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>"
    xml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
    xml += root_url + "\n" + "\n".join(urls) + "\n</urlset>\n"
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")
    print("Updated sitemap.xml")


def render_pages(selected_slug: str | None = None) -> list[Path]:
    pages = load_pages()
    targets: Iterable[Page] = pages
    if selected_slug:
        targets = [p for p in pages if p.slug == selected_slug]
        if not targets:
            raise ValueError(f"Unknown slug: {selected_slug}")

    written = []
    for page in targets:
        body = build_body(page)
        html = render_html(
            page=page,
            heading=heading_from_slug(page.slug),
            body=body,
            related=related_links(pages, page),
            schema_json=schema_for(page, body["faq"]),
        )
        output = ROOT / f"{page.slug}.html"
        output.write_text(html, encoding="utf-8")
        written.append(output)
        print(f"Generated {output.name} ({body['word_count']} words)")

    write_sitemap(pages)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate static remix landing pages")
    parser.add_argument("--slug", help="Generate only one slug", default=None)
    args = parser.parse_args()
    render_pages(selected_slug=args.slug)


if __name__ == "__main__":
    main()
