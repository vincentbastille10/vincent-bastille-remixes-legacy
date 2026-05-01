import os
import re

BASE_DIR = "remixes"
OLD_DOMAIN = "https://vincent-bastille-remixes-legacy.vercel.app"
NEW_DOMAIN = "https://remixes.vincentbastille.online"

def fix_canonical(content):
    pattern = r'<link\s+rel="canonical"\s+href="([^"]+)"\s*/?>'
    
    def replace(match):
        old_url = match.group(1)
        path = old_url.replace(OLD_DOMAIN, "")
        return f'<link rel="canonical" href="{NEW_DOMAIN}{path}">'

    return re.sub(pattern, replace, content)

def process():
    changed = 0

    for root, _, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".html"):
                path = os.path.join(root, file)

                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                new_content = fix_canonical(content)

                if new_content != content:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"✔ Updated {path}")
                    changed += 1

    print(f"\n🔥 Total modified: {changed}")

if __name__ == "__main__":
    process()
