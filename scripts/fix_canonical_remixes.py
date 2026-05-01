import os
import re

BASE_DIR = "remixes"
OLD_DOMAIN = "https://vincent-bastille-remixes-legacy.vercel.app"
NEW_DOMAIN = "https://remixes.vincentbastille.online"

def fix_canonical(content, filename):
    # remplace uniquement le canonical
    pattern = r'<link\s+rel="canonical"\s+href="([^"]+)"\s*/?>'
    
    def replace(match):
        old_url = match.group(1)

        # garde le path
        path = old_url.replace(OLD_DOMAIN, "")
        new_url = NEW_DOMAIN + path

        return f'<link rel="canonical" href="{new_url}">'

    new_content, count = re.subn(pattern, replace, content)

    return new_content, count

def process_files():
    total_modified = 0

    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(root, file)

                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                new_content, count = fix_canonical(content, file)

                if count > 0:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)

                    print(f"✔ Updated: {filepath}")
                    total_modified += 1

    print(f"\n🔥 Total files updated: {total_modified}")

if __name__ == "__main__":
    process_files()
