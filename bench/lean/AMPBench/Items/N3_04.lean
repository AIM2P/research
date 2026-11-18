import Mathlib.Tactic
import Mathlib.Order.Bounds.Basic
import Mathlib.Data.Nat.GCD.Basic

/-!
AMP-Bench-mini, problème N3-04 (niveau N3).
Source : google-deepmind/miniF2F, fichier MiniF2F/Test.lean, théorème `mathd_numbertheory_277`,
commit f0a20e14c1eeccd859d51bb4c2b3ee487889c303. Licence Apache-2.0.
Copyright (c) 2021 OpenAI. Auteurs du fichier source : Kunhao Zheng, Kudzo Ahegbebu,
Stanislas Polu, David Renshaw, OpenAI GPT-f.
Énoncé repris tel quel. Seuls changent le nom du théorème (`n3_04`) et les imports
(imports ciblés au lieu de `import MiniF2F.ProblemImports`, qui charge Mathlib en entier).
-/

open scoped Nat
open scoped Real

/--
The greatest common divisor of positive integers $m$ and $n$ is 6. The least common multiple of $m$ and $n$ is 126. What is the least possible value of $m+n$? -/
theorem n3_04 :
    IsLeast
       {(m + n) | (m : ℕ) (n : ℕ) (h₀ : Nat.gcd m n = 6) (h₁ : Nat.lcm m n = 126)}
      60 := by
  sorry
