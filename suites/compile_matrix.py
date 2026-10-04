# -*- coding: utf-8 -*-
"""`python -m compileall api` under every Python the production could run (3.12, 3.13, 3.14).   python suites/compile_matrix.py

Vercel's default Python is 3.12 and `.python-version` may name another, so the functions must compile under all three and use no
syntax newer than 3.12 (the check parses every file with feature_version 3.12). Interpreters are found with SNAPEYES_PYTHONS
(paths, separated like PATH), else the Windows launcher (`py -0p`), else python3.12, python3.13, python3.14 on PATH. A missing
interpreter is reported as such, not as a pass. The byte code goes to a temporary folder, never into api/. Exit 1 on any failure."""
import ast, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WANT = ("3.12", "3.13", "3.14")


def interpreters():
    found = {}
    env = os.environ.get("SNAPEYES_PYTHONS")
    paths = [p for p in env.split(os.pathsep) if p] if env else []
    if not paths:
        try:
            out = subprocess.run(["py", "-0p"], capture_output=True, text=True, timeout=20).stdout
            paths = [m.group(1) for m in re.finditer(r"^\s*-\S+\s+\*?\s*(\S.*?\.exe)\s*$", out, flags=re.M)]
        except (OSError, subprocess.SubprocessError):
            paths = []
        paths += [p for p in (shutil.which(f"python{v}") for v in WANT) if p]
    for p in paths:
        try:
            v = subprocess.run([p, "-c", "import sys;print('%d.%d' % sys.version_info[:2])"], capture_output=True, text=True, timeout=20).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            continue
        found.setdefault(v, p)
    return found


def main():
    found = interpreters()
    bad = 0
    for v in WANT:
        if v not in found:
            print(f"python {v}: NOT INSTALLED here (not checked)")
            continue
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([found[v], "-m", "compileall", "-q", "api"], cwd=ROOT, capture_output=True, text=True,
                               env=dict(os.environ, PYTHONPYCACHEPREFIX=tmp, PYTHONIOENCODING="utf-8"))
        ok = r.returncode == 0
        bad += 0 if ok else 1
        print(f"python {v}: compileall api {'ok' if ok else 'FAILED'}" + ("" if ok else "\n" + (r.stdout + r.stderr)[-800:]))
    n, errs = 0, []
    for root, ds, fs in os.walk(os.path.join(ROOT, "api")):
        ds[:] = [d for d in ds if d != "__pycache__"]
        for f in fs:
            if f.endswith(".py"):
                n += 1
                p = os.path.join(root, f)
                try:
                    ast.parse(open(p, encoding="utf-8").read(), p, feature_version=(3, 12))
                except SyntaxError as e:
                    errs.append(f"{os.path.relpath(p, ROOT)}: {e}")
    bad += len(errs)
    print(f"syntax of {n} api files as Python 3.12: " + ("ok" if not errs else "\n  " + "\n  ".join(errs)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
