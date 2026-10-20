# -*- coding: utf-8 -*-
"""The owner's advertising spend ledger (the admin page "Reklamos", 2026-10-20): what he spent on which campaign on which day, typed or pasted from Ads Manager, kept in the private bucket as ONE
object, ops/ads/ledger.json, so that the page can work out the cost of a preview, of a completed preview and of an order from the counter's steps (api/_lib/traffic.py, src/admin/traffic.ts).

A row: id, day (UTC, YYYY-MM-DD), src (a label of the platform, "meta" by default), cmp (the campaign: required), trm (the ad set), cnt (the advertisement), amount (euro cents), vat (true when the
typed amount is what the card was charged, with Meta's 21 percent VAT on top, false when it is the Ads Manager figure, which has none), impr and clicks (optional, from Ads Manager: the plan's CTR
and CPC need them). The codes are the plan's UTM names (counter.is_code); a row without a campaign, with a day in the future or an amount outside 0 to 10 000 euros is refused.
Ads Manager's own figures carry no VAT and the card is charged 21 percent more (the plan, section 0): net() is the Ads Manager figure of a row, card() what the card paid.

No personal data is in it (campaign names, days and amounts), so it is kept until the owner deletes a row; it is the owner's accounting of his own spend. Every change is written under a lock with a
revision number (a second tab's change is a 409 stale_view, as the style switch does) and into the admin audit log by the admin actions (ops.py ads_put, ads_delete).
Module rule: from __future__ import annotations (Vercel's default Python is 3.12)."""
from __future__ import annotations

import math
import re
import secrets
import threading
import time

from . import counter as CN
from . import store

LEDGER = "ops/ads/ledger.json"
ROWS_MAX = 3000
PUT_MAX = 200                    # rows in one request
AMOUNT_MAX = 1_000_000           # euro cents: 10 000 euros in one row
VAT = 1.21                       # Meta adds 21 percent VAT to what Ads Manager shows (MB Portretizuokis has no VAT code there: the ads plan, section 0)
_DAY = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_ID = re.compile(r"^[0-9a-f]{8}$")
_LOCK = threading.Lock()


def empty():
    return {"v": 1, "rev": 0, "rows": []}


def load():
    """The ledger as stored (a new empty one when there is none). A storage error is raised: the page must not show an empty ledger for a ledger it could not read."""
    obj = store.get_json(LEDGER, timeout=8.0)
    if not isinstance(obj, dict) or obj.get("v") != 1 or not isinstance(obj.get("rows"), list):
        return empty()
    obj["rev"] = obj["rev"] if isinstance(obj.get("rev"), int) and not isinstance(obj.get("rev"), bool) else 0
    return obj


def net(row) -> int:
    """The Ads Manager figure of a row in euro cents (the amount without the VAT Meta adds), rounded half up like the page does (Math.round)."""
    a = int(row.get("amount") or 0)
    return int(math.floor(a / VAT + 0.5)) if row.get("vat") else a


def card(row) -> int:
    """What the card was charged for a row in euro cents (the Ads Manager figure with 21 percent VAT)."""
    a = int(row.get("amount") or 0)
    return a if row.get("vat") else int(math.floor(a * VAT + 0.5))


def _int(v, hi, name, allow_none=False):
    if v in (None, "") and allow_none:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v != v or v < 0 or v > hi or int(v) != v:
        raise ValueError(f"{name} is a whole number from 0 to {hi}")
    return int(v)


def clean_row(raw, today=None):
    """One row from what a page sent, or ValueError with the sentence that says what is wrong. The id is kept when it is one of ours, else made."""
    if not isinstance(raw, dict):
        raise ValueError("a row is an object")
    today = today or time.strftime("%Y-%m-%d", time.gmtime())
    day = raw.get("day")
    if not isinstance(day, str) or not _DAY.fullmatch(day) or day > time.strftime("%Y-%m-%d", time.gmtime(time.mktime(time.strptime(today, "%Y-%m-%d")) + 86400 + 43200)):
        raise ValueError("day is a date, YYYY-MM-DD, not in the future")
    try:
        time.strptime(day, "%Y-%m-%d")
    except ValueError:
        raise ValueError("day is a date, YYYY-MM-DD") from None
    out = {"id": raw.get("id") if isinstance(raw.get("id"), str) and _ID.fullmatch(raw.get("id")) else secrets.token_hex(4), "day": day}
    for k in ("cmp", "trm", "cnt"):
        v = raw.get(k)
        v = v.strip().lower() if isinstance(v, str) else v
        if v not in (None, ""):
            if not CN.is_code(v):
                raise ValueError(f"{k} is a short code of letters, digits and _ . - (the name in the advertisement's link)")
            out[k] = v
    if "cmp" not in out:
        raise ValueError("the campaign (cmp) is needed")
    if "trm" not in out and "cnt" in out:
        raise ValueError("an advertisement (cnt) needs its ad set (trm)")
    src = raw.get("src")
    src = src.strip().lower() if isinstance(src, str) and src.strip() else "meta"
    if not CN.is_code(src):
        raise ValueError("src is a short code, for example meta")
    out["src"] = src
    out["amount"] = _int(raw.get("amount"), AMOUNT_MAX, "amount (euro cents)")
    out["vat"] = raw.get("vat") is True
    for k in ("impr", "clicks"):
        v = _int(raw.get(k), 2_000_000_000, k, allow_none=True)
        if v is not None:
            out[k] = v
    return out


def save(obj):
    obj = dict(obj, v=1, t=int(time.time()))
    store.put(LEDGER, store.json_bytes(obj), "application/json", upsert=True, timeout=10.0)
    return obj


def put(rows, rev=None, today=None):
    """Add rows (or replace the rows with the same id) under the lock: returns {rev, rows: the stored rows of this request, total}. rev, when the page sends it, must be the ledger's
    (the page saw the ledger as it is): ValueError("stale") otherwise. At most PUT_MAX rows a request and ROWS_MAX in all."""
    if not isinstance(rows, list) or not rows or len(rows) > PUT_MAX:
        raise ValueError(f"rows is a list of 1 to {PUT_MAX} rows")
    clean = [clean_row(r, today) for r in rows]
    with _LOCK:
        obj = load()
        if rev is not None and rev != obj["rev"]:
            raise ValueError("stale")
        have = {r.get("id"): i for i, r in enumerate(obj["rows"]) if isinstance(r, dict)}
        for r in clean:
            if r["id"] in have:
                obj["rows"][have[r["id"]]] = r
            else:
                obj["rows"].append(r)
        if len(obj["rows"]) > ROWS_MAX:
            raise ValueError(f"the ledger holds at most {ROWS_MAX} rows")
        obj["rows"].sort(key=lambda r: (r.get("day", ""), r.get("cmp", ""), r.get("id", "")))
        obj["rev"] += 1
        saved = save(obj)
    return {"rev": saved["rev"], "rows": clean, "total": len(saved["rows"])}


def delete(ids, rev=None):
    """Delete rows by id under the lock: returns {rev, deleted, total}."""
    if not isinstance(ids, list) or not ids or len(ids) > PUT_MAX or any(not (isinstance(i, str) and _ID.fullmatch(i)) for i in ids):
        raise ValueError(f"ids is a list of 1 to {PUT_MAX} row ids")
    with _LOCK:
        obj = load()
        if rev is not None and rev != obj["rev"]:
            raise ValueError("stale")
        want = set(ids)
        keep = [r for r in obj["rows"] if not (isinstance(r, dict) and r.get("id") in want)]
        gone = len(obj["rows"]) - len(keep)
        obj["rows"], obj["rev"] = keep, obj["rev"] + 1
        saved = save(obj)
    return {"rev": saved["rev"], "deleted": gone, "total": len(keep)}


def parse_lines(text, today=None):
    """Rows from pasted lines: "day; campaign; ad set; advertisement; amount; impressions; clicks" (a semicolon, a tab or a comma between the parts; the ad set, the advertisement,
    the impressions and the clicks may be empty; the amount is in euros with a comma or a point; a first line that starts with a letter is a header and is skipped). Returns (rows, errors)
    where errors is a list of "line N: sentence". The rows are not stored."""
    rows, errors = [], []
    for n, line in enumerate(str(text or "").splitlines(), 1):
        if not line.strip():
            continue
        parts = [p.strip() for p in re.split(r"[;\t]|,(?=\s|$)|(?<=[a-z0-9]),(?=[a-z0-9])", line)] if (";" not in line and "\t" not in line) else [p.strip() for p in re.split(r"[;\t]", line)]
        if n == 1 and parts and parts[0] and not parts[0][0].isdigit():
            continue
        parts += [""] * (7 - len(parts))
        try:
            amount = parts[4].replace(" ", "").replace(",", ".")
            cents = int(round(float(amount) * 100)) if amount else None
            if cents is None:
                raise ValueError("amount in euros is needed")
            rows.append(clean_row({"day": parts[0], "cmp": parts[1], "trm": parts[2], "cnt": parts[3], "amount": cents, "impr": int(parts[5]) if parts[5] else None,
                                   "clicks": int(parts[6]) if parts[6] else None}, today))
        except ValueError as e:
            errors.append(f"line {n}: {e}")
    return rows, errors
