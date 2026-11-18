# SPDX-License-Identifier: Apache-2.0
"""Harnais d'évaluation des baselines B0, B1 et B2 d'AIM²P (phase P3).

Voir harness/README.md. Protocole : docs/04_Research_Proposal_v0.1.md (§5.2 à §5.6) et
docs/05_Domain_Map.md (§3 à §5).
"""
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BENCH = REPO / "bench"
__version__ = "0.1.0"
