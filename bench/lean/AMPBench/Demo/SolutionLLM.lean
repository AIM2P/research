-- Preuve générée le 18 novembre 2026 par nvidia/nemotron-3-ultra-550b-a55b (OpenRouter, offre gratuite),
-- puis acceptée par `lake comparator` (comparator/demo_llm.json). Conservée telle que produite.
import Mathlib
import Aesop
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic

theorem demo_trig (x : ℝ) : Real.cos x ^ 2 + Real.sin x ^ 2 = 1 := by
  have h_main : Real.cos x ^ 2 + Real.sin x ^ 2 = 1 := by
    rw [Real.cos_sq_add_sin_sq]
    <;>
    simp [pow_two]
    <;>
    ring
    <;>
    norm_num
  
  rw [h_main]
  <;>
  norm_num
