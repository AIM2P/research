import Mathlib.Tactic
import Mathlib.Data.Set.Defs

/-!
AMP-Bench-mini, problème N3-08 (niveau N3).
Source : google-deepmind/miniF2F, fichier MiniF2F/Test.lean, théorème `imo_1997_p5`,
commit f0a20e14c1eeccd859d51bb4c2b3ee487889c303. Licence Apache-2.0.
Copyright (c) 2021 OpenAI. Auteurs du fichier source : Kunhao Zheng, Kudzo Ahegbebu,
Stanislas Polu, David Renshaw, OpenAI GPT-f.
Énoncé repris tel quel. Seuls changent le nom du théorème (`n3_08`) et les imports
(imports ciblés au lieu de `import MiniF2F.ProblemImports`, qui charge Mathlib en entier).
-/

open scoped Nat
open scoped Real

/-- Find all pairs $ (a,b)$ of positive integers that satisfy the equation: $ a^{b^2} ={} b^a$. -/
theorem n3_08 :
    {(x, y) | (x : ℕ) (y : ℕ) (h₀ : 0 < x ∧ 0 < y) (h₁ : x ^ y ^ 2 = y ^ x) }
      = {(1, 1), (16, 2), (27, 3)} := by
  sorry
