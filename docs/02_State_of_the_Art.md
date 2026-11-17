# Document 2 : State of the Art

**AIM²P — Cartographie du domaine et état de l'art**

Phase : Phase 0 (cadrage scientifique) · Projet : AIM²P Initiative · Version : 0.1

---

## 1. Panorama des technologies et approches existantes

L'intersection entre intelligence artificielle, raisonnement symbolique et preuve formelle s'articule aujourd'hui autour de quatre piliers technologiques majeurs :

| Domaine | Projets et acteurs clés | Forces majeures | Limites structurelles |
|---|---|---|---|
| **LLM de raisonnement** | DeepSeek-R1, OpenAI o1/o3, Llemma, AlphaProof | Excellente intuition mathématique, génération rapide de brouillons de preuve. | Hallucinations logiques, absence de garantie formelle, dépendance aux benchmarks de type olympiades (IMO). |
| **Assistants de preuve** | Lean 4 (Mathlib), Rocq (ex-Coq), Isabelle/HOL | Rigueur absolue (100 % vérifié par le noyau), zéro hallucination acceptée. | Courbe d'apprentissage très élevée, écriture manuelle des tactiques très lente. |
| **Solveurs symboliques** | SymPy, SageMath, Wolfram Mathematica | Calcul algébrique exact, simplifications analytiques, dérivation symbolique. | Incapables de structurer une preuve logique globale ou de manipuler la logique formelle. |
| **IA pour la physique** | IAIFI (MIT/Harvard), SciML, Physics-Informed Neural Networks (PINN) | Excellente modélisation numérique et approximation de données physiques. | Centrés sur le calcul numérique ; quasi-absence de vérification formelle des preuves. |

## 2. Anthologie des systèmes récents

- **AlphaProof (Google DeepMind) :** combine apprentissage par renforcement (RL) et recherche arborescente avec Lean 4. Très performant sur les olympiades de mathématiques, mais système propriétaire, fermé et non appliqué à la physique théorique.
- **DeepSeek-Prover-V1.5 (DeepSeek, ICLR 2025) :** modèle ouvert qui utilise les résultats de vérification de Lean 4 comme récompense d'apprentissage par renforcement, et une variante de MCTS (RMaxTS) dont l'arbre est construit à partir des messages de compilation de Lean. C'est la référence la plus proche de la boucle d'auto-correction visée par AIM²P, mais elle est évaluée sur des benchmarks de mathématiques pures (miniF2F, ProofNet).
- **Llemma (EleutherAI) :** modèle de langage open source spécialisé en mathématiques. Excellent pour le code Python/SymPy, mais nécessite un vérificateur externe pour valider ses preuves.
- **Lean Copilot :** outil qui exécute des LLM directement dans Lean 4 pour suggérer des tactiques et rechercher des preuves en temps réel.
- **HepLean, devenu PhysLean puis Physlib :** bibliothèque open source et communautaire qui formalise des résultats de physique en Lean 4 (physique des hautes énergies, théorème de Wick, information quantique). Elle montre que la physique formelle est possible, mais le corpus reste récent et ne couvre pas, à notre connaissance, la complexité de Krylov ni la croissance d'opérateurs.

> [!NOTE]
> Cette cartographie est une version préliminaire. La matrice comparative complète (LLM, Lean 4, SymPy, Rocq, Isabelle) est l'objet de la phase P1.

## Références

- Xin et al., *DeepSeek-Prover-V1.5: Harnessing Proof Assistant Feedback for Reinforcement Learning and Monte-Carlo Tree Search*, ICLR 2025. [arXiv:2408.08152](https://arxiv.org/abs/2408.08152)
- Tooby-Smith, *HepLean: Digitalising high energy physics*, 2024. [arXiv:2405.08863](https://arxiv.org/abs/2405.08863)
- Article PhysLean sur la formalisation du théorème de Wick en Lean 4, 2025. [arXiv:2505.07939](https://arxiv.org/abs/2505.07939)
- PhysLean / Physlib sur le Lean Reservoir : [reservoir.lean-lang.org/@HEPLean/PhysLean](https://reservoir.lean-lang.org/@HEPLean/PhysLean)
