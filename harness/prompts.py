# SPDX-License-Identifier: Apache-2.0
"""Rendu des invites à partir des gabarits versionnés de harness/prompts/ (answer_v1.md, proof_v1.md)."""
from __future__ import annotations

import hashlib
import re

from harness import REPO
from harness.items import Challenge, Item

PROMPTS = REPO / "harness" / "prompts"
NO_INFORMAL = "(non fourni : seul l'énoncé formel ci-dessous fait foi)"


def load_template(kind: str, version: str) -> tuple[str, str]:
    """Renvoie (gabarit sans les commentaires HTML de tête, empreinte SHA-256 du fichier)."""
    path = PROMPTS / f"{kind}_{version}.md"
    data = path.read_bytes()
    text = data.decode("utf-8").replace("\r\n", "\n")
    text = re.sub(r"\A(?:\s*<!--.*?-->\s*)+", "", text, flags=re.S)
    return text, hashlib.sha256(data).hexdigest()


def informal_statement(item: Item) -> str:
    if "PutnamBench" in item.source.get("name", "") or item.statement.startswith("Énoncé informel non reproduit"):
        return NO_INFORMAL
    return item.statement.strip()


def render_proof(item: Item, ch: Challenge, version: str) -> tuple[str, str]:
    tpl, sha = load_template("proof", version)
    out = (tpl.replace("{{STATEMENT}}", informal_statement(item))
              .replace("{{HEADER}}", ch.header_code)
              .replace("{{THEOREM}}", ch.theorem.strip())
              .replace("{{NAME}}", ch.name))
    return out.strip() + "\n", sha


def variables_line(answer: dict) -> str:
    names = answer.get("variables", [])
    if not names:
        return "La réponse est une constante : elle ne contient aucune variable."
    return "Symboles autorisés dans la réponse : " + ", ".join(f"`{n}`" for n in names) + "."


def render_answer(item: Item, version: str) -> tuple[str, str]:
    tpl, sha = load_template("answer", version)
    out = tpl.replace("{{STATEMENT}}", item.statement.strip()).replace("{{VARIABLES}}", variables_line(item.answer or {}))
    return out.strip() + "\n", sha
