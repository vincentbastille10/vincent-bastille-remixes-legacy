# Vincent Bastille Remixes Legacy Generator

Générateur statique SEO pour créer automatiquement un cluster massif de pages remix.

## Ce que le projet génère

- 70 pages HTML SEO (minimum) avec slug propre, title/meta uniques, H1/H2/H3.
- Contenu long (~800+ mots/page) orienté "remix legacy / classic remix / iconic remix / legendary remix".
- FAQ visible + JSON-LD (`FAQPage`) et metadata OpenGraph.
- Maillage interne fort (3 à 5 liens par page vers d'autres pages du cluster).
- CTA conversion sur chaque page : **Listen Vincent Bastille Remix** vers `https://remixes.vincentbastille.online/`.
- `sitemap.xml` régénéré automatiquement à chaque exécution.

## Exécution locale

```bash
python generate.py
```

## Génération quotidienne (bonus)

```bash
python daily.py
```

Le script quotidien:

- crée automatiquement une nouvelle page tendance basée sur un sujet remix/artiste,
- l'ajoute à `data/pages.json`,
- génère la page HTML,
- met à jour le sitemap,
- commit automatiquement si un changement est détecté.

## GitHub Actions

Le workflow `.github/workflows/seo-generator.yml` exécute tous les jours:

1. génération globale des pages,
2. ajout d'une page quotidienne,
3. commit/push automatique.

Aucune étape manuelle (hors clés API éventuelles si vous étendez la génération IA).
