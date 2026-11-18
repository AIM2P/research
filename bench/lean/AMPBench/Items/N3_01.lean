import Mathlib.Tactic
import Mathlib.Data.Real.Basic

/-!
AMP-Bench-mini, problème N3-01 (niveau N3).
Source : google-deepmind/miniF2F, fichier MiniF2F/Test.lean, théorème `mathd_algebra_141`,
commit f0a20e14c1eeccd859d51bb4c2b3ee487889c303. Licence Apache-2.0.
Copyright (c) 2021 OpenAI. Auteurs du fichier source : Kunhao Zheng, Kudzo Ahegbebu,
Stanislas Polu, David Renshaw, OpenAI GPT-f.
Énoncé repris tel quel. Seuls changent le nom du théorème (`n3_01`) et les imports
(imports ciblés au lieu de `import MiniF2F.ProblemImports`, qui charge Mathlib en entier).
-/

open scoped Nat
open scoped Real

/--
A rectangular patio has an area of $180$ square feet and a perimeter of $54$ feet. What is the length of the diagonal (in feet) squared? -/
theorem n3_01 (a b : ℝ) (h₁ : a * b = 180) (h₂ : 2 * (a + b) = 54) :
    a ^ 2 + b ^ 2 = 369 := by
  sorry
