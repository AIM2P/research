# Document 3 : Research Gap

**AIM²P — Identification des quatre verrous scientifiques non résolus**

Phase : Phase 0 (cadrage scientifique) · Projet : AIM²P Initiative · Version : 0.1

---

## 1. Les quatre verrous scientifiques

L'analyse de l'état de l'art met en évidence quatre lacunes que les travaux actuels ne comblent pas, à notre connaissance :

> [!IMPORTANT]
> **GAP 1 : le vide de la physique mathématique formelle**
>
> L'essentiel des efforts en preuve formelle (Lean 4, Rocq, Isabelle) porte sur les mathématiques de concours (IMO, Putnam), les mathématiques pures ou l'informatique théorique. La physique théorique y reste marginale : les initiatives existantes, comme HepLean (devenu PhysLean puis Physlib), sont récentes et centrées sur la physique des hautes énergies et l'information quantique. Des pans entiers, comme la complexité de Krylov et la croissance d'opérateurs, restent absents des corpus de preuve formelle certifiée.

> [!IMPORTANT]
> **GAP 2 : le découplage de la triade neuro-symbolique**
>
> Les outils actuels utilisent soit un LLM seul, soit un LLM + Lean, soit un LLM + SymPy. Il n'existe pas, à notre connaissance, d'architecture unifiée orchestrant simultanément le **calcul symbolique exact (SymPy)**, la **génération de preuve (LLM)** et la **certification formelle (Lean 4)** dans un pipeline tridirectionnel.

> [!IMPORTANT]
> **GAP 3 : une auto-correction guidée par le compilateur, encore cantonnée aux mathématiques pures**
>
> Les mécanismes d'auto-correction des LLM généralistes reposent surtout sur une réévaluation à l'aveugle (*prompting réflexif*). Des travaux récents utilisent déjà le retour de Lean 4 comme signal de récompense et pour guider une recherche arborescente : DeepSeek-Prover-V1.5 (ICLR 2025) emploie ainsi une variante de MCTS (RMaxTS) construite sur les messages de compilation de Lean. Ces boucles restent toutefois évaluées sur des benchmarks de mathématiques pures. Leur extension à un pipeline qui couple calcul symbolique et vérification formelle, appliqué à des objets de physique mathématique, reste à formaliser.

> [!IMPORTANT]
> **GAP 4 : l'absence d'infrastructure open science inclusive en Afrique**
>
> À notre connaissance, il n'existe aucune plateforme ni aucun benchmark open source majeur dédié au raisonnement scientifique formel basé sur le continent africain, ce qui limite la participation des chercheurs locaux aux avancées mondiales de l'IA fondamentale.

## 2. Positionnement de l'initiative AIM²P

AIM²P se positionne à l'intersection de ces quatre verrous pour apporter une solution logicielle et méthodologique intégrée.
