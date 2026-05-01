#!/usr/bin/env python3
"""
fix_root_urls.py
Corrige canonical, og:url, twitter:url dans tous les fichiers /remixes/*.html
et nettoie les sitemaps.

URL publique = https://remixes.vincentbastille.online/NOM_FICHIER.html
(pas de /remixes/ dans l'URL finale)
"""

import re
import sys
from pathlib import Path

BASE_URL = "https://remixes.vincentbastille.online"
REPO_ROOT = Path(__file__).parent.parent
REMIXES_DIR = REPO_ROOT / "remixes"

# Patterns de mauvais préfixes à corriger globalement dans tout le fichier
BAD_PREFIXES = [
    f"{BASE_URL}/remixes/",
    f"{BASE_URL}/seo-pages/",
    f"{BASE_URL}https://{BASE_URL.replace('https://', '')}/",  # domaine doublé
    f"{BASE_URL}{BASE_URL}/",  # variante doublon
]

DOUBLE_DOMAIN = re.compile(
    r'https://remixes\.vincentbastille\.online(?:https?://remixes\.vincentbastille\.online)+/'
)

def correct_url(filename: str) -> str:
    return f"{BASE_URL}/{filename}"

def fix_tag(content: str, pattern: str, replacement: str) -> str:
    """Remplace la valeur d'un attribut href/content dans un tag spécifique."""
    return re.sub(pattern, replacement, content)

def fix_file(filepath: Path) -> bool:
    filename = filepath.name  # ex: deep-house-remix.html
    target_url = correct_url(filename)

    original = filepath.read_text(encoding="utf-8", errors="ignore")
    text = original

    # ── 1. Corriger les mauvais préfixes globalement ───────────────────────
    for bad in BAD_PREFIXES:
        text = text.replace(bad, f"{BASE_URL}/")

    # ── 2. Corriger domaines doublés ───────────────────────────────────────
    text = DOUBLE_DOMAIN.sub(f"{BASE_URL}/", text)

    # ── 3. Forcer canonical ────────────────────────────────────────────────
    # Remplace n'importe quelle valeur existante dans rel="canonical"
    canonical_pattern = r'(<link\s+rel=["\']canonical["\']\s+href=["\'])([^"\']*?)(["\'])'
    if re.search(canonical_pattern, text):
        text = re.sub(canonical_pattern, rf'\g<1>{target_url}\g<3>', text)
    else:
        # Injecter après <head>
        text = text.replace('<head>', f'<head>\n  <link rel="canonical" href="{target_url}">', 1)

    # Variante attributs inversés
    canonical_pattern2 = r'(<link\s+href=["\'])([^"\']*?)(["\'](\s+)rel=["\']canonical["\'])'
    text = re.sub(canonical_pattern2, rf'\g<1>{target_url}\g<3>', text)

    # ── 4. Forcer og:url ───────────────────────────────────────────────────
    ogurl_pattern = r'(<meta\s+property=["\']og:url["\']\s+content=["\'])([^"\']*?)(["\'])'
    if re.search(ogurl_pattern, text):
        text = re.sub(ogurl_pattern, rf'\g<1>{target_url}\g<3>', text)
    else:
        ogurl_pattern2 = r'(<meta\s+content=["\'])([^"\']*?)(["\'](\s+)property=["\']og:url["\'])'
        if re.search(ogurl_pattern2, text):
            text = re.sub(ogurl_pattern2, rf'\g<1>{target_url}\g<3>', text)

    # ── 5. Forcer twitter:url ──────────────────────────────────────────────
    tw_pattern = r'(<meta\s+name=["\']twitter:url["\']\s+content=["\'])([^"\']*?)(["\'])'
    text = re.sub(tw_pattern, rf'\g<1>{target_url}\g<3>', text)

    # ── 6. Écrire si modifié ───────────────────────────────────────────────
    if text != original:
        filepath.write_text(text, encoding="utf-8")
        return True
    return False

def fix_sitemap(sitemap_path: Path) -> bool:
    if not sitemap_path.exists():
        return False
    original = sitemap_path.read_text(encoding="utf-8", errors="ignore")
    text = original
    for bad in BAD_PREFIXES:
        text = text.replace(bad, f"{BASE_URL}/")
    text = DOUBLE_DOMAIN.sub(f"{BASE_URL}/", text)
    if text != original:
        sitemap_path.write_text(text, encoding="utf-8")
        return True
    return False

def verify_file(filepath: Path) -> bool:
    filename = filepath.name
    target_url = correct_url(filename)
    content = filepath.read_text(encoding="utf-8", errors="ignore")
    has_canonical = f'rel="canonical" href="{target_url}"' in content or \
                    f"rel='canonical' href='{target_url}'" in content
    has_ogurl = f'og:url" content="{target_url}"' in content or \
                f"og:url' content='{target_url}'" in content
    return has_canonical and has_ogurl

def main():
    html_files = sorted(REMIXES_DIR.glob("*.html"))
    if not html_files:
        print("❌ Aucun fichier HTML trouvé dans /remixes")
        sys.exit(1)

    print(f"🔍 {len(html_files)} fichiers HTML dans /remixes\n")

    modified = []
    for fp in html_files:
        changed = fix_file(fp)
        if changed:
            modified.append(fp)
            print(f"  ✅ modifié : {fp.relative_to(REPO_ROOT)}")

    # Sitemaps
    sitemap_paths = [
        REPO_ROOT / "sitemap.xml",
        REPO_ROOT / "public" / "sitemap.xml",
        REMIXES_DIR / "sitemap.xml",
    ]
    for sp in sitemap_paths:
        if fix_sitemap(sp):
            print(f"  ✅ sitemap modifié : {sp.relative_to(REPO_ROOT)}")

    print(f"\n📊 {len(modified)} fichiers HTML modifiés sur {len(html_files)}")

    # ── Vérification finale sur deep-house-remix.html ─────────────────────
    test_file = REMIXES_DIR / "deep-house-remix.html"
    if test_file.exists():
        target_url = correct_url(test_file.name)
        content = test_file.read_text(encoding="utf-8", errors="ignore")

        ok_canonical = f'rel="canonical" href="{target_url}"' in content
        ok_ogurl = f'og:url" content="{target_url}"' in content

        print(f"\n🔎 Vérification finale : {test_file.name}")
        print(f"   canonical → {'✅ OK' if ok_canonical else '❌ MANQUANT ou FAUX'}")
        print(f"   og:url    → {'✅ OK' if ok_ogurl else '❌ MANQUANT ou FAUX'}")

        if not ok_canonical or not ok_ogurl:
            # Affiche les lignes concernées pour debug
            for i, line in enumerate(content.splitlines(), 1):
                if "canonical" in line or "og:url" in line:
                    print(f"   ligne {i}: {line.strip()}")
            print("\n❌ ÉCHEC : les balises ne correspondent pas à l'URL attendue.")
            print(f"   Attendu canonical : {target_url}")
            sys.exit(1)
        else:
            print(f"\n✅ SUCCÈS : deep-house-remix.html est correct.")
    else:
        print("⚠️  deep-house-remix.html introuvable — vérification ignorée.")

    print("\n🎉 Tous les fichiers sont corrects.")

if __name__ == "__main__":
    main()
