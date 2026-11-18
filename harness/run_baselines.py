#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Exécute les baselines B0, B1 et B2 (phase P3) sur des problèmes d'AMP-Bench-mini.

B0, B1 et B2 se calculent sur les mêmes générations (document 04, §5.3) : pour chaque problème et chaque
répétition r = 1..R, le harnais produit l'échantillon 1 (B0 seul) ou les k = 5 échantillons (B1, B2).
Chaque génération est journalisée sur une ligne JSONL ; une génération déjà notée est sautée (reprise
idempotente). Une réponse déjà reçue mais pas encore notée est notée sans nouvel appel au modèle.

Garde-fous :
- aucun appel au modèle sur un problème d'évaluation (split = "eval") sans --allow-eval ET
  campaign.eval_authorized = true dans la configuration (« go » explicite du fondateur) ;
- compteur quotidien persistant et plafond de session (--max-requests) : aucune requête au-delà ;
- invites, réponses brutes, solutions et journaux Lean vont dans results/raw/ (ignoré par git) ; le
  journal JSONL ne contient aucune sortie du modèle pour les problèmes privés ou PutnamBench.

Exemples (sous WSL, depuis la racine du dépôt, après `source ~/.aim2p_env`) :
  ~/aim2p-venv/bin/python harness/run_baselines.py --campaign pilot_dev --split dev --baselines B0 --runs 1 --max-requests 10
  ~/aim2p-venv/bin/python harness/run_baselines.py --campaign pilot_dev --split dev --dry-run
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import traceback
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness import BENCH, REPO, __version__  # noqa: E402
from harness.client import (ApiError, BudgetExceeded, DailyLimitReached, OpenRouterClient,  # noqa: E402
                            RequestBudget)
from harness.config import load_config, repo_path  # noqa: E402
from harness.grade_answer import grade_answer  # noqa: E402
from harness.grade_proof import LeanEnv, grade_proof  # noqa: E402
from harness.items import Item, load_challenge, load_items  # noqa: E402
from harness.prompts import render_answer, render_proof  # noqa: E402

SCHEMA = 1


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def gen_seed(base: int, item: str, run: int, sample: int) -> int:
    h = hashlib.sha256(f"{base}|{item}|{run}|{sample}".encode()).hexdigest()
    return int(h[:8], 16) & 0x7FFFFFFF


def samples_for(baselines: list[str], cfg: dict) -> list[int]:
    if set(baselines) <= {"B0"}:
        return [int(cfg["design"]["b0_sample"])]
    return list(range(1, int(cfg["design"]["k"]) + 1))


def membership(sample: int, cfg: dict) -> list[str]:
    return (["B0"] if sample == int(cfg["design"]["b0_sample"]) else []) + ["B1", "B2"]


def rel(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(REPO))
    except ValueError:
        return str(p)


def load_log(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                out[rec["key"]] = rec
    return out


def append_log(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def versions() -> dict:
    v = {"python": platform.python_version(), "harness": __version__, "platform": platform.platform()}
    for mod in ("sympy", "mpmath", "math_verify", "latex2sympy2_extended", "antlr4"):
        try:
            from importlib.metadata import version
            name = {"math_verify": "math-verify", "latex2sympy2_extended": "latex2sympy2_extended",
                    "antlr4": "antlr4-python3-runtime"}.get(mod, mod)
            v[mod] = version(name)
        except Exception:  # noqa: BLE001
            v[mod] = None
    v["lean_toolchain"] = (BENCH / "lean" / "lean-toolchain").read_text(encoding="utf-8").strip()
    v["lake_manifest_sha256"] = hashlib.sha256((BENCH / "lean" / "lake-manifest.json").read_bytes()).hexdigest()
    try:
        v["git_commit"] = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True,
                                         text=True, timeout=20).stdout.strip() or None
    except Exception:  # noqa: BLE001
        v["git_commit"] = None
    return v


def usage_summary(u: dict) -> dict:
    det = u.get("completion_tokens_details") or {}
    return {"prompt_tokens": u.get("prompt_tokens"), "completion_tokens": u.get("completion_tokens"),
            "reasoning_tokens": det.get("reasoning_tokens"), "total_tokens": u.get("total_tokens"),
            "cost": u.get("cost")}


def redact_grading(g: dict, kind: str) -> dict:
    """Ne garde que des champs sans contenu du problème ni de la sortie du modèle."""
    keep = ("verdict", "error_class", "taxonomy", "extraction", "method", "reader", "comparator_rc",
            "comparator_s", "error_categories", "deprecated_warnings", "forbidden_hits", "solution_module")
    out = {k: g.get(k) for k in keep if k in g}
    if kind == "answer":
        out["elements"] = [{k: d.get(k) for k in ("symbolic", "symbolic_method", "numeric", "verdict")}
                           for d in g.get("details", [])]
    return out


def select_items(items: dict[str, Item], ids: list[str] | None, split: str | None) -> list[Item]:
    if ids:
        missing = [i for i in ids if i not in items]
        if missing:
            raise SystemExit(f"problèmes inconnus : {', '.join(missing)}")
        return [items[i] for i in ids]
    if split:
        return [it for it in items.values() if it.split == split]
    raise SystemExit("préciser --items ou --split")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default=None)
    ap.add_argument("--campaign", required=True, help="nom de campagne (identifiant Lean : lettres, chiffres, _)")
    ap.add_argument("--items", default=None, help="liste d'identifiants séparés par des virgules")
    ap.add_argument("--split", choices=["dev", "eval"], default=None)
    ap.add_argument("--baselines", default="B0,B1,B2")
    ap.add_argument("--runs", type=int, default=None, help="R (par défaut : design.runs de la configuration)")
    ap.add_argument("--max-requests", type=int, default=None, help="plafond de requêtes HTTP pour cette session")
    ap.add_argument("--dry-run", action="store_true", help="rend les invites sans appeler le modèle")
    ap.add_argument("--regrade", action="store_true", help="renote les réponses déjà reçues, sans appel au modèle")
    ap.add_argument("--allow-eval", action="store_true")
    ap.add_argument("--no-sync", action="store_true", help="ne pas recopier bench/lean vers le projet WSL")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    baselines = [b.strip() for b in args.baselines.split(",") if b.strip()]
    if not set(baselines) <= {"B0", "B1", "B2"}:
        raise SystemExit("baselines permises en P3 : B0, B1, B2")
    runs = args.runs or int(cfg["design"]["runs"])
    items = select_items(load_items(), args.items.split(",") if args.items else None, args.split)

    evals = [it.id for it in items if it.is_eval]
    if evals and not args.regrade:
        if not (args.allow_eval and cfg["campaign"].get("eval_authorized") is True):
            print(f"REFUS : {len(evals)} problème(s) d'évaluation figés ({', '.join(evals[:5])}…). Le harnais "
                  "n'appelle le modèle sur la partition eval qu'avec --allow-eval ET campaign.eval_authorized = true "
                  "(« go » explicite du fondateur).", file=sys.stderr)
            return 2

    samples = samples_for(baselines, cfg)
    version = cfg["meta"]["prompt_version"]
    results = repo_path(cfg["paths"]["results_dir"]) / args.campaign
    raw_root = repo_path(cfg["paths"]["raw_dir"]) / args.campaign
    log_path = results / "generations.jsonl"
    done = load_log(log_path)
    budget = RequestBudget(repo_path(cfg["budget"]["counter_file"]), int(cfg["budget"]["daily_request_limit"]),
                           session_limit=args.max_requests)
    client = OpenRouterClient(cfg, budget)
    env = LeanEnv.from_config(cfg)
    if any(it.kind == "proof" for it in items) and cfg["lean"].get("sync_before_run") and not args.no_sync and not args.dry_run:
        env.sync_bench()

    planned = [(r, it, s) for r in range(1, runs + 1) for it in items for s in samples]
    todo = [(r, it, s) for r, it, s in planned
            if args.regrade or done.get(f"{it.id}|r{r}|s{s}", {}).get("status") != "graded"]
    print(f"campagne {args.campaign} : {len(items)} problème(s), R = {runs}, échantillons {samples}, "
          f"{len(planned)} générations prévues, {len(todo)} à faire ; budget restant aujourd'hui : {budget.remaining()}")

    if not args.dry_run:
        results.mkdir(parents=True, exist_ok=True)
        meta = {"campaign": args.campaign, "started_utc": now_utc(), "config": rel(Path(cfg["_path"])),
                "config_sha256": cfg["_sha256"], "baselines": baselines, "runs": runs, "samples": samples,
                "items": [it.id for it in items], "versions": versions(), "argv": sys.argv[1:]}
        with (results / "runs_meta.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(meta, ensure_ascii=False) + "\n")

    stop_reason = None
    challenges = {}
    for r, it, s in todo:
        key = f"{it.id}|r{r}|s{s}"
        tag = f"R{r}S{s}"
        raw_dir = raw_root / it.id
        t_start = time.monotonic()
        if it.kind == "proof":
            challenges.setdefault(it.id, load_challenge(it))
            prompt, prompt_sha = render_proof(it, challenges[it.id], version)
        else:
            prompt, prompt_sha = render_answer(it, version)
        seed = gen_seed(int(cfg["sampling"]["base_seed"]), it.id, r, s)
        params = {"temperature": cfg["sampling"]["temperature"], "top_p": cfg["sampling"]["top_p"],
                  "max_tokens": cfg["sampling"]["max_tokens"],
                  "seed": seed if cfg["sampling"].get("send_seed") else None}
        messages = ([{"role": "system", "content": cfg["sampling"]["system_prompt"]}]
                    if cfg["sampling"].get("system_prompt") else []) + [{"role": "user", "content": prompt}]
        resp_file = raw_dir / f"{tag}.response.json"
        if args.dry_run:
            print(f"--- {key} ({it.kind}, {len(prompt)} caractères, graine {seed}) ---")
            if not it.redact:
                print(prompt)
            continue
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / f"{tag}.prompt.md").write_text(prompt, encoding="utf-8")

        if resp_file.is_file():
            saved = json.loads(resp_file.read_text(encoding="utf-8"))
        elif args.regrade:
            continue
        else:
            try:
                res = client.chat(messages, params)
            except (BudgetExceeded, DailyLimitReached) as exc:
                stop_reason = f"{type(exc).__name__}: {exc}"
                print(f"ARRÊT avant {key} : {stop_reason}")
                break
            except ApiError as exc:
                rec = {"schema": SCHEMA, "campaign": args.campaign, "key": key, "item": it.id, "run": r, "sample": s,
                       "status": "api_error", "timestamp_utc": now_utc(), "error": str(exc)[:500],
                       "http_status": exc.status, "attempts": exc.attempts}
                append_log(log_path, rec)
                print(f"{key} : erreur d'API ({exc.status}) après {exc.attempts} tentative(s)")
                continue
            saved = {"requested_utc": now_utc(), "request": {"model": cfg["model"]["id"], "params": params,
                                                              "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()},
                     "meta": {"latency_s": res.latency_s, "attempts": res.attempts, "rate_headers": res.rate_headers},
                     "response": res.raw}
            resp_file.write_text(json.dumps(saved, ensure_ascii=False, indent=1), encoding="utf-8")

        resp = saved["response"]
        ch = (resp.get("choices") or [{}])[0]
        content = (ch.get("message") or {}).get("content") or ""
        t_grade = time.monotonic()
        status, grading, err = "graded", {}, None
        try:
            if it.kind == "proof":
                challenges.setdefault(it.id, load_challenge(it))
                g = grade_proof(content, it.lean["theorem"], it.lean["module"], challenges[it.id], env, cfg["lean"],
                                args.campaign, it.lean_id, tag, raw_dir=raw_dir)
                grading = g.to_dict()
                success = g.verdict == "accepted"
                extracted = g.extracted
            else:
                g = grade_answer(content, it.answer, cfg["answers"])
                grading = g.to_dict()
                success = g.verdict == "correct"
                extracted = g.extracted
        except Exception as exc:  # noqa: BLE001 - une génération ne doit pas arrêter la campagne
            status, success, extracted = "grading_error", False, None
            err = f"{type(exc).__name__}: {exc}"
            (raw_dir / f"{tag}.grading_error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        t_end = time.monotonic()
        u = resp.get("usage") or {}
        rec = {
            "schema": SCHEMA, "campaign": args.campaign, "key": key, "item": it.id, "level": it.level,
            "kind": it.kind, "split": it.split, "visibility": it.visibility, "baselines": membership(s, cfg),
            "run": r, "sample": s, "status": status, "timestamp_utc": now_utc(),
            "requested_utc": saved.get("requested_utc"), "params": saved["request"]["params"],
            "prompt_version": version, "prompt_sha256": prompt_sha, "config_sha256": cfg["_sha256"],
            "model_requested": saved["request"]["model"], "model_returned": resp.get("model"),
            "provider": resp.get("provider"), "response_id": resp.get("id"),
            "system_fingerprint": resp.get("system_fingerprint"), "finish_reason": ch.get("finish_reason"),
            "native_finish_reason": ch.get("native_finish_reason"),
            "latency_s": saved["meta"]["latency_s"], "attempts": saved["meta"]["attempts"], "usage": usage_summary(u),
            "raw_prompt_path": rel(raw_dir / f"{tag}.prompt.md"), "raw_response_path": rel(resp_file),
            "redacted": it.redact,
            "extracted": None if it.redact else extracted,
            "extracted_sha256": hashlib.sha256(extracted.encode()).hexdigest() if extracted else None,
            "verdict": grading.get("verdict"), "success": bool(success),
            "error_class": grading.get("error_class"), "taxonomy": grading.get("taxonomy"),
            "grading": redact_grading(grading, it.kind) if it.redact else grading,
            "grading_error": err,
            "timing": {"api_s": saved["meta"]["latency_s"], "grade_s": round(t_end - t_grade, 2),
                       "comparator_s": grading.get("comparator_s"),
                       # de bout en bout : invite, appel au modèle (s'il a eu lieu dans cette session), correction
                       "end_to_end_s": round(t_end - t_start, 2)},
        }
        rec["grading"].pop("extracted", None)  # déjà au premier niveau (ou masqué)
        append_log(log_path, rec)
        done[key] = rec
        print(f"{key} : {rec['verdict']} ({rec['error_class'] or 'ok'}) | API {rec['latency_s']} s, "
              f"correction {rec['timing']['grade_s']} s | modèle {rec['model_returned']} via {rec['provider']} | "
              f"tokens {rec['usage']['prompt_tokens']}+{rec['usage']['completion_tokens']}")

    print(f"requêtes envoyées pendant cette session : {budget.session_used} ; "
          f"compteur du jour ({budget.today()}, UTC) : {budget.used_today()}/{budget.daily_limit}")
    if stop_reason:
        print(f"campagne interrompue : {stop_reason} (relancer la même commande pour reprendre)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
