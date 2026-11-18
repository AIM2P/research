import Mathlib.Tactic
import Mathlib.Analysis.Complex.Basic

/-!
AMP-Bench-mini, problème N4-06 (niveau N4).
Source : PutnamBench (github.com/trishullab/PutnamBench), fichier lean4/src/putnam_1989_a3.lean,
commit a635813f5edf297d928f9bd5ef8324a26bdde09c. Énoncés Lean 4 sous licence Apache-2.0.
Énoncé informel : concours William Lowell Putnam (MAA), diffusé par PutnamBench avec la
permission de la MAA ; non reproduit ici.
Les mainteneurs de PutnamBench demandent de ne pas écrire ni publier de preuve formelle :
aucune preuve de ce problème n'est publiée par AIM²P.
Énoncé formel repris tel quel. Seuls changent le nom du théorème (`n4_06`), les imports
(imports ciblés au lieu de `import Mathlib`) et la forme du `sorry` final (`:= by sorry`).
Les `open` de l'en-tête d'origine sont gardés tels quels.
-/

open Complex

-- Énoncé informel (MAA) non reproduit : voir PutnamBench, lean4/src/putnam_1989_a3.lean.
theorem n4_06
(z : ℂ)
(hz : 11 * z ^ 10 + 10 * I * z ^ 9 + 10 * I * z - 11 = 0)
: (‖z‖ = 1) := by
  sorry
