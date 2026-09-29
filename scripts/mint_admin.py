# -*- coding: utf-8 -*-
"""mint_admin.py - the owner's key for the admin panel (https://snapeyes.com/admin).

    python scripts/mint_admin.py                    # a key valid for 30 days
    python scripts/mint_admin.py --days 90          # 1 to 90 days
    python scripts/mint_admin.py --check KEY        # does this machine's secret accept this key (and until when)?
    python scripts/mint_admin.py --new-secret       # a fresh random SNAPEYES_ADMIN_SECRET (once, when setting up)

Paste the key ONCE into the login field of /admin (never into an address bar, a chat or an email). The page keeps it
in this browser (localStorage) and sends it with every admin call as "Authorization: Bearer <key>".

What it is: "admin-v<SNAPEYES_ADMIN_EPOCH>.<expiry>.<signature>" ("admin-v1" while the variable is unset), signed by
api/_lib/ops.py mint_admin_key() with the ADMIN secret: SNAPEYES_ADMIN_SECRET (at least 32 characters), or, when that
is not set, SNAPEYES_TICKET_SECRET (at least 32 characters), under its own label, so an admin key is never an order
link key or a ticket. The Gemini key is never used: without one of these secrets the admin panel answers 503
"admin_not_configured" and this script mints nothing. The server checks the key in constant time on every admin call
and refuses a key that lives more than 90 days.

Setting up (once):
  1. python scripts/mint_admin.py --new-secret   -> a random value; keep it in your password manager.
  2. Vercel -> Settings -> Environment Variables -> SNAPEYES_ADMIN_SECRET = that value (Production), then redeploy.
  3. On this machine, the same value for this PowerShell window:  $env:SNAPEYES_ADMIN_SECRET = "..."
  4. python scripts/mint_admin.py | clip          -> paste the key into /admin.

Revoking: set SNAPEYES_ADMIN_EPOCH on Vercel to a new number (2, then 3, ...) and redeploy: every key minted before
stops working at once. Then mint a new one here with the same SNAPEYES_ADMIN_EPOCH set on this machine. If the admin
secret itself may have leaked, set a new SNAPEYES_ADMIN_SECRET instead: that revokes every key too, and the
customers' order links (SNAPEYES_TICKET_SECRET) keep working.

Only the key (or, with --new-secret, the new secret) is printed on stdout; nothing about an existing secret is
printed, so it can be piped into the clipboard:
    python scripts/mint_admin.py | clip
Anyone who holds the key can see every order and act on it until it expires: keep it in your password manager only.
This script is not deployed (vercel.json excludeFiles "scripts/**")."""
import os, sys, time, secrets, argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api"))
from _lib import ops  # noqa: E402

DAYS_MAX, DAYS_DEFAULT = 90, 30


def main(argv=None):
    ap = argparse.ArgumentParser(description="Mint the SnapEyes admin panel key.")
    ap.add_argument("--days", type=float, default=DAYS_DEFAULT, help=f"how long the key works (1-{DAYS_MAX} days, default {DAYS_DEFAULT})")
    ap.add_argument("--check", metavar="KEY", help="verify a key against this machine's secret instead of minting one")
    ap.add_argument("--new-secret", action="store_true", help="print a new random SNAPEYES_ADMIN_SECRET and mint nothing")
    a = ap.parse_args(argv)
    if a.new_secret:
        print("a new SNAPEYES_ADMIN_SECRET (set it on Vercel and on this machine, keep it in your password manager):",
              file=sys.stderr)
        print(secrets.token_urlsafe(48))
        return 0
    kind = ops.admin_kind()
    problem = ops.admin_problem()
    if problem:
        print(f"cannot {'check' if a.check is not None else 'mint'}: {problem}. On this machine (PowerShell): "
              f'$env:SNAPEYES_ADMIN_SECRET = "<the same value as on Vercel>"', file=sys.stderr)
        return 2
    if a.check is not None:
        tok = a.check.strip()
        if ops.check_admin_key(tok, kind=kind):
            exp = int(tok.split(".")[1])
            print(f"valid {kind} key, expires {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(exp))}")
            return 0
        print(f"NOT a valid {kind} key here (expired, another epoch, or minted with another secret)")
        return 1
    if not 1 <= a.days <= DAYS_MAX:
        ap.error(f"--days must be between 1 and {DAYS_MAX}")
    ttl = int(a.days * 86400)
    tok = ops.mint_admin_key(ttl, kind)
    exp = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(int(time.time()) + ttl))
    print(f"{kind} key, expires {exp}, signed with the admin secret from {ops.admin_secret_source()}", file=sys.stderr)
    print(tok)
    return 0


if __name__ == "__main__":
    sys.exit(main())
