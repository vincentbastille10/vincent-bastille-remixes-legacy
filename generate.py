#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape

try:
    from anthropic import Anthropic
except Exception:  # anthropic is optional at runtime
    Anthropic = None

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "pages.json"
TEMPLATE_FILE = "page.html.jinja"
TEMPLATE_DIR = ROOT / "templates"
SITE_URL = "https://remixes.vincentbastille.online"
CTA_URL = "https://remixes.vincentbastille.online/"


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


def fallback_paragraphs(page: Page, idx: int) -> list[str]:
    moods = [
        "neon-lit tension and late-night momentum",
        "sunrise warmth with deep low-end patience",
        "festival-scale impact with collector-level details",
        "minimal textures that leave room for emotion",
        "cinematic contrast between silence and release",
    ]
    focus = [
        "arrangement choices",
        "groove architecture",
        "vocal space and phrasing",
        "harmonic movement",
        "club-to-headphones translation",
    ]
    mood = moods[idx % len(moods)]
    craft = focus[(idx * 2) % len(focus)]

    return [
        (
            f"{heading_from_slug(page.slug)} is built for listeners who want more than a quick playlist pass. "
            f"This page frames {page.keyword} as a living dancefloor narrative with {mood}, where every transition "
            "feels intentional rather than accidental."
        ),
        (
            "Vincent Bastille approaches remixes like a producer and a storyteller at once. "
            f"The emphasis here is on {craft}: tiny production moves, controlled dynamics, and hooks that stay human "
            "instead of becoming over-processed wallpaper."
        ),
        (
            f"If {page.keyword} brought you here, follow the descriptive links below to branch into related styles. "
            "Each one maps a different angle—underground pressure, melodic lift, or cinematic detail—without breaking "
            "the broader artistic identity."
        ),
        (
            "Most importantly, this project is designed for direct artist support. "
            "The call-to-action always points to the main catalog so you can listen, choose favorites, and come back "
            "whenever you need fresh remix energy."
        ),
    ]


def ai_paragraphs(page: Page, client: Anthropic | None, model: str) -> list[str] | None:
    if client is None:
        return None

    prompt = (
        "Write exactly 4 unique paragraphs in English for a static remix landing page. "
        "Tone: passionate music expert, natural, not robotic, no keyword stuffing. "
        "Mention Vincent Bastille once. Mention the phrase '"
        + page.keyword
        + "' naturally once. Avoid markdown."
    )
    try:
        message = client.messages.create(
            model=model,
            max_tokens=900,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}],
        )
        text_blocks = [b.text for b in message.content if getattr(b, "type", "") == "text"]
        raw = "\n".join(text_blocks).strip()
        parts = [p.strip().replace("\n", " ") for p in raw.split("\n\n") if p.strip()]
        if len(parts) >= 4:
            return parts[:4]
    except Exception:
        return None
    return None


def related_links(all_pages: list[Page], current: Page, count: int = 4) -> list[dict[str, str]]:
    start = all_pages.index(current)
    picks = []
    for step in range(1, len(all_pages)):
        if len(picks) >= count:
            break
        candidate = all_pages[(start + step) % len(all_pages)]
        picks.append(
            {
                "slug": candidate.slug,
                "anchor": f"Explore {heading_from_slug(candidate.slug)} remix analysis",
            }
        )
    return picks


def schema_for(page: Page) -> str:
    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": page.title,
        "description": page.description,
        "url": f"{SITE_URL}/{page.slug}.html",
        "about": {
            "@type": "MusicAlbum",
            "name": "Vincent Bastille Remixes (Legacy)",
            "byArtist": {"@type": "MusicGroup", "name": "Vincent Bastille"},
            "genre": ["House", "Electronic", "Remix"],
        },
    }
    return json.dumps(schema, ensure_ascii=False)


def render_pages(selected_slug: str | None = None) -> list[Path]:
    load_dotenv()
    pages = load_pages()
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(TEMPLATE_FILE)

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest").strip()
    client = Anthropic(api_key=api_key) if (api_key and Anthropic) else None

    targets: Iterable[Page] = pages
    if selected_slug:
        targets = [p for p in pages if p.slug == selected_slug]
        if not targets:
            raise ValueError(f"Unknown slug: {selected_slug}")

    written = []
    for idx, page in enumerate(targets):
        paragraphs = ai_paragraphs(page, client, model) or fallback_paragraphs(page, idx)
        html = template.render(
            page=page,
            heading=heading_from_slug(page.slug),
            paragraphs=paragraphs,
            related=related_links(pages, page),
            cta_url=CTA_URL,
            site_url=SITE_URL,
            schema_json=schema_for(page),
        )
        output = ROOT / f"{page.slug}.html"
        output.write_text(html, encoding="utf-8")
        written.append(output)
        print(f"Generated {output.name}")

    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate static remix landing pages")
    parser.add_argument("--slug", help="Generate only one slug", default=None)
    args = parser.parse_args()
    render_pages(selected_slug=args.slug)


if __name__ == "__main__":
    main()
