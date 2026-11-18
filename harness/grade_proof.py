# SPDX-License-Identifier: Apache-2.0
"""Correcteur des problèmes de preuve : extraction, en-tête imposé, filtre de source, ``lake comparator``.

Chaîne (document 04, §5.2 ; document 05, §3 et §5) :

1. extraction du dernier bloc ```lean de la réponse (de préférence celui qui déclare le théorème) ;
2. suppression des lignes ``import`` (et ``module``) du modèle : la solution est reconstruite avec
   **exactement** l'en-tête du défi (imports, commentaires, ``open`` : tout ce qui précède le théorème),
   suivi du code du modèle ;
3. filtre de source sur le code du modèle, commentaires retirés : ``sorry``, ``admit``, ``axiom``,
   ``native_decide``, ``implemented_by``, ``extern``, ``unsafe``, ``debug.skipKernelTC`` ;
4. écriture du fichier dans le projet Lean de WSL (``~/aim2p-bench/AMPBench/Solutions/…``, hors dépôt)
   puis ``lake comparator`` dans son bac à sable ``bwrap``, avec un délai maximal. La solution n'est
   jamais compilée hors du bac à sable (hypothèse 2 de Comparator) ;
5. classement : ``accepted``, ``statement_mismatch`` (H-b), ``illegal_axiom`` (H-a), ``build_error``
   avec la catégorie de la première erreur Lean (identifiant inconnu = H-c), ``no_proof``,
   ``comparator_error``.
"""
from __future__ import annotations

import collections
import json
import os
import re
import signal
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from harness import BENCH
from harness.items import Challenge, decl_regex, strip_lean_comments

FENCE = re.compile(r"```[ \t]*(?P<lang>[A-Za-z0-9_+-]*)[^\n]*\n(?P<code>.*?)```", re.S)
IMPORT_LINE = re.compile(r"^\s*(?:(?:public|private|meta)\s+)*import\s+\S+.*$")
MODULE_LINE = re.compile(r"^\s*(?:module|prelude)\s*$")

ERROR_CATEGORIES = [
    ("timeout", r"deterministic timeout|maximum recursion depth|heartbeats|\(kernel\) deep recursion"),
    ("unknown_identifier", r"unknown (?:identifier|constant|namespace|declaration)|invalid field .*(?:does not contain|not found)"),
    ("typeclass", r"failed to synthesize|typeclass instance problem is stuck"),
    ("type_mismatch", r"type mismatch|but is expected to have type"),
    ("unsolved_goals", r"unsolved goals"),
    ("syntax", r"unexpected token|unexpected end of input|expected term|unknown tactic|unterminated"),
    ("tactic_failed", r"failed|did not|made no progress|could not|no goals|unable to|not supported"),
]


def lean_error_category(msg: str) -> str:
    for name, pat in ERROR_CATEGORIES:
        if re.search(pat, msg, re.I):
            return name
    return "other"


def extract_lean_block(text: str, theorem: str) -> tuple[str | None, str]:
    """Renvoie (code, note). Préférence : dernier bloc ```lean qui déclare le théorème."""
    blocks = [(m.group("lang").lower(), m.group("code")) for m in FENCE.finditer(text or "")]
    decl = decl_regex(theorem)
    lean = [c for lang, c in blocks if lang in ("lean", "lean4")]
    for pool, note in ((lean, "bloc lean déclarant le théorème"), ([c for _, c in blocks], "bloc déclarant le théorème")):
        hits = [c for c in pool if decl.search(strip_lean_comments(c))]
        if hits:
            return hits[-1], note
    if lean:
        return lean[-1], "dernier bloc lean (théorème absent)"
    if re.search(r"```[ \t]*lean", text or "", re.I):
        return None, "bloc lean non fermé (sortie tronquée ?)"
    return None, "aucun bloc lean"


def drop_imports(code: str) -> tuple[str, list[str]]:
    kept, dropped = [], []
    for ln in code.splitlines():
        if IMPORT_LINE.match(ln) or MODULE_LINE.match(ln):
            dropped.append(ln.strip())
        else:
            kept.append(ln)
    return "\n".join(kept).strip("\n") + "\n", dropped


def source_filter(code: str, forbidden: list[str]) -> list[str]:
    """Mots interdits présents dans le code du modèle, commentaires retirés (recherche par mot entier)."""
    bare = strip_lean_comments(code)
    hits = []
    for w in forbidden:
        if re.search(rf"(?<![\w.']){re.escape(w)}(?![\w'])", bare):
            hits.append(w)
    return hits


def build_solution(ch: Challenge, model_code: str) -> str:
    """Fichier solution = en-tête exact du défi + code du modèle (sans ses imports) + fin éventuelle du défi."""
    header = ch.header if ch.header.endswith("\n") else ch.header + "\n"
    out = header + model_code.strip("\n") + "\n"
    if ch.trailer:
        out += "\n" + ch.trailer + "\n"
    return out


@dataclass
class LeanEnv:
    project: Path                      # ~/aim2p-bench (WSL)
    elan_bin: Path
    solutions_dir: str = "AMPBench/Solutions"
    comparator_dir: str = "comparator/solutions"
    permitted_axioms: tuple = ("propext", "Quot.sound", "Classical.choice")

    @classmethod
    def from_config(cls, cfg: dict) -> "LeanEnv":
        lc = cfg["lean"]
        return cls(project=Path(os.path.expanduser(lc["project"])), elan_bin=Path(os.path.expanduser(lc["elan_bin"])),
                   solutions_dir=lc["solutions_dir"], comparator_dir=lc["comparator_dir"],
                   permitted_axioms=tuple(lc["permitted_axioms"]))

    def sync_bench(self) -> None:
        """Copie bench/lean vers le projet WSL (sans .lake), comme bench/tools/check_lean_wsl.sh."""
        self.project.mkdir(parents=True, exist_ok=True)
        src = BENCH / "lean"
        p1 = subprocess.Popen(["tar", "-C", str(src), "--exclude=.lake", "-cf", "-", "."], stdout=subprocess.PIPE)
        p2 = subprocess.run(["tar", "-C", str(self.project), "-xf", "-"], stdin=p1.stdout, capture_output=True)
        p1.stdout.close()
        if p1.wait() != 0 or p2.returncode != 0:
            raise RuntimeError(f"synchronisation de bench/lean impossible : {p2.stderr.decode()[:300]}")

    def solution_paths(self, campaign: str, item_lean_id: str, tag: str) -> tuple[str, Path, str, Path]:
        """Renvoie (module, fichier .lean, config relative, fichier config)."""
        for part in (campaign, item_lean_id, tag):
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", part):
                raise ValueError(f"composant de nom de module Lean invalide : {part!r}")
        rel = Path(self.solutions_dir) / campaign / item_lean_id / f"{tag}.lean"
        module = ".".join(rel.with_suffix("").parts)
        cfg_rel = str(Path(self.comparator_dir) / campaign / f"{item_lean_id}_{tag}.json")
        return module, self.project / rel, cfg_rel, self.project / cfg_rel

    def run_comparator(self, challenge_module: str, solution_module: str, theorem: str, cfg_rel: str,
                       cfg_file: Path, timeout_s: float) -> tuple[int | None, str, float, bool]:
        cfg_file.parent.mkdir(parents=True, exist_ok=True)
        cfg_file.write_text(json.dumps({
            "challenge_module": challenge_module, "solution_module": solution_module,
            "theorem_names": [theorem], "permitted_axioms": list(self.permitted_axioms)}, indent=1), encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if "API_KEY" not in k and "TOKEN" not in k}
        env["PATH"] = f"{self.elan_bin}:{env.get('PATH', '/usr/bin:/bin')}"
        t0 = time.monotonic()
        p = subprocess.Popen(["lake", "comparator", "--config", cfg_rel], cwd=self.project, env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
        timed_out = False
        try:
            out, _ = p.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            out, _ = p.communicate()
        return (None if timed_out else p.returncode), out or "", round(time.monotonic() - t0, 2), timed_out


@dataclass
class ProofGrade:
    verdict: str                 # accepted, statement_mismatch, illegal_axiom, build_error, no_proof, comparator_error
    error_class: str | None = None
    taxonomy: str | None = None
    extraction: str = ""
    extracted: str | None = None
    dropped_imports: list = field(default_factory=list)
    forbidden_hits: list = field(default_factory=list)
    solution_module: str | None = None
    comparator_rc: int | None = None
    comparator_s: float | None = None
    first_error: str | None = None
    error_categories: dict = field(default_factory=dict)
    deprecated_warnings: int = 0
    comparator_log: str | None = None

    def to_dict(self) -> dict:
        return dict(self.__dict__)


def parse_lean_errors(output: str, sol_rel: str) -> list[str]:
    """Messages d'erreur Lean situés dans le fichier solution (première ligne + suite indentée)."""
    msgs, cur = [], None
    pat = re.compile(rf"^error: (?:\./)*{re.escape(sol_rel)}:\d+:\d+: (.*)$")
    for ln in output.splitlines():
        m = pat.match(ln)
        if m:
            if cur is not None:
                msgs.append(cur)
            cur = m.group(1)
        elif cur is not None and not re.match(r"^(error|warning|info|✖|⚠|Build|Some required|- )", ln):
            cur += "\n" + ln
        elif cur is not None:
            msgs.append(cur)
            cur = None
    if cur is not None:
        msgs.append(cur)
    return msgs


def classify_comparator(rc: int | None, output: str, timed_out: bool, sol_rel: str) -> ProofGrade:
    g = ProofGrade(verdict="comparator_error", error_class="other")
    g.deprecated_warnings = len(re.findall(rf"warning: (?:\./)*{re.escape(sol_rel)}:\d+:\d+: .*deprecated", output))
    errors = parse_lean_errors(output, sol_rel)
    cats = collections.Counter(lean_error_category(e) for e in errors)
    g.error_categories = dict(cats)
    if errors:
        g.first_error = errors[0][:400]
    if timed_out:
        g.verdict, g.error_class = "build_error", "timeout"
        g.first_error = g.first_error or "délai maximal du comparateur dépassé"
        return g
    if rc == 0 and "Your solution is okay" in output:
        g.verdict, g.error_class = "accepted", None
        return g
    m = re.search(r"Illegal axiom detected: '([^']+)'", output)
    if m:
        g.verdict, g.error_class, g.taxonomy = "illegal_axiom", f"axiom:{m.group(1)}", "H-a"
        return g
    if re.search(r"statement do not match|statements? (?:does|do) not match", output):
        g.verdict, g.error_class, g.taxonomy = "statement_mismatch", "statement_mismatch", "H-b"
        return g
    if errors:
        g.verdict = "build_error"
        g.error_class = lean_error_category(errors[0])
        g.taxonomy = "H-c" if cats.get("unknown_identifier") else None
        return g
    tail = [ln for ln in output.splitlines() if ln.startswith("error")]
    g.first_error = (tail[0] if tail else output.strip()[-400:])[:400]
    if re.search(r"not found|does not (?:contain|exist)|unknown", g.first_error or "", re.I):
        g.verdict, g.error_class, g.taxonomy = "statement_mismatch", "missing_theorem", "H-b"
    return g


def grade_proof(text: str, theorem: str, challenge_module: str, ch: Challenge, env: LeanEnv, gcfg: dict,
                campaign: str, item_lean_id: str, tag: str, raw_dir: Path | None = None,
                apply_filter: bool = True) -> ProofGrade:
    code, note = extract_lean_block(text, theorem)
    if code is None:
        return ProofGrade(verdict="no_proof", error_class="no_lean_block", extraction=note)
    body, dropped = drop_imports(code)
    g0 = ProofGrade(verdict="comparator_error", extraction=note, extracted=body, dropped_imports=dropped)
    if not decl_regex(theorem).search(strip_lean_comments(body)):
        g0.verdict, g0.error_class, g0.taxonomy = "statement_mismatch", "missing_theorem", "H-b"
        return g0
    hits = source_filter(body, list(gcfg["forbidden"]))
    g0.forbidden_hits = hits
    if hits and apply_filter:
        g0.verdict, g0.error_class, g0.taxonomy = "illegal_axiom", "source_filter:" + ",".join(hits), "H-a"
        return g0
    module, sol_file, cfg_rel, cfg_file = env.solution_paths(campaign, item_lean_id, tag)
    sol_file.parent.mkdir(parents=True, exist_ok=True)
    sol_text = build_solution(ch, body)
    sol_file.write_text(sol_text, encoding="utf-8")
    if raw_dir is not None:
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / f"{tag}.solution.lean").write_text(sol_text, encoding="utf-8")
    rc, out, secs, timed_out = env.run_comparator(challenge_module, module, theorem, cfg_rel, cfg_file,
                                                  float(gcfg["comparator_timeout_s"]))
    sol_rel = str(sol_file.relative_to(env.project))
    g = classify_comparator(rc, out, timed_out, sol_rel)
    g.extraction, g.extracted, g.dropped_imports, g.forbidden_hits = note, body, dropped, hits
    g.solution_module, g.comparator_rc, g.comparator_s = module, rc, secs
    if raw_dir is not None:
        log = raw_dir / f"{tag}.comparator.log"
        log.write_text(out, encoding="utf-8")
        g.comparator_log = str(log)
    return g
