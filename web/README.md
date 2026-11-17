# Site web AIM²P

Site public du programme AIM²P, en ligne sur **https://aim2p.github.io/research/**.

Il est construit avec [Astro](https://astro.build) et utilise React pour les parties interactives : atelier de preuve, laboratoire Krylov, carte des phases, diagramme de Venn, citation. Il est bilingue : le français est le texte source, l'anglais est disponible sous `/en/`.

## Travailler en local

Il faut Node.js 22 ou plus récent.

```bash
cd web
npm install        # une seule fois
npm run dev        # http://localhost:4321, rechargement automatique
npm run build      # vérification des types (astro check) + site statique dans dist/
npm run preview    # sert dist/ pour un dernier contrôle
```

Avant `dev` et `build`, le script `scripts/sync-assets.mjs` copie le logo, l'image de partage et les PDF depuis `../branding` et `../docs/pdf`. Ces fichiers n'ont donc qu'une seule source de vérité.

## Structure

```text
web/
  src/pages/            routes : accueil FR et EN, pages des documents, 404
  src/components/home/  une section de la page d'accueil par fichier
  src/components/islands/  composants React interactifs
  src/data/phases.ts    les 19 phases de la feuille de route et leur statut
  src/i18n/strings.ts   tous les textes, en français puis en anglais
  src/lib/docs.ts       liste des documents ; lit et met en forme ../docs/*.md
  src/lib/krylov.ts     calcul du laboratoire Krylov (RK4 + solutions exactes)
  src/styles/global.css thèmes clair/sombre, mise en page, animations
  scripts/sync-assets.mjs  copie du logo et des PDF
```

## Mises à jour courantes

- **Faire avancer la feuille de route :** dans `src/data/phases.ts`, changez le champ `status` d'une phase (`done`, `current`, `next`, `planned`). Mettez aussi à jour le bandeau du hero : la largeur de la barre dans `src/components/home/Hero.astro`, ainsi que les clés `hero.status.v`, `hero.status.aria` et `rm.title` dans `src/i18n/strings.ts`, en FR et en EN.
- **Modifier un texte :** cherchez la clé dans `src/i18n/strings.ts` et modifiez-la en français et en anglais.
- **Ajouter un document de recherche :** placez le fichier `.md` dans `../docs/` et régénérez les PDF avec `python tools/build_pdfs.py`. Ajoutez ensuite une entrée dans `DOCS` (`src/lib/docs.ts`) et les clés `res.dN.t` et `res.dN.d` dans `strings.ts`. La page est générée à la construction du site.
- **Publier des résultats :** la section « Hypothèses » affiche « à mesurer » tant qu'aucune mesure n'existe, conformément à la règle d'or du programme. Ne remplacez ces mentions que par des résultats publiés avec leurs scripts.

## Paramètres d'URL utiles

- `?static` affiche toutes les sections sans animation et exécute la simulation Krylov d'un coup. Pratique pour les captures d'écran et l'impression.

## Mise en ligne

Le workflow `.github/workflows/deploy-web.yml` construit le site et le publie sur GitHub Pages à chaque push sur `main` qui touche `web/`, `docs/` ou `branding/`. On peut aussi le lancer à la main depuis l'onglet **Actions**. Le sous-chemin `/research` est fourni automatiquement par GitHub (variables `SITE_URL` et `BASE_PATH`, lues dans `astro.config.mjs`).

Prérequis, une seule fois : **Settings → Pages → Source = « GitHub Actions »**.

> Sous Windows avec Git Bash, pour tester localement le sous-chemin, préfixez la commande par `MSYS_NO_PATHCONV=1`, sinon `/research` est transformé en chemin Windows :
> `MSYS_NO_PATHCONV=1 BASE_PATH=/research npm run build`
