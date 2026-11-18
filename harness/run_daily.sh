#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
#
# Lot quotidien de la campagne P3 (baselines B0, B1, B2 sur Nemotron 3 Ultra).
# À lancer une fois par jour dans Ubuntu (WSL) :
#   bash "/mnt/c/Users/LENOVO/Documents/Research Project AIM²P/harness/run_daily.sh"
#
#  1. Jeu de contrôle : DEV-03 et DEV-04 en B0 (2 requêtes), pour détecter un changement
#     silencieux du modèle servi (document 05, §4).
#  2. Campagne p3_nemotron sur les 40 problèmes figés, jusqu'à épuisement du budget du jour
#     (50 requêtes au total, compteur en UTC ; le harnais s'arrête seul).
#  3. Synthèse provisoire (results/p3_nemotron/).
#
# Reprenable : relancer la commande ne refait jamais une génération déjà faite.
set -uo pipefail
REPO="/mnt/c/Users/LENOVO/Documents/Research Project AIM²P"
export PATH="$HOME/.elan/bin:$HOME/.local/bin:$PATH"
# shellcheck disable=SC1091
source "$HOME/.aim2p_env"
PY="$HOME/aim2p-venv/bin/python"
cd "$REPO" || exit 1
DAY=$(date -u +%Y%m%d)

echo "== Contrôle du jour ($DAY, UTC)"
"$PY" harness/run_baselines.py --campaign "control_$DAY" --items DEV-03,DEV-04 --baselines B0 --runs 1 --max-requests 2

echo "== Campagne p3_nemotron"
"$PY" harness/run_baselines.py --campaign p3_nemotron --split eval --baselines B0,B1,B2 --allow-eval

echo "== Synthèse provisoire"
"$PY" harness/summarize.py --campaign p3_nemotron
