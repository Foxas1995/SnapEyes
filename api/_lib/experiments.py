# -*- coding: utf-8 -*-
"""The price experiments of snapeyes.com: THE ONE PLACE that says which price tests exist and what every variant costs.
Read by the server (api/_lib/abtest.py: who is assigned what, what Stripe charges, the checks of every paid session, the
admin page "Kainų testai") and by the build (scripts/check_experiments.mjs parses the two literals below as JSON: every
variant ladder is validated before a build finishes). api/_lib/markets.py stays the place of the standard prices; an
experiment only names other full ladders for the visitors it assigns to a variant.

Nothing here is on by itself. An experiment runs only while the owner has switched it on in the admin page (the state is
stored in the private bucket, ops/experiments/<key>.json, and every start and stop is written to the admin audit log);
until then every visitor gets the standard ladder of markets.py, exactly as before this file existed. Switching an
experiment on or off is the only thing that is not a code change.

Rules for the two literals (JSON inside Python, like markets.py): double quotes only, no trailing commas, no comments
inside them, no True/False/None (use 1/0), COSTS first and EXPERIMENTS last, and nothing after EXPERIMENTS.

COSTS   what one artwork costs us, for the loss warning of the admin page and of the build (never used for a price)
  unit_usd_per_eye   the image work per eye in US dollars: a 4K render 0.153 + a 1K preview 0.067 + the photo check
                     0.003 (api/_lib/ops.py PRICES_USD), rounded up
  per_usd            units of a currency for one US dollar (2026-09-30 rates of the market notes: 1 AUD = 0.58 EUR,
                     1 USD = 0.86 EUR, 1000 HUF = 2.5 EUR)
  per_eur            units of a currency for one euro
  fee_pct            Stripe's card fee in percent, currency conversion included (an EEA card in euros 1.5, a card from
                     outside the EEA paid in Australian dollars 3.15 + 2, forints 1.5 + 2)
  fee_fixed_eur      Stripe's fixed fee per payment, in euros

EXPERIMENTS   {key: experiment}; key: lower case letters, digits and "_" (it is written into events, the Stripe metadata
              and paid.json, so it never changes once an experiment has run: a changed test gets a new key)
  title, about   the words of the admin page (Lithuanian), never shown to visitors and holding no price
  markets        the markets it changes prices in (keys of markets.py, all in one currency). A visitor of another market
                 is never part of it
  changes        which of the four prices differ from the control ladder: a sanity check (the build compares it with the
                 ladders), and the words "affected orders" of the statistics
  hit_label      what "affected order" means for this test, in the admin's words
  split          percent of the assigned visitors per variant (whole numbers that add up to 100)
  retired        optional, 1: the test is finished and kept for its history (the admin page still shows its numbers): it is
                 never assigned, never started again, and its control ladder may differ from the standard one, so the
                 owner can adopt a winner by changing markets.py and setting retired to 1 in the same change. Order of
                 events for that: stop the test, wait 24 hours (a Stripe page opened just before stays valid that long;
                 it is paid and recorded at the price its own session carries whatever is edited here), then change
                 prices and definitions
  variants       {name: {label, prices: {market: {one_eye_studio_black, one_eye_art, two_eyes, each_further_eye}}}}
                 EVERY variant carries its FULL ladder for EVERY market of the experiment, in Stripe's smallest unit
                 (cents; AUD whole dollars; HUF forint x 100), never a difference to another ladder: a visitor is only
                 ever charged a ladder written here. The variant "control" is the standard ladder of markets.py (the
                 build checks that they are the same). Never edit a ladder that has run: sessions already open are
                 checked against it. Add a new experiment (a new key) instead.

The two tests the owner approved on 2026-09-30 (the numbers are the literals'):
  extra_eye_eur   the price of each further eye (3 and more eyes) in the euro markets: the standard +15 EUR against
                  +10 EUR. Studios ask about +17 to +30 EUR for every further person, the web sells extra eyes for about
                  +4 to +6 EUR; one and two eyes stay as they are, so only groups see a difference.
  au_ladder_high  the Australian ladder: the standard A$39 / A$49 / A$79 / +A$29 against A$49 / A$59 / A$89 / +A$35.
                  A$49 for one eye is 39-45 % under the studios' A$80-89 files and level with the A$50 files of the cheapest
                  studios; A$89 for two eyes is 44 % under Iris Photography's A$158 pair and 37-44 % under the A$140-160
                  pairs; a further eye at A$35 sits inside the studios' A$28-40; six eyes come to A$229 against the
                  studios' A$270-280; the art background at A$59 is level with the A$50-60 effect files, so the case
                  there is the instant preview and no trip to a studio, not the price. The owner named A$89-99 for two
                  eyes: A$89 is tested first (two arms, so the little Australian traffic is not split three ways); a
                  later test of A$99 against the winner is one more block here."""
COSTS = {
    "unit_usd_per_eye": 0.22,
    "per_usd": {"eur": 0.86, "aud": 1.483, "huf": 344.0},
    "per_eur": {"eur": 1.0, "aud": 1.724, "huf": 400.0},
    "fee_pct": {"eur": 1.5, "aud": 5.15, "huf": 3.5},
    "fee_fixed_eur": 0.25
}
EXPERIMENTS = {
    "extra_eye_eur": {
        "title": "Papildomos akies kaina eurų rinkose (eu ir lt)",
        "about": "Tikrinama, ar pigesnė papildoma akis (trečia ir kiekviena kita akis viename kūrinyje) padidina grupinių užsakymų skaičių tiek, kad atsiperka mažesnė kaina. Vienos ir dviejų akių kainos nesikeičia, todėl skirtumą mato tik tie, kas renkasi tris ar daugiau akių.",
        "markets": ["eu", "lt"],
        "changes": ["each_further_eye"],
        "hit_label": "užsakymai su 3 ir daugiau akių",
        "split": {"control": 50, "extra10": 50},
        "variants": {
            "control": {
                "label": "Dabartinė papildomos akies kaina",
                "prices": {
                    "eu": {"one_eye_studio_black": 1997, "one_eye_art": 2497, "two_eyes": 3997, "each_further_eye": 1500},
                    "lt": {"one_eye_studio_black": 1997, "one_eye_art": 2497, "two_eyes": 3997, "each_further_eye": 1500}
                }
            },
            "extra10": {
                "label": "Pigesnė papildoma akis",
                "prices": {
                    "eu": {"one_eye_studio_black": 1997, "one_eye_art": 2497, "two_eyes": 3997, "each_further_eye": 1000},
                    "lt": {"one_eye_studio_black": 1997, "one_eye_art": 2497, "two_eyes": 3997, "each_further_eye": 1000}
                }
            }
        }
    },
    "au_ladder_high": {
        "title": "Australijos kainynas: dabartinis ar aukštesnis (au)",
        "about": "Tikrinama, ar Australijoje galima kelti visą kainyną, kol jis vis dar gerokai pigesnis už vietines studijas. Keičiasi visos keturios kainos: viena akis su juodu fonu, viena akis su meniniu fonu, dvi akys ir kiekviena papildoma akis.",
        "markets": ["au"],
        "changes": ["one_eye_studio_black", "one_eye_art", "two_eyes", "each_further_eye"],
        "hit_label": "visi užsakymai",
        "split": {"control": 50, "high": 50},
        "variants": {
            "control": {
                "label": "Dabartinis kainynas",
                "prices": {
                    "au": {"one_eye_studio_black": 3900, "one_eye_art": 4900, "two_eyes": 7900, "each_further_eye": 2900}
                }
            },
            "high": {
                "label": "Aukštesnis kainynas",
                "prices": {
                    "au": {"one_eye_studio_black": 4900, "one_eye_art": 5900, "two_eyes": 8900, "each_further_eye": 3500}
                }
            }
        }
    }
}
