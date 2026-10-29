# -*- coding: utf-8 -*-
"""The prints SnapEyes offers beside the digital file: THE ONE PLACE to change a print's retail price, to take a print off the offer, or to
choose the markets that offer prints. Nothing else holds a print price.

Read by the server (api/_lib/prints.py: what Stripe charges for a print, the checks of every paid session) AND by the site's build
(src/shared/prints.ts imports this very file as text and parses the PRINT_OFFER literal below as JSON: /try, the order page, the terms and
the admin panel print these numbers). The build refuses to finish when the literal is not plain JSON, when a rule below is broken, or when a
print sells under the margin floor in any country it ships to (scripts/check_prices.mjs, run on every build).

What a print COSTS us is not here: the partner's price of each SKU and its shipping per country are in api/_lib/print_rates.py, a table
that scripts/print_rates.py writes from the merchOne API (run it again when merchOne changes its prices; the build then checks the margins
again). merchOne adds German VAT (19 %) to the product and the shipping, because the seller is not registered for VAT: a print costs
(merchOne price + shipping) x (100 + vat_pct) / 100.

Rules for the literal (JSON inside Python): double quotes only, no trailing commas, no comments inside it, nothing after it in this file.
  currency      "eur": prints are sold on the euro price lists only
  markets       the markets (api/_lib/markets.py) whose checkout offers prints: only euro markets that read the EU edition of the legal texts
                (eu, lt, hr). Not us (it needs merchOne's North American store), not uk (behind its switch), not au, not hu (forints).
  vat_pct       the VAT merchOne adds to its price and its shipping (the owner is not VAT registered): 19
  fee_pct       the payment provider's fee taken into the margin check, in percent of what the customer pays for the print and its shipping
  margin_floor  the build refuses a print that would earn less than this (cents) in any country after its cost, VAT and the fee
  products      the prints, in the order the checkout shows them:
                  id     a short key (lower case letters and digits): what the order records and the page sends
                  kind   "acrylic", "canvas" or "poster" (the words are in api/_lib/print_names.py)
                  cm     the side of the square, in cm (every SnapEyes artwork is square)
                  sku    the merchOne SKU (api/_lib/print_rates.py must hold it: its cost and print file size)
                  price  the retail price in euro cents, final (no VAT is charged by SnapEyes); the shipping is added per country
                  on     1: offered; 0: kept for the orders made with it, not offered any more
Owner decisions of 2026-10-28: Premium Acrylic (12-colour photo paper behind 3 mm acrylic glass, with the hanger set for plates) 30, 40 and
60 cm; Canvas 40 cm with the black floating frame and the hanger set (mirrored edge; the SKU without the ink pad); Poster 50 cm. A framed
canvas of 60 cm was asked for, but merchOne makes the black floating frame for square canvases up to 40 x 40 cm only (2026-10-28), so it is
not in the list. 2026-10-28, after the review: the poster at 35 EUR (at 29 EUR it earned about 20 EUR, under the owner's target of about
25 EUR; at 35 EUR about 25.8 EUR)."""
PRINT_OFFER = {
    "currency": "eur",
    "markets": ["eu", "lt", "hr"],
    "vat_pct": 19,
    "fee_pct": 3,
    "margin_floor": 1500,
    "products": [
        {"id": "acrylic30", "kind": "acrylic", "cm": 30, "sku": "ACP0300301HP", "price": 5900, "on": 1},
        {"id": "acrylic40", "kind": "acrylic", "cm": 40, "sku": "ACP0400401HP", "price": 7900, "on": 1},
        {"id": "acrylic60", "kind": "acrylic", "cm": 60, "sku": "ACP0600601HP", "price": 12900, "on": 1},
        {"id": "canvas40", "kind": "canvas", "cm": 40, "sku": "CVS0400401LMSBF2HC", "price": 6900, "on": 1},
        {"id": "poster50", "kind": "poster", "cm": 50, "sku": "PSD0500501", "price": 3500, "on": 1}
    ]
}
