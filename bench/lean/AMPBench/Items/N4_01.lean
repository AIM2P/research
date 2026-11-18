import Mathlib.Tactic
import Mathlib.Algebra.Group.Subgroup.Basic

/-!
AMP-Bench-mini, problème N4-01 (niveau N4).
Source : ProofNet# (jeu de données Hugging Face PAug/ProofNetSharp, partie test, révision
a8da405fbd1e348a87445c2e562c747b7e26dc8f), identifiant `Dummit-Foote|exercise_4_4_6b`. Licence MIT.
ProofNet# : Poiroux, Weiss, Kunčak, Bosselut (arXiv:2406.07222), version corrigée de ProofNet
(Azerbayev et al., arXiv:2302.12433).
Énoncé formel repris tel quel. Seuls changent le nom du théorème (`n4_01`) et les imports
(imports ciblés au lieu de `import Mathlib`). Les `open` de l'en-tête d'origine sont gardés tels quels.
-/

open Fintype Subgroup Set Polynomial Ideal
open scoped BigOperators

theorem n4_01 :
  ∃ (G : Type*) (hG : Group G) (H : @Subgroup G hG), @Normal G hG H ∧ ¬ @Characteristic G hG H := by
  sorry
