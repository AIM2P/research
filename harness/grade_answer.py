# SPDX-License-Identifier: Apache-2.0
"""Correcteur des problèmes à réponse fermée (document 04, §2 et §5.2, point 5).

Réussite vérifiée = réponse équivalente à la clé **à la fois** selon un critère symbolique et selon un
test numérique. Étapes :

1. extraction de la dernière ligne « Réponse finale : … » (à défaut : dernier ``\\boxed{…}``) ;
2. lecture : SymPy (``parse_expr`` sur une entrée filtrée par liste blanche, car la sortie du modèle
   n'est pas fiable) ou Math-Verify pour le LaTeX ; les listes sont découpées élément par élément ;
3. comparaison à la clé, élément par élément et dans l'ordre pour une liste :
   - symbolique : ``simplify(c − k) == 0``, sinon polynôme minimal de ``c − k`` pour un nombre
     algébrique (égal à X si et seulement si c = k), sinon ``math_verify.verify`` avec la clé
     canonique en premier argument (sa fonction est asymétrique) ;
   - numérique : évaluation à 50 chiffres en au moins 3 points tirés avec une graine fixe
     (ou directe pour une constante), tolérance relative 1e-10 ;
4. verdict : ``correct`` si les deux critères concluent à l'égalité, ``incorrect`` si aucun ne
   conclut, ``needs_audit`` en cas de désaccord (audit manuel exigé par le protocole).

La méthode qui a tranché est consignée. Un échec de ``simplify`` ne prouve pas l'inégalité.
"""
from __future__ import annotations

import contextlib
import random
import re
import signal
import threading
from dataclasses import dataclass, field

import sympy as sp
from sympy.parsing.sympy_parser import (convert_xor, implicit_application, implicit_multiplication,
                                        parse_expr, standard_transformations)

TRANSFORMS = standard_transformations + (convert_xor, implicit_multiplication, implicit_application)

FUNCTIONS = {
    "sqrt": sp.sqrt, "exp": sp.exp, "log": sp.log, "ln": sp.log, "sin": sp.sin, "cos": sp.cos,
    "tan": sp.tan, "cot": sp.cot, "sec": sp.sec, "csc": sp.csc, "sinh": sp.sinh, "cosh": sp.cosh,
    "tanh": sp.tanh, "coth": sp.coth, "sech": sp.sech, "csch": sp.csch, "asin": sp.asin,
    "acos": sp.acos, "atan": sp.atan, "arcsin": sp.asin, "arccos": sp.acos, "arctan": sp.atan,
    "asinh": sp.asinh, "acosh": sp.acosh, "atanh": sp.atanh, "Abs": sp.Abs, "abs": sp.Abs,
    "factorial": sp.factorial, "binomial": sp.binomial, "gamma": sp.gamma, "Rational": sp.Rational,
    "root": sp.root, "cbrt": sp.cbrt,
}
CONSTANTS = {"pi": sp.pi, "E": sp.E, "e": sp.E, "I": sp.I, "oo": sp.oo}

GREEK = {
    "α": "alpha", "β": "beta", "γ": "gamma_", "δ": "delta", "ε": "epsilon", "ζ": "zeta", "η": "eta",
    "θ": "theta", "κ": "kappa", "λ": "lamda", "μ": "mu", "ν": "nu", "ξ": "xi", "ρ": "rho",
    "σ": "sigma", "τ": "tau", "φ": "phi", "χ": "chi", "ψ": "psi", "ω": "omega", "ħ": "hbar",
}
SUPERSCRIPTS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
SUBSCRIPTS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")

FINAL_RE = re.compile(r"r[ée]ponse\s+finale\s*(?:\*\*)?\s*[:：]\s*(?P<ans>.+?)\s*$", re.I | re.M)
FINAL_EN_RE = re.compile(r"final\s+answer\s*(?:\*\*)?\s*[:：]\s*(?P<ans>.+?)\s*$", re.I | re.M)
SAFE_CHARS = re.compile(r"^[0-9A-Za-z_\s+\-*/^().,]*$")
IDENT = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")


@contextlib.contextmanager
def time_limit(seconds: float | None):
    """Délai maximal (SIGALRM, fil principal sous POSIX) ; sans effet ailleurs."""
    if not seconds or not hasattr(signal, "SIGALRM") or threading.current_thread() is not threading.main_thread():
        yield
        return

    def _raise(signum, frame):
        raise TimeoutError(f"délai de {seconds} s dépassé")

    old = signal.signal(signal.SIGALRM, _raise)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)


# --------------------------------------------------------------------------- extraction

def _last_boxed(text: str) -> str | None:
    i = text.rfind("\\boxed{")
    if i < 0:
        return None
    j, depth = i + len("\\boxed{"), 1
    k = j
    while k < len(text) and depth:
        depth += {"{": 1, "}": -1}.get(text[k], 0)
        k += 1
    return text[j:k - 1] if depth == 0 else None


def extract_final_answer(text: str) -> tuple[str | None, str]:
    """Renvoie (réponse brute, méthode d'extraction)."""
    m = list(FINAL_RE.finditer(text or ""))
    if m:
        return clean_answer(m[-1].group("ans")), "ligne « Réponse finale »"
    b = _last_boxed(text or "")
    if b is not None:
        return clean_answer(b), "dernier \\boxed"
    m = list(FINAL_EN_RE.finditer(text or ""))
    if m:
        return clean_answer(m[-1].group("ans")), "ligne « Final answer »"
    return None, "aucune"


def clean_answer(s: str) -> str:
    s = s.strip().strip("`").strip()
    s = re.sub(r"^\*\*|\*\*$", "", s).strip().rstrip(".").strip()
    b = _last_boxed(s)
    if b is not None:
        s = b
    for a, z in (("$$", "$$"), ("$", "$"), ("\\(", "\\)"), ("\\[", "\\]")):
        if s.startswith(a) and s.endswith(z) and len(s) > len(a) + len(z) - 1:
            s = s[len(a):len(s) - len(z)].strip()
    return s.rstrip(".").strip()


# --------------------------------------------------------------------------- lecture

def _split_top(s: str, sep: str) -> list[str]:
    parts, depth, cur = [], 0, []
    for ch in s:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return parts


def split_list(s: str) -> list[str] | None:
    """Découpe « [a, b, c] » ou « (a, b, c) » en éléments ; None si ce n'est pas une liste."""
    t = re.sub(r"\\left|\\right", "", s).strip()
    if len(t) >= 2 and ((t[0], t[-1]) in (("[", "]"), ("(", ")"))):
        inner = t[1:-1]
        parts = _split_top(inner, ",")
        if t[0] == "[" or len(parts) > 1:
            return [p.strip() for p in parts if p.strip()]
    return None


def _rhs(s: str) -> str:
    """« b_1 = α » -> « α » : garde ce qui suit le dernier « = » de premier niveau."""
    parts = _split_top(s, "=")
    return parts[-1].strip() if len(parts) > 1 else s.strip()


def normalize(s: str, symbols: dict | None = None) -> str:
    symbols = symbols or {}
    s = s.replace("−", "-").replace("–", "-").replace("×", "*").replace("·", "*").replace("⋅", "*")
    s = s.replace("∞", " oo ").replace("π", " pi ")
    s = re.sub(r"([⁰¹²³⁴⁵⁶⁷⁸⁹]+)", lambda m: "**" + m.group(1).translate(SUPERSCRIPTS), s)
    s = s.translate(SUBSCRIPTS)
    for g, name in GREEK.items():
        if name == "gamma_" and "gamma" in symbols:
            name = "gamma"
        s = s.replace(g, f" {name} ")
    s = re.sub(r"√\s*\(", "sqrt(", s)
    s = re.sub(r"√\s*(\d+(?:\.\d+)?|[A-Za-z_]\w*)", r"sqrt(\1)", s)
    # « 2alpha » -> « 2 alpha » (le tokeniseur de Python refuse un nombre collé à un nom),
    # sauf la notation scientifique (1e-5)
    s = re.sub(r"(?<![A-Za-z_\d.])(\d+(?:\.\d+)?)(?![eE][+-]?\d)([A-Za-z_])", r"\1 \2", s)
    return s.strip()


def looks_latex(s: str) -> bool:
    return "\\" in s or "^{" in s or "_{" in s or "{" in s


def symbols_for(variables: list[str], assumptions: dict | None = None) -> dict[str, sp.Symbol]:
    assumptions = assumptions or {}
    out = {}
    for v in variables:
        a = assumptions.get(v)
        out[v] = sp.Symbol(v, **({a: True} if a else {}))
    return out


def _local_dict(symbols: dict[str, sp.Symbol]) -> dict:
    d = dict(FUNCTIONS)
    d.update(CONSTANTS)
    d["gamma_"] = sp.Symbol("gamma")
    d.update(symbols)
    return d


def _safe_sympy(s: str, symbols: dict[str, sp.Symbol]):
    """``parse_expr`` sur une chaîne filtrée : caractères et identifiants en liste blanche seulement."""
    if not SAFE_CHARS.match(s) or "__" in s or re.search(r"\.\s*[A-Za-z_]", s):
        raise ValueError("caractères non autorisés")
    allowed = set(_local_dict(symbols))
    unknown = sorted({w for w in IDENT.findall(s) if w not in allowed})
    if unknown:
        raise ValueError(f"identifiants inconnus : {', '.join(unknown)}")
    return parse_expr(s, local_dict=_local_dict(symbols), transformations=TRANSFORMS, evaluate=True)


def _rename(expr, symbols: dict[str, sp.Symbol]):
    """Remplace les symboles lus par Math-Verify par ceux de l'item (mêmes noms, hypothèses de l'item)."""
    rep = {s: symbols[s.name] for s in expr.free_symbols if s.name in symbols}
    if any(s.name == "e" for s in expr.free_symbols) and "e" not in symbols:
        rep.update({s: sp.E for s in expr.free_symbols if s.name == "e"})
    return expr.xreplace(rep)


def _mathverify(s: str, symbols: dict[str, sp.Symbol], timeout: int):
    from math_verify import ExprExtractionConfig, LatexExtractionConfig, parse
    src = s if s.startswith("$") else f"${s}$"
    res = parse(src, extraction_config=[LatexExtractionConfig(), ExprExtractionConfig()], parsing_timeout=timeout)
    for r in res:
        if isinstance(r, sp.Basic):
            return _rename(r, symbols)
    return None


def parse_scalar(s: str, symbols: dict[str, sp.Symbol], mv_timeout: int = 5):
    """Renvoie (expression SymPy ou None, lecteur, message d'erreur)."""
    raw = _rhs(s)
    if looks_latex(raw):
        try:
            e = _mathverify(raw, symbols, mv_timeout)
            if e is not None:
                return e, "math_verify", ""
        except Exception as exc:  # noqa: BLE001
            err = f"math_verify : {exc}"
        else:
            err = "math_verify : aucune expression"
        return None, "", err
    t = normalize(raw, symbols)
    try:
        return _safe_sympy(t, symbols), "sympy", ""
    except Exception as exc:  # noqa: BLE001
        err = f"sympy : {exc}"
    try:
        e = _mathverify(raw, symbols, mv_timeout)
        if e is not None:
            return e, "math_verify", ""
    except Exception:  # noqa: BLE001
        pass
    return None, "", err


def parse_answer(s: str, symbols: dict[str, sp.Symbol], mv_timeout: int = 5):
    """Renvoie (valeur : expression ou liste d'expressions, lecteurs, erreur)."""
    elems = split_list(_rhs(s) if "=" in s and not s.strip().startswith(("[", "(")) else s)
    if elems is None:
        e, how, err = parse_scalar(s, symbols, mv_timeout)
        return e, how, err
    out, hows = [], []
    for el in elems:
        e, how, err = parse_scalar(el, symbols, mv_timeout)
        if e is None:
            return None, "", f"élément illisible {el!r} ({err})"
        out.append(e)
        hows.append(how)
    return out, "+".join(sorted(set(hows))), ""


def parse_key(value: str, symbols: dict[str, sp.Symbol]):
    k = sp.sympify(value, locals=symbols)
    if isinstance(k, (list, tuple, sp.Tuple)):
        return [sp.sympify(x) for x in k]
    return k


# --------------------------------------------------------------------------- comparaison

def numeric_points(names: list[str], n: int, seed: int, interval: tuple[float, float]) -> list[dict]:
    rng = random.Random(seed)
    lo, hi = interval
    return [{v: rng.uniform(lo, hi) for v in sorted(names)} for _ in range(max(1, n))]


def numeric_equal(c, k, symbols: dict[str, sp.Symbol], points: list[dict], rel_tol: float, dps: int):
    """Renvoie (égal ?, explication). Une constante est évaluée une fois ; sinon en chaque point."""
    try:
        free = c.free_symbols | k.free_symbols
    except AttributeError:
        return False, "valeur non symbolique"
    names = {s.name for s in free}
    extra = names - set(symbols)
    if extra:
        return False, f"symboles libres inattendus : {sorted(extra)}"
    pts = points if free else [{}]
    for pt in pts:
        subs = {s: sp.Float(pt[s.name], dps) for s in free}
        try:
            cv = complex(sp.N(c.subs(subs), dps))
            kv = complex(sp.N(k.subs(subs), dps))
        except (TypeError, ValueError, ZeroDivisionError) as exc:
            return False, f"évaluation impossible ({type(exc).__name__})"
        if any(x != x or abs(x) == float("inf") for x in (cv.real, cv.imag, kv.real, kv.imag)):
            return False, "valeur non finie"
        if abs(cv - kv) > rel_tol * max(1.0, abs(kv)):
            return False, f"écart numérique au point {pt}"
    return True, f"{len(pts)} point(s)"


def symbolic_equal(c, k, timeout: float, mv_timeout: int):
    """Renvoie (égal ? True/False, méthode, définitif ?)."""
    try:
        with time_limit(timeout):
            if sp.simplify(c - k) == 0:
                return True, "simplify", True
    except Exception:  # noqa: BLE001 - délai ou échec de SymPy : on tente la suite
        pass
    try:
        if not (c.free_symbols | k.free_symbols) and not c.has(sp.Float):
            with time_limit(timeout):
                X = sp.Dummy("X")
                mp = sp.minimal_polynomial(c - k, X)
            return (mp == X), "polynôme minimal", True
    except Exception:  # noqa: BLE001 - non algébrique (exp, pi…) ou délai
        pass
    if not c.has(sp.Float):
        try:
            from math_verify import verify
            if verify(k, c, timeout_seconds=mv_timeout):
                return True, "math_verify", False
        except Exception:  # noqa: BLE001
            pass
    return False, "non établi", False


@dataclass
class AnswerGrade:
    verdict: str                      # correct, incorrect, needs_audit, no_answer
    extracted: str | None
    extraction: str
    parsed: str | None = None
    reader: str = ""
    method: str = ""
    error_class: str | None = None
    taxonomy: str | None = None
    details: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return dict(self.__dict__)


def compare(cand, key, symbols, acfg: dict) -> tuple[str, str, list]:
    """Compare une réponse lue à la clé ; renvoie (verdict, méthode, détails par élément)."""
    if isinstance(key, list) != isinstance(cand, list):
        return "incorrect", "forme", [{"note": "liste attendue" if isinstance(key, list) else "valeur unique attendue"}]
    pairs = list(zip(cand, key)) if isinstance(key, list) else [(cand, key)]
    if isinstance(key, list) and len(cand) != len(key):
        return "incorrect", "forme", [{"note": f"{len(cand)} éléments au lieu de {len(key)}"}]
    pts = numeric_points(list(symbols), int(acfg["numeric_points"]), int(acfg["numeric_seed"]),
                         tuple(acfg["numeric_interval"]))
    details, verdicts, methods = [], [], set()
    for c, k in pairs:
        s_ok, s_how, s_def = symbolic_equal(c, k, float(acfg["simplify_timeout_s"]), int(acfg["mathverify_timeout_s"]))
        n_ok, n_how = numeric_equal(c, k, symbols, pts, float(acfg["numeric_rel_tol"]), int(acfg["numeric_dps"]))
        if s_ok and n_ok:
            v = "correct"
        elif not s_ok and not n_ok:
            v = "incorrect"
        else:
            v = "needs_audit"
        methods.add(f"{s_how}+numérique" if v == "correct" else s_how)
        verdicts.append(v)
        details.append({"candidate": str(c), "symbolic": s_ok, "symbolic_method": s_how,
                        "symbolic_definitive": s_def, "numeric": n_ok, "numeric_note": n_how, "verdict": v})
    if all(v == "correct" for v in verdicts):
        return "correct", ", ".join(sorted(methods)), details
    if any(v == "incorrect" for v in verdicts):
        return "incorrect", ", ".join(sorted(methods)), details
    return "needs_audit", ", ".join(sorted(methods)), details


def grade_answer(text: str, answer: dict, acfg: dict) -> AnswerGrade:
    """Note une sortie de modèle contre la table [answer] d'un item (value, variables, assumptions)."""
    symbols = symbols_for(answer.get("variables", []), answer.get("assumptions"))
    extracted, how = extract_final_answer(text)
    if extracted is None or not extracted.strip():
        return AnswerGrade("no_answer", None, how, error_class="no_final_answer")
    cand, reader, err = parse_answer(extracted, symbols, int(acfg["mathverify_timeout_s"]))
    if cand is None:
        return AnswerGrade("incorrect", extracted, how, error_class="unparseable", taxonomy="H-e",
                           details=[{"note": err}])
    key = parse_key(answer["value"], symbols)
    verdict, method, details = compare(cand, key, symbols, acfg)
    parsed = str(cand) if not isinstance(cand, list) else "[" + ", ".join(map(str, cand)) + "]"
    ec = {"correct": None, "incorrect": "wrong_value", "needs_audit": "needs_audit"}[verdict]
    if verdict == "incorrect" and method == "forme":
        ec = "wrong_shape"
    return AnswerGrade(verdict, extracted, how, parsed=parsed, reader=reader, method=method, error_class=ec,
                       taxonomy="H-e" if verdict == "incorrect" else None, details=details)


def answers_agree(a, b, symbols, acfg: dict) -> bool:
    """Équivalence entre deux réponses lues (sans la clé), pour le vote majoritaire de B2."""
    if isinstance(a, list) != isinstance(b, list):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(answers_agree(x, y, symbols, acfg) for x, y in zip(a, b))
    pts = numeric_points(list(symbols), int(acfg["numeric_points"]), int(acfg["numeric_seed"]),
                         tuple(acfg["numeric_interval"]))
    ok, _ = numeric_equal(a, b, symbols, pts, float(acfg["numeric_rel_tol"]), int(acfg["numeric_dps"]))
    if ok:
        return True
    s_ok, _, _ = symbolic_equal(a, b, float(acfg["simplify_timeout_s"]), int(acfg["mathverify_timeout_s"]))
    return s_ok
