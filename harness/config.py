# SPDX-License-Identifier: Apache-2.0
"""Lecture de la configuration TOML du harnais (harness/config/p3_baselines.toml)."""
from __future__ import annotations

import hashlib
import os
import tomllib
from pathlib import Path

from harness import REPO

DEFAULT_CONFIG = REPO / "harness" / "config" / "p3_baselines.toml"


def load_config(path: str | Path | None = None) -> dict:
    """Charge la configuration et ajoute ``_path`` et ``_sha256`` (empreinte consignée dans les journaux)."""
    p = Path(path) if path else DEFAULT_CONFIG
    data = p.read_bytes()
    cfg = tomllib.loads(data.decode("utf-8"))
    cfg["_path"] = str(p)
    cfg["_sha256"] = hashlib.sha256(data).hexdigest()
    return cfg


def repo_path(rel: str) -> Path:
    """Chemin relatif à la racine du dépôt (ou absolu, ou commençant par ~)."""
    p = Path(os.path.expanduser(rel))
    return p if p.is_absolute() else REPO / p


def home_path(rel: str) -> Path:
    return Path(os.path.expanduser(rel))
