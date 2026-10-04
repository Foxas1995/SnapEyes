#!/bin/bash
# usage: run_all.sh <spdir> <repo> <outdir> [name ...]
# Runs the suites of suites.list three at a time (no names = every suite) in the prepared tree <spdir> (mksp.py), against the
# checkout <repo>. Results: <outdir>/<name>.out and <name>.exit ("<name> EXIT <code>"; 77 = skipped), then all.done.
export PYTHONIOENCODING=utf-8
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SP=$1; export SNAPEYES_REPO=$2; OUT=$3; shift 3
mkdir -p "$OUT"; rm -f "$OUT"/*
ALL=$(grep -v '^[[:space:]]*#' "$HERE/suites.list" | grep -v '^[[:space:]]*$' | tr -d '\r')
export SP OUT
run() {
  IFS=: read name dir script needs <<< "$1"
  if [ "$needs" = fixtures ] && [ -f "$SP/.no_fixtures" ]; then
    echo "SKIPPED: the private image fixtures are missing (suites/README.md, SNAPEYES_FIXTURES)" > "$OUT/$name.out"
    echo "$name EXIT 77" > "$OUT/$name.exit"; return
  fi
  if [ ! -f "$SP/$dir/$script" ]; then
    echo "MISSING: $dir/$script is not in the prepared tree" > "$OUT/$name.out"
    echo "$name EXIT 78" > "$OUT/$name.exit"; return
  fi
  (cd "$SP/$dir" && timeout 1800 python "$script" > "$OUT/$name.out" 2>&1; echo "$name EXIT $?" > "$OUT/$name.exit")
}
export -f run
if [ $# -gt 0 ]; then
  LIST=""
  for n in "$@"; do while IFS= read -r e; do [ "${e%%:*}" = "$n" ] && LIST="$LIST"$'\n'"$e"; done <<< "$ALL"; done
else
  LIST="$ALL"
fi
printf '%s\n' "$LIST" | grep -v '^$' | xargs -r -P 3 -I{} bash -c 'run {}'
echo ALLDONE > "$OUT/all.done"
