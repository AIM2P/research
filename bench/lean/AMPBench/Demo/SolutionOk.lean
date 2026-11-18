import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic

/-! Solution correcte : doit être acceptée. -/
theorem demo_trig (x : ℝ) : Real.cos x ^ 2 + Real.sin x ^ 2 = 1 := by
  rw [add_comm]
  exact Real.sin_sq_add_cos_sq x
