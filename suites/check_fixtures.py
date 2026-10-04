# -*- coding: utf-8 -*-
"""Compares the private image fixtures with suites/fixtures.sha256.   python suites/check_fixtures.py [folder]

The folder (default SNAPEYES_FIXTURES, else suites/private/fixtures) holds the replies the admin suites replay in place of the
image model, recorded from the owner's own photos. It is never committed (a real eye is biometric data); this list is how a copy
kept elsewhere is verified. Exit 1 when a file is missing, extra or different; nothing is read from anywhere else."""
import hashlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else (os.environ.get("SNAPEYES_FIXTURES") or os.path.join(HERE, "private", "fixtures"))
    want = {}
    for line in open(os.path.join(HERE, "fixtures.sha256"), encoding="utf-8"):
        if line.strip() and not line.startswith("#"):
            digest, size, name = line.split(None, 2)
            want[name.strip()] = (digest, int(size))
    have = sorted(os.listdir(folder)) if os.path.isdir(folder) else []
    bad = [f"missing: {n}" for n in want if n not in have] + [f"extra: {n}" for n in have if n not in want]
    for n in have:
        if n in want:
            b = open(os.path.join(folder, n), "rb").read()
            if (hashlib.sha256(b).hexdigest(), len(b)) != want[n]:
                bad.append(f"different: {n}")
    print("\n".join(bad) if bad else f"fixtures ok: {len(want)} files in {folder}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
