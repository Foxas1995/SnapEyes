# -*- coding: utf-8 -*-
"""Prepares one run of the guard suites.   python suites/mksp.py <dst> <checkout>

  * copies suites/tree (sources only) to <dst>, with the folder names the suites use among themselves (wave-pv/tests, ...);
  * copies the checkout's own suites (REPO_DIRS: the style suites in scripts/styles_tests) next to them, so a suite that
    lives in the repository is reached by the same `name:dir:script` entry of suites.list as the old ones;
  * puts the private image fixtures (replies recorded from the owner's own photos, never in git) where the two admin
    suites look, or leaves the marker <dst>/.no_fixtures (run_all.sh then skips exactly the entries that need them);
  * puts the checkout's built legal pack (dist/legal/order-mail.json, `npm run build`) beside each admin suite.

The suites find the checkout under test through SNAPEYES_REPO and their own tree through SNAPEYES_SP: suites/run_main.sh sets
both. Nothing in the tree names a path of this machine."""
import os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = os.path.join(HERE, "tree")
REPO_DIRS = ["scripts/styles_tests"]          # relative to the checkout under test; may be absent
FIXTURES = os.environ.get("SNAPEYES_FIXTURES") or os.path.join(HERE, "private", "fixtures")
FIXTURES_AT = "wave-b/try-multi/fixtures"      # where the admin suites look, relative to the prepared tree
ADMIN_SUITES = ["wave-pv/tests/admin", "wave-q/admin"]
SKIP = {"__pycache__"}


def copy_tree(src, dst):
    n = 0
    for root, ds, fs in os.walk(src):
        ds[:] = [d for d in ds if d not in SKIP]
        for f in fs:
            if f.endswith(".pyc"):
                continue
            out = os.path.join(dst, os.path.relpath(os.path.join(root, f), src))
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copy2(os.path.join(root, f), out)
            n += 1
    return n


def main(dst, repo):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    n = copy_tree(TREE, dst)
    for d in REPO_DIRS:
        src = os.path.join(repo, *d.split("/"))
        if os.path.isdir(src):
            n += copy_tree(src, os.path.join(dst, *d.split("/")))
    print(f"mksp: {n} suite files -> {dst}")
    if os.path.isdir(FIXTURES) and os.listdir(FIXTURES):
        copy_tree(FIXTURES, os.path.join(dst, *FIXTURES_AT.split("/")))
        print(f"mksp: private fixtures from {FIXTURES}")
    else:
        open(os.path.join(dst, ".no_fixtures"), "w").write("missing\n")
        print(f"mksp: WARNING private fixtures not found at {FIXTURES} (SNAPEYES_FIXTURES); the suites that need them are skipped")
    pack = os.path.join(repo, "dist", "legal", "order-mail.json")
    for a in ADMIN_SUITES:
        if os.path.isfile(pack):
            out = os.path.join(dst, *a.split("/"), "dist", "legal")
            os.makedirs(out, exist_ok=True)
            shutil.copy2(pack, os.path.join(out, "order-mail.json"))
    if not os.path.isfile(pack):
        print("mksp: WARNING no dist/legal/order-mail.json in the checkout: run `npm run build` first (the admin suites read it)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
