#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Résumé d'une campagne : taux de réussite vérifiée par niveau pour B0, B1 et B2, intervalles de Wilson.

Définitions (document 04, §5.3 à §5.5) :
- B0 : l'échantillon 1 de chaque (problème, répétition) ;
- B1 : succès si l'un des k = 5 échantillons est correct (pass@5, indicatif : suppose un oracle) ;
- B2 : un échantillon choisi sans la clé, par le même vérificateur. Preuves : premier échantillon
  accepté par Lean (B2 = B1 par construction). Réponses : vote majoritaire par équivalence
  SymPy/numérique, égalité -> premier échantillon (règle À VALIDER PAR LE FONDATEUR) ;
- par problème : proportion de répétitions réussies ; par niveau : moyenne de ces proportions sur les
  problèmes, avec un intervalle de Wilson à 95 % calculé sur n = nombre de problèmes (unité statistique :
  le problème) ; l'intervalle « regroupé » sur problèmes × répétitions est donné à titre secondaire.
  Une répétition incomplète (moins de k échantillons notés) n'entre pas dans B1/B2.

Les réponses à départager pour B2 sont relues dans les fichiers bruts (results/raw/, local), jamais dans
le journal JSONL, qui ne contient pas les sorties des problèmes privés.

Usage : python harness/summarize.py --campaign pilot_dev [--config …]
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import statistics
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness.config import load_config, repo_path  # noqa: E402
from harness.items import load_items  # noqa: E402

Z95 = 1.959963984540054


def wilson(p: float, n: int, z: float = Z95) -> tuple[float, float]:
    if n <= 0:
        return (float("nan"), float("nan"))
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, center - half), min(1.0, center + half)


def load_graded(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                out[rec["key"]] = rec            # la dernière ligne d'une clé l'emporte
    return {k: v for k, v in out.items() if v.get("status") == "graded"}


def b2_answer_choice(recs: list[dict], item, acfg: dict) -> dict:
    """Vote majoritaire sans la clé (relit les réponses brutes) ; égalité ou rien de lisible -> 1er échantillon."""
    from harness.grade_answer import answers_agree, extract_final_answer, parse_answer, symbols_for
    from harness.config import repo_path as rp
    symbols = symbols_for(item.answer.get("variables", []), item.answer.get("assumptions"))
    parsed = []
    for rec in recs:
        try:
            saved = json.loads(rp(rec["raw_response_path"]).read_text(encoding="utf-8"))
            content = ((saved["response"].get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            ans, _ = extract_final_answer(content)
            val = parse_answer(ans, symbols, int(acfg["mathverify_timeout_s"]))[0] if ans else None
        except Exception:  # noqa: BLE001
            val = None
        parsed.append((rec, val))
    clusters: list[list[dict]] = []
    reps: list = []
    for rec, val in parsed:
        if val is None:
            continue
        for i, rep in enumerate(reps):
            if answers_agree(val, rep, symbols, acfg):
                clusters[i].append(rec)
                break
        else:
            reps.append(val)
            clusters.append([rec])
    if not clusters:
        return recs[0]
    best = max(clusters, key=lambda c: (len(c), -min(r["sample"] for r in c)))
    return min(best, key=lambda r: r["sample"])


def summarize(campaign: str, cfg: dict) -> dict:
    items = load_items()
    recs = load_graded(repo_path(cfg["paths"]["results_dir"]) / campaign / "generations.jsonl")
    k, b0s = int(cfg["design"]["k"]), int(cfg["design"]["b0_sample"])
    by_ir: dict[tuple[str, int], dict[int, dict]] = collections.defaultdict(dict)
    for rec in recs.values():
        by_ir[(rec["item"], rec["run"])][rec["sample"]] = rec

    per_item: dict[str, dict[str, list[bool]]] = collections.defaultdict(lambda: {"B0": [], "B1": [], "B2": []})
    for (iid, run), samples in sorted(by_ir.items()):
        it = items[iid]
        if b0s in samples:
            per_item[iid]["B0"].append(bool(samples[b0s]["success"]))
        if all(s in samples for s in range(1, k + 1)):
            ordered = [samples[s] for s in range(1, k + 1)]
            per_item[iid]["B1"].append(any(r["success"] for r in ordered))
            if it.kind == "proof":
                per_item[iid]["B2"].append(any(r["success"] for r in ordered))
            else:
                per_item[iid]["B2"].append(bool(b2_answer_choice(ordered, it, cfg["answers"])["success"]))

    levels = sorted({items[i].level for i in per_item}) + ["Tous"]
    table = {}
    for lvl in levels:
        ids = [i for i in per_item if lvl == "Tous" or items[i].level == lvl]
        row = {}
        for b in ("B0", "B1", "B2"):
            props = [sum(v) / len(v) for i in ids if (v := per_item[i][b])]
            trials = [x for i in ids for x in per_item[i][b]]
            if not props:
                row[b] = None
                continue
            p = statistics.fmean(props)
            lo, hi = wilson(p, len(props))
            pp = sum(trials) / len(trials)
            plo, phi = wilson(pp, len(trials))
            row[b] = {"items": len(props), "mean": p, "wilson95": [lo, hi], "trials": len(trials),
                      "successes": sum(trials), "pooled_wilson95": [plo, phi]}
        table[lvl] = row

    gen = list(recs.values())
    ops = {
        "generations": len(gen),
        "verdicts": dict(collections.Counter(r["verdict"] for r in gen)),
        "error_classes": dict(collections.Counter(r["error_class"] for r in gen if r["error_class"])),
        "taxonomy": dict(collections.Counter(r["taxonomy"] for r in gen if r["taxonomy"])),
        "models_returned": dict(collections.Counter(r["model_returned"] for r in gen)),
        "providers": dict(collections.Counter(r["provider"] for r in gen)),
        "needs_audit": sorted(r["key"] for r in gen if r["verdict"] == "needs_audit"),
        "tokens_prompt": sum((r["usage"].get("prompt_tokens") or 0) for r in gen),
        "tokens_completion": sum((r["usage"].get("completion_tokens") or 0) for r in gen),
    }
    rows = []
    for rec in sorted(gen, key=lambda r: (r["item"], r["run"], r["sample"])):
        rows.append({k2: rec.get(k2) for k2 in ("key", "level", "kind", "verdict", "error_class", "latency_s",
                                                  "model_returned", "provider")} |
                    {"tokens": f"{rec['usage'].get('prompt_tokens')}+{rec['usage'].get('completion_tokens')}"
                               f" (raisonnement {rec['usage'].get('reasoning_tokens')})",
                     "comparator_s": rec["timing"].get("comparator_s"), "end_to_end_s": rec["timing"].get("end_to_end_s"),
                     "finish_reason": rec.get("finish_reason")})
    return {"campaign": campaign, "levels": table, "operations": ops, "generations": rows}


def fmt(cell) -> str:
    if not cell:
        return "n/d"
    lo, hi = cell["wilson95"]
    return f"{cell['mean'] * 100:.0f} % [{lo * 100:.0f} ; {hi * 100:.0f}] (n = {cell['items']})"


def to_markdown(s: dict) -> str:
    out = [f"# Résumé de la campagne `{s['campaign']}`", "",
           "Taux de réussite vérifiée (moyenne des proportions par problème), IC de Wilson à 95 % sur n problèmes.", "",
           "| Niveau | B0 | B1 (pass@5, indicatif) | B2 |", "|---|---|---|---|"]
    for lvl, row in s["levels"].items():
        out.append(f"| {lvl} | {fmt(row['B0'])} | {fmt(row['B1'])} | {fmt(row['B2'])} |")
    out += ["", "## Générations", "",
            "| Génération | Niveau | Type | Verdict | Classe d'erreur | Latence API (s) | Comparateur (s) | De bout en bout (s) | Tokens | Fin | Modèle renvoyé | Fournisseur |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for g in s["generations"]:
        out.append(f"| {g['key']} | {g['level']} | {g['kind']} | {g['verdict']} | {g['error_class'] or '—'} | "
                   f"{g['latency_s']} | {g['comparator_s'] if g['comparator_s'] is not None else '—'} | "
                   f"{g['end_to_end_s']} | {g['tokens']} | {g['finish_reason']} | {g['model_returned']} | {g['provider']} |")
    o = s["operations"]
    out += ["", "## Exploitation", "", f"- générations notées : {o['generations']}",
            f"- verdicts : {o['verdicts']}", f"- classes d'erreur : {o['error_classes']}",
            f"- taxonomie (document 04, §5.4) : {o['taxonomy']}", f"- modèles renvoyés : {o['models_returned']}",
            f"- fournisseurs : {o['providers']}", f"- tokens : {o['tokens_prompt']} en entrée, {o['tokens_completion']} en sortie",
            f"- à auditer à la main (needs_audit) : {o['needs_audit'] or 'aucune'}"]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--config", default=None)
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    s = summarize(args.campaign, cfg)
    out_dir = repo_path(cfg["paths"]["results_dir"]) / args.campaign
    out_dir.mkdir(parents=True, exist_ok=True)
    md = to_markdown(s)
    (out_dir / "summary.md").write_text(md, encoding="utf-8")
    (out_dir / "summary.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
