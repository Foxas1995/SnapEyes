# -*- coding: utf-8 -*-
"""WP11 of the v3 engine work: the picker and /try UI, the parts of it that a Python suite can hold equal to the server.
  1. the letters the artwork font can draw: src/try/nameChars.ts is what the font says (scripts/bake_name_chars.py --check), and the page's reading of a
     name (src/try/names.ts, run by Node through Vite's module runner) equals the server's (api/_lib/styles/text.py unsupported, clean, split_names)
     for every code point from the space to U+2FFF, a battery of tricky strings and the limits (24, 200, 20, 24): a letter the page lets through and the
     font cannot draw would be an empty box in a delivered file (I24)
  2. the tile rows of the compose API carry what the retake state needs (the gate policy and the rule it reads, api/_lib/catalogue.py tile_row)
     and are equal to the registry and the engine entry for every style and eye count; the page's reading of them (picker.ts) is in suites/ts
  3. the family name field is offered for a layout only where an engine draws it (nothing does yet)
  4. hygiene: the new page files hold no en or em dash, no written price, no invisible character, no style id, no key
  5. what the page sells is what checkout accepts (review of WP11, M1): for every style and eye count of the registry, under four assignments of stages
     (as the literals stand, everything live, a live style whose non-default looks only preview, a live style whose default look only previews), the
     page's buy card (src/try/picker.ts buyState, run by Node on the tile rows the server sends) is "normal" exactly when checkout would take the order
     (api/_lib/catalogue.py orderable and look_orderable): a price and a button for something checkout refuses is the bug this holds out
  6. the wiring of the page that no DOM test reaches: TryApp reads the buy state with the look on screen and refuses to buy anything but a normal state
No network, no image model, no real eye.
    python test_picker.py        prints PASS/FAIL per check, "N of M passed"; exits 1 on any failure
Run by suites/run_main.sh as the entry v3picker (SNAPEYES_REPO names the checkout)."""
import json
import os
import re
import shutil
import subprocess
import sys

REPO = os.environ.get("SNAPEYES_REPO") or sys.exit("SNAPEYES_REPO is not set: run suites/run_main.sh")
API = os.path.join(REPO, "api")
NODE = shutil.which("node") or "node"
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"   <- {str(detail)[:600]}"), flush=True)


def section(title):
    print(f"\n== {title}", flush=True)


for k in list(os.environ):
    if k.startswith(("VERCEL", "SNAPEYES_", "STRIPE_", "RESEND_", "CRON_", "LEGAL_", "STYLE_", "GEMINI", "AWS_", "NOW_", "LAMBDA_")):
        if k not in ("SNAPEYES_REPO", "SNAPEYES_SP"):
            os.environ.pop(k)
os.environ.update({"SNAPEYES_TICKET_SECRET": "wp11-ticket-secret-for-tests-0123456789abcdef", "PYTHONIOENCODING": "utf-8"})
sys.path.insert(0, API)
from _lib import catalogue as C  # noqa: E402
from _lib import styles_registry as R, styles_engine as X  # noqa: E402
from _lib.styles import text as TX  # noqa: E402

DASH = re.compile("[" + "".join(chr(c) for c in (0x2012, 0x2013, 0x2014, 0x2015)) + "]")


def read(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8", newline="") as f:
        return f.read().replace("\r\n", "\n")


def node(script, payload):
    r = subprocess.run([NODE, os.path.join(REPO, "scripts", "styles_tests", script)], cwd=REPO, input=json.dumps(payload).encode("utf-8"), capture_output=True, timeout=300)
    if r.returncode:
        raise RuntimeError(r.stderr.decode("utf-8", "replace")[:1500])
    return json.loads(r.stdout.decode("utf-8"))


# ---------------------------------------------------------------------------------------------------- 1. the letters
section("1. the letters the artwork font can draw, on the page and on the server")
bake = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "bake_name_chars.py"), "--check"], cwd=REPO, capture_output=True)
check("src/try/nameChars.ts is what the artwork font's cmap says (scripts/bake_name_chars.py --check)", bake.returncode == 0, bake.stdout.decode("utf-8", "replace") + bake.stderr.decode("utf-8", "replace"))
codes = list(range(32, 0x3000)) + [0x1F600, 0x20000, 0x1D400, 0x1F1E6, 0xE000, 0xFFFD, 0x10FFFF]
tricky = ["Anna", "  Anna \t Max ", "A" + chr(0x200b) + "nna", "e" + chr(0x301), chr(0xe9), "ß", "ŉ", "Ǆ", "ǆ", "ǈ", "ﬁ", "İ", "ı", "ῼ", "ᾳ", "Ж", "中文", "Anna;Max\nLina", "\x07bell", "a\u2028b", "x" * 40,
          "O'Neil-Smith & Co.", "14.06.2026", "ąčęėįšųūžőűäöüßĄČĘĖĮŠŲŪŽŐŰÄÖÜ", "😀 emoji", "Ω Δ π µ", chr(0x2014), "‹x›", "“q”", "€ 5"]
got = node("names_probe.mjs", {"codes": codes, "strings": tricky})
page_bad = got["unsupported"]
diff = [(hex(c), TX.unsupported(chr(c)), p) for c, p in zip(codes, page_bad) if sorted(TX.unsupported(chr(c))) != sorted(p)]
check(f"the page and the server agree on {len(codes)} code points (space to U+2FFF and the astral ones): what the font cannot draw", not diff, diff[:6])
check("the page and the server clean a string the same way (NFC, control and zero width characters out, white space one space, trimmed)",
      all(TX.clean(s) == c for s, c in zip(tricky, got["clean"])), [(s, TX.clean(s), c) for s, c in zip(tricky, got["clean"]) if TX.clean(s) != c][:4])
check("the page and the server split the old wire string and a name per line the same way", all(TX.split_names(s) == p for s, p in zip(tricky, got["split"])),
      [(s, TX.split_names(s), p) for s, p in zip(tricky, got["split"]) if TX.split_names(s) != p][:4])
check("the page and the server agree on the letters of whole strings (the Lithuanian, Hungarian and German alphabets draw; Cyrillic, CJK, an emoji do not)",
      all(sorted(TX.unsupported(s)) == sorted(p) for s, p in zip(tricky, got["unsupported_strings"])) and got["unsupported_strings"][tricky.index("ąčęėįšųūžőűäöüßĄČĘĖĮŠŲŪŽŐŰÄÖÜ")] == []
      and got["unsupported_strings"][tricky.index("Ж")] == ["Ж"], got["unsupported_strings"][-8:])
lim = got["limits"]
check("the limits are the server's: 24 a name, 200 in all, 20 a date, 24 a family name", lim == {"NAME_MAX": TX.NAME_MAX, "NAMES_TOTAL_MAX": TX.NAMES_TOTAL_MAX, "DATE_MAX": TX.DATE_MAX, "FAMILY_MAX": TX.FAMILY_MAX}, lim)
check("the page's separator of names on the wire is the server's", "NAMES_SEPARATOR = '" + TX.SEPARATOR + "'" in read("src/try/names.ts"))

# ---------------------------------------------------------------------------------------------------- 2. the tile rows
section("2. the tile rows carry the gate policy and the rule (the retake state names the eye by them)")
rows_ok, why = True, ""
for sid, d in R.STYLES.items():
    for n in range(d["eyes"][0], d["eyes"][1] + 1):
        r = C.tile_row(sid, n)
        if r["gate"] != d["gate"] or r["rule"] != X.ENGINE[sid]["gate_rules"] or r["gate"] not in ("none", "advisory", "hard") or r["rule"] not in ("lid", "fill"):
            rows_ok, why = False, (sid, n, r["gate"], r["rule"])
check(f"tile_row says the style's gate policy and the rule it reads for every style and eye count of the registry ({len(R.STYLES)} ids)", rows_ok, why)
check("every tile of tiles_for and tile_list has them", all("gate" in t and "rule" in t for n in (1, 2, 3, 5) for t in C.tile_list(n)["tiles"]) and all("gate" in t and "rule" in t for t in C.tiles_for(1)))
check("an advisory style reads the lid rule and the Universe styles the fill rule (what the page's advisory warning and the held Universe tile assume)",
      all(X.ENGINE[s]["gate_rules"] == "lid" for s, d in R.STYLES.items() if d["gate"] == "advisory") and all(X.ENGINE[s]["gate_rules"] == "fill" for s in R.STYLES if s.endswith("universe") and s.split(".")[0] in ("solo", "duo", "grp")))
check("the six old styles have policy none: nothing warns and nothing is held back for them", all(C.tile_row(s, 1)["gate"] == "none" for s in C.legacy_ids()))

# ---------------------------------------------------------------------------------------------------- 3. the family name
section("3. the family name field")
drawers = []
for base, _dirs, files in os.walk(os.path.join(API, "_lib", "styles")):
    for f in files:
        if f.endswith(".py") and f != "text.py":
            src = open(os.path.join(base, f), encoding="utf-8").read()
            if re.search(r"family_name|draw_line\(", src):
                drawers.append(os.path.relpath(os.path.join(base, f), REPO))
check("the page offers a family name only for a layout an engine draws it for: while no engine file draws one, FAMILY_NAME_LAYOUTS is empty (an engine that starts to must add its layout to src/try/names.ts)",
      (not drawers and got["family_layouts"] == []) or (drawers and got["family_layouts"] != []), (drawers, got["family_layouts"]))

# ---------------------------------------------------------------------------------------------------- 4. hygiene
section("4. hygiene of the new files")
NEW = ["src/try/picker.ts", "src/try/names.ts", "src/try/nameChars.ts", "src/try/composeApi.ts", "src/try/usePreviews.ts", "src/try/StylePicker.tsx", "src/try/Words.tsx",
       "scripts/bake_name_chars.py", "scripts/styles_tests/names_probe.mjs", "scripts/styles_tests/picker_probe.mjs", "scripts/styles_tests/test_picker.py",
       "suites/ts/picker_state.test.ts", "suites/ts/picker_page.test.ts"]
price = re.compile(r"\d[\d., ]*\s?(€|EUR|A\$|Ft)|(€|A\$)\s?\d")
for rel in NEW:
    try:
        t = read(rel)
    except OSError:
        check(f"{rel} exists", False)
        continue
    invisible = [hex(ord(c)) for c in t if ord(c) in (0xFEFF, 0x200B, 0x200C, 0x200D, 0x2060, 0x00AD, 0x2028, 0x2029) or (ord(c) < 32 and c not in "\n\t")]
    ids = re.findall(r"""['"](solo\.[a-z_]+|duo\.[a-z_]+|grp\.[a-z_]+|pet\.[a-z_]+)['"]""", t) if rel.startswith("src/") else []
    # the tests may name ids freely; the page's code never does (it reads the server's tile list)
    ok = not DASH.search(t) and not invisible and not ids and (rel.startswith(("suites/", "scripts/styles_tests/")) or not price.search(t))
    check(f"{rel}: no en or em dash, no invisible character, no style id, no written price", ok, (DASH.search(t), invisible[:3], ids[:3]))

# ---------------------------------------------------------------------------------------------------- 5. what the page sells is what checkout accepts
section("5. the buy card sells exactly what checkout accepts: stage of the style and stage of the look")
import copy  # noqa: E402

C.set_override_source(None)          # the literals alone: no owner's override (a test's own source, as test_registry.py does)


def scenario(name):
    """Assign stages in the registry in place (and restore them afterwards): the literal ceilings, a live registry with every look live, a live registry
    whose non-default looks only preview, a live registry whose DEFAULT look only previews (the look a request that names none draws)."""
    if name == "literal":
        return
    for sid, d in R.STYLES.items():
        d["stage"] = "live"
        d["stage_by_eyes"] = {k: "live" for k in d["stage_by_eyes"]}
        looks = X.ENGINE[sid]["engine"].get("looks")
        if looks:
            names = list(looks)
            for i, k in enumerate(names):
                if name == "all_live":
                    looks[k] = "live"
                elif name == "extra_looks_preview":
                    looks[k] = "live" if i == 0 else "preview"
                elif name == "default_look_preview":
                    looks[k] = "preview" if i == 0 else "live"


cases, expect, where = [], [], []
for sc in ("literal", "all_live", "extra_looks_preview", "default_look_preview"):
    saved_styles, saved_engine = copy.deepcopy(dict(R.STYLES)), copy.deepcopy(dict(X.ENGINE))
    try:
        scenario(sc)
        for sid, d in R.STYLES.items():
            for n in range(d["eyes"][0], d["eyes"][1] + 1):
                if not C.previewable(sid, n):
                    continue                                   # the server sends no tile for it
                row = C.tile_row(sid, n)
                look_codes = list(row["looks"]) or [None]
                for look in look_codes + ([] if look_codes == [None] else [None]):      # each look by name, and no look named (the default one)
                    opts = {"look": look} if look else {}
                    sells = bool(C.orderable(sid, n, strict=False) and C.look_orderable(sid, n, opts))
                    cases.append({"n": n, "row": row, "look": look})
                    expect.append(sells)
                    where.append((sc, sid, n, look))
    finally:
        R.STYLES.clear(); R.STYLES.update(saved_styles)
        X.ENGINE.clear(); X.ENGINE.update(saved_engine)
kinds = node("picker_probe.mjs", {"cases": cases})["kinds"]
wrong = [(where[i], kinds[i], expect[i]) for i in range(len(cases)) if (kinds[i] == "normal") != expect[i]]
check(f"the page's buy state is normal exactly when checkout accepts the style and its look, for {len(cases)} cases (every style and eye count, every look and the default, four stage assignments)",
      len(kinds) == len(cases) and not wrong, wrong[:4])
sold_somewhere = sum(1 for e in expect if e)
soon_look_cases = [w for w, e, k in zip(where, expect, kinds) if w[0] in ("extra_looks_preview", "default_look_preview") and not e and k == "soon"]
check("the cases include what the review found (a live style with a look that only previews): checkout refuses it and the page says Soon, and there is something sold in the same run",
      sold_somewhere > 0 and len(soon_look_cases) > 0, (sold_somewhere, len(soon_look_cases)))

# ---------------------------------------------------------------------------------------------------- 6. the wiring
section("6. the wiring of the page that no DOM test reaches")
app = read("src/try/TryApp.tsx")
check("TryApp reads the buy state with the look on screen and gives that very state to the card",
      re.search(r"const buying = buyState\(\{[^}]*look: lookNow", app) is not None and "state={buying}" in app)
check("TryApp's buy handler refuses anything but a normal buy state (a button that is not drawn cannot be pressed, and a stale click cannot buy a Soon look)",
      re.search(r"const onBuy = async \(\) => \{\n[^\n]*\n[^\n]*buying\.kind !== 'normal'\) return;", app) is not None)
check("TryApp gives the picker the way to remove an eye and counts a manual-route click with a reason even when no style could be drawn at all",
      "onRemoveEye:" in app and "'no_style'" in app)

print(f"\n{sum(RESULTS)} of {len(RESULTS)} passed", flush=True)
sys.exit(0 if all(RESULTS) else 1)
