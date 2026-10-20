# -*- coding: utf-8 -*-
"""The reports of the owner's visitor pages in the admin panel (Saltiniai, Piltuvas, Kodel nepavyksta, Nuotrauku kokybe, Reklamos), worked out from the usage events' day
counts: pure functions of one merged summary (events.merge of the daily counts), no storage, no clock. api/_lib/ops.py reads the days and calls them; the pages (src/admin)
only draw what these return and work out the shares themselves (src/admin/traffic.ts), always with the count behind them.

THE TABLES THEY READ (events.py empty()):
  hits   "<step>|<src>|<med>|<cmp>|<trm>|<cnt>|<lang>|<market>|<dev>|<br>" -> count. The step is a page step of the counter (landing, try, photo, result, soon, buy, order: units
         are page loads and clicks) or a server step with the same codes (an: analyses, anok: usable analyses, en: restorations started, rs: result sets, sv: style previews
         drawn, co: checkout sessions started, pd: payments, help: the manual route; units are requests). An empty code is "-".
  hit_cc "<step>|<country>" -> count;  hit_ms "<dev>|<br>|<bucket of events.TTP_MS>" -> count (the page's own time from a photo to its preview).
  fx     "<metric>|<value>|<src>|<cmp>|<dev>|<br>" -> count: what the server saw of the photos and what went wrong, by campaign, device and browser (FX_METRICS).
  fx_ms  "<what>|<dev>|<br>|<bucket of events.HIST_MS>" -> count: server times of the analysis, the restoration and the style preview.
Keys that do not have the expected shape (the "overflow" key of a table that reached its cap) are counted as `other` and never break a report.
"""
from __future__ import annotations

from . import events as E

HIT_COLS = ("step", "src", "med", "cmp", "trm", "cnt", "lang", "market", "dev", "br")
FX_COLS = ("metric", "value", "src", "cmp", "dev", "br")
FILTERS = ("market", "lang", "dev", "br")
GROUPS = {"src": 2, "cmp": 3, "trm": 4, "cnt": 5}          # how many of src, med, cmp, trm, cnt a row of the sources page is keyed by
PAGE_STEPS = ("landing", "try", "photo", "result", "soon", "buy", "order")
SERVER_STEPS = ("an", "anok", "en", "rs", "sv", "co", "pd", "help")
FUNNEL = ("landing", "try", "photo", "result", "buy", "order")      # the page steps in the order a visit meets them (soon is a branch of buy)
PHOTO_METRICS = ("an_verdict", "an_res", "an_ori", "an_iris", "an_source", "en_cls", "en_pupil", "en_gate", "en_reason", "set_eyes", "sv_style")
WHY_METRICS = ("an_verdict", "an_block", "an_lock", "en_gate", "en_reason", "en_retry", "en_qa", "set_gate", "set_retake", "err_ep", "err_cls", "err_reason", "req")
MS_WHAT = ("analyze", "enhance", "compose")


def _int(v):
    return v if isinstance(v, int) and not isinstance(v, bool) else (int(v) if isinstance(v, float) and v == v and abs(v) < 1e12 else 0)


def filters_from(body):
    """The filters of a request ({market, lang, dev, br}: each one code or absent) and the campaign filters (src, cmp), checked as codes. Raises ValueError for a value that is no code."""
    out = {}
    for k in FILTERS + ("src", "cmp"):
        v = body.get(k) if isinstance(body, dict) else None
        if v in (None, "", "all"):
            continue
        if not isinstance(v, str) or not E._CODE.fullmatch(v):
            raise ValueError(f"{k} is a short code")
        out[k] = v
    return out


def _split(key, cols):
    parts = key.split("|")
    return dict(zip(cols, parts)) if len(parts) == len(cols) else None


def hit_rows(agg, f=None):
    """[(columns dict, n)] of the hits table that pass the filters; and the count of keys that had no shape (overflow)."""
    f = f or {}
    rows, other = [], 0
    for key, n in (agg.get("hits") or {}).items():
        c = _split(key, HIT_COLS)
        if c is None:
            other += _int(n)
            continue
        if any(f.get(k) and c[k] != f[k] for k in FILTERS + ("src", "cmp")):
            continue
        rows.append((c, _int(n)))
    return rows, other


def available(agg):
    """The values each filter can take in these counts, for the page's menus: {market, lang, dev, br, src, cmp}: sorted lists of the codes seen."""
    seen = {k: set() for k in FILTERS + ("src", "cmp")}
    for key in (agg.get("hits") or {}):
        c = _split(key, HIT_COLS)
        if c:
            for k in seen:
                if c[k] != "-":
                    seen[k].add(c[k])
    return {k: sorted(v) for k, v in seen.items()}


def key_of(c, group):
    """The campaign key of a row at a grouping level: (src, med, cmp, trm, cnt) cut to the first n parts, the rest empty; a code the visit did not have ("-" in the tables) is empty too."""
    n = GROUPS[group]
    return tuple((("" if c[k] == "-" else c[k]) if i < n else "") for i, k in enumerate(("src", "med", "cmp", "trm", "cnt")))


def sources_report(agg, f, group):
    """The Saltiniai page: one row per campaign key at the chosen level (source and medium, campaign, ad set, advertisement): the steps counted for it. Orders and revenue are added by the caller
    (attach_orders) from the order records. {rows: [{key: {src, med, cmp, trm, cnt}, steps: {step: n}}], totals: {step: n}, other: n}"""
    if group not in GROUPS:
        raise ValueError("group is one of: " + ", ".join(GROUPS))
    rows, other = hit_rows(agg, f)
    by, totals = {}, {}
    for c, n in rows:
        k = key_of(c, group)
        r = by.setdefault(k, {})
        r[c["step"]] = r.get(c["step"], 0) + n
        totals[c["step"]] = totals.get(c["step"], 0) + n
    out = [{"key": dict(zip(("src", "med", "cmp", "trm", "cnt"), k)), "steps": s} for k, s in by.items()]
    out.sort(key=lambda r: (-(r["steps"].get("landing", 0) + r["steps"].get("try", 0)), -sum(r["steps"].values()), str(r["key"])))
    return {"rows": out, "totals": totals, "other": other}


def order_key(camp, group):
    """The key an order's packed campaign code has at a grouping level (the same tuple as key_of)."""
    parts = (camp or "").split("|") if isinstance(camp, str) else []
    parts = (parts + [""] * 5)[:5]
    n = GROUPS[group]
    return tuple((p if i < n else "") for i, p in enumerate(parts))


def attach_orders(report, orders, group):
    """Add the paid orders and their revenue to a sources report: orders is a list of {camp, amount, currency} (live, paid and not withdrawn: the caller picks them). An order whose code
    matches no row gets one of its own, so revenue is never lost; an order with no code is under the key of no source (all "-"). Revenue is summed per currency, never across them."""
    rows = {tuple(r["key"][k] for k in ("src", "med", "cmp", "trm", "cnt")): r for r in report["rows"]}
    for r in report["rows"]:
        r.setdefault("orders", 0)
        r.setdefault("revenue", {})
    tot_o, tot_r = 0, {}
    for o in orders:
        k = order_key(o.get("camp"), group)
        r = rows.get(k)
        if r is None:
            r = {"key": dict(zip(("src", "med", "cmp", "trm", "cnt"), k)), "steps": {}, "orders": 0, "revenue": {}}
            rows[k] = r
            report["rows"].append(r)
        cur = str(o.get("currency") or "eur").lower()
        amt = _int(o.get("amount"))
        r["orders"] += 1
        r["revenue"][cur] = r["revenue"].get(cur, 0) + amt
        tot_o += 1
        tot_r[cur] = tot_r.get(cur, 0) + amt
    report["orders"], report["revenue"] = tot_o, tot_r
    return report


def percentile(hist, bounds, q):
    """The upper bound of the bucket where the cumulative count first reaches q (0 to 1) of a histogram {bucket index (str): n}; None for an empty one. A bucket above the last bound
    answers None with over true (the page prints it as above the last bound, not as a time)."""
    cells = sorted((int(k), _int(v)) for k, v in hist.items() if str(k).lstrip("-").isdigit())
    total = sum(n for _i, n in cells)
    if total <= 0:
        return {"ms": None, "over": False, "n": 0}
    need, run = q * total, 0
    for i, n in cells:
        run += n
        if run >= need:
            return {"ms": bounds[i] if i < len(bounds) else None, "over": i >= len(bounds), "n": total}
    return {"ms": None, "over": False, "n": total}


def funnel_report(agg, f):
    """The Piltuvas page: the steps of a visit in order (FUNNEL, with soon beside buy), the server steps, each as a total and split by device class and by browser family, and the
    time from a photo to its preview (p50 and p95, split the same way). {steps: {step: n}, by_dev: {dev: {step: n}}, by_br: {br: {step: n}}, ttp: {all, by_dev, by_br}, cc: {step: {cc: n}}}"""
    rows, other = hit_rows(agg, f)
    steps, by_dev, by_br = {}, {}, {}
    for c, n in rows:
        s = c["step"]
        steps[s] = steps.get(s, 0) + n
        d = by_dev.setdefault(c["dev"], {})
        d[s] = d.get(s, 0) + n
        b = by_br.setdefault(c["br"], {})
        b[s] = b.get(s, 0) + n

    def hist(sel):
        h = {}
        for key, n in (agg.get("hit_ms") or {}).items():
            p = key.split("|")
            if len(p) != 3:
                continue
            if f.get("dev") and p[0] != f["dev"] or f.get("br") and p[1] != f["br"] or sel(p):
                continue
            h[p[2]] = h.get(p[2], 0) + _int(n)
        return h

    def pcts(h):
        return {"p50": percentile(h, E.TTP_MS, 0.5), "p95": percentile(h, E.TTP_MS, 0.95)}

    devs = sorted({k.split("|")[0] for k in (agg.get("hit_ms") or {}) if k.count("|") == 2})
    brs = sorted({k.split("|")[1] for k in (agg.get("hit_ms") or {}) if k.count("|") == 2})
    ttp = {"all": pcts(hist(lambda p: False)), "by_dev": {d: pcts(hist(lambda p, d=d: p[0] != d)) for d in devs}, "by_br": {b: pcts(hist(lambda p, b=b: p[1] != b)) for b in brs}}
    cc = {}
    for key, n in (agg.get("hit_cc") or {}).items():
        p = key.split("|")
        if len(p) == 2:
            cc.setdefault(p[0], {})[p[1]] = _int(n)
    return {"steps": steps, "by_dev": by_dev, "by_br": by_br, "ttp": ttp, "cc": cc, "other": other}


def fx_rows(agg, f=None, metrics=None):
    """[(columns dict, n)] of the fx table that pass the filters (device, browser, campaign source and campaign; market and language are not in it) and are of the metrics asked."""
    f = f or {}
    rows = []
    for key, n in (agg.get("fx") or {}).items():
        c = _split(key, FX_COLS)
        if c is None or (metrics and c["metric"] not in metrics):
            continue
        if any(f.get(k) and c[k] != f[k] for k in ("src", "cmp", "dev", "br")):
            continue
        rows.append((c, _int(n)))
    return rows


def fx_report(agg, f, metrics, by=None):
    """{metric: {value: {group: n}}} where group is the whole ("all"), the device class (by dev), the browser family (by br) or the campaign (by cmp: "<src> / <cmp>")."""
    out = {}
    for c, n in fx_rows(agg, f, metrics):
        g = "all" if not by else (c["dev"] if by == "dev" else c["br"] if by == "br" else f"{c['src']} / {c['cmp']}")
        d = out.setdefault(c["metric"], {}).setdefault(c["value"], {})
        d[g] = d.get(g, 0) + n
        if by:
            d["all"] = d.get("all", 0) + n
    return out


def ms_report(agg, f):
    """Server times by step, p50 and p95 in milliseconds, whole and by device class and browser family: {what: {all, by_dev, by_br}} (HIST_MS buckets)."""
    out = {}
    for what in MS_WHAT:
        hs = {"all": {}, "dev": {}, "br": {}}
        for key, n in (agg.get("fx_ms") or {}).items():
            p = key.split("|")
            if len(p) != 4 or p[0] != what:
                continue
            if f.get("dev") and p[1] != f["dev"] or f.get("br") and p[2] != f["br"]:
                continue
            for g, k in (("all", "all"), ("dev", p[1]), ("br", p[2])):
                h = hs[g].setdefault(k, {})
                h[p[3]] = h.get(p[3], 0) + _int(n)
        pc = lambda h: {"p50": percentile(h, E.HIST_MS, 0.5), "p95": percentile(h, E.HIST_MS, 0.95)}      # noqa: E731
        out[what] = {"all": pc(hs["all"].get("all", {})), "by_dev": {k: pc(h) for k, h in hs["dev"].items()}, "by_br": {k: pc(h) for k, h in hs["br"].items()}}
    return out


def why_report(agg, f, by=None):
    """The Kodel nepavyksta page: analysis refusals by reason, the restoration gate by code and sub-code, the retake and second-restoration shares, server times and the error counts per endpoint
    with the requests behind them, by device and browser (by dev or br: each count has the group as a key beside "all")."""
    return {"fx": fx_report(agg, f, WHY_METRICS, by), "times": ms_report(agg, f), "by": by}


def photos_report(agg, f, by="cmp"):
    """The Nuotrauku kokybe page: what the server saw of the photos (resolution class, orientation, iris size, eye class, pupil class, the lid and fill results with the reason codes, how many
    eyes, the style chosen), by campaign (default), device or browser, and the server times. Anonymous classes only: no photo is ever stored."""
    return {"fx": fx_report(agg, f, PHOTO_METRICS, by), "times": ms_report(agg, f), "by": by}
