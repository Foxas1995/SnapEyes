# -*- coding: utf-8 -*-
"""Refresh api/_lib/print_rates.py, the table of what a print costs SnapEyes, from the merchOne API.

    python scripts/print_rates.py                 # asks merchOne, prints the changes, writes the file
    python scripts/print_rates.py --dry-run       # asks merchOne and prints the changes, writes nothing

For every SKU of api/_lib/print_offer.py: its price (EUR, without VAT), its print area (the design area and the print file with its trim, in
mm and px, and the minimum dpi) from GET /blueprints/{id}/variants and /variants/{vid}/options; and for every member state of the EU the
tracked shipping of one such print (POST /shipment/rates, the first item). A country is in the table only when merchOne ships every SKU of the
offer there from the store's print location (Europe). Nothing is written when any call fails: the old table stays.

The credentials come from MERCHONE_API_USER and MERCHONE_API_KEY, or from --key-file (the owner's file of four lines, "api user:", the user,
"api key:", the key; the values are never printed). 60 calls a minute are allowed: the script waits a little between calls (about two minutes
for the whole table). The checkout reads the table, never the API: run this again when merchOne changes its prices, then npm run build (the
build checks every margin again) and deploy."""
import argparse, json, os, re, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api"))
OUT = os.path.join(ROOT, "api", "_lib", "print_rates.py")
# a postcode of the capital of every member state (merchOne asks for one; the rate depends on the country)
ZIP = {"AT": "1010", "BE": "1000", "BG": "1000", "HR": "10000", "CY": "1010", "CZ": "11000", "DK": "1050", "EE": "10111", "FI": "00100",
       "FR": "75001", "DE": "10115", "GR": "10431", "IE": "D01F5P2", "IT": "00118", "LV": "LV-1050", "LT": "01100", "LU": "1111",
       "MT": "VLT1010", "NL": "1012AB", "PL": "00-001", "PT": "1100-148", "RO": "010011", "SK": "81101", "SI": "1000", "ES": "28001",
       "SE": "11120", "HU": "1011"}
# the merchOne product (blueprint) of each SKU family: Premium Acrylic Print, Canvas, Poster
BLUEPRINT = {"ACP": 80, "CVS": 2, "PSD": 47}
PAUSE = 1.1          # seconds between two calls (60 a minute)

HEADER = '''# -*- coding: utf-8 -*-
"""What a print costs SnapEyes at merchOne: WRITTEN BY scripts/print_rates.py from the merchOne API, do not edit by hand (run the script again).

Read by the server (api/_lib/prints.py: the shipping a checkout adds, the print file's size) and the site's build (src/shared/prints.ts reads
this file as text: the shipping shown per country; scripts/check_prices.mjs checks every margin of api/_lib/print_offer.py against it).
  fetched    the day the table was read
  skus       {sku: {cost, blueprint, variant, design_mm, design_px, file_mm, file_px, trim_mm, dpi}}: the price in euro cents without VAT,
             merchOne's product and size, the design area and the print file (design area plus the trim cut off on every side) in mm and
             px at the minimum resolution, and that minimum (dpi)
  shipping   {country: {sku: cents}}: tracked shipping of one print, without VAT, for the countries merchOne ships every SKU to from Europe
The customer pays the shipping with VAT and rounded up to the next .49 or .99 (prints.py ship_price, src/shared/prints.ts shipPrice)."""
'''


def creds_from_file(path):
    lines = [l.strip() for l in open(path, encoding="utf-8-sig").read().splitlines()]
    out = {}
    for i, line in enumerate(lines):
        label = line.lower().rstrip(":").strip()
        if label in ("api user", "api key"):
            out[label] = next((x for x in lines[i + 1:] if x), "")
    if not out.get("api user") or not out.get("api key"):
        sys.exit(f"{path}: expected the lines 'api user:' and 'api key:', each followed by its value")
    return out["api user"], out["api key"]


def literal(obj):
    return json.dumps(obj, ensure_ascii=False, indent=4, sort_keys=True)


def read_offer():
    from _lib.print_offer import PRINT_OFFER
    return PRINT_OFFER


def fetch(M, offer, say):
    skus = sorted({p["sku"] for p in offer["products"]})
    out = {}
    by_bp = {}
    for sku in skus:
        m = re.fullmatch(r"([A-Z]{3})(\d{3})(\d{3})\d([A-Z0-9]*)", sku)
        if not m or m.group(1) not in BLUEPRINT:
            sys.exit(f"{sku}: not a SKU this script knows how to look up (families {', '.join(BLUEPRINT)})")
        bp, w, h = BLUEPRINT[m.group(1)], int(m.group(2)), int(m.group(3))
        if bp not in by_bp:
            by_bp[bp] = M.variants(bp)
            time.sleep(PAUSE)
        cands = [v for v in by_bp[bp] if str(v.get("name") or "").startswith(f"{w}x{h} cm")]
        hit = None
        for v in cands:
            opts = M.variant_options(bp, v["id"])
            time.sleep(PAUSE)
            for o in opts.get("variants") or []:
                if o.get("sku") == sku:
                    hit = (v, o)
                    break
            if hit:
                break
        if not hit:
            sys.exit(f"{sku}: merchOne lists no such SKU for {w}x{h} cm in blueprint {bp}")
        v, o = hit
        area = next((a for a in o.get("print_areas") or [] if a.get("position") == "front"), None)
        pf, da = v.get("printfile") or {}, v.get("design_area") or {}
        if not area or not pf.get("width_px") or not da.get("width_px"):
            sys.exit(f"{sku}: merchOne gives no print area")
        out[sku] = {"cost": int(round(float(o["price"]) * 100)), "blueprint": bp, "variant": int(v["id"]),
                    "design_mm": [float(da["width"]), float(da["height"])], "design_px": [int(da["width_px"]), int(da["height_px"])],
                    "file_mm": [float(pf["width"]), float(pf["height"])], "file_px": [int(pf["width_px"]), int(pf["height_px"])],
                    "trim_mm": float(v.get("trim") or 0), "dpi": int(area.get("dpi") or 0)}
        say(f"  {sku}: {out[sku]['cost'] / 100:.2f} EUR, print file {out[sku]['file_px'][0]} x {out[sku]['file_px'][1]} px "
            f"(design {out[sku]['design_px'][0]} px, trim {out[sku]['trim_mm']} mm, {out[sku]['dpi']} dpi)")
    ship = {}
    for cc in sorted(ZIP):
        row = {}
        for sku in skus:
            try:
                rates = M.shipping_rates(cc, ZIP[cc], sku)
            except M.Refused as e:
                rates = []
                say(f"  {cc} {sku}: not shipped ({e.message[:80]})")
            time.sleep(PAUSE)
            tracked = [r for r in rates if str(r.get("type") or "").lower() == "tracked" and str(r.get("currency") or "").upper() == "EUR"]
            if tracked:
                row[sku] = int(round(float(tracked[0]["cost"]) * 100))
        if len(row) == len(skus):
            ship[cc] = row
            say(f"  {cc}: " + ", ".join(f"{s} {c / 100:.2f}" for s, c in sorted(row.items())))
        else:
            say(f"  {cc}: left out (merchOne does not ship every print there)")
    if not ship:
        sys.exit("no country with a rate for every print: nothing written")
    return {"fetched": time.strftime("%Y-%m-%d", time.gmtime()), "skus": out, "shipping": ship}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--key-file", default=r"C:\kuriam\.merchone-key" if os.name == "nt" else "")
    a = ap.parse_args()
    if not (os.environ.get("MERCHONE_API_USER") and os.environ.get("MERCHONE_API_KEY")):
        if not a.key_file or not os.path.isfile(a.key_file):
            sys.exit("set MERCHONE_API_USER and MERCHONE_API_KEY, or give --key-file")
        os.environ["MERCHONE_API_USER"], os.environ["MERCHONE_API_KEY"] = creds_from_file(a.key_file)
    os.environ.pop("MERCHONE_API_BASE", None)
    from _lib import merchone as M
    offer = read_offer()
    print("asking merchOne (about two minutes):", flush=True)
    table = fetch(M, offer, lambda s: print(s, flush=True))
    old = None
    try:
        from _lib.print_rates import PRINT_RATES as old
    except Exception:  # noqa: a first run has no table
        old = None
    if old is not None:
        same = {k: v for k, v in table.items() if k != "fetched"} == {k: v for k, v in old.items() if k != "fetched"}
        print("the table is the same as before" if same else "the table CHANGED: run npm run build (the margin check) and deploy", flush=True)
    if a.dry_run:
        print("dry run: nothing written")
        return
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(HEADER + "PRINT_RATES = " + literal(table) + "\n")
    print(f"written: {os.path.relpath(OUT, ROOT)} ({len(table['shipping'])} countries, {len(table['skus'])} prints)")


if __name__ == "__main__":
    main()
