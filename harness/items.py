# SPDX-License-Identifier: Apache-2.0
"""Chargement des problèmes d'AMP-Bench-mini et découpage des fichiers de défi Lean.

Un fichier de défi contient : imports ciblés, commentaires, ``open``, puis un seul théorème terminé
par ``sorry``. L'« en-tête » est tout ce qui précède ce théorème (et sa docstring éventuelle) : c'est
exactement l'environnement dans lequel la solution d'un modèle est compilée.
"""
from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from harness import BENCH

LEAN_ROOT = BENCH / "lean"


@dataclass
class Item:
    id: str
    level: str
    kind: str
    split: str
    visibility: str
    title: str
    statement: str
    source: dict
    path: Path
    lean: dict | None = None
    answer: dict | None = None
    raw: dict = field(default_factory=dict, repr=False)

    @property
    def is_eval(self) -> bool:
        return self.split == "eval"

    @property
    def redact(self) -> bool:
        """Vrai si les sorties du modèle ne doivent jamais apparaître hors du dossier ignoré par git :
        problèmes inédits (privés) et problèmes PutnamBench (aucune preuve publiée)."""
        return self.visibility == "private" or "PutnamBench" in self.source.get("name", "")

    @property
    def lean_file(self) -> Path:
        assert self.lean is not None
        return LEAN_ROOT.joinpath(*self.lean["module"].split(".")).with_suffix(".lean")

    @property
    def lean_id(self) -> str:
        """Identifiant utilisable dans un nom de module Lean (DEV-01 -> DEV_01)."""
        return self.id.replace("-", "_")


def load_items(bench: Path = BENCH) -> dict[str, Item]:
    files = sorted((bench / "items").glob("*.toml"))
    if (bench / "private").is_dir():
        files += sorted((bench / "private").glob("*.toml"))
    items: dict[str, Item] = {}
    for f in files:
        d = tomllib.loads(f.read_text(encoding="utf-8"))
        it = Item(id=d["id"], level=d["level"], kind=d["kind"], split=d["split"],
                  visibility=d["visibility"], title=d.get("title", ""), statement=d["statement"].strip(),
                  source=d.get("source", {}), path=f, lean=d.get("lean"), answer=d.get("answer"), raw=d)
        if it.id in items:
            raise ValueError(f"identifiant en double : {it.id}")
        items[it.id] = it
    return items


@dataclass
class Challenge:
    name: str
    text: str
    header: str          # tout ce qui précède le théorème (imports, commentaires, open), tel quel
    theorem: str         # docstring éventuelle + déclaration + `sorry`
    trailer: str         # ce qui suit le `sorry` (vide pour les défis actuels)

    @property
    def header_code(self) -> str:
        """En-tête sans commentaires ni lignes vides : imports et ``open``, pour l'invite."""
        lines = [ln.rstrip() for ln in strip_lean_comments(self.header).splitlines()]
        return "\n".join(ln for ln in lines if ln.strip())

    @property
    def imports(self) -> list[str]:
        return [ln.split()[1] for ln in self.header.splitlines() if ln.strip().startswith("import ")]


def decl_regex(name: str) -> re.Pattern:
    return re.compile(rf"^(?:@\[[^\]]*\]\s*)?(?:protected\s+)?(?:theorem|lemma)\s+{re.escape(name)}(?![\w'.])", re.M)


def parse_challenge(text: str, name: str) -> Challenge:
    m = decl_regex(name).search(text)
    if not m:
        raise ValueError(f"théorème {name} introuvable dans le défi")
    start = m.start()
    doc = re.search(r"/--(?:(?!-/).)*-/\s*\Z", text[:start], re.S)
    if doc:
        start = doc.start()
    s = re.search(r"\bsorry\b", text[m.end():])
    if not s:
        raise ValueError(f"le défi {name} ne se termine pas par `sorry`")
    end = m.end() + s.end()
    header = text[:start]
    if re.search(r"\bsorry\b", strip_lean_comments(header)):
        raise ValueError("l'en-tête du défi contient `sorry`")
    return Challenge(name=name, text=text, header=header, theorem=text[start:end], trailer=text[end:].strip())


def load_challenge(item: Item) -> Challenge:
    return parse_challenge(item.lean_file.read_text(encoding="utf-8"), item.lean["theorem"])


def strip_lean_comments(code: str) -> str:
    """Retire les commentaires Lean (``--`` et ``/- … -/`` imbriqués, docstrings comprises).

    Les chaînes ``"…"`` sont conservées telles quelles (un ``--`` dans une chaîne n'ouvre pas de
    commentaire). Les retours à la ligne des commentaires de bloc sont gardés pour préserver les
    numéros de ligne.
    """
    out, i, n = [], 0, len(code)
    while i < n:
        c = code[i]
        if c == '"':
            j = i + 1
            while j < n and code[j] != '"':
                j += 2 if code[j] == "\\" else 1
            out.append(code[i:j + 1])
            i = j + 1
        elif code.startswith("--", i):
            j = code.find("\n", i)
            i = n if j < 0 else j
        elif code.startswith("/-", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if code.startswith("/-", j):
                    depth, j = depth + 1, j + 2
                elif code.startswith("-/", j):
                    depth, j = depth - 1, j + 2
                else:
                    j += 1
            out.append("\n" * code.count("\n", i, j))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)
