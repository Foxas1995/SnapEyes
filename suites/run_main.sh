#!/bin/bash
# usage: bash suites/run_main.sh [name ...]
# Every guard suite of suites.list (or the named ones) and the page-code tests (scripts/run_ts_tests.mjs, entry "ts"), against
# the checkout this folder lives in (override: SNAPEYES_REPO). Three suites at a time. Prints the table of summary.py and exits 1
# when anything is red, runs fewer checks than suites/baseline.json records, or did not run (SKIPPED: the private image fixtures
# are missing; SNAPEYES_ALLOW_SKIPPED=1 accepts that on purpose).
#   SNAPEYES_SUITES_OUT   where the prepared tree and the results go (default suites/out, not in git)
#   SNAPEYES_FIXTURES     the private image fixtures (default suites/private/fixtures, not in git)
#   SNAPEYES_ALLOW_SKIPPED=1   do not fail the run because the two admin suites were skipped (no fixtures on this machine)
export PYTHONIOENCODING=utf-8
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${SNAPEYES_REPO:-$(cd "$HERE/.." && pwd)}"
OUT="${SNAPEYES_SUITES_OUT:-$HERE/out}"
if command -v cygpath > /dev/null 2>&1; then REPO="$(cygpath -m "$REPO")"; OUT="$(cygpath -m "$OUT")"; fi
export SNAPEYES_REPO="$REPO" SNAPEYES_SP="$OUT/sp"
mkdir -p "$OUT"
if [ ! -f "$REPO/dist/legal/order-mail.json" ]; then
  echo "run_main: no dist/legal/order-mail.json in $REPO, running npm run build first (the admin suites read the legal pack)"
  (cd "$REPO" && npm run build > "$OUT/build.log" 2>&1) || { echo "run_main: npm run build FAILED, see $OUT/build.log"; exit 1; }
fi
python "$HERE/mksp.py" "$OUT/sp" "$REPO" || exit 1
bash "$HERE/run_all.sh" "$OUT/sp" "$REPO" "$OUT/results" "$@"
want_ts=1
if [ $# -gt 0 ]; then want_ts=0; for n in "$@"; do [ "$n" = ts ] && want_ts=1; done; fi
if [ $want_ts = 1 ]; then
  (cd "$REPO" && node scripts/run_ts_tests.mjs > "$OUT/results/ts.out" 2>&1; echo "ts EXIT $?" > "$OUT/results/ts.exit")
fi
BASE=(); [ -f "$HERE/baseline.json" ] && BASE=(--baseline "$HERE/baseline.json")
[ $# -eq 0 ] && BASE+=(--all)
python "$HERE/summary.py" "$OUT/results" "${BASE[@]}"
