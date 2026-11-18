# AMP-Bench-mini

AMP-Bench-mini est le benchmark de la phase P2 d'AIM²P : **40 problèmes** de mathématiques et de physique mathématique, audités puis **figés avant toute mesure**. Le protocole complet est décrit dans [docs/04_Research_Proposal_v0.1.md](../docs/04_Research_Proposal_v0.1.md), et les choix d'outils dans [docs/05_Domain_Map.md](../docs/05_Domain_Map.md).

| Niveau | Nombre | Contenu | Source | Vérification |
|---|---|---|---|---|
| N1 | 6 | Calcul élémentaire, réponse fermée | AIM²P | SymPy + test numérique |
| N2 | 6 | Calcul avancé, physique de premier cycle | AIM²P | SymPy + test numérique |
| N3 | 8 | Preuves de niveau olympiade | miniF2F (google-deepmind), tirage stratifié | `lake comparator` |
| N4 | 8 | Preuves de premier cycle et du Putnam | ProofNet#, PutnamBench | `lake comparator` |
| N5 | 12 | Physique mathématique (Krylov, mécanique hamiltonienne, unités) | AIM²P | SymPy exact + Lean |

## Structure

```text
bench/
  items/            problèmes publics (un fichier TOML par problème) et tirages (N3_selection.json…)
  private/          problèmes inédits, hors dépôt jusqu'à l'évaluation (ignoré par git)
  lean/             projet Lean figé (Lean, Mathlib, Physlib v4.35.0)
    AMPBench/Items/ un fichier de défi Lean par problème de preuve
  tools/            tirage reproductible, vérification Lean sous WSL
  validate.py       validateur (format, imports, réponses SymPy, effectifs, empreintes)
  HASHES.txt        empreintes SHA-256 publiées au gel
```

## Format d'un problème

Un fichier `bench/items/<ID>.toml` par problème. L'identifiant est `N1-01` … `N5-12`, ou `DEV-01` … pour les problèmes de développement, qui servent aux pilotes et ne sont jamais évalués.

```toml
id = "N3-01"
level = "N3"            # N1 … N5
kind = "proof"          # "proof" (preuve Lean) ou "answer" (réponse fermée)
split = "eval"          # "eval" (les 40 problèmes figés) ou "dev"
visibility = "public"   # "private" : fichier dans bench/private/, publié après l'évaluation
title = "Diagonale d'un rectangle"
statement = """
Énoncé en langue naturelle (LaTeX autorisé).
"""

[source]
name = "google-deepmind/miniF2F"
ref = "MiniF2F/Test.lean : mathd_algebra_141"   # identifiant d'origine
commit = "f0a20e14c1eeccd859d51bb4c2b3ee487889c303"
licence = "Apache-2.0"
modified = false        # true si l'énoncé a été modifié lors du portage (décrire dans audit.notes)

[lean]                  # seulement pour kind = "proof"
module = "AMPBench.Items.N3_01"
theorem = "n3_01"

# [answer]              # seulement pour kind = "answer"
# value = "391"         # expression SymPy de la réponse attendue
# variables = []        # symboles libres éventuels

[audit]
status = "pending"      # pending, ok ou rejected
notes = ""
```

### Fichier de défi Lean (problèmes de preuve)

`bench/lean/AMPBench/Items/<ID avec _>.lean` contient :
- **un bloc d'imports ciblés** de Mathlib ou de Physlib. `import Mathlib` complet est interdit : sous WSL, il demande 5,4 Go de mémoire et de 20 à 92 s, contre 3,2 Go et 4,7 s pour `import Mathlib.Tactic`.
- les `open` nécessaires, puis l'énoncé, terminé par `:= by sorry`.

**Règle de choix des imports** (validée le 18 novembre 2026) : l'en-tête contient les modules dont l'énoncé a besoin, plus ceux des résultats principaux qu'une preuve standard cite (par exemple le théorème fondamental de l'algèbre pour N3-05). Sans eux, certains problèmes seraient impossibles à prouver, quelle que soit la qualité du modèle.

La solution d'un modèle est compilée **avec exactement cet en-tête**, et ses propres imports sont ignorés. La certification se fait par `lake comparator`, avec les axiomes `propext`, `Quot.sound` et `Classical.choice` seulement.

## Vérifier

```bash
python bench/validate.py            # format, imports, réponses SymPy, effectifs
python bench/validate.py --final    # avant le gel : effectifs complets et audits « ok » obligatoires
python bench/validate.py --hashes   # écrit HASHES.txt (empreintes SHA-256 des problèmes d'évaluation)
```

Sous Windows, lancez `python -X utf8 bench/validate.py` si les accents s'affichent mal.

Pour vérifier que les énoncés Lean compilent, sous Ubuntu (WSL) :

```bash
bash "/mnt/c/Users/LENOVO/Documents/Research Project AIM²P/bench/tools/check_lean_wsl.sh"
```

## Gel et problèmes inédits

Les problèmes inédits (N1, N2, N5) restent dans `bench/private/` jusqu'à la fin de l'évaluation. Au gel, seules leurs empreintes SHA-256 sont publiées (`HASHES.txt`) : chacun pourra vérifier ensuite que les problèmes publiés sont ceux qui ont été évalués. Un défaut découvert après le gel donne lieu à un erratum public. Le problème concerné est alors exclu dans une analyse de sensibilité, jamais corrigé en silence.

## Licences

- **Code** (`validate.py`, `tools/`, projet Lean) : Apache-2.0, voir [LICENSE](LICENSE).
- **Problèmes rédigés par AIM²P** : CC BY 4.0, comme les documents du dépôt.
- **Problèmes repris de sources tierces** : licence de leur source, voir [THIRD_PARTY.md](THIRD_PARTY.md). Aucune preuve des problèmes PutnamBench n'est publiée, à la demande de ses mainteneurs. Par prudence, le texte informel de ces problèmes (concours Putnam, MAA) n'est pas reproduit : seul l'énoncé formel Lean (Apache-2.0) l'est, avec un renvoi au fichier PutnamBench.
