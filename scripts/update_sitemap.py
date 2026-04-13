#!/usr/bin/env python3
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://remixes.vincentbastille.online"

PAGES = [
    "",
    "house-remix-album.html",
    "electronic-remix-album.html",
    "madonna-house-remix.html",
    "michael-jackson-house-remix.html",
    "sade-remix-electronic.html",
    "daft-punk-style-remix.html",
    "disco-house-remix-album.html",
    "best-house-remixes-2026.html",
    "deep-house-remix-album.html",
    "cinematic-electronic-remix.html",
]

def main():
    today = date.today().isoformat()
    items = []
    for p in PAGES:
        loc = SITE_URL + ("/" + p if p else "/")
        items.append(f"  <url><loc>{loc}</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>{'1.0' if p == '' else '0.8'}</priority></url>")
    xml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n" + "\n".join(items) + "\n</urlset>\n"
    (ROOT / "sitemap.xml").write_text(xml, encoding="utf-8")
    print("Updated sitemap.xml")

if __name__ == "__main__":
    main()
