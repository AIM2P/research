#!/usr/bin/env python3
"""Tirage aléatoire stratifié des problèmes N3 d'AMP-Bench-mini dans miniF2F (partie test).

Source : google-deepmind/miniF2F, fichier MiniF2F/Test.lean, au commit donné en argument.
Le tirage est reproductible : liste triée par nom dans chaque strate, puis mélange par
random.Random(graine). Les premiers de chaque strate sont retenus ; les suivants forment
la réserve ordonnée, utilisée seulement si un problème retenu est rejeté à l'audit.

Exclusions (avant tirage) : énoncés qui dépendent de FormalConjectures (macro `answer(`,
racines n-ièmes `nthRoot`), car l'environnement figé ne contient que Mathlib et Physlib.

Usage :
  python bench/tools/select_minif2f.py Test.lean --commit <sha> [--seed 20261118] [--reserve 3]

Code sous licence Apache-2.0 (voir bench/LICENSE).
"""
from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path

QUOTAS = {"mathd_algebra": 2, "mathd_numbertheory": 2, "amc12": 2, "aime": 1, "imo": 1}
EXCLUDE = ("answer(", "nthRoot", "FormalConjectures")
BLOCK = re.compile(
    r"(?:/--(?P<doc>.*?)-/\s*)?theorem\s+(?P<name>[A-Za-z0-9_']+)(?P<stmt>.*?):=\s*by\s*\n\s*sorry",
    re.S,
)


def stratum(name: str) -> str | None:
    for key in ("mathd_algebra", "mathd_numbertheory", "aime", "imo"):
        if name.startswith(key):
            return key
    if name.startswith("amc12"):
        return "amc12"
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("test_lean", type=Path)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--seed", type=int, default=20261118)
    ap.add_argument("--reserve", type=int, default=3)
    args = ap.parse_args()

    text = args.test_lean.read_text(encoding="utf-8")
    blocks = [m.groupdict() for m in BLOCK.finditer(text)]
    pools: dict[str, list[dict]] = {k: [] for k in QUOTAS}
    excluded = 0
    for b in blocks:
        full = b["name"] + b["stmt"]
        if any(x in full for x in EXCLUDE):
            excluded += 1
            continue
        s = stratum(b["name"])
        if s:
            pools[s].append(b)

    rng = random.Random(args.seed)
    selection = {"source": "google-deepmind/miniF2F", "file": "MiniF2F/Test.lean",
                 "commit": args.commit, "seed": args.seed, "quotas": QUOTAS,
                 "parsed": len(blocks), "excluded_formalconjectures": excluded, "strata": {}}
    for key, quota in QUOTAS.items():
        pool = sorted(pools[key], key=lambda b: b["name"])
        rng.shuffle(pool)
        selection["strata"][key] = {
            "pool_size": len(pool),
            "selected": [b["name"] for b in pool[:quota]],
            "reserve": [b["name"] for b in pool[quota:quota + args.reserve]],
        }
    print(json.dumps(selection, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
