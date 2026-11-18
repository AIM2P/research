# SPDX-License-Identifier: Apache-2.0
"""Correcteur des preuves : extraction, en-tête imposé, filtre de source, classement des sorties.

La classe ``Comparator`` lance réellement ``lake comparator`` (WSL, ~15 à 30 s par cas) sur les démos de
bench/lean/AMPBench/Demo et sur les problèmes de développement. Elle est sautée si ``lake`` est absent
ou si AIM2P_SKIP_LEAN=1.
"""
from __future__ import annotations

import os
import shutil
import unittest
from pathlib import Path

from harness import BENCH
from harness.config import load_config
from harness.grade_proof import (LeanEnv, build_solution, classify_comparator, drop_imports, extract_lean_block,
                                 grade_proof, lean_error_category, source_filter)
from harness.items import load_challenge, load_items, parse_challenge

CFG = load_config()
DEMO = BENCH / "lean" / "AMPBench" / "Demo"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
CHALLENGE = parse_challenge((DEMO / "Challenge.lean").read_text(encoding="utf-8"), "demo_trig")


def as_model_output(code: str) -> str:
    return f"Voici la preuve.\n\n```lean\n{code}\n```\n"


class Challenges(unittest.TestCase):
    def test_all_public_challenges_split_cleanly(self):
        items = load_items()
        for it in items.values():
            if it.kind != "proof" or it.visibility != "public":
                continue
            with self.subTest(item=it.id):
                ch = load_challenge(it)
                self.assertTrue(ch.header_code.startswith("import "))
                self.assertNotIn("sorry", ch.header_code)
                self.assertTrue(ch.theorem.rstrip().endswith("sorry"))
                self.assertIn(f"theorem {it.lean['theorem']}", ch.theorem)
                self.assertEqual(ch.trailer, "")

    def test_header_is_everything_before_theorem_docstring(self):
        it = load_items()["DEV-01"]
        ch = load_challenge(it)
        self.assertTrue(ch.theorem.startswith("/-- Show that"))
        self.assertTrue(ch.header.rstrip().endswith("open scoped Real"))
        self.assertEqual(ch.imports, ["Mathlib.Tactic", "Mathlib.Algebra.BigOperators.Group.Finset.Basic"])


class Extraction(unittest.TestCase):
    def test_prefers_last_block_declaring_theorem(self):
        text = ("```lean\ntheorem demo_trig (x : ℝ) : 1 = 1 := rfl\n```\nautre essai :\n"
                "```lean\nlemma aux : True := trivial\n```\n```lean4\ntheorem demo_trig (x : ℝ) : 2 = 2 := rfl\n```")
        code, note = extract_lean_block(text, "demo_trig")
        self.assertIn("2 = 2", code)
        self.assertIn("déclarant", note)

    def test_missing_or_truncated(self):
        self.assertIsNone(extract_lean_block("pas de code", "demo_trig")[0])
        code, note = extract_lean_block("```lean\ntheorem demo_trig : True := by\n  trivi", "demo_trig")
        self.assertIsNone(code)
        self.assertIn("non fermé", note)

    def test_drop_imports(self):
        body, dropped = drop_imports("import Mathlib\nimport Aesop\n\ntheorem t : True := trivial\n")
        self.assertEqual(dropped, ["import Mathlib", "import Aesop"])
        self.assertNotIn("import", body)

    def test_solution_uses_exact_challenge_header(self):
        llm = (DEMO / "SolutionLLM.lean").read_text(encoding="utf-8")
        body, dropped = drop_imports(extract_lean_block(as_model_output(llm), "demo_trig")[0])
        sol = build_solution(CHALLENGE, body)
        self.assertTrue(sol.startswith(CHALLENGE.header))
        self.assertNotIn("import Mathlib\n", sol)
        self.assertEqual(sum(1 for ln in sol.splitlines() if ln.startswith("import ")), 1)
        self.assertIn("import Mathlib", dropped)


class SourceFilter(unittest.TestCase):
    def test_forbidden_words(self):
        forbidden = CFG["lean"]["forbidden"]
        self.assertEqual(source_filter("theorem t : P := by sorry", forbidden), ["sorry"])
        self.assertEqual(source_filter("axiom cheat : False\ntheorem t : P := cheat.elim", forbidden), ["axiom"])
        self.assertEqual(source_filter("theorem t : 2 + 2 = 4 := by native_decide", forbidden), ["native_decide"])
        self.assertEqual(source_filter("set_option debug.skipKernelTC true in\ntheorem t : P := x", forbidden),
                         ["debug.skipKernelTC"])
        self.assertEqual(source_filter("@[implemented_by f] def g := 1", forbidden), ["implemented_by"])
        self.assertEqual(source_filter("theorem t : P := by admit", forbidden), ["admit"])

    def test_comments_and_identifiers_are_not_hits(self):
        forbidden = CFG["lean"]["forbidden"]
        code = "-- aucun sorry ici\n/- ni axiom -/\n/-- doc : native_decide -/\ntheorem sorry_free_axioms : True := trivial"
        self.assertEqual(source_filter(code, forbidden), [])


class Classification(unittest.TestCase):
    SOL = "AMPBench/Solutions/c/I/R1S1.lean"

    def test_comparator_outputs(self):
        ok = "Running Lean default kernel on solution\nLean default kernel accepts the solution\nYour solution is okay!\n"
        self.assertEqual(classify_comparator(0, ok, False, self.SOL).verdict, "accepted")
        g = classify_comparator(1, "Build completed successfully.\nerror: Illegal axiom detected: 'sorryAx'\n", False, self.SOL)
        self.assertEqual((g.verdict, g.error_class, g.taxonomy), ("illegal_axiom", "axiom:sorryAx", "H-a"))
        g = classify_comparator(1, "error: Challenge and solution theorem statement do not match: 'demo_trig'\n", False, self.SOL)
        self.assertEqual((g.verdict, g.taxonomy), ("statement_mismatch", "H-b"))
        out = (f"✖ [1/1] Building X\nerror: {self.SOL}:5:8: Unknown constant `Real.foo`\n"
               "Some required targets logged failures:\n- X\nerror: build failed\n")
        g = classify_comparator(1, out, False, self.SOL)
        self.assertEqual((g.verdict, g.error_class, g.taxonomy), ("build_error", "unknown_identifier", "H-c"))
        g = classify_comparator(None, "", True, self.SOL)
        self.assertEqual((g.verdict, g.error_class), ("build_error", "timeout"))

    def test_error_categories(self):
        self.assertEqual(lean_error_category("unknown identifier 'foo'"), "unknown_identifier")
        self.assertEqual(lean_error_category("type mismatch\n  h\nhas type"), "type_mismatch")
        self.assertEqual(lean_error_category("failed to synthesize\n  OfNat ℝ 2"), "typeclass")
        self.assertEqual(lean_error_category("(deterministic) timeout at `whnf`, maximum number of heartbeats"), "timeout")
        self.assertEqual(lean_error_category("unsolved goals\nx : ℝ"), "unsolved_goals")
        self.assertEqual(lean_error_category("linarith failed to find a contradiction"), "tactic_failed")
        self.assertEqual(lean_error_category("quelque chose d'autre"), "other")


LEAN_OK = shutil.which("lake", path=os.path.expanduser(CFG["lean"]["elan_bin"])) is not None and \
    os.environ.get("AIM2P_SKIP_LEAN") != "1" and Path(os.path.expanduser(CFG["lean"]["project"])).is_dir()


@unittest.skipUnless(LEAN_OK, "lake comparator indisponible (WSL) ou AIM2P_SKIP_LEAN=1")
class Comparator(unittest.TestCase):
    """Cas réels dans le bac à sable bwrap (campagne « tests », fichiers hors dépôt)."""

    @classmethod
    def setUpClass(cls):
        cls.env = LeanEnv.from_config(CFG)
        cls.env.sync_bench()
        cls.gcfg = dict(CFG["lean"])

    def run_demo(self, code: str, tag: str, apply_filter=True):
        return grade_proof(as_model_output(code), "demo_trig", "AMPBench.Demo.Challenge", CHALLENGE, self.env,
                           self.gcfg, "tests", "Demo", tag, apply_filter=apply_filter)

    def demo(self, name: str) -> str:
        return (DEMO / f"{name}.lean").read_text(encoding="utf-8")

    def test_solution_ok_accepted(self):
        g = self.run_demo(self.demo("SolutionOk"), "Ok")
        self.assertEqual(g.verdict, "accepted", g.first_error)

    def test_solution_llm_accepted_with_imposed_header(self):
        g = self.run_demo(self.demo("SolutionLLM"), "LLM")
        self.assertEqual(g.verdict, "accepted", g.first_error)
        self.assertIn("import Mathlib", g.dropped_imports)

    def test_solution_sorry_illegal_axiom(self):
        g = self.run_demo(self.demo("SolutionSorry"), "SorryFiltered")
        self.assertEqual((g.verdict, g.error_class), ("illegal_axiom", "source_filter:sorry"))
        self.assertIsNone(g.comparator_rc)                  # arrêté par le filtre, avant Lean
        g = self.run_demo(self.demo("SolutionSorry"), "Sorry", apply_filter=False)
        self.assertEqual((g.verdict, g.error_class), ("illegal_axiom", "axiom:sorryAx"))

    def test_solution_drift_mismatch(self):
        g = self.run_demo(self.demo("SolutionDrift"), "Drift")
        self.assertEqual(g.verdict, "statement_mismatch")

    def test_build_errors_are_categorised(self):
        g = self.run_demo("theorem demo_trig (x : ℝ) : Real.cos x ^ 2 + Real.sin x ^ 2 = 1 := by\n"
                          "  exact Real.cos_sq_add_sin_sq_inexistant x", "UnknownId")
        self.assertEqual((g.verdict, g.error_class, g.taxonomy), ("build_error", "unknown_identifier", "H-c"))
        g = self.run_demo("theorem demo_trig (x : ℝ) : Real.cos x ^ 2 + Real.sin x ^ 2 = 1 :=\n"
                          "  Real.sin_sq_add_cos_sq x", "Mismatch")
        self.assertEqual((g.verdict, g.error_class), ("build_error", "type_mismatch"), g.first_error)

    def test_dev_reference_proofs_accepted(self):
        items = load_items()
        for iid in ("DEV-01", "DEV-02"):
            with self.subTest(item=iid):
                it = items[iid]
                code = (FIXTURES / f"{it.lean_id}_ref.lean").read_text(encoding="utf-8")
                g = grade_proof(as_model_output(code), it.lean["theorem"], it.lean["module"], load_challenge(it),
                                self.env, self.gcfg, "tests", it.lean_id, "Ref")
                self.assertEqual(g.verdict, "accepted", g.first_error)


if __name__ == "__main__":
    unittest.main()
