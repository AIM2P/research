# SPDX-License-Identifier: Apache-2.0
"""Correcteur des réponses fermées : extraction, lecture, formes équivalentes, listes ordonnées, mauvaise clé."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from harness.config import load_config
from harness.grade_answer import (answers_agree, extract_final_answer, grade_answer, parse_answer,
                                  symbols_for)
from harness.items import load_items

ACFG = load_config()["answers"]
ITEMS = load_items()


def out(ans: str) -> str:
    return f"Raisonnement…\nDonc le résultat suit.\nRéponse finale : {ans}\n"


class Extraction(unittest.TestCase):
    def test_final_line_variants(self):
        self.assertEqual(extract_final_answer(out("sqrt(2)"))[0], "sqrt(2)")
        self.assertEqual(extract_final_answer("**Réponse finale :** $\\sqrt{2}+\\sqrt{3}$.")[0], "\\sqrt{2}+\\sqrt{3}")
        self.assertEqual(extract_final_answer("Reponse finale: 42")[0], "42")
        # la dernière occurrence l'emporte
        self.assertEqual(extract_final_answer("Réponse finale : 1\n…\nRéponse finale : 2")[0], "2")

    def test_boxed_fallback_and_missing(self):
        ans, how = extract_final_answer("donc \\boxed{\\frac{1}{2}} est la valeur")
        self.assertEqual(ans, "\\frac{1}{2}")
        self.assertIn("boxed", how)
        self.assertIsNone(extract_final_answer("pas de réponse ici")[0])


class EquivalentForms(unittest.TestCase):
    def grade(self, key: str, ans: str, variables=(), assumptions=None):
        a = {"value": key, "variables": list(variables)}
        if assumptions:
            a["assumptions"] = assumptions
        return grade_answer(out(ans), a, ACFG)

    def test_exp3_vs_e_cubed(self):
        for ans in ("e**3", "e^3", "exp(3)", "E**3", "$e^{3}$", "\\exp(3)"):
            with self.subTest(ans=ans):
                self.assertEqual(self.grade("exp(3)", ans).verdict, "correct")

    def test_rationals_and_radicals(self):
        self.assertEqual(self.grade("1/3", "0.333333").verdict, "incorrect")   # approximation décimale refusée
        self.assertEqual(self.grade("sqrt(2)/2", "1/sqrt(2)").verdict, "correct")
        self.assertEqual(self.grade("sqrt(2)/2", "\\frac{\\sqrt{2}}{2}").verdict, "correct")
        self.assertEqual(self.grade("pi/4", "π/4").verdict, "correct")

    def test_dev03_expression_with_variable(self):
        a = ITEMS["DEV-03"].answer
        for ans in ("(3x^2+2x)e^{3x}", "x*(3*x + 2)*exp(3*x)", "2*x*exp(3*x) + 3*x**2*exp(3*x)", "(3x² + 2x)·e^(3x)"):
            with self.subTest(ans=ans):
                g = grade_answer(out(ans), a, ACFG)
                self.assertEqual(g.verdict, "correct", g.details)
        g = grade_answer(out("2*x*exp(3*x)"), a, ACFG)
        self.assertEqual(g.verdict, "incorrect")
        self.assertEqual(g.taxonomy, "H-e")

    def test_dev04_algebraic_number_minimal_polynomial(self):
        a = ITEMS["DEV-04"].answer
        g = grade_answer(out("sqrt(5 + 2*sqrt(6))"), a, ACFG)
        self.assertEqual(g.verdict, "correct", g.details)
        g = grade_answer(out("√3 - √2"), a, ACFG)
        self.assertEqual(g.verdict, "incorrect")
        self.assertTrue(g.details[0]["symbolic_definitive"])

    def test_wrong_key(self):
        g = self.grade("sqrt(2) + sqrt(5)", "sqrt(2) + sqrt(3)")
        self.assertEqual(g.verdict, "incorrect")
        self.assertEqual(g.error_class, "wrong_value")


class Lists(unittest.TestCase):
    def test_dev05_ordered_list(self):
        a = ITEMS["DEV-05"].answer
        for ans in ("[α, √2 α, √3 α, 2α, √5 α]", "[alpha, sqrt(2)*alpha, sqrt(3)*alpha, 2*alpha, sqrt(5)*alpha]",
                    "[\\alpha, \\sqrt{2}\\alpha, \\sqrt{3}\\alpha, 2\\alpha, \\sqrt{5}\\alpha]",
                    "[b₁ = α, b₂ = √2 α, b₃ = √3 α, b₄ = 2α, b₅ = √5 α]",
                    "[alpha, sqrt(2*alpha**2), sqrt(3*alpha^2), 2*alpha, alpha*sqrt(5)]"):
            with self.subTest(ans=ans):
                g = grade_answer(out(ans), a, ACFG)
                self.assertEqual(g.verdict, "correct", g.details)

    def test_list_order_matters(self):
        a = ITEMS["DEV-05"].answer
        g = grade_answer(out("[sqrt(5)*alpha, 2*alpha, sqrt(3)*alpha, sqrt(2)*alpha, alpha]"), a, ACFG)
        self.assertEqual(g.verdict, "incorrect")

    def test_list_shape(self):
        a = ITEMS["DEV-05"].answer
        self.assertEqual(grade_answer(out("[alpha, sqrt(2)*alpha]"), a, ACFG).error_class, "wrong_shape")
        self.assertEqual(grade_answer(out("alpha*sqrt(n)"), a, ACFG).verdict, "incorrect")


class Robustness(unittest.TestCase):
    def test_untrusted_input_is_never_evaluated(self):
        marker = Path(tempfile.gettempdir()) / "aim2p_pwned_marker"
        marker.unlink(missing_ok=True)
        payload = f"__import__('os').system('touch {marker}')"
        g = grade_answer(out(payload), {"value": "1", "variables": []}, ACFG)
        self.assertEqual(g.verdict, "incorrect")
        self.assertEqual(g.error_class, "unparseable")
        self.assertFalse(marker.exists())

    def test_no_final_answer(self):
        g = grade_answer("Je ne sais pas.", {"value": "1", "variables": []}, ACFG)
        self.assertEqual(g.verdict, "no_answer")

    def test_disagreement_goes_to_audit(self):
        # sans hypothèse de signe, sqrt(x**2) = x n'est pas établi symboliquement, mais les points
        # numériques (positifs) concordent : verdict « à auditer », jamais « correct » automatiquement
        g = grade_answer(out("sqrt(x**2)"), {"value": "x", "variables": ["x"]}, ACFG)
        self.assertIn(g.verdict, ("needs_audit", "correct"))
        if g.verdict == "correct":
            self.assertIn("math_verify", g.method)


class MajorityHelpers(unittest.TestCase):
    def test_answers_agree(self):
        syms = symbols_for(["x"])
        a, _, _ = parse_answer("(3x^2+2x)e^{3x}", syms)
        b, _, _ = parse_answer("x*(3*x+2)*exp(3*x)", syms)
        c, _, _ = parse_answer("2*x*exp(3*x)", syms)
        self.assertTrue(answers_agree(a, b, syms, ACFG))
        self.assertFalse(answers_agree(a, c, syms, ACFG))

    def test_b2_majority_vote_without_key(self):
        from harness.summarize import b2_answer_choice
        item = ITEMS["DEV-04"]
        answers = ["sqrt(3) - sqrt(2)", "sqrt(2) + sqrt(3)", "sqrt(5 + 2*sqrt(6))", "3.146", "sqrt(3) - sqrt(2)"]
        with tempfile.TemporaryDirectory() as d:
            recs = []
            for i, ans in enumerate(answers, start=1):
                p = Path(d) / f"s{i}.json"
                p.write_text(json.dumps({"response": {"choices": [{"message": {"content": out(ans)}}]}}))
                recs.append({"sample": i, "raw_response_path": str(p), "success": None})
            chosen = b2_answer_choice(recs, item, ACFG)
            # classes : {1, 5} (√3 − √2) et {2, 3} (√2 + √3), à égalité -> la classe du premier échantillon
            self.assertEqual(chosen["sample"], 1)
            recs[4]["raw_response_path"] = recs[1]["raw_response_path"]   # 3 voix pour √2 + √3
            self.assertEqual(b2_answer_choice(recs, item, ACFG)["sample"], 2)


if __name__ == "__main__":
    unittest.main()
