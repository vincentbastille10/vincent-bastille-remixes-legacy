import os
import shutil
from pathlib import Path
from datetime import datetime

BASE_URL = "https://remixes.vincentbastille.online"
SEO_DIR = Path("SEO")
ROOT = Path(".")

# --- CONFIG ---
EXCLUDE = {"index.html", "404.html"}

# --- CREATE SEO DIR ---
SEO_DIR.mkdir(exist_ok=True)

# --- STEP 1: MOVE HTML FILES ---
print("📦 Moving HTML files to /SEO ...")

moved_files = []

for file in ROOT.glob("*.html"):
    if file.name in EXCLUDE:
        continue

    target = SEO_DIR / file.name

    shutil.move(str(file), str(target))
    moved_files.append(file.name)

print(f"✅ Moved {len(moved_files)} files")

# --- STEP 2: COLLECT ALL SEO FILES ---
print("🔍 Scanning SEO folder...")

html_files = list(SEO_DIR.glob("*.html"))

print(f"📄 Total SEO pages: {len(html_files)}")

# --- STEP 3: GENERATE SITEMAP ---
print("🧠 Generating sitemap.xml ...")

today = datetime.utcnow().strftime("%Y-%m-%d")

urls = []

# homepage
urls.append(f"""
  <url>
    <loc>{BASE_URL}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
""")

# SEO pages
for file in html_files:
    url = f"{BASE_URL}/SEO/{file.name}"

    urls.append(f"""
  <url>
    <loc>{url}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
""")

sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{''.join(urls)}
</urlset>
"""

with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write(sitemap)

print("✅ sitemap.xml updated")

# --- STEP 4: REPORT ---
print("\n📊 REPORT")
print(f"Moved files: {len(moved_files)}")
print(f"SEO pages: {len(html_files)}")
