# -*- coding: utf-8 -*-
"""Uploads the 4K plates of the baked library (api/_lib/plates_registry.py) to private storage, where fetch_4k() reads them at a master.
Idempotent, never deletes, verifies every hash. A DRY RUN unless --yes is given: nothing leaves this machine otherwise.

    python scripts/upload_plates.py --y2 <wave-y2/plates> --y3 <wave-y3> [--families P-SN-CLOUD ...] [--release1] [--yes] [--local-dir DIR]

  what is uploaded  the plates the registry gives a 4K file (k4) in the families named (--release1: the families a style of the first release
                    fetches: P-SN-CLOUD (Powder Burst), P-SP-CROWN (Splash), P-DN-SPIRAL (the Vortex look of Universe) and P-UV-DUST (the dust of the
                    collision family and of Universe): 109 plates; nothing is chosen by default: name the families). The source
                    file is found under --y2 (plates_4k/<family>/<file>) or --y3 (plates_uv/plates_4k/<family>/<file>) and must have the exact
                    size and sha256 the registry records, else the plate is refused (the registry names a file, not "a file like it")
  where             plates/v1/<family>/<file> in the private bucket (api/_lib/store.py: the service key and the bucket come from the environment as
                    everywhere else; this script never reads, prints or writes a key). --local-dir DIR uses a folder instead (tests, a dry run of
                    the whole flow): it sets STORE_LOCAL_DIR
  idempotent        an object already there is read back and compared with the registry's sha256: equal, it is left alone ("present"); different,
                    it is reported as WRONG and never overwritten (upsert is off: a wrong object is for a person to look at)
  the end           the counts and the bytes per family (the storage figure V6 of the plan asks for), and the exit code: 0 when every plate asked for is
                    present (or would be uploaded, in a dry run), 1 when a source is missing or wrong or a stored object is wrong

The size to expect (MiB of 4K files, from the registry): the first release's four families are 413.5 MiB (CLOUD 237.6, SPIRAL 72.5, CROWN 59.7,
DUST 43.7) of the free tier's 1 GB, to be read against the project's real storage plan before this runs with --yes (V6).

The sources are the two scratch folders the plates were made in, which are not in git and may be cleaned: scripts/stage_release1_plates.py copies the 109 files (after
checking every size and sha256 against the registry) to a permanent folder first, and scripts/upload_release1_plates.ps1 does the dry run, the upload and the read-back on
the owner's machine without ever writing the service key to a file (README, "Uploading the plates"). The last pass of this script (the same command again with --yes)
downloads every plate and compares its sha256: that, and not /api/health plates_4k (the first and the last plate of every family), is the proof that every plate is there.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "api"))

MIB = 1048576
TYPES = {".png": "image/png", ".webp": "image/webp"}


def sources(y2, y3):
    """Where a 4K file may be found: the two scratch layouts."""
    return [os.path.join(y2, "plates_4k"), os.path.join(y3, "plates_uv", "plates_4k")] if y2 or y3 else []


def find_source(roots, family, name):
    for r in roots:
        p = os.path.join(r, family, name)
        if os.path.isfile(p):
            return p
    return None


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def plan(table, families, roots):
    """[{id, family, path, bytes, sha256, source, why}] for every plate with a 4K file in these families: why is None when the source file is the
    registry's file, else no_source, size or sha256."""
    rows = []
    for pid, rec in sorted(table.items()):
        k4 = rec.get("k4")
        if not k4 or not rec.get("usable") or rec["family"] not in families:
            continue
        row = {"id": pid, "family": rec["family"], "path": f"plates/v1/{rec['family']}/{k4['file']}", "bytes": k4["bytes"], "sha256": k4["sha256"],
               "source": None, "why": None}
        src = find_source(roots, rec["family"], k4["file"])
        if src is None:
            row["why"] = "no_source"
        elif os.path.getsize(src) != k4["bytes"]:
            row["source"], row["why"] = src, "size"
        elif sha256_of(src) != k4["sha256"]:
            row["source"], row["why"] = src, "sha256"
        else:
            row["source"] = src
        rows.append(row)
    return rows


def run(rows, store, yes=False, out=print):
    """Upload what is missing (yes), compare what is there. Returns {present, uploaded, would, wrong, bad_source, bytes_by_family}."""
    tot = {"present": 0, "uploaded": 0, "would": 0, "wrong": 0, "bad_source": 0, "bytes_by_family": {}}
    for r in rows:
        if r["why"]:
            tot["bad_source"] += 1
            out(f"SOURCE {r['why'].upper():9s} {r['id']}")
            continue
        got = store.get(r["path"], max_bytes=16 << 20)
        if got is not None:
            if hashlib.sha256(got).hexdigest() == r["sha256"]:
                tot["present"] += 1
                tot["bytes_by_family"][r["family"]] = tot["bytes_by_family"].get(r["family"], 0) + r["bytes"]
            else:
                tot["wrong"] += 1
                out(f"WRONG     {r['path']}: the stored object is not the registry's file (left as it is)")
            continue
        if not yes:
            tot["would"] += 1
            tot["bytes_by_family"][r["family"]] = tot["bytes_by_family"].get(r["family"], 0) + r["bytes"]
            continue
        with open(r["source"], "rb") as f:
            data = f.read()
        try:
            store.put(r["path"], data, TYPES[os.path.splitext(r["path"])[1]], upsert=False)
        except Exception as e:  # noqa: a timeout or a dropped connection ends the run with a sentence, not a traceback; the same command continues where it stopped
            tot["failed"] = tot.get("failed", 0) + 1
            out(f"FAILED    {r['path']}: {type(e).__name__}: run the same command again, it continues where it stopped (an object that is already there is compared, never overwritten)")
            return tot
        tot["uploaded"] += 1
        tot["bytes_by_family"][r["family"]] = tot["bytes_by_family"].get(r["family"], 0) + r["bytes"]
        out(f"uploaded  {r['path']} ({r['bytes'] / MIB:.2f} MiB)")
    return tot


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--y2", default="", help="the plate workflow folder (wave-y2/plates of the scratch tree)")
    ap.add_argument("--y3", default="", help="the wave-y3 folder of the scratch tree")
    ap.add_argument("--families", nargs="*", default=[], help="plate families to upload, e.g. P-SN-CLOUD")
    ap.add_argument("--release1", action="store_true", help="the families a style of the first release fetches")
    ap.add_argument("--yes", action="store_true", help="really upload (without it: a dry run)")
    ap.add_argument("--local-dir", default="", help="use a folder instead of the bucket (STORE_LOCAL_DIR)")
    a = ap.parse_args(argv)
    if a.local_dir:
        os.environ["STORE_LOCAL_DIR"] = os.path.abspath(a.local_dir)
    from _lib import plates_registry as REG, store
    table, fams = REG.PLATES_REGISTRY["plates"], REG.PLATES_REGISTRY["families"]
    want = set(a.families) | ({f for f, d in fams.items() if d["release1"]} if a.release1 else set())
    unknown = sorted(f for f in want if f not in fams or not fams[f]["store4k"])
    if unknown:
        sys.exit(f"not a family with 4K files: {', '.join(unknown)} (families: {', '.join(f for f, d in fams.items() if d['store4k'])})")
    if not want:
        sys.exit("name the families to upload (--families P-SN-CLOUD ...) or --release1")
    if not store.configured():
        sys.exit(f"no storage to write to: {store.problem()} (or --local-dir)")
    rows = plan(table, want, sources(a.y2, a.y3))
    tot = run(rows, store, a.yes)
    mode = "uploaded" if a.yes else "would upload"
    print(f"\n{len(rows)} plates in {', '.join(sorted(want))}: {tot['present']} present, {tot['uploaded'] if a.yes else tot['would']} {mode}, "
          f"{tot['wrong']} wrong in storage, {tot['bad_source']} with a bad or missing source")
    for fam, b in sorted(tot["bytes_by_family"].items()):
        print(f"  {fam:14s} {b / MIB:8.2f} MiB")
    print(f"  {'total':14s} {sum(tot['bytes_by_family'].values()) / MIB:8.2f} MiB" + ("" if a.yes else "   (dry run: nothing was written; --yes uploads)"))
    return 1 if (tot["wrong"] or tot["bad_source"] or tot.get("failed")) else 0


if __name__ == "__main__":
    sys.exit(main())
