from pathlib import Path
from datetime import date
import html

BASE_URL = "https://remixes.vincentbastille.online"

SEO_DIRS = [
    Path("SEO"),
    Path("seo-pages"),
]

EXCLUDE_NAMES = {
    "404.html",
}

def should_include(path: Path) -> bool:
    name = path.name.lower()

    if name in EXCLUDE_NAMES:
        return False

    if name.startswith("google") and name.endswith(".html"):
        return False

    return path.suffix.lower() == ".html"

def main():
    today = date.today().isoformat()
    urls = []

    # Homepage
    urls.append(("/", "1.0", "daily"))

    seen = {"/"}

    for folder in SEO_DIRS:
        if not folder.exists():
            continue

        for file in sorted(folder.glob("*.html")):
            if not should_include(file):
                continue

            url_path = "/" + str(file).replace("\\", "/")

            if url_path in seen:
                continue

            seen.add(url_path)
            urls.append((url_path, "0.8", "weekly"))

    sitemap_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]

    for path, priority, changefreq in urls:
        loc = html.escape(BASE_URL + path)
        sitemap_lines.append("  <url>")
        sitemap_lines.append(f"    <loc>{loc}</loc>")
        sitemap_lines.append(f"    <lastmod>{today}</lastmod>")
        sitemap_lines.append(f"    <changefreq>{changefreq}</changefreq>")
        sitemap_lines.append(f"    <priority>{priority}</priority>")
        sitemap_lines.append("  </url>")

    sitemap_lines.append("</urlset>")

    Path("sitemap.xml").write_text("\n".join(sitemap_lines) + "\n", encoding="utf-8")

    print(f"✅ sitemap.xml généré")
    print(f"✅ URLs déclarées : {len(urls)}")
    print("✅ Dossiers inclus : /SEO/ et /seo-pages/")
    print("✅ Doublons évités")
    print("✅ Fichiers google*.html exclus")

if __name__ == "__main__":
    main()
