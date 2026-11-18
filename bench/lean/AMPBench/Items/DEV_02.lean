import Mathlib.Tactic

/-!
AMP-Bench-mini, problème de DÉVELOPPEMENT DEV-02 (jamais évalué ; sert aux pilotes de P3).
Source : google-deepmind/miniF2F, fichier MiniF2F/Valid.lean, théorème `numbertheory_sqmod3in01d`,
commit f0a20e14c1eeccd859d51bb4c2b3ee487889c303. Licence Apache-2.0.
Copyright (c) 2021 OpenAI. Auteurs du fichier source : Kunhao Zheng, Stanislas Polu,
David Renshaw, OpenAI GPT-f.
Tirage reproductible (graine 20261118) : bench/items/DEV_selection.json.
Énoncé repris tel quel. Seuls changent le nom du théorème (`dev_02`) et les imports
(imports ciblés au lieu de `import MiniF2F.ProblemImports`, qui charge Mathlib en entier).
-/

open scoped Nat
open scoped Real

/-- Show that a square number must either be a multiple of 3 or have a remainder of 1 when divided by 3. -/
theorem dev_02 (a : ℤ) : a ^ 2 % 3 = 0 ∨ a ^ 2 % 3 = 1 := by
  sorry
