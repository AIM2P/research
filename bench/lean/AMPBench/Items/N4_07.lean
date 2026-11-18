import Mathlib.Tactic
import Mathlib.Analysis.Calculus.Taylor
import Mathlib.Analysis.SpecialFunctions.ExpDeriv
import Mathlib.Data.Nat.Prime.Basic

/-!
AMP-Bench-mini, problème N4-07 (niveau N4).
Source : PutnamBench (github.com/trishullab/PutnamBench), fichier lean4/src/putnam_2014_a1.lean,
commit a635813f5edf297d928f9bd5ef8324a26bdde09c. Énoncés Lean 4 sous licence Apache-2.0.
Énoncé informel : concours William Lowell Putnam (MAA), diffusé par PutnamBench avec la
permission de la MAA ; non reproduit ici.
Les mainteneurs de PutnamBench demandent de ne pas écrire ni publier de preuve formelle :
aucune preuve de ce problème n'est publiée par AIM²P.
Énoncé formel repris tel quel. Seuls changent le nom du théorème (`n4_07`), les imports
(imports ciblés au lieu de `import Mathlib`) et la forme du `sorry` final (`:= by sorry`).
Les `open` de l'en-tête d'origine sont gardés tels quels.
-/

open Topology Filter

-- Énoncé informel (MAA) non reproduit : voir PutnamBench, lean4/src/putnam_2014_a1.lean.
theorem n4_07
(f : ℝ → ℝ)
(hf : ∀ x : ℝ, f x = (1 - x + x ^ 2) * Real.exp x)
(hfdiff : ContDiff ℝ ⊤ f)
(c : ℕ → ℝ)
(hc : ∀ k : ℕ, c k = taylorCoeffWithin f k Set.univ 0)
: ∀ k : ℕ, c k ≠ 0 → ∃ q : ℚ, c k = q ∧ (q.num = 1 ∨ Prime q.num.natAbs) := by
  sorry
