-- SPDX-License-Identifier: Apache-2.0
-- Preuve de référence du problème de développement DEV-02 (test du harnais, jamais montrée au modèle).
theorem dev_02 (a : ℤ) : a ^ 2 % 3 = 0 ∨ a ^ 2 % 3 = 1 := by
  have h : a % 3 = 0 ∨ a % 3 = 1 ∨ a % 3 = 2 := by omega
  rcases h with h | h | h <;> simp [pow_two, Int.mul_emod, h]
