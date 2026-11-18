import Mathlib.Tactic
import Mathlib.Data.Set.Finite.Basic

/-!
AMP-Bench-mini, problème N4-04 (niveau N4).
Source : ProofNet# (jeu de données Hugging Face PAug/ProofNetSharp, partie test, révision
a8da405fbd1e348a87445c2e562c747b7e26dc8f), identifiant `Munkres|exercise_13_3b`. Licence MIT.
ProofNet# : Poiroux, Weiss, Kunčak, Bosselut (arXiv:2406.07222), version corrigée de ProofNet
(Azerbayev et al., arXiv:2302.12433).
Énoncé formel repris tel quel. Seuls changent le nom du théorème (`n4_04`) et les imports
(imports ciblés au lieu de `import Mathlib`). Les `open` de l'en-tête d'origine sont gardés tels quels.
-/

open Filter Set TopologicalSpace
open scoped Topology

theorem n4_04 : ¬ ∀ X : Type, ∀s : Set (Set X),
  (∀ t : Set X, t ∈ s → (Set.Infinite tᶜ ∨ t = ∅ ∨ t = ⊤)) →
  (Set.Infinite (⋃₀ s)ᶜ ∨ (⋃₀ s) = ∅ ∨ (⋃₀ s) = ⊤) := by
  sorry
