import os
import json
import requests
import sys

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

if not TOGETHER_API_KEY:
    print("❌ ERREUR : TOGETHER_API_KEY est absente ou vide.")
    print("   → Ajoute-la dans GitHub > Settings > Secrets > Actions")
    sys.exit(1)

print("✅ API KEY OK")

API_URL = "https://api.together.xyz/v1/chat/completions"
MODEL = "meta-llama/Meta-Llama-3-8B-Instruct-Lite"

HEADERS = {
    "Authorization": f"Bearer {TOGETHER_API_KEY}",
    "Content-Type": "application/json",
}

SEO_TOPICS = [
    "vincent bastille remixes",
    "remixes house music france",
    "dj vincent bastille mix",
]

def generate_seo_page(topic: str) -> str:
    print(f"\n📡 Calling Together AI for topic: '{topic}'...")
    payload = {
        "model": MODEL,
        "max_tokens": 800,
        "temperature": 0.7,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Tu es un expert SEO. Génère une page HTML complète et optimisée SEO "
                    "avec title, meta description, h1, h2, et 300 mots de contenu naturel "
                    "autour du sujet donné. Réponds UNIQUEMENT avec le code HTML, sans explications."
                ),
            },
            {
                "role": "user",
                "content": f"Génère une page SEO optimisée pour : {topic}",
            },
        ],
    }
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print(f"❌ Timeout sur l'appel API pour '{topic}'")
        sys.exit(1)
    except requests.exceptions.HTTPError:
        print(f"❌ Erreur HTTP {response.status_code} : {response.text}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau : {e}")
        sys.exit(1)

    print("✅ Response received")
    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        print(f"❌ Format de réponse inattendu : {json.dumps(data, indent=2)}")
        sys.exit(1)
    return content

def slugify(text: str) -> str:
    return text.lower().replace(" ", "-").replace("/", "-")

def main():
    output_dir = "seo-pages"
    os.makedirs(output_dir, exist_ok=True)
    for topic in SEO_TOPICS:
        html_content = generate_seo_page(topic)
        slug = slugify(topic)
        filepath = os.path.join(output_dir, f"{slug}.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"✅ Page sauvegardée : {filepath}")
    print(f"\n🎉 {len(SEO_TOPICS)} pages SEO générées avec succès !")

if __name__ == "__main__":
    main()
