# Deploy Debug — remixes.vincentbastille.online

## Fichiers devant être accessibles (output dir = public/)

| Fichier dans repo       | URL publique attendue                                              |
|-------------------------|--------------------------------------------------------------------|
| public/index.html       | https://remixes.vincentbastille.online/                            |
| public/__debug-build.html | https://remixes.vincentbastille.online/__debug-build.html        |
| public/robots.txt       | https://remixes.vincentbastille.online/robots.txt                  |
| public/sitemap.xml      | https://remixes.vincentbastille.online/sitemap.xml                 |
| public/sitemap-test.html | https://remixes.vincentbastille.online/sitemap-test.html          |
| public/robots-test.html | https://remixes.vincentbastille.online/robots-test.html            |

## URLs à tester après redéploiement

1. https://remixes.vincentbastille.online/__debug-build.html  → doit afficher "DEBUG BUILD PUBLIC OK - 2026-05-03"
2. https://remixes.vincentbastille.online/robots.txt          → doit afficher le contenu robots
3. https://remixes.vincentbastille.online/sitemap.xml         → doit afficher le XML du sitemap
4. https://remixes.vincentbastille.online/sitemap-test.html   → doit charger
5. https://remixes.vincentbastille.online/robots-test.html    → doit charger

## Diagnostic

Si **/__debug-build.html** est en 404 après redéploiement :
- Le problème n'est PAS dans le repo (le fichier existe bien dans public/)
- Le problème est dans Vercel : soit le Output Directory n'est pas configuré sur `public`,
  soit le domaine pointe encore vers un ancien build/projet.

Si **/__debug-build.html** répond 200 mais **/robots.txt** reste en 404 :
- Vercel sert bien public/ mais un middleware ou une règle intercepte ces URLs.

## Commit contenant ce debug

Voir commits récents sur main — message : "debug: add __debug-build.html to verify public/ output dir"

## Config Vercel attendue

- Output Directory : `public`
- Framework Preset : Other
- Root Directory : (vide)
- Pas de vercel.json dans le repo
