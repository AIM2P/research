import Mathlib.Tactic
import Mathlib.Algebra.BigOperators.Group.Finset.Basic

/-!
AMP-Bench-mini, problème de DÉVELOPPEMENT DEV-01 (jamais évalué ; sert aux pilotes de P3).
Source : google-deepmind/miniF2F, fichier MiniF2F/Valid.lean, théorème `induction_sum_odd`,
commit f0a20e14c1eeccd859d51bb4c2b3ee487889c303. Licence Apache-2.0.
Copyright (c) 2021 OpenAI. Auteurs du fichier source : Kunhao Zheng, Stanislas Polu,
David Renshaw, OpenAI GPT-f.
Tirage reproductible (graine 20261118) : bench/items/DEV_selection.json.
Énoncé repris tel quel. Seuls changent le nom du théorème (`dev_01`) et les imports
(imports ciblés au lieu de `import MiniF2F.ProblemImports`, qui charge Mathlib en entier).
-/

open scoped Nat
open scoped Real

/-- Show that the sum of the first $n$ odd numbers is $n^2$. -/
theorem dev_01 (n : ℕ) : ∑ k ∈ Finset.range n, (2 * k + 1) = n ^ 2 := by
  sorry
