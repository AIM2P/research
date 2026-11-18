#!/usr/bin/env python3
"""Validateur d'AMP-Bench-mini (phase P2).

Vérifie chaque fichier de problème (``bench/items/*.toml`` et, s'il existe, ``bench/private/*.toml``) :

- champs obligatoires et valeurs permises (niveau, type, partition, visibilité, statut d'audit) ;
- identifiant unique, égal au nom du fichier ;
- problèmes de preuve : le fichier Lean existe, commence par un bloc d'imports ciblés de Mathlib ou
  Physlib (``import Mathlib`` complet est interdit : 5,4 Go de mémoire mesurés sous WSL), déclare le
  théorème annoncé et contient ``sorry`` (c'est un défi). La solution d'un modèle est compilée avec
  exactement cet en-tête ; ses propres imports sont ignorés ;
- problèmes à réponse : la réponse attendue se lit comme une expression SymPy ;
- effectifs par niveau de la partition d'évaluation (cible : N1 6, N2 6, N3 8, N4 8, N5 12).

Options :
  --final    les effectifs cibles et les audits « ok » deviennent obligatoires (avant le gel)
  --hashes   écrit bench/HASHES.txt : empreinte SHA-256 de chaque problème (fichier TOML + fichier Lean)

Code sous licence Apache-2.0 (voir bench/LICENSE).
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import tomllib
from pathlib import Path

BENCH = Path(__file__).resolve().parent
LEAN = BENCH / "lean"
TARGETS = {"N1": 6, "N2": 6, "N3": 8, "N4": 8, "N5": 12}
LEVELS = set(TARGETS)
KINDS = {"answer", "proof"}
SPLITS = {"eval", "dev"}
VISIBILITY = {"public", "private"}
AUDIT = {"pending", "ok", "rejected"}
ID_RE = re.compile(r"^(N[1-5]|DEV)-\d{2}$")
FORBIDDEN = ("native_decide", "implemented_by", "extern", "unsafe", "debug.skipKernelTC")


def load_items() -> list[tuple[Path, dict]]:
    files = sorted((BENCH / "items").glob("*.toml"))
    if (BENCH / "private").is_dir():
        files += sorted((BENCH / "private").glob("*.toml"))
    items = []
    for f in files:
        with f.open("rb") as fh:
            items.append((f, tomllib.load(fh)))
    return items


def lean_path(module: str) -> Path:
    return LEAN.joinpath(*module.split(".")).with_suffix(".lean")


def check_imports(text: str) -> list[str]:
    """Renvoie les problèmes de l'en-tête : imports ciblés de Mathlib ou Physlib seulement."""
    problems, imports = [], []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("--"):
            continue
        if s.startswith("import "):
            imports.append(s.split()[1])
            continue
        break
    if not imports:
        problems.append("aucun import en tête de fichier")
    for mod in imports:
        if mod == "Mathlib":
            problems.append("`import Mathlib` complet interdit (imports ciblés seulement)")
        elif not (mod.startswith("Mathlib.") or mod.startswith("Physlib.")):
            problems.append(f"import hors Mathlib/Physlib : {mod}")
    return problems


def check_item(path: Path, it: dict, errors: list[str], warnings: list[str]) -> None:
    def err(msg):
        errors.append(f"{path.name}: {msg}")

    for key in ("id", "level", "kind", "split", "visibility", "title", "statement", "source", "audit"):
        if key not in it:
            err(f"champ obligatoire manquant : {key}")
    if errors and errors[-1].startswith(path.name):
        return
    if not ID_RE.match(it["id"]):
        err(f"identifiant mal formé : {it['id']!r} (attendu N1-01 … N5-12 ou DEV-01)")
    if path.stem != it["id"]:
        err(f"le nom du fichier doit être l'identifiant ({it['id']}.toml)")
    if it["level"] not in LEVELS:
        err(f"niveau inconnu : {it['level']}")
    if it["kind"] not in KINDS:
        err(f"type inconnu : {it['kind']}")
    if it["split"] not in SPLITS:
        err(f"partition inconnue : {it['split']}")
    if it["visibility"] not in VISIBILITY:
        err(f"visibilité inconnue : {it['visibility']}")
    if it["visibility"] == "private" and path.parent.name != "private":
        err("un problème privé doit se trouver dans bench/private/ (hors dépôt jusqu'à l'évaluation)")
    src = it["source"]
    for key in ("name", "licence"):
        if key not in src:
            err(f"source.{key} manquant")
    if it["audit"].get("status") not in AUDIT:
        err(f"audit.status doit valoir {sorted(AUDIT)}")

    if it["kind"] == "proof":
        lean = it.get("lean", {})
        if not {"module", "theorem"} <= lean.keys():
            err("[lean] doit donner module et theorem")
            return
        expected = "AMPBench.Private." if it["visibility"] == "private" else "AMPBench.Items."
        if not lean["module"].startswith(expected):
            err(f"module Lean {lean['module']} : doit commencer par {expected} "
                "(défis privés hors dépôt jusqu'à l'évaluation)")
        lf = lean_path(lean["module"])
        if not lf.is_file():
            err(f"fichier Lean introuvable : {lf.relative_to(BENCH)}")
            return
        text = lf.read_text(encoding="utf-8")
        for problem in check_imports(text):
            err(f"{lf.name} : {problem}")
        if not re.search(rf"\btheorem\s+{re.escape(lean['theorem'])}\b", text):
            err(f"{lf.name} ne déclare pas le théorème {lean['theorem']}")
        if "sorry" not in text:
            err(f"{lf.name} doit contenir `sorry` (fichier de défi)")
        for word in FORBIDDEN:
            if word in text:
                err(f"{lf.name} contient un mot interdit : {word}")
    else:
        ans = it.get("answer", {})
        if "value" not in ans:
            err("[answer] doit donner value")
            return
        try:
            try:
                import sympy
            except ImportError:  # SymPy installé dans le dossier utilisateur, invisible sous `python -I`
                import site
                sys.path.append(site.getusersitepackages())
                import sympy
            syms = {name: sympy.Symbol(name) for name in ans.get("variables", [])}
            sympy.sympify(ans["value"], locals=syms)
        except ImportError:
            warnings.append("SymPy absent : réponses non vérifiées")
        except Exception as exc:  # noqa: BLE001 - message lisible pour l'auteur
            err(f"réponse illisible par SymPy : {ans['value']!r} ({exc})")


def item_hash(path: Path, it: dict) -> str:
    h = hashlib.sha256(path.read_bytes())
    if it.get("kind") == "proof" and "lean" in it:
        lf = lean_path(it["lean"]["module"])
        if lf.is_file():
            h.update(lf.read_bytes())
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--hashes", action="store_true")
    args = ap.parse_args()

    items = load_items()
    errors: list[str] = []
    warnings: list[str] = []
    seen: dict[str, str] = {}
    for path, it in items:
        check_item(path, it, errors, warnings)
        if it.get("id") in seen:
            errors.append(f"{path.name}: identifiant déjà utilisé par {seen[it['id']]}")
        seen[it.get("id", "?")] = path.name

    counts = {lvl: 0 for lvl in TARGETS}
    pending = 0
    for _, it in items:
        if it.get("split") == "eval" and it.get("level") in counts:
            counts[it["level"]] += 1
            pending += it.get("audit", {}).get("status") != "ok"
    dev = sum(1 for _, it in items if it.get("split") == "dev")

    print(f"{len(items)} problèmes lus ({dev} de développement)")
    for lvl, target in TARGETS.items():
        mark = "ok" if counts[lvl] == target else "à compléter"
        print(f"  {lvl} : {counts[lvl]}/{target}  {mark}")
        if args.final and counts[lvl] != target:
            errors.append(f"{lvl} : {counts[lvl]} problèmes d'évaluation au lieu de {target}")
    if args.final and pending:
        errors.append(f"{pending} problème(s) d'évaluation sans audit « ok »")
    for w in sorted(set(warnings)):
        print("avertissement :", w)

    if args.hashes:
        lines = [f"{item_hash(p, it)}  {it['id']}" for p, it in sorted(items, key=lambda x: x[1].get("id", ""))
                 if it.get("split") == "eval"]
        (BENCH / "HASHES.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"empreintes écrites dans HASHES.txt ({len(lines)} problèmes)")

    if errors:
        print(f"\n{len(errors)} erreur(s) :")
        for e in errors:
            print("  -", e)
        return 1
    print("validation : OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
