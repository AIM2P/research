# Document 1 : Research Question

**AIM²P — Formulation de la question centrale et des hypothèses expérimentales**

Phase : Phase 0 (cadrage scientifique) · Projet : AIM²P Initiative · Version : 0.1

---

## 1. Question scientifique centrale

La question pivot à laquelle répondra l'initiative AIM²P s'énonce comme suit :

> [!IMPORTANT]
> **Question principale**
>
> « Dans quelle mesure une architecture neuro-symbolique intégrée (articulant génération de raisonnement par LLM, calcul symbolique par SymPy et vérification formelle par Lean 4) permet-elle de garantir la rigueur, l'auto-correction et la reproductibilité des preuves en mathématiques pures et en physique théorique, tout en réduisant le taux d'hallucination à zéro ? »

## 2. Sous-questions de recherche (SQ)

- **SQ1 (interface neuro-symbolique) :** Comment traduire automatiquement un raisonnement scientifique exprimé en langage naturel enrichi (LaTeX) en une série de tactiques formelles exécutables par l'assistant de preuve Lean 4 ?
- **SQ2 (boucle de rétroaction et erreurs) :** De quelle manière les messages d'erreur générés par le compilateur Lean 4 peuvent-ils être réinjectés dans le prompt du LLM pour guider un algorithme de recherche arborescente (MCTS) vers une preuve valide ?
- **SQ3 (physique mathématique et invariants) :** Comment adapter les vérificateurs formels aux objets de la physique théorique (opérateurs de Lanczos, complexité de Krylov, hamiltoniens quantiques) qui combinent dérivation analytique et structures algébriques avancées ?

## 3. Hypothèses expérimentales (H)

- **H1 (supériorité hybride) :** L'exactitude des démonstrations produites par la boucle LLM + SymPy + Lean 4 surpasse de plus de 40 % celle d'un LLM de pointe utilisé seul, sur le benchmark AMP-Bench. Les modèles de référence et leurs versions exactes seront fixés lors de la phase P3 (baselines expérimentales).
- **H2 (convergence de l'auto-correction) :** Une boucle d'auto-correction guidée par les erreurs du compilateur Lean converge vers une preuve certifiée en moins de *k* = 5 itérations pour au moins 70 % des lemmes intermédiaires.
- **H3 (transposabilité à la physique) :** L'approche formelle permet d'identifier et de corriger des erreurs de conditions aux limites ou d'invariance dans des calculs théoriques complexes (par exemple, la croissance d'opérateurs dans l'espace de Krylov).
