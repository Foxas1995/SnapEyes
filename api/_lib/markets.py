# -*- coding: utf-8 -*-
"""The markets snapeyes.com sells in and their prices: THE ONE PLACE to change a price, a currency, a market's Stripe
language or whether a market can be chosen. Nothing else holds a price.

Read by the server (api/_lib/pay.py: what Stripe charges, the checks of every paid session) AND by the site's build
(src/shared/markets.ts imports this very file as text and parses the MARKETS literal below as JSON: the landing page,
/try, the order page, the terms and the admin panel all print these numbers). The build refuses to finish when the
literal is not plain JSON, when a rule below is broken, or when another file holds its own copy of a price
(scripts/check_prices.mjs, run by vite.config.ts on every build; `npm run check:prices` runs it alone).

Rules for the literal (JSON inside Python): double quotes only, no trailing commas, no comments inside it, no
True/False/None (use 1/0), and nothing after it in this file.
  currency       "eur", "aud" or "huf" (Stripe's lower-case codes)
  prices         Stripe's smallest unit: cents for EUR and AUD, and for HUF the forint times 100 (Stripe takes HUF
                 as a two-decimal currency: 6 990 Ft is 699000; the site shows whole forints). AUD and HUF prices are
                 whole units (A$39, 6 990 Ft).
                   one_eye_studio_black  1 eye, Studio Black
                   one_eye_art           1 eye, any of the five art backgrounds
                   two_eyes              2 eyes (any style)
                   each_further_eye      each eye after the second, up to 8
  selectable     1: the site offers it (?m=<key>) and /api/checkout sells in it; 0: priced, but refused at checkout
                 and ignored in links. A market in another currency than the default market's can be 1 only with its
                 own edition of the legal texts, whose terms print its prices (src/shared/legal.ts EDITION_MARKETS =
                 api/_lib/pay.py EDITION_MARKETS; the build checks it): au has the Australian edition, hu the
                 Hungarian one (the EU texts with the forint prices, in English, German, Lithuanian and Hungarian).
                 Setting au or hu to 0 pauses new orders there; the texts stay readable for the orders already made
                 (their links carry m=au / m=hu). Setting hu to 0 only closes the FORINT market: the Hungarian
                 LANGUAGE is not a market, so a Hungarian page on the euro market (?lang=hu, a Hungarian browser)
                 still sells, in euros, under the Hungarian terms (README: go-live gates).
  lang           the market's own page language: the language a page of it opens in when the link and the visitor
                 named none (src/shared/lang.ts detectLang; lt: Lithuanian, hu: Hungarian; "en" changes nothing,
                 it is the site's language of last resort). The language and the market stay independent: ?lang=
                 always wins, and the market never redirects.
  stripe_locale  the language of Stripe's payment page per page language, where it differs from the page's own
                 (Stripe has no en-AU: the Australian market gets en-GB)
  countries      ISO codes of the visitor's country (Vercel's x-vercel-ip-country) for which GET /api/checkout suggests
                 this market; only ever a suggestion, never a redirect
Owner decisions of 2026-09-29 (the numbers are the literal's): eu and lt share one euro price list (lt is its own key
for the statistics and later tests); au in Australian dollars (one total price, no GST charged); hu in forints,
selectable together with the Hungarian edition of the legal texts (Lithuanian and Hungarian wired 2026-09-30)."""
DEFAULT_MARKET = "eu"
MARKETS = {
    "eu": {
        "currency": "eur",
        "prices": {"one_eye_studio_black": 1997, "one_eye_art": 2497, "two_eyes": 3997, "each_further_eye": 1500},
        "selectable": 1,
        "lang": "en",
        "stripe_locale": {},
        "countries": []
    },
    "lt": {
        "currency": "eur",
        "prices": {"one_eye_studio_black": 1997, "one_eye_art": 2497, "two_eyes": 3997, "each_further_eye": 1500},
        "selectable": 1,
        "lang": "lt",
        "stripe_locale": {},
        "countries": ["LT"]
    },
    "au": {
        "currency": "aud",
        "prices": {"one_eye_studio_black": 3900, "one_eye_art": 4900, "two_eyes": 7900, "each_further_eye": 2900},
        "selectable": 1,
        "lang": "en",
        "stripe_locale": {"en": "en-GB"},
        "countries": ["AU"]
    },
    "hu": {
        "currency": "huf",
        "prices": {"one_eye_studio_black": 699000, "one_eye_art": 899000, "two_eyes": 1399000, "each_further_eye": 499000},
        "selectable": 1,
        "lang": "hu",
        "stripe_locale": {},
        "countries": ["HU"]
    }
}
