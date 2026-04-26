import os
from datetime import datetime

# 🔧 CONFIG
BASE_URL = "https://remixes.vincentbastille.online/remixes"
FOLDER_PATH = "./remixes"   # ton dossier local
OUTPUT_FILE = "sitemap.xml"

def generate_sitemap():
    urls = []
    today = datetime.today().strftime('%Y-%m-%d')

    # 🔍 scan dossier
    for root, dirs, files in os.walk(FOLDER_PATH):
        for file in files:
            if file.endswith(".html"):
                full_path = os.path.join(root, file)

                # 👉 chemin relatif propre
                relative_path = os.path.relpath(full_path, FOLDER_PATH)
                relative_path = relative_path.replace("\\", "/")

                url = f"{BASE_URL}/{relative_path}"
                urls.append(url)

    # 🧱 construction sitemap
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for url in urls:
        sitemap.append("  <url>")
        sitemap.append(f"    <loc>{url}</loc>")
        sitemap.append(f"    <lastmod>{today}</lastmod>")
        sitemap.append("    <changefreq>weekly</changefreq>")
        sitemap.append("    <priority>0.7</priority>")
        sitemap.append("  </url>")

    sitemap.append("</urlset>")

    # 💾 write fichier
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sitemap))

    print(f"✅ Sitemap généré : {len(urls)} pages")

# 🚀 run
generate_sitemap()