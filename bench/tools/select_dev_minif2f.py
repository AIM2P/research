#!/usr/bin/env python3
"""Tirage reproductible des problèmes de DÉVELOPPEMENT de preuve (DEV-…) dans miniF2F, partie Valid.

Ces problèmes servent aux pilotes de la phase P3 (harnais, coûts, prompts) et ne sont jamais évalués.
Ils viennent de MiniF2F/Valid.lean (jamais de Test.lean, d'où sont tirés les problèmes N3 figés).

Méthode, reprise de select_minif2f.py :
- découpage des blocs `theorem … := by sorry` avec la même expression régulière ;
- exclusion des énoncés qui dépendent de FormalConjectures (`answer(`, `nthRoot`), absent de
  l'environnement figé, et des noms déjà retenus pour N3 (garde-fou : Valid et Test sont disjoints) ;
- liste triée par nom, mélangée par random.Random(graine) ; les `--count` premiers sont retenus,
  les `--reserve` suivants forment la réserve ordonnée (utilisée si un énoncé ne compile pas).

Usage :
  python -I bench/tools/select_dev_minif2f.py Valid.lean --commit <sha> [--seed 20261118] [--count 2]

Code sous licence Apache-2.0 (voir bench/LICENSE).
"""
from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path

EXCLUDE = ("answer(", "nthRoot", "FormalConjectures")
BLOCK = re.compile(
    r"(?:/--(?P<doc>.*?)-/\s*)?theorem\s+(?P<name>[A-Za-z0-9_']+)(?P<stmt>.*?):=\s*by\s*\n\s*sorry",
    re.S,
)
N3_SELECTION = Path(__file__).resolve().parent.parent / "items" / "N3_selection.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("valid_lean", type=Path)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--seed", type=int, default=20261118)
    ap.add_argument("--count", type=int, default=2)
    ap.add_argument("--reserve", type=int, default=3)
    args = ap.parse_args()

    n3 = json.loads(N3_SELECTION.read_text(encoding="utf-8"))
    n3_names = {n for s in n3["strata"].values() for n in s["selected"] + s["reserve"]}

    text = args.valid_lean.read_text(encoding="utf-8")
    blocks = [m.groupdict() for m in BLOCK.finditer(text)]
    pool, excluded = [], 0
    for b in blocks:
        if any(x in b["name"] + b["stmt"] for x in EXCLUDE) or b["name"] in n3_names:
            excluded += 1
            continue
        pool.append(b["name"])
    pool.sort()
    random.Random(args.seed).shuffle(pool)
    selection = {
        "purpose": "problèmes de développement (split = dev), jamais évalués",
        "source": "google-deepmind/miniF2F", "file": "MiniF2F/Valid.lean", "commit": args.commit,
        "seed": args.seed, "parsed": len(blocks), "excluded": excluded,
        "excluded_rule": "FormalConjectures (answer(, nthRoot) ou nom déjà dans N3_selection.json",
        "pool_size": len(pool),
        "selected": pool[:args.count],
        "reserve": pool[args.count:args.count + args.reserve],
    }
    print(json.dumps(selection, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
