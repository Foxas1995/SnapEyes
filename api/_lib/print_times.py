# -*- coding: utf-8 -*-
"""How long a print takes: THE ONE PLACE for the production time of each kind of print and the delivery time per country. merchOne's published
times, read on 2026-11-24 (change them here when merchOne changes them; nothing else holds these numbers).

Read by the server (api/_lib/prints.py: the delivery estimate Stripe shows, the sentence of the confirmation e-mails) and by the site's build
(src/shared/prints.ts reads this file as text and parses the PRINT_TIMES literal as JSON: the line under the print a customer chooses, the
terms' delivery paragraph in src/legal/docs/prints.ts). The WORDS of these times are in api/_lib/print_names.py (times). The build refuses a
kind of api/_lib/print_offer.py without its production time and a country here that prints do not ship to (scripts/check_prints.mjs).

Rules for the literal: plain JSON (double quotes, no trailing commas, no comments inside it), nothing after it in this file.
  production      {kind: business days}: how long merchOne takes to make a print of that kind (canvas and poster 2, everything else 3)
  transit         {ISO country: [from, to]}: working days on the way from merchOne's plant, for the countries merchOne publishes a time for
                  (Lithuania, Latvia and Estonia 4 to 6, Finland 5 to 8, Germany 3 to 6)
  transit_other   [from, to]: every other country prints ship to. The pages and the e-mails SAY "usually about a week" for them (no number is
                  published); these two numbers are only what Stripe's payment page needs for its delivery estimate, which takes no words"""
PRINT_TIMES = {
    "production": {"acrylic": 3, "metal": 3, "canvas": 2, "poster": 2, "block": 3, "keyring": 3},
    "transit": {"LT": [4, 6], "LV": [4, 6], "EE": [4, 6], "FI": [5, 8], "DE": [3, 6]},
    "transit_other": [3, 9]
}
