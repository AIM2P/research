import Mathlib.Tactic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic
import Mathlib.Data.Finset.Card

/-!
AMP-Bench-mini, problème N3-06 (niveau N3).
Source : google-deepmind/miniF2F, fichier MiniF2F/Test.lean, théorème `amc12a_2020_p9`,
commit f0a20e14c1eeccd859d51bb4c2b3ee487889c303. Licence Apache-2.0.
Copyright (c) 2021 OpenAI. Auteurs du fichier source : Kunhao Zheng, Kudzo Ahegbebu,
Stanislas Polu, David Renshaw, OpenAI GPT-f.
Énoncé repris tel quel. Seuls changent le nom du théorème (`n3_06`) et les imports
(imports ciblés au lieu de `import MiniF2F.ProblemImports`, qui charge Mathlib en entier).
-/

open scoped Nat
open scoped Real

/--
How many solutions does the equation $\tan{(2x)} = \cos{(\tfrac{x}{2})}$ have on the interval $[0, 2\pi]?$

$\textbf{(A) } 1 \qquad \textbf{(B) } 2 \qquad \textbf{(C) } 3 \qquad \textbf{(D) } 4 \qquad \textbf{(E) } 5$ -/
theorem n3_06 (S : Finset ℝ)
    (h₀ : ∀ x : ℝ, x ∈ S ↔ 0 ≤ x ∧ x ≤ 2 * Real.pi ∧ Real.tan (2 * x) = Real.cos (x / 2)) :
    S.card = 5 := by
  sorry
