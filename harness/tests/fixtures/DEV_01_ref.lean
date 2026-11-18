-- SPDX-License-Identifier: Apache-2.0
-- Preuve de référence du problème de développement DEV-01 (test du harnais, jamais montrée au modèle).
theorem dev_01 (n : ℕ) : ∑ k ∈ Finset.range n, (2 * k + 1) = n ^ 2 := by
  induction n with
  | zero => simp
  | succ n ih =>
    rw [Finset.sum_range_succ, ih]
    ring
