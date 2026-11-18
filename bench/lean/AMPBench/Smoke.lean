import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic
import Physlib.Units.Dimension

/-!
# Test de fumée de l'environnement figé

Vérifie que Mathlib et Physlib (module `Units`, utile pour H3a) s'importent
avec Lean v4.35.0, et qu'une preuve simple passe le noyau en n'utilisant que
les axiomes standard (`propext`, `Quot.sound`, `Classical.choice`).
-/

namespace AMPBench.Smoke

/-- Identité trigonométrique élémentaire (Mathlib). -/
theorem cos_sq_add_sin_sq (x : ℝ) : Real.cos x ^ 2 + Real.sin x ^ 2 = 1 := by
  rw [add_comm]
  exact Real.sin_sq_add_cos_sq x

/-- Calcul exact : premier coefficient de Lanczos pour C(t) = cos³(αt),
b₁² = μ₂ = 3α² (problème candidat de la tranche N5, version numérique α = 1). -/
theorem lanczos_b1_sq_cos_cubed : (3 : ℚ) * 1 ^ 2 = 3 := by
  norm_num

end AMPBench.Smoke

#print axioms AMPBench.Smoke.cos_sq_add_sin_sq
