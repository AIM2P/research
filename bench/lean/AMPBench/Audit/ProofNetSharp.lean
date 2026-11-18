import Mathlib.Tactic
import Mathlib.Topology.Separation.Regular
import Mathlib.Topology.Order
import Mathlib.Topology.UniformSpace.UniformConvergence
import Mathlib.Topology.MetricSpace.Pseudo.Defs
import Mathlib.Topology.MetricSpace.Pseudo.Lemmas
import Mathlib.Analysis.SpecialFunctions.ExpDeriv

/-!
# Audit d'AMP-Bench-mini : défauts trouvés dans ProofNet# (18 novembre 2026)

Lors du tirage des items N4, deux énoncés de ProofNet# (PAug/ProofNetSharp, partie test,
révision a8da405f) se sont révélés **faux tels que formalisés**. Ce fichier le démontre en Lean,
avec les seuls axiomes standard. Les deux items ont été rejetés et remplacés (voir
`bench/items/N4_selection.json`, champ `replacements`). Ces défauts sont peut-être déjà connus
des mainteneurs : à signaler en amont.

- Munkres 31.1 : `RegularSpace` de Mathlib n'inclut pas la condition T1 que Munkres met dans
  « régulier » ; un espace grossier à deux points contredit l'énoncé.
- Munkres 21.6b : dans `Icc 0 1`, les littéraux sont des entiers naturels ; le domaine est {0, 1}
  et xⁿ y converge uniformément.
-/

open Filter Set TopologicalSpace
open scoped Topology

/-- Munkres 31.1 as formalised in ProofNet# is false: indiscrete two-point space. -/
theorem munkres_31_1_false :
    ¬ (∀ {X : Type} [TopologicalSpace X], RegularSpace X → ∀ (x y : X), x ≠ y →
      ∃ (U V : Set X), IsOpen U ∧ IsOpen V ∧ x ∈ U ∧ y ∈ V ∧ closure U ∩ closure V = ∅) := by
  intro h
  let t : TopologicalSpace Bool := ⊤
  have hreg : RegularSpace Bool := by
    refine ⟨fun {s a} hs ha => ?_⟩
    rcases (TopologicalSpace.isOpen_top_iff sᶜ).1 hs.isOpen_compl with h1 | h1
    · have : s = univ := compl_empty_iff.mp h1
      exact absurd (this ▸ mem_univ a) ha
    · have : s = ∅ := compl_univ_iff.mp h1
      subst this
      simp
  obtain ⟨U, V, hU, hV, hxU, hyV, hUV⟩ := h hreg true false (by decide)
  rcases (TopologicalSpace.isOpen_top_iff U).1 hU with rfl | rfl
  · simp at hxU
  rcases (TopologicalSpace.isOpen_top_iff V).1 hV with rfl | rfl
  · simp at hyV
  rw [closure_univ, inter_self] at hUV
  exact univ_nonempty.ne_empty hUV

/-- Munkres 21.6b as formalised in ProofNet#: `Icc 0 1` elaborates in ℕ, and the
statement is false (uniform convergence on the two-point set {0, 1}). -/
theorem munkres_21_6b_false :
    ¬ (∀ (f : ℕ → Icc 0 1 → ℝ), (∀ x n, f n x = ↑x ^ n) →
      ¬ ∃ f₀, TendstoUniformly f f₀ atTop) := by
  intro h
  let f : ℕ → Icc 0 1 → ℝ := fun n x => ((x : ℕ) : ℝ) ^ n
  refine h f (fun x n => rfl) ⟨fun x => ((x : ℕ) : ℝ), ?_⟩
  refine Metric.tendstoUniformly_iff.2 fun ε hε => eventually_atTop.2 ⟨1, fun n hn x => ?_⟩
  obtain ⟨x, hx0, hx1⟩ := x
  interval_cases x <;> simp [f, Nat.pos_iff_ne_zero.mp hn, hε]

/-- Non-vacuity of `hfdiff` in putnam_2014_a1 (`⊤` = analytic): the hypothesis holds. -/
example : ContDiff ℝ ⊤ (fun x : ℝ => (1 - x + x ^ 2) * Real.exp x) := by
  fun_prop

#print axioms munkres_31_1_false
#print axioms munkres_21_6b_false
