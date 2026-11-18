import Mathlib.Tactic
import Mathlib.Analysis.Complex.Basic

/-!
AMP-Bench-mini, problème N4-08 (niveau N4).
Source : PutnamBench (github.com/trishullab/PutnamBench), fichier lean4/src/putnam_2020_b5.lean,
commit a635813f5edf297d928f9bd5ef8324a26bdde09c. Énoncés Lean 4 sous licence Apache-2.0.
Énoncé informel : concours William Lowell Putnam (MAA), diffusé par PutnamBench avec la
permission de la MAA ; non reproduit ici.
Les mainteneurs de PutnamBench demandent de ne pas écrire ni publier de preuve formelle :
aucune preuve de ce problème n'est publiée par AIM²P.
Énoncé formel repris tel quel. Seuls changent le nom du théorème (`n4_08`), les imports
(imports ciblés au lieu de `import Mathlib`) et la forme du `sorry` final (`:= by sorry`).
Les `open` de l'en-tête d'origine sont gardés tels quels.
-/

open Filter Topology Set

-- Énoncé informel (MAA) non reproduit : voir PutnamBench, lean4/src/putnam_2020_b5.lean.
theorem n4_08
(z : Fin 4 → ℂ)
(hzle1 : ∀ n, ‖z n‖ = 1)
(hzne1 : ∀ n, z n ≠ 1)
: 3 - z 0 - z 1 - z 2 - z 3 + (z 0) * (z 1) * (z 2) * (z 3) ≠ 0:= by
  sorry
