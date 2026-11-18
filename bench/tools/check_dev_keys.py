#!/usr/bin/env python3
"""Vérifie les clés des problèmes de développement à réponse fermée (DEV-03, DEV-04, DEV-05).

Chaque clé est confirmée par deux méthodes indépendantes (calcul exact SymPy, puis calcul numérique
mpmath ou une seconde voie exacte). Les problèmes de développement sont publics et ne sont jamais évalués.

Usage (environnement épinglé SymPy 1.14.0 / mpmath 1.3.0, par exemple ~/aim2p-venv sous WSL) :
  python -I bench/tools/check_dev_keys.py

Code sous licence Apache-2.0 (voir bench/LICENSE).
"""
from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import mpmath
import sympy as sp

ITEMS = Path(__file__).resolve().parent.parent / "items"


def key(item_id: str):
    it = tomllib.loads((ITEMS / f"{item_id}.toml").read_text(encoding="utf-8"))
    ans = it["answer"]
    assumptions = ans.get("assumptions", {})
    syms = {v: sp.Symbol(v, **({assumptions[v]: True} if v in assumptions else {})) for v in ans.get("variables", [])}
    return sp.sympify(ans["value"], locals=syms), syms


def check_dev03() -> bool:
    k, syms = key("DEV-03")
    x = syms["x"]
    f = x**2 * sp.exp(3 * x)
    exact = sp.simplify(sp.diff(f, x) - k) == 0                       # méthode 1 : dérivation exacte
    mpmath.mp.dps = 40
    fn = sp.lambdify(x, f, "mpmath")
    kn = sp.lambdify(x, k, "mpmath")
    numeric = all(abs(mpmath.diff(fn, t) - kn(t)) < mpmath.mpf(10) ** -25  # méthode 2 : dérivée numérique
                  for t in (mpmath.mpf("-1.3"), mpmath.mpf("0.4"), mpmath.mpf("2.1")))
    print(f"DEV-03  f'(x) = {k}  exact={exact}  numérique={numeric}")
    return exact and numeric


def check_dev04() -> bool:
    k, _ = key("DEV-04")
    X = sp.Symbol("X")
    p = X**4 - 10 * X**2 + 1
    exact = sp.expand(p.subs(X, k)) == 0 and sp.minimal_polynomial(k, X) == p    # méthode 1 : racine exacte
    roots = sorted(sp.re(r) for r in sp.Poly(p, X).nroots(n=40))                  # méthode 2 : racines numériques
    mpmath.mp.dps = 40
    largest = max(mpmath.polyroots([1, 0, -10, 0, 1], extraprec=80), key=lambda z: mpmath.re(z))
    numeric = abs(mpmath.re(largest) - sp.N(k, 40)) < 1e-30 and abs(roots[-1] - sp.N(k, 40)) < 1e-30
    print(f"DEV-04  plus grande racine = {k}  exact={exact}  numérique={numeric}  racines={[float(r) for r in roots]}")
    return bool(exact and numeric)


def lanczos_from_moments(mu: list, n: int) -> list:
    """Méthode 1 : récursion des moments (Viswanath–Müller ; Parker et al., 2019, annexe), cas aₙ = 0."""
    M = {(-1, l): 0 for l in range(n + 1)}
    M.update({(0, l): mu[2 * l] for l in range(n + 1)})
    b2 = {-1: 1, 0: 1}
    for j in range(1, n + 1):
        for l in range(j, n + 1):
            M[(j, l)] = sp.simplify(M[(j - 1, l)] / b2[j - 1] - M[(j - 2, l - 1)] / b2[j - 2])
        b2[j] = M[(j, j)]
    return [sp.sqrt(b2[j]) for j in range(1, n + 1)]


def lanczos_hankel(mu: list, n: int) -> list:
    """Méthode 2 : déterminants de Hankel, bₙ² = Δₙ₋₂ Δₙ / Δₙ₋₁², Δₘ = det(μ_{i+j})_{0 ≤ i, j ≤ m}."""
    def delta(m):
        return 1 if m < 0 else sp.Matrix(m + 1, m + 1, lambda i, j: mu[i + j]).det()
    return [sp.sqrt(sp.simplify(delta(j - 2) * delta(j) / delta(j - 1) ** 2)) for j in range(1, n + 1)]


def check_dev05() -> bool:
    k, syms = key("DEV-05")
    a = syms["alpha"]
    t = sp.Symbol("t", real=True)
    n = 5
    # moments pairs μ₂ₖ = (2k−1)!! α²ᵏ, impairs nuls ; contrôle : ce sont ceux de C(t) = exp(−α²t²/2)
    mu = [0 if m % 2 else sp.factorial2(m - 1) * a**m for m in range(2 * n + 2)]
    series = sp.series(sp.exp(-a**2 * t**2 / 2), t, 0, 2 * n + 2).removeO()
    from_c = all(sp.simplify((-1) ** (m // 2) * mu[m] / sp.factorial(m) - series.coeff(t, m)) == 0
                 for m in range(0, 2 * n + 2, 2))
    m1 = lanczos_from_moments(mu, n)
    m2 = lanczos_hankel(mu, n)
    ok1 = all(sp.simplify(u - v) == 0 for u, v in zip(m1, k))
    ok2 = all(sp.simplify(u - v) == 0 for u, v in zip(m2, k))
    print(f"DEV-05  b₁…b₅ = {list(k)}  moments↔C(t)={from_c}  récursion={ok1} {m1}  Hankel={ok2} {m2}")
    return from_c and ok1 and ok2 and len(k) == n


def main() -> int:
    print(f"SymPy {sp.__version__}, mpmath {mpmath.__version__}")
    results = [check_dev03(), check_dev04(), check_dev05()]
    print("clés DEV : OK" if all(results) else "clés DEV : ÉCHEC")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
