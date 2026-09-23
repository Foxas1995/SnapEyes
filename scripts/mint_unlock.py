# -*- coding: utf-8 -*-
"""mint_unlock.py - developer tool: mint an unlock ticket so the owner can test the paid path before Stripe exists.

    python scripts/mint_unlock.py --order test-0001               # a ticket for that one order, valid for 1 hour
    python scripts/mint_unlock.py --order test-0001 --ttl 900     # seconds, 60 to 86400
    python scripts/mint_unlock.py --order test-0001 --check TICKET   # does this machine's secret accept it?
    python scripts/mint_unlock.py --preview                       # a plain "unlock" ticket for /api/compose only

What it does: calls the server's own L.mint_ticket(kind, ttl) from api/_lib/iris.py, so the ticket is signed exactly
as the server signs and checks it (HMAC-SHA256 over "<kind>.<expiry>" with the ticket secret).

Kinds:
  --order ORDER  kind "unlock-<order>" (store.unlock_kind). It opens /api/master_eye (4K renders, about $0.15 each,
                 billed to the Gemini key) and /api/master_compose (the final artwork and its 7-day link) for that
                 order and no other. Order ids are lower-case letters, digits and "-", 4-64 characters. The Stripe
                 webhook will mint the same kind for each paid order.
  --preview      kind "unlock": only removes the watermark from /api/compose previews. It opens neither paid
                 endpoint.

The secret decides where the ticket works. Both sides derive it the same way: SNAPEYES_TICKET_SECRET if it is
set, otherwise the Gemini key (GEMINI_API_KEY, or C:\\kuriam\\.gemini-key on this machine). A ticket minted here
works on a deployment only when that deployment derives the same secret: set the same SNAPEYES_TICKET_SECRET in
both places, or leave it unset in both (then both use the same Gemini key).

Anyone who holds a ticket can use it until it expires: keep the TTL short, never paste a ticket into a public
place, and never ship this script's output to a browser. Only the ticket is printed on stdout (nothing about the
secret), so it can be piped:  TICKET=$(python scripts/mint_unlock.py --order test-0001 --ttl 600)

This script is excluded from the deployed functions (vercel.json excludeFiles "scripts/**")."""
import os, sys, time, argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api"))
from _lib import iris as L  # noqa: E402
from _lib import store  # noqa: E402

TTL_MIN, TTL_MAX, TTL_DEFAULT = 60, 86400, 3600


def main(argv=None):
    ap = argparse.ArgumentParser(description="Mint a SnapEyes unlock ticket for testing the paid path.")
    who = ap.add_mutually_exclusive_group(required=True)
    who.add_argument("--order", help="the order the ticket opens (lower-case letters, digits, '-'; 4-64 characters)")
    who.add_argument("--preview", action="store_true", help='a plain "unlock" ticket: clean /api/compose previews only')
    ap.add_argument("--ttl", type=int, default=TTL_DEFAULT, help=f"seconds the ticket lives ({TTL_MIN}-{TTL_MAX}, default {TTL_DEFAULT})")
    ap.add_argument("--check", metavar="TICKET", help="verify a ticket against this machine's secret instead of minting one")
    a = ap.parse_args(argv)
    if a.preview:
        kind = "unlock"
    else:
        try:
            kind = store.unlock_kind(a.order)
        except L.ClientError:
            ap.error("--order must be lower-case letters, digits and '-', 4-64 characters, starting with a letter or digit")
    if a.check is not None:
        ok = L.check_ticket(a.check.strip(), kind=kind)
        print(f"valid {kind} ticket" if ok else f"NOT a valid {kind} ticket here (expired, another kind or order, or signed with another secret)")
        return 0 if ok else 1
    if not TTL_MIN <= a.ttl <= TTL_MAX:
        ap.error(f"--ttl must be between {TTL_MIN} and {TTL_MAX} seconds")
    try:
        tok = L.mint_ticket(kind, a.ttl)
    except RuntimeError as e:        # no SNAPEYES_TICKET_SECRET and no Gemini key on this machine
        print(f"cannot mint: {e}", file=sys.stderr)
        return 2
    exp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(int(time.time()) + a.ttl))
    src = "SNAPEYES_TICKET_SECRET" if os.environ.get("SNAPEYES_TICKET_SECRET", "").strip() else "the Gemini key"
    print(f"{kind} ticket, expires {exp}, signed with the secret derived from {src}", file=sys.stderr)
    print(tok)
    return 0


if __name__ == "__main__":
    sys.exit(main())
