# -*- coding: utf-8 -*-
"""Size of the Python dependencies of the functions, two ways. Used by scripts/bundle_report.mjs, runnable alone.

    python scripts/bundle_deps.py local            # the packages installed in THIS interpreter (the requirements.txt names and
                                                   # everything they pull in), summed from each package's RECORD
    python scripts/bundle_deps.py pypi             # the Linux wheels PyPI lists for the pinned versions, summed from the zip
                                                   # directories of the wheels (read with HTTP range requests: about 100 KB each,
                                                   # no wheel is downloaded or unpacked)

Both print one JSON object: {"how", "platform", "python", "dists": [{"name", "version", "bytes", "file"?}], "total", "notes": []}.

Why two: `vercel build` on this Windows machine would install Windows wheels (numpy 39 MB, Pillow 14 MB, onnxruntime 37 MB), which is
not what a Linux function holds, so `local` is only a floor of the Windows kind; `pypi` reads the sizes of the wheels the Linux build
would install (the interpreter is `.python-version`, the platform manylinux x86_64) without a Linux machine. It is still an
estimate: pip's real resolution of the packages the pins pull in may pick other versions, an installer may add .dist-info files and
byte code, and Vercel may place dependencies differently; the Preview deployment's function list (or `vercel inspect`) is the number
that counts (closing step V1 of the plan). Bytes are uncompressed file sizes, byte code (.pyc) left out, as the unpacked wheel has it."""
from __future__ import annotations

import json
import os
import re
import struct
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIMEOUT = 30


def requirements() -> list[tuple[str, str | None]]:
    """[(name, pinned version or None)] of requirements.txt (comments and blank lines skipped)."""
    out = []
    for line in open(os.path.join(ROOT, "requirements.txt"), encoding="utf-8"):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        m = re.match(r"^([A-Za-z0-9_.-]+)\s*(?:==\s*([A-Za-z0-9_.!+-]+))?", line)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def python_minor() -> str:
    try:
        v = open(os.path.join(ROOT, ".python-version"), encoding="utf-8").read().strip()
        m = re.match(r"^(\d+)\.(\d+)", v)
        return f"{m.group(1)}.{m.group(2)}" if m else "3.12"
    except OSError:
        return "3.12"


# ----------------------------------------------------------------------------- local: this interpreter's site-packages
def local() -> dict:
    from importlib import metadata
    from packaging.requirements import Requirement
    seen, order, notes = {}, [], []

    def visit(name: str):
        key = norm(name)
        if key in seen:
            return
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            seen[key] = None
            notes.append(f"{name}: not installed in this interpreter (skipped)")
            return
        size = 0
        for f in dist.files or []:
            if f.name.endswith(".pyc") or "__pycache__" in f.parts:
                continue
            p = dist.locate_file(f)
            try:
                size += os.path.getsize(p)
            except OSError:
                pass
        seen[key] = {"name": dist.metadata["Name"], "version": dist.version, "bytes": size}
        order.append(key)
        for r in dist.requires or []:
            req = Requirement(r)
            if req.marker is not None and not req.marker.evaluate({"extra": ""}):
                continue
            visit(req.name)

    for name, _ in requirements():
        visit(name)
    dists = [seen[k] for k in order if seen[k]]
    return {"how": "local", "platform": sys.platform, "python": sys.version.split()[0], "dists": dists,
            "total": sum(d["bytes"] for d in dists), "notes": notes}


# ----------------------------------------------------------------------------- pypi: Linux wheels, zip directories by range
def _get(url: str, headers: dict | None = None) -> tuple[bytes, dict]:
    req = urllib.request.Request(url, headers=dict({"User-Agent": "snapeyes-bundle-report"}, **(headers or {})))
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read(), dict(r.headers)


def _wheel_bytes(url: str) -> int:
    """Sum of the uncompressed sizes of the files in a wheel (a zip), from its central directory only."""
    try:
        tail, h = _get(url, {"Range": "bytes=-131072"})
    except urllib.error.HTTPError as e:
        if e.code != 416:               # a wheel smaller than the range: the server refuses it, the whole file is the tail
            raise
        tail, h = _get(url)
    m = re.match(r"bytes (\d+)-(\d+)/(\d+)", h.get("Content-Range", "") or h.get("content-range", ""))
    if m:
        start, total = int(m.group(1)), int(m.group(3))
    elif len(tail) < 4 * 1048576:       # the whole file came back (no Content-Range)
        start, total = 0, len(tail)
    else:
        raise RuntimeError("the server did not answer the range request")
    at = tail.rfind(b"PK\x05\x06")
    if at < 0:
        raise RuntimeError("no zip directory found")
    entries, cd_size, cd_off = struct.unpack("<HII", tail[at + 10:at + 20])
    if entries == 0xFFFF or cd_off == 0xFFFFFFFF:
        raise RuntimeError("zip64 wheel (not handled)")
    if cd_off >= start:
        cd = tail[cd_off - start:cd_off - start + cd_size]
    else:
        cd, _ = _get(url, {"Range": f"bytes={cd_off}-{cd_off + cd_size - 1}"})
    pos, size, n = 0, 0, 0
    while pos + 46 <= len(cd) and cd[pos:pos + 4] == b"PK\x01\x02":
        usize = struct.unpack("<I", cd[pos + 24:pos + 28])[0]
        nlen, elen, clen = struct.unpack("<HHH", cd[pos + 28:pos + 34])
        name = cd[pos + 46:pos + 46 + nlen].decode("utf-8", "replace")
        if not name.endswith("/") and not name.endswith(".pyc"):
            size += usize
        pos += 46 + nlen + elen + clen
        n += 1
    if n != entries:
        raise RuntimeError(f"read {n} of {entries} directory entries")
    return size


def _tag_ok(fn: str, py: str) -> int:
    """0 = not for this target; higher is better. cpXY manylinux x86_64, else a pure py3-none-any wheel."""
    cp = "cp" + py.replace(".", "")
    if fn.endswith("py3-none-any.whl") or "-py2.py3-none-any" in fn:
        return 1
    if f"-{cp}-{cp}-" in fn and "manylinux" in fn and "x86_64" in fn and "musllinux" not in fn:
        return 3 if "manylinux_2_28" in fn or "manylinux_2_27" in fn else 2
    if "-abi3-" in fn and "manylinux" in fn and "x86_64" in fn:
        return 2
    return 0


def pypi() -> dict:
    from packaging.requirements import Requirement
    from packaging.version import Version, InvalidVersion
    py = python_minor()
    env = {"sys_platform": "linux", "platform_system": "Linux", "platform_machine": "x86_64", "os_name": "posix",
           "python_version": py, "python_full_version": py + ".0", "implementation_name": "cpython", "platform_python_implementation": "CPython",
           "extra": ""}
    notes, dists, seen = [], [], set()

    def meta(name: str, version: str | None) -> dict:
        url = f"https://pypi.org/pypi/{norm(name)}/{version}/json" if version else f"https://pypi.org/pypi/{norm(name)}/json"
        return json.loads(_get(url)[0])

    def choose(name: str, specs) -> str | None:
        # the versions of a project from the simple API (PEP 691 and 700), the interface PyPI keeps stable
        d = json.loads(_get(f"https://pypi.org/simple/{norm(name)}/", {"Accept": "application/vnd.pypi.simple.v1+json"})[0])
        good = []
        for v in d.get("versions", []):
            try:
                ver = Version(v)
            except InvalidVersion:
                continue
            if not ver.is_prerelease and not ver.is_devrelease and all(ver in s for s in specs):
                good.append(ver)
        return str(max(good)) if good else None

    def visit(name: str, version: str | None, specs=()):
        key = norm(name)
        if key in seen:
            return
        seen.add(key)
        if version is None:
            version = choose(name, specs)
            if version is None:
                notes.append(f"{name}: no release satisfies {', '.join(str(s) for s in specs) or 'the requirement'}")
                return
            notes.append(f"{name} {version}: not pinned, the newest release that fits was taken")
        d = meta(name, version)
        files = sorted(((_tag_ok(f["filename"], py), f) for f in d["urls"] if f["filename"].endswith(".whl")), key=lambda t: -t[0])
        if not files or files[0][0] == 0:
            notes.append(f"{name} {version}: no wheel for Python {py} on Linux x86_64 (skipped)")
            return
        f = files[0][1]
        try:
            size = _wheel_bytes(f["url"])
        except Exception as e:  # noqa: a network failure is reported, not hidden
            notes.append(f"{name} {version}: {f['filename']} could not be read ({type(e).__name__}: {e})")
            return
        dists.append({"name": name, "version": version, "bytes": size, "file": f["filename"], "wheel_bytes": f["size"]})
        for r in d["info"].get("requires_dist") or []:
            req = Requirement(r)
            if req.marker is not None and not req.marker.evaluate(env):
                continue
            visit(req.name, None, (req.specifier,))

    for name, version in requirements():
        visit(name, version)
    return {"how": "pypi", "platform": "linux x86_64", "python": py, "dists": dists, "total": sum(d["bytes"] for d in dists), "notes": notes}


def main(argv: list[str]) -> int:
    how = argv[0] if argv else ""
    if how not in ("local", "pypi"):
        print(__doc__)
        return 2
    try:
        res = local() if how == "local" else pypi()
    except ImportError as e:
        print(json.dumps({"how": how, "error": f"needs the 'packaging' package ({e})"}))
        return 1
    except urllib.error.URLError as e:
        print(json.dumps({"how": how, "error": f"PyPI could not be reached ({e})"}))
        return 1
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
