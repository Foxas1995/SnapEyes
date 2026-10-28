# -*- coding: utf-8 -*-
"""One real print order against merchOne's API, end to end through the production code (api/_lib/prints.py step), as a TEST order:

    python scripts/print_sandbox_test.py [--product canvas40] [--key-file C:\\kuriam\\.merchone-key] [--keep]

What it does, on a throw-away local store (nothing of the site's storage, Stripe or e-mail is touched):
  1. a paid order of ours with a print (the delivery address: "SnapEyes Test", Vilnius, LT-01100, the seller's own city) and a delivered 4096 px
     test master (drawn here: a synthetic iris on a dark ground, no real eye);
  2. prints.step: the print file is made from the master at the SKU's print file size and stored beside the order, and the merchOne order is
     created with external_id = our order id and is_test true (MERCHONE_LIVE is never set here);
  3. the order is read back from merchOne (it exists, it is a test order, its external id and SKU are ours), a second step makes no second order,
     and merchOne itself refuses a second order with the same external id and names the first one (the idempotency guard prints.step relies on);
  4. the order is cancelled through prints.cancel (merchOne's DELETE) and read back as cancelled (unless --keep).
merchOne must be able to download the print file from a public URL. The local store has none, so the link handed to merchOne is --file-url
(default: a public picture of the live site, the sample eye of /try); the print file the code made is checked here for its size instead.
The credentials come from MERCHONE_API_USER / MERCHONE_API_KEY or --key-file; they are never printed. Exit code 1 on any failed step."""
import argparse, atexit, io, json, os, secrets, shutil, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
DEFAULT_URL = "https://snapeyes.com/assets/sample_eye_blue_restored.jpg"


def master_jpeg(side=4096):
    """A synthetic iris artwork: a dark ground, a ring of radial fibres in blue and gold, a black pupil. No real eye."""
    import numpy as np
    from PIL import Image
    y, x = np.mgrid[0:side, 0:side].astype(np.float32)
    c = side / 2
    r = np.hypot(x - c, y - c) / (side * 0.36)
    a = np.arctan2(y - c, x - c)
    fib = 0.5 + 0.5 * np.sin(a * 90) * np.sin(a * 37 + r * 9)
    ring = np.clip(1.15 - r, 0, 1) * (r > 0.28)
    img = np.zeros((side, side, 3), np.float32)
    img[..., 0] = 10 + ring * (60 + 120 * fib * (r > 0.55))
    img[..., 1] = 12 + ring * (90 + 80 * fib)
    img[..., 2] = 18 + ring * (170 + 60 * fib * (r < 0.6))
    img[r <= 0.28] = (4, 4, 6)
    b = io.BytesIO()
    Image.fromarray(np.clip(img, 0, 255).astype("uint8")).save(b, "JPEG", quality=92)
    return b.getvalue()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--product", default="canvas40")
    ap.add_argument("--key-file", default=r"C:\kuriam\.merchone-key" if os.name == "nt" else "")
    ap.add_argument("--file-url", default=DEFAULT_URL)
    ap.add_argument("--keep", action="store_true", help="do not cancel the test order")
    a = ap.parse_args()
    for k in ("MERCHONE_LIVE", "MERCHONE_API_BASE", "VERCEL", "VERCEL_ENV", "SNAPEYES_SUPABASE_URL", "SNAPEYES_SUPABASE_SERVICE_KEY", "STRIPE_SECRET_KEY",
              "RESEND_API_KEY"):
        os.environ.pop(k, None)
    if not (os.environ.get("MERCHONE_API_USER") and os.environ.get("MERCHONE_API_KEY")):
        from print_rates import creds_from_file
        if not a.key_file or not os.path.isfile(a.key_file):
            sys.exit("set MERCHONE_API_USER and MERCHONE_API_KEY, or give --key-file")
        os.environ["MERCHONE_API_USER"], os.environ["MERCHONE_API_KEY"] = creds_from_file(a.key_file)
    tmp = tempfile.mkdtemp(prefix="snapeyes_print_sandbox_")
    atexit.register(shutil.rmtree, tmp, ignore_errors=True)
    os.environ.update(STORE_LOCAL_DIR=os.path.join(tmp, "store"), SNAPEYES_TICKET_SECRET=secrets.token_hex(24), PYTHONIOENCODING="utf-8")
    os.makedirs(os.environ["STORE_LOCAL_DIR"])
    from PIL import Image
    from _lib import store, pay
    from _lib import prints as PR
    from _lib import merchone as M

    ok = []

    def step(name, cond, detail=""):
        ok.append(bool(cond))
        print(("OK   " if cond else "FAIL ") + name + ("" if cond else f"   <- {str(detail)[:600]}"), flush=True)
        return cond

    p = PR.product(a.product)
    if not p:
        sys.exit(f"no product {a.product} in api/_lib/print_offer.py")
    order = time.strftime("%y%m%d", time.gmtime()) + "-sandbox-" + secrets.token_hex(4)
    now = int(time.time())
    ship = PR.shipping("LT", p["id"])
    pp = {"product": p["id"], "sku": p["sku"], "kind": p["kind"], "cm": p["cm"], "country": "LT", "price": p["price"], "ship": ship,
          "name": "SnapEyes Test", "address": {"line1": "Gedimino pr. 1", "line2": "", "city": "Vilnius", "postal_code": "01100", "state": "", "country": "LT"},
          "consent": {"version": pay.CONSENT_VERSION, "at": pay.iso(now), "lang": "en", "text": PR.PRINT_CONSENT_TEXT["en"], "text_sha256": "-"}}
    paid = {"paid": True, "order": order, "session_id": "cs_test_sandbox", "amount_total": pay.price_list("eu")["one_eye_art"] + p["price"] + ship, "currency": "eur", "market": "eu",
            "livemode": False, "email": None, "paid_at": now, "paid_iso": pay.iso(now), "spec": {"eyes": 1, "style": "sandbox", "lang": "en", "market": "eu"},
            "print": pp}
    rec = {"v": 1, "order": order, "created_at": now, "lang": "en"}
    store.put(f"orders/{order}/order.json", store.json_bytes(rec), "application/json")
    store.put(f"orders/{order}/paid.json", store.json_bytes(paid), "application/json")
    raw = master_jpeg()
    key = f"orders/{order}/artwork_sandbox.jpg"
    store.put(key, raw, "image/jpeg")
    store.put(f"orders/{order}/delivery.json", store.json_bytes({"key": key, "width": 4096, "height": 4096, "bytes": len(raw), "needs_review": False,
                                                                 "created_at": now}), "application/json")
    PR.on_paid(order, paid)
    print(f"order {order}: {PR.product_name(p['id'], 'en')} to Vilnius, LT (shipping {ship / 100:.2f} EUR), a TEST order")

    real_sign = store.signed_url
    store.signed_url = lambda path, seconds: a.file_url if path.startswith(f"orders/{order}/print_") else real_sign(path, seconds)
    r = PR.step(order, rec, paid, by="sandbox")
    cur = PR.record(order) or {}
    if not step(f"prints.step created the merchOne order ({r})", r == "created" and cur.get("merchone_id"), cur):
        return 1
    oid = cur["merchone_id"]
    f = cur.get("file") or {}
    want = PR.file_geometry(p["sku"], 4096)
    with Image.open(os.path.join(os.environ["STORE_LOCAL_DIR"], *f["path"].split("/"))) as im:
        size = im.size
    step(f"the print file made from the 4096 px master is the SKU's print file: {size[0]} x {size[1]} px at {f.get('dpi')} dpi "
         f"(design {want[1]} px, merchOne's minimum {PR.sku_rec(p['sku'])['design_px'][0]} px), {f.get('bytes', 0) / 1e6:.1f} MB",
         size == (want[0], want[0]) and want[1] >= PR.sku_rec(p["sku"])["design_px"][0], (size, want))
    o = M.get_order(oid)
    step(f"merchOne has {oid}: a test order, external id {o.get('external_id') if o else None}, status {o.get('status') if o else None}",
         bool(o) and o.get("is_test") is True and o.get("external_id") == order and str(oid).endswith("T"), o)
    items = (o or {}).get("items") or []
    step(f"its item is our SKU ({items[0].get('name') if items else None}, {(items[0].get('price_details') or {}).get('formatted') if items else None})",
         bool(items) and (items[0].get("external_id") == f"{order}-1"), items[:1])
    step("a second step makes no second order (done)", PR.step(order, rec, paid) == "done")
    try:
        M.create_order(PR.payload(order, paid, pp, a.file_url, 1, True))
        dup = None
    except M.Refused as e:
        dup = M.existing_id(e)
    step(f"merchOne refuses a second order with the same external id and names the first ({dup})", dup == oid, dup)
    if a.keep:
        print(f"kept: {oid} stays in the sandbox store (a test order: never produced, never charged)")
    else:
        st, t0 = None, time.time()
        while st is None and time.time() - t0 < 120:
            try:
                st = PR.cancel(order)
            except store.Answer as e:
                # merchOne cancels during its hold time, not in the first seconds while it reads the order in
                print(f"  merchOne: not cancellable yet ({e.body.get('reason')}), asking again in 10 s", flush=True)
                time.sleep(10)
        o2 = M.get_order(oid)
        step(f"cancelled through prints.cancel: our state {st}, merchOne's {o2.get('status') if o2 else None}",
             st == "canceled" and o2 and str(o2.get("status")).upper() in ("CANCELLED", "CANCELED"), o2)
    print(f"\n{sum(ok)} of {len(ok)} steps ok")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
