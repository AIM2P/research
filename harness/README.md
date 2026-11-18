<!-- SPDX-License-Identifier: Apache-2.0 -->
# Harnais des baselines (phase P3)

Ce dossier soumet les problèmes d'AMP-Bench-mini au modèle, note les réponses avec la chaîne de vérification du protocole et journalise chaque génération. Il couvre les baselines **B0, B1 et B2** du [document 04](../docs/04_Research_Proposal_v0.1.md) (§5.3). B3, A1 et A2 relèvent de la phase P4 (`engine/`).

> **Règle de gel.** Le harnais refuse d'appeler le modèle sur les 40 problèmes figés (`split = "eval"`) tant que `campaign.eval_authorized` vaut `false` dans la configuration, même avec l'option `--allow-eval`. Ce verrou ne se lève que sur le « go » explicite du fondateur. Les pilotes tournent sur les problèmes de développement (`DEV-01` …), jamais évalués.

## Contenu

```text
harness/
  config/p3_baselines.toml   configuration (modèle, décodage, graines, R, k, délais, budget) ; non gelée
  prompts/answer_v1.md       invite « réponse fermée » (version v1)
  prompts/proof_v1.md        invite « preuve Lean » (version v1)
  client.py                  client OpenRouter (bibliothèque standard) et compteur de requêtes
  items.py                   lecture des problèmes, découpage des défis Lean (en-tête / théorème)
  prompts.py                 rendu des invites
  grade_answer.py            correcteur des réponses fermées (SymPy, Math-Verify, test numérique)
  grade_proof.py             correcteur des preuves (en-tête imposé, filtre de source, lake comparator)
  run_baselines.py           exécution reprenable des générations, journal JSONL
  summarize.py               taux par niveau pour B0, B1, B2, intervalles de Wilson
  requirements-lock.txt      versions Python épinglées
  tests/                     tests hors ligne (aucun appel à l'API)
```

## Installation (Ubuntu sous WSL2, sans sudo)

```bash
curl -LsSf https://astral.sh/uv/install.sh -o /tmp/uv-install.sh
UV_NO_MODIFY_PATH=1 sh /tmp/uv-install.sh            # installe uv dans ~/.local/bin
export PATH="$HOME/.local/bin:$PATH"
uv venv ~/aim2p-venv --python /usr/bin/python3
uv pip install --python ~/aim2p-venv/bin/python -r harness/requirements-lock.txt
```

Versions épinglées : SymPy 1.14.0, mpmath 1.3.0, Math-Verify 0.9.0 avec son runtime ANTLR 4.13.2 (`latex2sympy2_extended` 1.11.0), sous CPython 3.14.4. Le projet Lean est la copie WSL `~/aim2p-bench` de `bench/lean` (Lean v4.35.0, Mathlib et Physlib v4.35.0), que le harnais resynchronise avant chaque campagne comme `bench/tools/check_lean_wsl.sh`.

La clé OpenRouter est lue seulement dans la variable `OPENROUTER_API_KEY` (fichier `~/.aim2p_env` sous WSL). Elle n'est jamais affichée ni écrite, et elle est retirée de l'environnement de `lake comparator`.

## Utilisation

Toutes les commandes se lancent sous WSL, depuis la racine du dépôt.

```bash
source ~/.aim2p_env                        # charge OPENROUTER_API_KEY sans l'afficher
PY=~/aim2p-venv/bin/python

# 1. Vérifier les invites, sans appel au modèle
$PY harness/run_baselines.py --campaign pilot_dev_b0 --split dev --baselines B0 --runs 1 --dry-run

# 2. Pilote B0 sur les problèmes de développement, 10 requêtes au plus
$PY harness/run_baselines.py --campaign pilot_dev_b0 --split dev --baselines B0 --runs 1 --max-requests 10

# 3. Résumé (results/<campagne>/summary.md et summary.json)
$PY harness/summarize.py --campaign pilot_dev_b0

# Campagne complète B0–B2 (5 échantillons, R = 3) : seulement après le gel de S8 et le « go » du fondateur
$PY harness/run_baselines.py --campaign p3_nemotron --split eval --baselines B0,B1,B2 --allow-eval
```

**Reprise.** Relancer la même commande reprend là où la campagne s'est arrêtée : une génération déjà notée est sautée, une réponse déjà reçue mais pas notée est notée sans nouvel appel. `--regrade` renote toutes les réponses reçues, sans appel au modèle (utile après une correction du correcteur, avec une nouvelle ligne de journal par génération).

**Budget.** Chaque tentative HTTP, réussie ou non, est d'abord réservée dans `results/raw/request_counter.json` (jour UTC). Le client refuse toute requête au-delà de `budget.daily_request_limit` (50, limite de l'offre gratuite d'OpenRouter) ou de `--max-requests`. Sur un 429 « limite quotidienne », la campagne s'arrête proprement ; il suffit de la relancer le lendemain.

## Baselines

| Code | Définition dans le harnais |
|---|---|
| B0 | L'échantillon 1 de chaque (problème, répétition) |
| B1 | Succès si l'un des k = 5 échantillons est correct (pass@5) ; indicatif, car il suppose un oracle |
| B2 | Un seul échantillon, choisi sans la clé. Preuves : le premier accepté par Lean, donc B2 = B1 par construction. Réponses : vote majoritaire par équivalence SymPy/numérique, égalité tranchée par le premier échantillon (**à valider**) |

B0, B1 et B2 partagent les mêmes générations : la campagne B0–B2 produit 5 échantillons par problème et par répétition. Chaque échantillon reçoit sa graine, dérivée de `sampling.base_seed` par SHA-256.

## Correction

**Réponses fermées** (`grade_answer.py`). Le correcteur extrait la dernière ligne « Réponse finale : … » ou, à défaut, le dernier `\boxed{…}`. Il lit la réponse avec SymPy, sur une entrée filtrée par liste blanche puisque la sortie du modèle n'est pas fiable, ou avec Math-Verify pour le LaTeX. Les listes sont comparées élément par élément, dans l'ordre. Le verdict `correct` exige deux accords :

- un accord symbolique : `simplify(c − k) == 0`, ou le polynôme minimal de `c − k` pour un nombre algébrique, ou `math_verify.verify(clé, réponse)` ;
- un accord numérique à 50 chiffres, en au moins 3 points tirés avec une graine fixe pour une expression à variables.

En cas de désaccord, le verdict est `needs_audit`, et la réponse doit être auditée à la main (document 04, §5.2). La méthode qui a tranché est journalisée.

Champ facultatif d'un problème : `answer.assumptions = { alpha = "positive" }` déclare le signe d'une variable (utilisé par DEV-05).

**Preuves** (`grade_proof.py`). Le correcteur extrait le dernier bloc ```lean qui déclare le théorème et supprime les lignes `import` du modèle. Il reconstruit la solution avec **exactement** l'en-tête du défi : tout ce qui précède le théorème. Il applique ensuite le filtre de source : `sorry`, `admit`, `axiom`, `native_decide`, `implemented_by`, `extern`, `unsafe`, `debug.skipKernelTC`, commentaires exclus. La solution est écrite dans `~/aim2p-bench/AMPBench/Solutions/<campagne>/<problème>/R<r>S<s>.lean`, hors dépôt, puis soumise à `lake comparator` dans son bac à sable `bwrap`, avec un délai maximal. Elle n'est jamais compilée hors du bac à sable.

| Verdict | Signification | Taxonomie (doc. 04, §5.4) |
|---|---|---|
| `accepted` | Même énoncé que le défi, axiomes permis, accepté par le noyau | — |
| `illegal_axiom` | Filtre de source (`source_filter:sorry`…) ou axiome refusé par Comparator (`axiom:sorryAx`…) | H-a |
| `statement_mismatch` | Énoncé modifié, ou théorème absent (`missing_theorem`) | H-b |
| `build_error` | Échec de compilation ; la classe est celle de la première erreur : `unknown_identifier` (H-c), `type_mismatch`, `typeclass`, `unsolved_goals`, `syntax`, `tactic_failed`, `timeout`, `other` | H-c si identifiant inconnu |
| `no_proof` | Aucun bloc ```lean exploitable (par exemple une sortie tronquée) | — |

## Journaux

- `results/<campagne>/generations.jsonl` : une ligne par génération, avec le problème, les baselines servies, la répétition, l'échantillon, l'horodatage, les paramètres (graine comprise), la version et l'empreinte de l'invite et de la configuration, le modèle renvoyé, le fournisseur, l'identifiant de réponse, la raison d'arrêt, la latence, les tokens (dont ceux de raisonnement), les chemins des fichiers bruts, la réponse ou la preuve extraite, le verdict, la classe d'erreur, la taxonomie et les durées (API, correction, comparateur, de bout en bout). Pour un problème privé ou PutnamBench, la sortie extraite et les messages Lean sont **masqués** : seules leurs empreintes et leurs classes figurent dans le journal.
- `results/<campagne>/runs_meta.jsonl` : une ligne par lancement (configuration, versions de Python, SymPy, Math-Verify, Lean, empreinte du manifeste Lake, commit git).
- `results/raw/` (**ignoré par git**) : invites, réponses brutes de l'API, solutions reconstruites, journaux de `lake comparator`, compteur de requêtes.

## Tests

```bash
~/aim2p-venv/bin/python -m unittest discover -s harness/tests -t . -v
AIM2P_SKIP_LEAN=1 ~/aim2p-venv/bin/python -m unittest discover -s harness/tests -t .   # sans Lean (1 s)
```

Les tests ne font aucun appel à l'API. Ils couvrent :

- le correcteur de réponses : formes équivalentes (`exp(3)` et `e**3`, radicaux imbriqués), ordre des listes, mauvaise clé, entrée malveillante jamais évaluée ;
- le compteur de requêtes et le client (ouvreur HTTP simulé : 5xx, 429, limite quotidienne) ;
- le refus des problèmes d'évaluation ;
- de vrais passages de `lake comparator` (environ 2 minutes) sur les démos de `bench/lean/AMPBench/Demo` : `SolutionOk` et `SolutionLLM` acceptées, `SolutionSorry` refusée (filtre, puis `sorryAx`), `SolutionDrift` en dérive d'énoncé, plus deux erreurs de compilation classées et les preuves de référence de DEV-01 et DEV-02.

## Points à valider par le fondateur

Ils sont marqués « À VALIDER PAR LE FONDATEUR » dans `config/p3_baselines.toml` :

- température et `top_p` ;
- `max_tokens` ;
- envoi du paramètre `seed` ;
- absence d'invite système ;
- routage du fournisseur ;
- règle de B2 pour les réponses fermées ;
- domaine des points numériques ;
- traitement de `needs_audit` ;
- délai de `lake comparator` ;
- jour de remise à zéro du compteur.

## Licence

Code sous licence Apache-2.0 (texte : [bench/LICENSE](../bench/LICENSE)).
