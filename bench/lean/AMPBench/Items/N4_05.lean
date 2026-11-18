import Mathlib.Tactic
import Mathlib.Data.Set.Card

/-!
AMP-Bench-mini, problème N4-05 (niveau N4).
Source : PutnamBench (github.com/trishullab/PutnamBench), fichier lean4/src/putnam_1988_b6.lean,
commit a635813f5edf297d928f9bd5ef8324a26bdde09c. Énoncés Lean 4 sous licence Apache-2.0.
Énoncé informel : concours William Lowell Putnam (MAA), diffusé par PutnamBench avec la
permission de la MAA ; non reproduit ici.
Les mainteneurs de PutnamBench demandent de ne pas écrire ni publier de preuve formelle :
aucune preuve de ce problème n'est publiée par AIM²P.
Énoncé formel repris tel quel. Seuls changent le nom du théorème (`n4_05`), les imports
(imports ciblés au lieu de `import Mathlib`) et la forme du `sorry` final (`:= by sorry`).
Les `open` de l'en-tête d'origine sont gardés tels quels.
-/

open Set Filter Topology

-- Énoncé informel (MAA) non reproduit : voir PutnamBench, lean4/src/putnam_1988_b6.lean.
theorem n4_05
(trinums : Set ℤ)
(htrinums : trinums = {t : ℤ | ∃ n : ℤ, t ≥ 0 ∧ t = (n * (n + 1)) / 2})
: {(a, b) : ℤ × ℤ | ∀ t > 0, (a * t + b) ∈ trinums ↔ t ∈ trinums}.encard = ⊤ := by
  sorry
