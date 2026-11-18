# Gel d'AMP-Bench-mini v1.0

**Date du gel : 18 novembre 2026.** Phase P2 (spécification du benchmark), avant toute exécution d'un modèle sur les problèmes d'évaluation.

## Contenu figé

| Niveau | Problèmes | Source | Type | Statut |
|---|---|---|---|---|
| N1 | 6 | AIM²P (inédits) | réponse fermée | privés jusqu'à l'évaluation |
| N2 | 6 | AIM²P (inédits) | réponse fermée | privés jusqu'à l'évaluation |
| N3 | 8 | miniF2F (google-deepmind, commit `f0a20e14`), tirage stratifié, graine 20261118 | preuve Lean | publics |
| N4 | 8 | ProofNet# (révision `a8da405f`) et PutnamBench (commit `a635813f`), même graine | preuve Lean | publics |
| N5 | 12 | AIM²P (inédits), sélection pré-enregistrée dans le document 04, §6.2 | 5 réponses fermées, 7 preuves Lean | privés jusqu'à l'évaluation |

Les 40 problèmes ont été audités et validés par le fondateur. La validation des 24 problèmes inédits a été déclarée en conversation le 18 novembre 2026, puis reportée dans les fichiers par l'assistant : le champ `audit.validated_by` le précise.

## Empreintes

`HASHES.txt` donne l'empreinte SHA-256 de chaque problème d'évaluation : le fichier TOML, suivi pour les problèmes de preuve du fichier de défi Lean. Ces empreintes sont publiées dès maintenant. Les problèmes inédits, leurs clés, leurs preuves de référence et leurs scripts de vérification seront publiés après l'évaluation. Chacun pourra alors vérifier qu'ils sont identiques à ceux qui ont été figés.

| Fichier | SHA-256 |
|---|---|
| `bench/HASHES.txt` | `66cd3fc8afe2d244bebe40fbd888a2725dff967273fda9654c4f6a35c163e9ec` |
| `bench/lean/lake-manifest.json` | `3a76524addc7f270601697bbe438c7a4a4d3e699a88cb72a3068ad2a726f39fe` |
| `bench/lean/lean-toolchain` | `ca5f1f601d34c49079e38d7e7041eb0f2a9c227fbc1df0f404820069a052330c` |
| `bench/validate.py` | `524940808274c25980e412a7d16d590c13eb43498c28a907c4019e1d06d628d9` |

## Environnement de vérification

- Lean v4.35.0, Mathlib v4.35.0, Physlib v4.35.0 (commits exacts dans `lean/lake-manifest.json`), sous WSL2 (Ubuntu 26.04.1).
- Certification des preuves : `lake comparator` dans son bac à sable `bwrap`, avec les seuls axiomes `propext`, `Quot.sound` et `Classical.choice`.
- Clés des réponses fermées : SymPy 1.14.0 et mpmath 1.3.0, deux méthodes indépendantes par clé (trois pour N5-06).
- Contrôles au gel :
  - `validate.py --final` sans erreur ;
  - les 23 défis Lean compilent ;
  - les 7 preuves de référence N5 sont acceptées par `lake comparator` ;
  - les 17 clés N1, N2 et N5 sont confirmées par les scripts de vérification privés.

## Règles après le gel

- **Aucune modification des problèmes d'évaluation.** Un défaut découvert après le gel donne lieu à un erratum public, daté. Le problème est alors exclu dans une analyse de sensibilité, sans jamais être corrigé en silence.
- **Pilotes uniquement sur des problèmes de développement** (`split = "dev"`), jamais sur les 40 problèmes figés.
- **Les problèmes inédits ne sont envoyés à aucun service** dont les conditions permettent l'entraînement sur les données soumises. Pour la route gratuite d'OpenRouter, la décision est ouverte (document 05, §9).
- **Aucune preuve des problèmes PutnamBench n'est publiée.**
