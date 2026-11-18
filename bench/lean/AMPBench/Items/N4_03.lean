import Mathlib.Tactic
import Mathlib.Algebra.Module.Torsion.Field

/-!
AMP-Bench-mini, problème N4-03 (niveau N4).
Source : ProofNet# (jeu de données Hugging Face PAug/ProofNetSharp, partie test, révision
a8da405fbd1e348a87445c2e562c747b7e26dc8f), identifiant `Axler|exercise_1_4`. Licence MIT.
ProofNet# : Poiroux, Weiss, Kunčak, Bosselut (arXiv:2406.07222), version corrigée de ProofNet
(Azerbayev et al., arXiv:2302.12433).
Énoncé formel repris tel quel. Seuls changent le nom du théorème (`n4_03`) et les imports
(imports ciblés au lieu de `import Mathlib`). Les `open` de l'en-tête d'origine sont gardés tels quels.
-/

open Fintype Complex Polynomial LinearMap FiniteDimensional Module Module.End
open scoped BigOperators

theorem n4_03 {F V : Type*} [AddCommGroup V] [Field F]
  [Module F V] (v : V) (a : F): a • v = 0 → a = 0 ∨ v = 0 := by
  sorry
