# -*- coding: utf-8 -*-
"""The world the OLD guard suites test: the site before the v3 catalogue switch (work package WP18).

The twenty older suites (r2 to r5, fix, admin, pay, advance, refund, preview, review, fixmk, markets, au, payrev, fixer, oldpay, oldadv, oldadmin, exp)
guard the payments, the ordering chain, the refunds, the admin panel, the markets, the price tests and the legal texts, and they use the six legacy
styles as their vehicle: they check out a Studio Black or a Celestial Gold, preview one, mail one. Since the cutover those six ids are RETIRED (a customer
can no longer order or preview them; the orders already made still render) and every style of the v3 engine waits for the owner's tick, so a checkout of
a legacy id is a 409 now and these suites would test a refusal instead of what they were written to guard.

So the runner (suites/run_all.sh, the entries of suites.list that end in `:pre`) starts them with this folder on PYTHONPATH and SNAPEYES_WORLD=pre-cutover,
and this file, which Python imports on its own at start (also in the processes a suite starts: the dev server, the cron call), puts the catalogue back the
way it was before the cutover THE MOMENT api/_lib/catalogue.py is imported: the six legacy ids live, every style of the v3 engine that has an engine at
`lab` (the ceilings of the literal before WP18), the Universe looks at `lab`, no effective default, the legacy style as the default style. Nothing is
patched in the files of api/ and no setting of the deployed code reads SNAPEYES_WORLD: a deployment never has this folder on its path (suites/ is in
`excludeFiles` of every function and in .vercelignore), and without the variable this file does nothing.

What this proves and what it does not. The old suites still prove that the checkout, the chain, the refund, the admin, the prices and the texts work for the
six legacy styles exactly as they did, which is what an order made before the cutover and paid after it relies on (a Stripe page is open for 24 hours). What
the cutover itself does (the retired ids, the ceilings, the effective default, nothing orderable before the owner's tick, the rollback) is proved by the
suite v3cutover, which runs in the real, post-cutover world.
"""
import os
import sys

if os.environ.get("SNAPEYES_WORLD") == "pre-cutover":
    import importlib.abc
    import importlib.machinery

    TARGET = "_lib.catalogue"

    def _pre_cutover(module):
        """The registry as it stood the day before the switch. The literals are the module's own dicts (api/_lib/styles_registry.py and styles_engine.py)."""
        for i, d in module.STYLES.items():
            if d["legacy"] == 1:
                d["stage"] = "live"
                d["stage_by_eyes"] = {}
            elif d["stage"] not in ("planned", "retired"):
                d["stage"] = "lab"
                d["stage_by_eyes"] = {}
        for e in module.ENGINE.values():
            looks = (e.get("engine") or {}).get("looks")
            if looks:
                for k in looks:
                    looks[k] = "lab"
        module.EFFECTIVE_DEFAULT = None
        module.DEFAULT_STYLE = module.legacy_ids()[0]

    class _Finder(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path, target=None):
            if fullname != TARGET:
                return None
            spec = importlib.machinery.PathFinder.find_spec(fullname, path)
            if spec is None or spec.loader is None:
                return None
            loader = spec.loader
            orig = loader.exec_module

            def exec_module(module):
                orig(module)
                _pre_cutover(module)

            loader.exec_module = exec_module
            return spec

    sys.meta_path.insert(0, _Finder())
