# Environnement Lean figé d'AMP-Bench

Projet Lake `AMPBench`. Ses versions sont figées en phase P1 (voir [docs/05_Domain_Map.md](../../docs/05_Domain_Map.md)) :

- Lean `v4.35.0` (`lean-toolchain`) ;
- Physlib, tag `v4.35.0`, qui dépend de Mathlib au tag `v4.35.0` ;
- commits exacts dans `lake-manifest.json`.

L'option `autoImplicit = false` est active.

## Installation

```bash
cd bench/lean
lake update          # récupère Physlib, Mathlib et leurs dépendances (~15 min la première fois)
lake exe cache get   # fichiers compilés de Mathlib, si `lake update` ne l'a pas déjà fait
lake build           # compile AMPBench (test de fumée inclus)
```

`AMPBench/Smoke.lean` vérifie que Mathlib et `Physlib.Units` s'importent. Il affiche aussi les axiomes utilisés par une preuve simple, qui doivent se limiter à `propext`, `Classical.choice` et `Quot.sound`.

## Environnement recommandé : WSL2 (Ubuntu)

Sur le portable de référence, l'élaboration du fichier de fumée prend **5,9 s sous WSL2** contre 171 s sous Windows, et l'installation complète environ 8 min contre 26 min. La boucle d'évaluation tourne donc sous WSL2, avec Lean gardé chargé (REPL et LeanInteract) plutôt que relancé à chaque essai.

## Certification : `lake comparator`

`lake comparator` vérifie trois choses pour chaque théorème nommé : la solution prouve le même énoncé que le défi, elle n'utilise que les axiomes permis, et le noyau l'accepte. La compilation se fait dans un bac à sable `bwrap` (bubblewrap), disponible seulement sous Linux, donc sous WSL2 ici.

Le dossier `AMPBench/Demo/` contient un énoncé figé (`Challenge.lean`) et trois solutions :

```bash
lake comparator --config comparator/demo_ok.json     # preuve correcte : acceptée (code 0)
lake comparator --config comparator/demo_sorry.json  # sorry : refusée (code 1, sorryAx)
lake comparator --config comparator/demo_drift.json  # énoncé modifié : refusée (code 1)
```

Résultats mesurés le 18 novembre 2026 : 13 à 20 s par cas.
