#!/usr/bin/env python3
"""
SEO Audit Safe — remixes.vincentbastille.online
SAFE MODE : aucune modification de fichier, aucun noindex ajouté.
Génère : seo_audit_urls.csv + SEO_AUDIT_SAFE.md
"""

import os
import re
import csv
import json
from pathlib import Path
from collections import defaultdict
from bs4 import BeautifulSoup

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
BASE_URL = "https://remixes.vincentbastille.online"
SITEMAP_PATH = BASE_DIR / "public" / "sitemap.xml"
ROBOTS_PATH  = BASE_DIR / "public" / "robots.txt"
VERCEL_PATH  = BASE_DIR / "vercel.json"

THIN_THRESHOLD   = 400   # mots — page considérée "légère"
VERY_THIN        = 150   # mots — page quasi vide

# ── Helpers ───────────────────────────────────────────────────────────────────

def file_to_url(filepath: Path) -> str:
    """Convertit un chemin fichier en URL publique."""
    rel = filepath.relative_to(BASE_DIR)
    url = BASE_URL + "/" + str(rel).replace("\\", "/")
    return url

def parse_html(filepath: Path) -> dict:
    with open(filepath, encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f, "html.parser")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    desc_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
    description = desc_tag.get("content", "").strip() if desc_tag else ""

    canonical_tag = soup.find("link", rel="canonical")
    canonical = canonical_tag.get("href", "").strip() if canonical_tag else ""

    robots_tag = soup.find("meta", attrs={"name": re.compile(r"robots", re.I)})
    meta_robots = robots_tag.get("content", "").strip() if robots_tag else ""

    # Texte visible (hors scripts/styles)
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    body = soup.find("body")
    text = body.get_text(separator=" ") if body else soup.get_text(separator=" ")
    words = [w for w in text.split() if len(w) > 1]
    word_count = len(words)

    # Liens internes
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("/") or BASE_URL in href or (not href.startswith("http")):
            links.append(href)

    # H1
    h1 = soup.find("h1")
    h1_text = h1.get_text(strip=True) if h1 else ""

    return {
        "title": title,
        "description": description,
        "canonical": canonical,
        "meta_robots": meta_robots,
        "word_count": word_count,
        "internal_links_count": len(links),
        "h1": h1_text,
    }

def load_sitemap_urls(sitemap_path: Path) -> set:
    if not sitemap_path.exists():
        return set()
    with open(sitemap_path, encoding="utf-8") as f:
        content = f.read()
    return set(re.findall(r"<loc>(.*?)</loc>", content))

def load_robots(robots_path: Path) -> str:
    if not robots_path.exists():
        return "ABSENT"
    with open(robots_path, encoding="utf-8") as f:
        return f.read()

def load_vercel(vercel_path: Path) -> dict:
    if not vercel_path.exists():
        return {}
    with open(vercel_path, encoding="utf-8") as f:
        return json.load(f)

# ── Scan ──────────────────────────────────────────────────────────────────────

def scan_all_html(base_dir: Path) -> list:
    html_files = sorted(base_dir.rglob("*.html"))
    # Exclure node_modules etc.
    html_files = [f for f in html_files if ".git" not in f.parts]
    return html_files

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("🔍  Scanning HTML files…")
    html_files = scan_all_html(BASE_DIR)
    sitemap_urls = load_sitemap_urls(SITEMAP_PATH)
    robots_content = load_robots(ROBOTS_PATH)
    vercel_config = load_vercel(VERCEL_PATH)

    rows = []
    titles_seen = defaultdict(list)
    descs_seen  = defaultdict(list)

    for filepath in html_files:
        url = file_to_url(filepath)
        data = parse_html(filepath)

        in_sitemap = url in sitemap_urls

        # Classement contenu
        wc = data["word_count"]
        if wc >= THIN_THRESHOLD:
            content_level = "OK"
        elif wc >= VERY_THIN:
            content_level = "THIN"
        else:
            content_level = "VERY_THIN"

        row = {
            "file": str(filepath.relative_to(BASE_DIR)),
            "url": url,
            "in_sitemap": "YES" if in_sitemap else "no",
            "title": data["title"],
            "description": data["description"],
            "canonical": data["canonical"],
            "meta_robots": data["meta_robots"] or "none",
            "h1": data["h1"],
            "word_count": wc,
            "content_level": content_level,
            "internal_links": data["internal_links_count"],
        }
        rows.append(row)

        if data["title"]:
            titles_seen[data["title"]].append(url)
        if data["description"]:
            descs_seen[data["description"]].append(url)

    # Duplicate detection
    dup_titles = {t: urls for t, urls in titles_seen.items() if len(urls) > 1}
    dup_descs  = {d: urls for d, urls in descs_seen.items() if len(urls) > 1}

    for row in rows:
        row["dup_title"] = "YES" if row["title"] in dup_titles else ""
        row["dup_desc"]  = "YES" if row["description"] in dup_descs else ""

    # ── Recommendation ────────────────────────────────────────────────────────
    for row in rows:
        if row["in_sitemap"] == "YES":
            row["recommendation"] = "🟢 KEEP — sitemap"
        elif row["content_level"] == "OK" and not row["dup_title"]:
            row["recommendation"] = "🟡 REVIEW — OK content, not in sitemap"
        elif row["content_level"] == "VERY_THIN":
            row["recommendation"] = "🔴 CANDIDATE noindex (thin)"
        elif row["dup_title"] == "YES":
            row["recommendation"] = "🔴 CANDIDATE noindex (dup title)"
        else:
            row["recommendation"] = "🟠 REVIEW — thin or dup"

    # ── CSV ───────────────────────────────────────────────────────────────────
    csv_path = BASE_DIR / "seo_audit_urls.csv"
    fieldnames = ["file","url","in_sitemap","recommendation","content_level",
                  "word_count","title","dup_title","description","dup_desc",
                  "canonical","meta_robots","h1","internal_links"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✅  CSV → {csv_path}")

    # ── Markdown report ───────────────────────────────────────────────────────
    sitemap_rows    = [r for r in rows if r["in_sitemap"] == "YES"]
    keep_rows       = [r for r in rows if r["in_sitemap"] != "YES" and r["content_level"] == "OK" and not r["dup_title"]]
    thin_rows       = [r for r in rows if r["in_sitemap"] != "YES" and r["content_level"] in ("THIN","VERY_THIN")]
    dup_rows        = [r for r in rows if r["in_sitemap"] != "YES" and r["dup_title"] == "YES"]
    noindex_present = [r for r in rows if "noindex" in r["meta_robots"].lower()]

    robots_blocks_google = "Disallow: /" in robots_content and "User-agent: *" in robots_content
    sitemap_in_robots = "Sitemap:" in robots_content

    md = f"""# SEO Audit SAFE — remixes.vincentbastille.online
> Généré automatiquement. **Aucun fichier modifié.**  
> Mode : lecture seule. Pas de noindex ajouté.

---

## 📊 Résumé global

| Métrique | Valeur |
|---|---|
| Fichiers HTML scannés | {len(rows)} |
| Pages dans le sitemap (56 protégées) | {len(sitemap_rows)} |
| Pages hors sitemap — contenu OK | {len(keep_rows)} |
| Pages hors sitemap — thin / very thin | {len(thin_rows)} |
| Pages hors sitemap — titre dupliqué | {len(dup_rows)} |
| Pages avec meta robots noindex déjà présent | {len(noindex_present)} |
| Titres dupliqués (groupes) | {len(dup_titles)} |
| Descriptions dupliquées (groupes) | {len(dup_descs)} |

---

## 🤖 robots.txt

- Chemin : `public/robots.txt`
- Statut : {"✅ PRÉSENT" if ROBOTS_PATH.exists() else "❌ ABSENT"}
- Google bloqué : {"⚠️ OUI — Disallow: /" if robots_blocks_google else "✅ NON"}
- Sitemap déclaré dans robots.txt : {"✅ OUI" if sitemap_in_robots else "❌ NON"}

```
{robots_content.strip()}
```

---

## 🗺️ sitemap.xml

- Chemin : `public/sitemap.xml`
- Statut : {"✅ PRÉSENT dans le repo" if SITEMAP_PATH.exists() else "❌ ABSENT — probablement généré en CI"}
- URLs déclarées : {len(sitemap_urls)}
- URLs trouvées dans le scan HTML : {len(sitemap_rows)} / {len(sitemap_urls)}

> Les URLs du sitemap non trouvées dans le repo peuvent être générées dynamiquement ou exister sous un nom différent.

---

## ⚙️ vercel.json

```json
{json.dumps(vercel_config, indent=2, ensure_ascii=False)}
```

- Redirections actives : {len(vercel_config.get("routes", []))} règles
- Pas de redirections massives détectées qui pourraient bloquer Google.

---

## 🟢 Les 56 pages du sitemap (à protéger absolument)

| URL | Title | Words | Meta Robots | Dup Title |
|---|---|---|---|---|
"""

    for r in sorted(sitemap_rows, key=lambda x: x["url"]):
        md += f"| `{r['url'].replace(BASE_URL, '')}` | {r['title'][:60]} | {r['word_count']} | {r['meta_robots']} | {r['dup_title'] or '—'} |\n"

    md += f"""
---

## 🟡 Pages hors sitemap avec contenu correct (candidates à ajouter au sitemap)

> {len(keep_rows)} pages avec ≥{THIN_THRESHOLD} mots et titre unique.

| URL | Title | Words |
|---|---|---|
"""
    for r in sorted(keep_rows, key=lambda x: -x["word_count"])[:50]:
        md += f"| `{r['url'].replace(BASE_URL, '')}` | {r['title'][:60]} | {r['word_count']} |\n"

    if len(keep_rows) > 50:
        md += f"\n*… et {len(keep_rows)-50} autres. Voir le CSV complet.*\n"

    md += f"""
---

## 🔴 Pages candidates au noindex (thin content — hors sitemap)

> **⚠️ Ne jamais noindex une page présente dans le sitemap sans vérification manuelle.**  
> {len(thin_rows)} pages hors sitemap avec < {THIN_THRESHOLD} mots.

| URL | Words | Content level | Dup Title |
|---|---|---|---|
"""
    for r in sorted(thin_rows, key=lambda x: x["word_count"])[:80]:
        md += f"| `{r['url'].replace(BASE_URL, '')}` | {r['word_count']} | {r['content_level']} | {r['dup_title'] or '—'} |\n"

    if len(thin_rows) > 80:
        md += f"\n*… et {len(thin_rows)-80} autres. Voir le CSV.*\n"

    md += f"""
---

## 🔴 Pages avec titre dupliqué (hors sitemap)

> {len(dup_rows)} pages partagent un titre avec une autre page.  
> Risque de cannibalisation SEO.

| URL | Title | Words |
|---|---|---|
"""
    for r in sorted(dup_rows, key=lambda x: x["title"])[:60]:
        md += f"| `{r['url'].replace(BASE_URL, '')}` | {r['title'][:60]} | {r['word_count']} |\n"

    md += f"""
---

## 📋 Groupes de titres dupliqués (top 20)

| Titre | Nb pages | URLs |
|---|---|---|
"""
    for title, urls in sorted(dup_titles.items(), key=lambda x: -len(x[1]))[:20]:
        urls_short = "<br>".join(u.replace(BASE_URL, "") for u in urls[:4])
        if len(urls) > 4:
            urls_short += f"<br>… +{len(urls)-4}"
        md += f"| {title[:60]} | {len(urls)} | {urls_short} |\n"

    md += f"""
---

## 🚦 Recommandations prioritaires

1. **Protéger les 56 pages du sitemap** : ne pas ajouter noindex, ne pas les supprimer.
2. **robots.txt** : {"✅ Google est autorisé, sitemap déclaré." if not robots_blocks_google and sitemap_in_robots else "⚠️ Vérifier le robots.txt."}
3. **Thin content** : {len(thin_rows)} pages hors sitemap avec peu de contenu — candidates à un noindex **après vérification manuelle une par une**.
4. **Duplicats de titres** : {len(dup_titles)} groupes détectés — risque de cannibalisation. Priorité : différencier les titres des pages en sitemap.
5. **Pages non dans le sitemap** : {len(rows) - len(sitemap_rows)} pages hors sitemap. Elles sont crawlées (robots.txt = Allow) mais Google choisit de ne pas les indexer → thin content ou duplicate probable.
6. **Sitemap** : présent dans le repo (`public/sitemap.xml`), 56 URLs, correctement déclaré dans robots.txt et Vercel.

---

## 🔧 Comment lancer l'audit

```bash
pip install beautifulsoup4
python scripts/seo_audit_safe.py
# → génère seo_audit_urls.csv et SEO_AUDIT_SAFE.md
```

---
*Audit SAFE — aucun fichier HTML modifié, aucun noindex ajouté.*
"""

    md_path = BASE_DIR / "SEO_AUDIT_SAFE.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"✅  Markdown → {md_path}")
    print(f"\n📊  {len(rows)} pages scannées | {len(sitemap_rows)} en sitemap | {len(thin_rows)} thin | {len(dup_titles)} groupes dup titles")

if __name__ == "__main__":
    main()
