import Mathlib.Tactic
import Mathlib.Topology.MetricSpace.Basic
import Mathlib.Topology.Bases
import Mathlib.Topology.EMetricSpace.Basic
import Mathlib.Topology.Compactness.SigmaCompact

/-!
AMP-Bench-mini, problème N4-02 (niveau N4).
Source : ProofNet# (jeu de données Hugging Face PAug/ProofNetSharp, partie test, révision
a8da405fbd1e348a87445c2e562c747b7e26dc8f), identifiant `Rudin|exercise_2_25`. Licence MIT.
ProofNet# : Poiroux, Weiss, Kunčak, Bosselut (arXiv:2406.07222), version corrigée de ProofNet
(Azerbayev et al., arXiv:2302.12433).
Énoncé formel repris tel quel. Seuls changent le nom du théorème (`n4_02`) et les imports
(imports ciblés au lieu de `import Mathlib`). Les `open` de l'en-tête d'origine sont gardés tels quels.
-/

open Topology Filter Real Complex TopologicalSpace Finset
open scoped BigOperators

theorem n4_02 {K : Type*} [MetricSpace K] [CompactSpace K] :
  ∃ (B : Set (Set K)), Set.Countable B ∧ IsTopologicalBasis B := by
  sorry
