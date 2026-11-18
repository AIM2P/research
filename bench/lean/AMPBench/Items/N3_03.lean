import Mathlib.Tactic

/-!
AMP-Bench-mini, problème N3-03 (niveau N3).
Source : google-deepmind/miniF2F, fichier MiniF2F/Test.lean, théorème `mathd_numbertheory_517`,
commit f0a20e14c1eeccd859d51bb4c2b3ee487889c303. Licence Apache-2.0.
Copyright (c) 2021 OpenAI. Auteurs du fichier source : Kunhao Zheng, Kudzo Ahegbebu,
Stanislas Polu, David Renshaw, OpenAI GPT-f.
Énoncé repris tel quel. Seuls changent le nom du théorème (`n3_03`) et les imports
(imports ciblés au lieu de `import MiniF2F.ProblemImports`, qui charge Mathlib en entier).
-/

open scoped Nat
open scoped Real

/-- Find the modulo 4 residue of $121 \cdot 122 \cdot 123$. -/
theorem n3_03 : 121 * 122 * 123 % 4 = 2 := by
  sorry
