import Mathlib.Tactic
import Mathlib.Analysis.SpecialFunctions.Log.Basic

/-!
AMP-Bench-mini, problème N3-07 (niveau N3).
Source : google-deepmind/miniF2F, fichier MiniF2F/Test.lean, théorème `aime_1983_p1`,
commit f0a20e14c1eeccd859d51bb4c2b3ee487889c303. Licence Apache-2.0.
Copyright (c) 2021 OpenAI. Auteurs du fichier source : Kunhao Zheng, Kudzo Ahegbebu,
Stanislas Polu, David Renshaw, OpenAI GPT-f.
Énoncé repris tel quel. Seuls changent le nom du théorème (`n3_07`) et les imports
(imports ciblés au lieu de `import MiniF2F.ProblemImports`, qui charge Mathlib en entier).
-/

open scoped Nat
open scoped Real

/--
Let $x$, $y$, and $z$ all exceed 1 and let $w$ be a positive number such that \[\log_x w = 24,\quad \log_y w = 40 \quad\text{and}\quad \log_{xyz} w = 12.\]  Find $\log_z w$. -/
theorem n3_07 (x y z w : ℕ) (ht : 1 < x ∧ 1 < y ∧ 1 < z) (hw : 0 ≤ w)
    (h0 : Real.log w / Real.log x = 24) (h1 : Real.log w / Real.log y = 40)
    (h2 : Real.log w / Real.log (x * y * z) = 12) : Real.log w / Real.log z = 60 := by
  sorry
