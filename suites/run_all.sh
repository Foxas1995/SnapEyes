#!/bin/bash
# usage: run_all.sh <spdir> <repo> <outdir> [name ...]
# Runs the suites of suites.list three at a time (no names = every suite) in the prepared tree <spdir> (mksp.py), against the
# checkout <repo>. Results: <outdir>/<name>.out and <name>.exit ("<name> EXIT <code>"; 77 = skipped), <name>.secs (the seconds it took), then all.done.
# A suite is stopped after SNAPEYES_SUITE_TIMEOUT seconds (default 3600: v3coll takes 15 to 20 minutes alone and more with three suites and another
# builder's process on one machine, v3uni 12 to 14; a timeout is exit 124, RED, and says so in the table).
# An entry of suites.list that ends in `:pre` (name:dir:script:needs:pre, needs may be empty) runs in the world BEFORE the v3 catalogue switch: the older suites use the
# six legacy styles, which the switch retired, as the vehicle of what they guard, so they start with suites/shim on PYTHONPATH and SNAPEYES_WORLD=pre-cutover
# (suites/shim/sitecustomize.py puts the catalogue back the way it was, in memory, the moment it is imported; the file explains what that proves). The v3 suites
# have no `pre`: they run in the real world.
export PYTHONIOENCODING=utf-8
# Second line against a real model call (release review, security M2; the first line is iris._key(), which no longer reads the developer's key file): no suite may reach a
# real service. Every request to a host other than this machine goes to a closed local port and fails at once (ProxyError); the local servers some suites start stay reachable.
# Every suite stubs the model and the payment service; a path that forgot to is stopped here instead of costing money.
export HTTPS_PROXY=http://127.0.0.1:9 HTTP_PROXY=http://127.0.0.1:9 ALL_PROXY=http://127.0.0.1:9 NO_PROXY=127.0.0.1,localhost,::1
export https_proxy=$HTTPS_PROXY http_proxy=$HTTP_PROXY all_proxy=$ALL_PROXY no_proxy=$NO_PROXY
unset GEMINI_API_KEY GOOGLE_API_KEY SNAPEYES_DEV_KEYFILE
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ $# -lt 3 ] || [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
  echo "usage: run_all.sh <spdir> <repo> <outdir> [name ...]   (suites/run_main.sh calls it with all three)" >&2; exit 2
fi
SP=$1; export SNAPEYES_REPO=$2; OUT=$3; shift 3
case "$OUT" in /|.|..|./|../) echo "run_all.sh: refusing to clear the results folder '$OUT'" >&2; exit 2;; esac
mkdir -p "$OUT" && find "$OUT" -maxdepth 1 -type f -delete
ALL=$(grep -v '^[[:space:]]*#' "$HERE/suites.list" | grep -v '^[[:space:]]*$' | tr -d '\r')
SHIM="$HERE/shim"; if command -v cygpath > /dev/null 2>&1; then SHIM="$(cygpath -m "$SHIM")"; fi
export SP OUT SHIM
run() {
  IFS=: read name dir script needs world <<< "$1"
  if [ "$needs" = fixtures ] && [ -f "$SP/.no_fixtures" ]; then
    echo "SKIPPED: the private image fixtures are missing (suites/README.md, SNAPEYES_FIXTURES)" > "$OUT/$name.out"
    echo "$name EXIT 77" > "$OUT/$name.exit"; return
  fi
  if [ ! -f "$SP/$dir/$script" ]; then
    echo "MISSING: $dir/$script is not in the prepared tree" > "$OUT/$name.out"
    echo "$name EXIT 78" > "$OUT/$name.exit"; return
  fi
  t0=$(date +%s)
  if [ "$world" = pre ]; then echo "pre-cutover" > "$OUT/$name.world"; fi
  (cd "$SP/$dir" && { if [ "$world" = pre ]; then export SNAPEYES_WORLD=pre-cutover PYTHONPATH="$SHIM${PYTHONPATH:+;$PYTHONPATH}"; fi; timeout "${SNAPEYES_SUITE_TIMEOUT:-3600}" python "$script" > "$OUT/$name.out" 2>&1; echo "$name EXIT $?" > "$OUT/$name.exit"; })
  echo $(( $(date +%s) - t0 )) > "$OUT/$name.secs"
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
