#!/usr/bin/env python3
"""Tirage aléatoire stratifié des problèmes N4 d'AMP-Bench-mini dans ProofNet# et PutnamBench.

Sources, figées par leur révision :
- ProofNet# : jeu de données Hugging Face PAug/ProofNetSharp, partie test
  (fichier data/test-00000-of-00001.parquet), à la révision donnée en argument. Licence MIT.
- PutnamBench : dépôt trishullab/PutnamBench, dossier lean4/src (un fichier par problème), au
  commit donné en argument. Énoncés Lean 4 sous licence Apache-2.0.

Le tirage est reproductible : dans chaque strate, liste triée par identifiant, puis mélange par
random.Random(graine). Un seul générateur sert à toutes les strates, parcourues dans l'ordre fixe
de QUOTAS (ProofNet# d'abord, puis PutnamBench). Les premiers de chaque strate sont retenus ; les
suivants forment la réserve ordonnée, utilisée seulement si un problème retenu est rejeté à l'audit.

Strates ProofNet# (un problème chacune) : le domaine du manuel dont l'exercice est tiré, d'après
les quatre domaines annoncés par ProofNet (analyse réelle et complexe, algèbre linéaire, algèbre
abstraite, topologie). Les exercices d'Ireland-Rosen (théorie des nombres) sont rangés en algèbre.
Un manuel inconnu arrête le script.

Exclusions (avant tirage) :
- ProofNet# : les exercices issus du Putnam (préfixe « Putnam| »), pour éviter un doublon avec
  la moitié PutnamBench de N4.
- PutnamBench : les problèmes à réponse, qui contiennent une définition à compléter
  (`abbrev putnam_..._solution ... := sorry`) en plus du théorème. On ne garde que les fichiers
  sans `_solution`, avec un seul théorème et un seul `sorry` : un théorème par problème.

Lecture du fichier parquet : nécessite pyarrow (pip install pyarrow). Les fichiers sources sont lus
comme des données ; aucun code qu'ils contiennent n'est exécuté.

Usage :
  python -I bench/tools/select_n4.py \\
      --proofnet test-00000-of-00001.parquet --proofnet-revision <sha> \\
      --putnam-src PutnamBench/lean4/src --putnam-commit <sha> [--seed 20261118] [--reserve 3]

Code sous licence Apache-2.0 (voir bench/LICENSE).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from pathlib import Path

QUOTAS = {
    "proofnet_algebre": 1,
    "proofnet_analyse": 1,
    "proofnet_algebre_lineaire": 1,
    "proofnet_topologie": 1,
    "putnambench": 4,
}
BOOKS = {
    "proofnet_algebre": ("Artin", "Dummit-Foote", "Herstein", "Ireland-Rosen"),
    "proofnet_analyse": ("Pugh", "Rudin", "Shakarchi"),
    "proofnet_algebre_lineaire": ("Axler",),
    "proofnet_topologie": ("Munkres",),
}
PROOFNET_EXCLUDED_BOOKS = ("Putnam",)


def proofnet_pools(parquet: Path) -> tuple[dict[str, list[str]], int, int]:
    import pyarrow.parquet as pq  # dépendance optionnelle, seulement pour ce tirage

    ids = pq.read_table(parquet, columns=["id"]).column("id").to_pylist()
    if len(ids) != len(set(ids)):
        raise SystemExit("identifiants ProofNet# en double")
    book_to_stratum = {b: s for s, books in BOOKS.items() for b in books}
    pools: dict[str, list[str]] = {s: [] for s in BOOKS}
    excluded = 0
    for pid in ids:
        book = pid.split("|", 1)[0]
        if book in PROOFNET_EXCLUDED_BOOKS:
            excluded += 1
        elif book in book_to_stratum:
            pools[book_to_stratum[book]].append(pid)
        else:
            raise SystemExit(f"manuel inconnu dans ProofNet# : {book!r} ({pid})")
    return pools, len(ids), excluded


def putnam_pool(src: Path) -> tuple[list[str], int, int, int]:
    files = sorted(src.glob("putnam_*.lean"))
    pool, with_solution, other = [], 0, 0
    for f in files:
        text = f.read_text(encoding="utf-8")
        if "_solution" in text:
            with_solution += 1
            continue
        n_thm = len(re.findall(r"^\s*theorem\s", text, re.M))
        n_sorry = len(re.findall(r"\bsorry\b", text))
        if n_thm != 1 or n_sorry != 1 or not re.search(rf"\btheorem\s+{re.escape(f.stem)}\b", text):
            other += 1
            continue
        pool.append(f.stem)
    return pool, len(files), with_solution, other


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--proofnet", type=Path, required=True, help="fichier parquet de la partie test")
    ap.add_argument("--proofnet-revision", required=True)
    ap.add_argument("--putnam-src", type=Path, required=True, help="dossier lean4/src de PutnamBench")
    ap.add_argument("--putnam-commit", required=True)
    ap.add_argument("--seed", type=int, default=20261118)
    ap.add_argument("--reserve", type=int, default=3)
    args = ap.parse_args()

    pn_pools, pn_rows, pn_excluded = proofnet_pools(args.proofnet)
    pb_pool, pb_files, pb_solution, pb_other = putnam_pool(args.putnam_src)
    pools = {**pn_pools, "putnambench": pb_pool}

    selection = {
        "sources": {
            "proofnet_sharp": {
                "dataset": "PAug/ProofNetSharp", "split": "test",
                "file": "data/test-00000-of-00001.parquet", "revision": args.proofnet_revision,
                "sha256": hashlib.sha256(args.proofnet.read_bytes()).hexdigest(),
                "licence": "MIT", "rows": pn_rows, "excluded_putnam": pn_excluded,
                "books": BOOKS,
            },
            "putnambench": {
                "repo": "trishullab/PutnamBench", "dir": "lean4/src", "commit": args.putnam_commit,
                "licence": "Apache-2.0", "files": pb_files, "excluded_solution": pb_solution,
                "excluded_other": pb_other,
            },
        },
        "seed": args.seed,
        "quotas": QUOTAS,
        "strata": {},
    }
    rng = random.Random(args.seed)
    for key, quota in QUOTAS.items():
        pool = sorted(pools[key])
        rng.shuffle(pool)
        selection["strata"][key] = {
            "pool_size": len(pool),
            "selected": pool[:quota],
            "reserve": pool[quota:quota + args.reserve],
        }
    # Identifiants : N4-01 … N4-04 pour ProofNet# (ordre des strates), N4-05 … N4-08 pour
    # PutnamBench (ordre du tirage).
    chosen = [name for key in QUOTAS for name in selection["strata"][key]["selected"]]
    selection["ids"] = {f"N4-{k:02d}": name for k, name in enumerate(chosen, start=1)}
    print(json.dumps(selection, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
