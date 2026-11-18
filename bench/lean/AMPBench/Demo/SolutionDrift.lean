import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic

/-! Énoncé modifié (≤ au lieu de =) : doit être refusé (dérive d'énoncé). -/
theorem demo_trig (x : ℝ) : Real.cos x ^ 2 + Real.sin x ^ 2 ≤ 1 :=
  le_of_eq (by rw [add_comm]; exact Real.sin_sq_add_cos_sq x)
