# -*- coding: utf-8 -*-
r"""Step 1 of the plates upload: copy the 109 release-1 4K plates (413.5 MiB, and ONLY those) out of the build's scratch folders into a
permanent folder, so the upload does not depend on a temp folder that Windows or Claude may clean.

    python scripts/stage_release1_plates.py --repo C:\kuriam\snapeyes --y2 <...\wave-y2\plates> --y3 <...\wave-y3> --dest D:\snapeyes-plates-4k

--repo   a checkout that holds the release (api/_lib/plates_registry.py): the registry names every file with its size and sha256
--y2/--y3 the two scratch folders the registry's plates were made in (the same two the upload script takes)
--dest   where the copy goes: <dest>/plates_4k/<family>/<file>, which is exactly the layout `upload_plates.py --y2 <dest>` reads

A file is copied only when its size and sha256 equal the registry's; one that is wrong or missing is reported and the exit code is 1.
Idempotent: a file already in --dest with the right hash is left alone. Nothing is deleted. No network, no key.
"""
import argparse, hashlib, os, shutil, sys

MIB = 1048576

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--y2", required=True)
    ap.add_argument("--y3", required=True)
    ap.add_argument("--dest", required=True)
    a = ap.parse_args()
    sys.path.insert(0, os.path.join(a.repo, "api"))
    from _lib import plates_registry as REG
    table, fams = REG.PLATES_REGISTRY["plates"], REG.PLATES_REGISTRY["families"]
    want = {f for f, d in fams.items() if d["release1"] and d["store4k"]}
    roots = [os.path.join(a.y2, "plates_4k"), os.path.join(a.y3, "plates_uv", "plates_4k")]
    n = bad = copied = present = 0
    total = 0
    for pid, rec in sorted(table.items()):
        k4 = rec.get("k4")
        if not k4 or not rec.get("usable") or rec["family"] not in want:
            continue
        n += 1
        total += k4["bytes"]
        dst = os.path.join(a.dest, "plates_4k", rec["family"], k4["file"])
        if os.path.isfile(dst) and os.path.getsize(dst) == k4["bytes"] and sha256_of(dst) == k4["sha256"]:
            present += 1
            continue
        src = next((p for p in (os.path.join(r, rec["family"], k4["file"]) for r in roots) if os.path.isfile(p)), None)
        if src is None:
            bad += 1; print(f"MISSING  {pid}"); continue
        if os.path.getsize(src) != k4["bytes"] or sha256_of(src) != k4["sha256"]:
            bad += 1; print(f"WRONG    {pid}: the source file is not the registry's file"); continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst + ".part")
        os.replace(dst + ".part", dst)
        if sha256_of(dst) != k4["sha256"]:
            bad += 1; print(f"WRONG    {pid}: copy does not verify"); continue
        copied += 1
    print(f"{n} plates ({total / MIB:.1f} MiB) in {', '.join(sorted(want))}: {copied} copied, {present} already there, {bad} bad or missing")
    print(f"next: python scripts/upload_plates.py --y2 {a.dest} --release1   (dry run), then the same with --yes")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
