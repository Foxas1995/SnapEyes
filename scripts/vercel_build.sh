#!/bin/bash
# The build of a Vercel deployment (vercel.json: installCommand "echo skip", buildCommand "bash scripts/vercel_build.sh").
#
# WHY IT IS NOT JUST `npm install && npm run build`: Vercel bundles every Python function (api/*.py) from the project folder
# right after the install step, while the build command still runs, and a node_modules folder in the project folder rides into
# every bundle (the excludeFiles of vercel.json did not keep it out, measured on Preview deployments of 2026-10-06). With it
# the four rendering functions (62 MiB of api/ plus the Python packages) went over the size limit of a function and the
# deployment failed before anything was served; the same tree without node_modules deploys. So the site is built in a copy of
# the project outside the project folder, and only dist/ comes back. The project folder never holds node_modules.
#
# Locally nothing changes: `npm run build` is still the build (this script is for Vercel's build container only).
set -euo pipefail
HERE="$(pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
# the copy: everything the build reads (api/ for the registry, the plates and the function entries, src/, scripts/, public/, the pages), nothing it makes
tar --exclude=./node_modules --exclude=./dist --exclude=./.git --exclude=./.vercel -cf - . | tar -xf - -C "$WORK"
cd "$WORK"
npm ci --no-audit --no-fund
npm run build
rm -rf "$HERE/dist"
cp -a "$WORK/dist" "$HERE/dist"
echo "vercel_build: dist/ is in place ($(find "$HERE/dist" -type f | wc -l) files); node_modules stayed in $WORK and goes away with it"
