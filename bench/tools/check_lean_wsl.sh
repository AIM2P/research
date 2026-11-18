#!/usr/bin/env bash
# Synchronise bench/lean vers ~/aim2p-bench (WSL, hors .lake) puis vérifie que chaque énoncé
# de défi compile avec Lean v4.35.0. Un énoncé de défi contient `sorry` : on n'exige donc que
# l'absence d'erreur, pas l'absence d'avertissement.
#
# Usage, depuis Ubuntu (WSL) :
#   bash "/mnt/c/Users/LENOVO/Documents/Research Project AIM²P/bench/tools/check_lean_wsl.sh" [module ...]
# Sans argument : tous les fichiers de AMPBench/Items/ et AMPBench/Private/ (défis privés, hors dépôt).
#
# Code sous licence Apache-2.0 (voir bench/LICENSE).
set -uo pipefail
export PATH="$HOME/.elan/bin:$PATH"
SRC="$(cd "$(dirname "$0")/../lean" && pwd)"
DST="$HOME/aim2p-bench"
mkdir -p "$DST"
tar -C "$SRC" --exclude=.lake -cf - . | tar -C "$DST" -xf -
cd "$DST"

if [ "$#" -gt 0 ]; then
  files=()
  for m in "$@"; do files+=("$(echo "$m" | tr . /).lean"); done
else
  mapfile -t files < <(ls AMPBench/Items/*.lean AMPBench/Private/*.lean 2>/dev/null | sort)
fi

# Mathlib arrive compilé par son cache (`lake exe cache get`). Les modules Physlib importés, eux,
# se compilent localement à la première utilisation : on les construit avant `lake env lean`.
mapfile -t mods < <(grep -h '^import Physlib' "${files[@]}" 2>/dev/null | awk '{print $2}' | sort -u)
if [ "${#mods[@]}" -gt 0 ]; then
  lake build "${mods[@]}" > /tmp/aim2p_build_imports.log 2>&1     || { echo "avertissement : construction des imports Physlib incomplète (voir /tmp/aim2p_build_imports.log)"; }
fi

fail=0
for f in "${files[@]}"; do
  t0=$(date +%s)
  out=$(lake env lean "$f" 2>&1)
  rc=$?
  dt=$(( $(date +%s) - t0 ))
  if [ $rc -eq 0 ] && ! grep -q "error" <<<"$out"; then
    echo "ok      ${dt}s  $f"
  else
    echo "ERREUR  ${dt}s  $f"
    grep -m5 "error" <<<"$out" | sed 's/^/          /'
    fail=$((fail + 1))
  fi
done
echo "${#files[@]} fichier(s), ${fail} en erreur"
exit $fail
