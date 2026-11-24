# -*- coding: utf-8 -*-
"""What a print costs SnapEyes at merchOne: WRITTEN BY scripts/print_rates.py from the merchOne API, do not edit by hand (run the script again).

Read by the server (api/_lib/prints.py: the shipping a checkout adds, the print file's size) and the site's build (src/shared/prints.ts reads
this file as text: the shipping shown per country; scripts/check_prices.mjs checks every margin of api/_lib/print_offer.py against it).
  fetched    the day the table was read
  skus       {sku: {cost, blueprint, variant, design_mm, design_px, file_mm, file_px, trim_mm, dpi}}: the price in euro cents without VAT,
             merchOne's product and size, the design area and the print file (design area plus the trim cut off on every side) in mm and
             px at the minimum resolution, and that minimum (dpi)
  shipping   {country: {sku: cents}}: tracked shipping of one print, without VAT, for the countries merchOne ships every SKU to from Europe
The customer pays the shipping with VAT and rounded up to the next .49 or .99 (prints.py ship_price, src/shared/prints.ts shipPrice)."""
PRINT_RATES = {
    "fetched": "2026-11-24",
    "shipping": {
        "AT": {
            "ABS0100101": 550,
            "ABS0200201": 550,
            "ACP0300301HP": 550,
            "ACP0400401HP": 550,
            "ACP0600601HP": 550,
            "ALP0300301HP": 550,
            "ALP0400401HP": 550,
            "ALP0600601HP": 699,
            "CVS0400401LMF2HC": 550,
            "CVS0600601LMF2HC": 699,
            "KRR0050041": 490,
            "PSD0500501": 550
        },
        "BE": {
            "ABS0100101": 550,
            "ABS0200201": 550,
            "ACP0300301HP": 550,
            "ACP0400401HP": 550,
            "ACP0600601HP": 550,
            "ALP0300301HP": 550,
            "ALP0400401HP": 550,
            "ALP0600601HP": 699,
            "CVS0400401LMF2HC": 550,
            "CVS0600601LMF2HC": 699,
            "KRR0050041": 690,
            "PSD0500501": 550
        },
        "BG": {
            "ABS0100101": 699,
            "ABS0200201": 699,
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "ALP0300301HP": 699,
            "ALP0400401HP": 699,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 699,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 690,
            "PSD0500501": 699
        },
        "CY": {
            "ABS0100101": 799,
            "ABS0200201": 799,
            "ACP0300301HP": 799,
            "ACP0400401HP": 799,
            "ACP0600601HP": 799,
            "ALP0300301HP": 799,
            "ALP0400401HP": 799,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 799,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 799,
            "PSD0500501": 799
        },
        "CZ": {
            "ABS0100101": 550,
            "ABS0200201": 550,
            "ACP0300301HP": 550,
            "ACP0400401HP": 550,
            "ACP0600601HP": 550,
            "ALP0300301HP": 550,
            "ALP0400401HP": 550,
            "ALP0600601HP": 699,
            "CVS0400401LMF2HC": 550,
            "CVS0600601LMF2HC": 699,
            "KRR0050041": 550,
            "PSD0500501": 550
        },
        "DE": {
            "ABS0100101": 399,
            "ABS0200201": 399,
            "ACP0300301HP": 399,
            "ACP0400401HP": 399,
            "ACP0600601HP": 550,
            "ALP0300301HP": 399,
            "ALP0400401HP": 399,
            "ALP0600601HP": 550,
            "CVS0400401LMF2HC": 399,
            "CVS0600601LMF2HC": 550,
            "KRR0050041": 390,
            "PSD0500501": 399
        },
        "DK": {
            "ABS0100101": 550,
            "ABS0200201": 550,
            "ACP0300301HP": 550,
            "ACP0400401HP": 550,
            "ACP0600601HP": 550,
            "ALP0300301HP": 550,
            "ALP0400401HP": 550,
            "ALP0600601HP": 699,
            "CVS0400401LMF2HC": 550,
            "CVS0600601LMF2HC": 699,
            "KRR0050041": 690,
            "PSD0500501": 550
        },
        "EE": {
            "ABS0100101": 699,
            "ABS0200201": 699,
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "ALP0300301HP": 699,
            "ALP0400401HP": 699,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 699,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 699,
            "PSD0500501": 699
        },
        "ES": {
            "ABS0100101": 699,
            "ABS0200201": 699,
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "ALP0300301HP": 699,
            "ALP0400401HP": 699,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 699,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 690,
            "PSD0500501": 699
        },
        "FI": {
            "ABS0100101": 699,
            "ABS0200201": 699,
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "ALP0300301HP": 699,
            "ALP0400401HP": 699,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 699,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 699,
            "PSD0500501": 699
        },
        "FR": {
            "ABS0100101": 699,
            "ABS0200201": 699,
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "ALP0300301HP": 699,
            "ALP0400401HP": 699,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 699,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 490,
            "PSD0500501": 699
        },
        "GR": {
            "ABS0100101": 699,
            "ABS0200201": 699,
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "ALP0300301HP": 699,
            "ALP0400401HP": 699,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 699,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 699,
            "PSD0500501": 699
        },
        "HR": {
            "ABS0100101": 699,
            "ABS0200201": 699,
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "ALP0300301HP": 699,
            "ALP0400401HP": 699,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 699,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 699,
            "PSD0500501": 699
        },
        "HU": {
            "ABS0100101": 699,
            "ABS0200201": 699,
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "ALP0300301HP": 699,
            "ALP0400401HP": 699,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 699,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 699,
            "PSD0500501": 699
        },
        "IE": {
            "ABS0100101": 699,
            "ABS0200201": 699,
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "ALP0300301HP": 699,
            "ALP0400401HP": 699,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 699,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 699,
            "PSD0500501": 699
        },
        "IT": {
            "ABS0100101": 699,
            "ABS0200201": 699,
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "ALP0300301HP": 699,
            "ALP0400401HP": 699,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 699,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 690,
            "PSD0500501": 699
        },
        "LT": {
            "ABS0100101": 699,
            "ABS0200201": 699,
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "ALP0300301HP": 699,
            "ALP0400401HP": 699,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 699,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 699,
            "PSD0500501": 699
        },
        "LU": {
            "ABS0100101": 550,
            "ABS0200201": 550,
            "ACP0300301HP": 550,
            "ACP0400401HP": 550,
            "ACP0600601HP": 550,
            "ALP0300301HP": 550,
            "ALP0400401HP": 550,
            "ALP0600601HP": 699,
            "CVS0400401LMF2HC": 550,
            "CVS0600601LMF2HC": 699,
            "KRR0050041": 550,
            "PSD0500501": 550
        },
        "LV": {
            "ABS0100101": 699,
            "ABS0200201": 699,
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "ALP0300301HP": 699,
            "ALP0400401HP": 699,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 699,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 699,
            "PSD0500501": 699
        },
        "MT": {
            "ABS0100101": 799,
            "ABS0200201": 799,
            "ACP0300301HP": 799,
            "ACP0400401HP": 799,
            "ACP0600601HP": 799,
            "ALP0300301HP": 799,
            "ALP0400401HP": 799,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 799,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 799,
            "PSD0500501": 799
        },
        "NL": {
            "ABS0100101": 550,
            "ABS0200201": 550,
            "ACP0300301HP": 550,
            "ACP0400401HP": 550,
            "ACP0600601HP": 550,
            "ALP0300301HP": 550,
            "ALP0400401HP": 550,
            "ALP0600601HP": 699,
            "CVS0400401LMF2HC": 550,
            "CVS0600601LMF2HC": 699,
            "KRR0050041": 550,
            "PSD0500501": 550
        },
        "PL": {
            "ABS0100101": 550,
            "ABS0200201": 550,
            "ACP0300301HP": 550,
            "ACP0400401HP": 550,
            "ACP0600601HP": 550,
            "ALP0300301HP": 550,
            "ALP0400401HP": 550,
            "ALP0600601HP": 699,
            "CVS0400401LMF2HC": 550,
            "CVS0600601LMF2HC": 699,
            "KRR0050041": 550,
            "PSD0500501": 550
        },
        "PT": {
            "ABS0100101": 699,
            "ABS0200201": 699,
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "ALP0300301HP": 699,
            "ALP0400401HP": 699,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 699,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 699,
            "PSD0500501": 699
        },
        "RO": {
            "ABS0100101": 699,
            "ABS0200201": 699,
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "ALP0300301HP": 699,
            "ALP0400401HP": 699,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 699,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 699,
            "PSD0500501": 699
        },
        "SE": {
            "ABS0100101": 799,
            "ABS0200201": 799,
            "ACP0300301HP": 799,
            "ACP0400401HP": 799,
            "ACP0600601HP": 799,
            "ALP0300301HP": 799,
            "ALP0400401HP": 799,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 799,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 690,
            "PSD0500501": 799
        },
        "SI": {
            "ABS0100101": 699,
            "ABS0200201": 699,
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "ALP0300301HP": 699,
            "ALP0400401HP": 699,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 699,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 699,
            "PSD0500501": 699
        },
        "SK": {
            "ABS0100101": 699,
            "ABS0200201": 699,
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "ALP0300301HP": 699,
            "ALP0400401HP": 699,
            "ALP0600601HP": 1099,
            "CVS0400401LMF2HC": 699,
            "CVS0600601LMF2HC": 1099,
            "KRR0050041": 699,
            "PSD0500501": 699
        }
    },
    "skus": {
        "ABS0100101": {
            "blueprint": 18,
            "cost": 1265,
            "design_mm": [
                100.0,
                100.0
            ],
            "design_px": [
                284,
                284
            ],
            "dpi": 72,
            "file_mm": [
                104.0,
                104.0
            ],
            "file_px": [
                295,
                295
            ],
            "trim_mm": 2.0,
            "variant": 194
        },
        "ABS0200201": {
            "blueprint": 18,
            "cost": 3173,
            "design_mm": [
                200.0,
                200.0
            ],
            "design_px": [
                567,
                567
            ],
            "dpi": 72,
            "file_mm": [
                204.0,
                204.0
            ],
            "file_px": [
                579,
                579
            ],
            "trim_mm": 2.0,
            "variant": 197
        },
        "ACP0300301HP": {
            "blueprint": 80,
            "cost": 1916,
            "design_mm": [
                300.0,
                300.0
            ],
            "design_px": [
                1418,
                1418
            ],
            "dpi": 120,
            "file_mm": [
                305.0,
                305.0
            ],
            "file_px": [
                1441,
                1441
            ],
            "trim_mm": 2.5,
            "variant": 754
        },
        "ACP0400401HP": {
            "blueprint": 80,
            "cost": 2743,
            "design_mm": [
                400.0,
                400.0
            ],
            "design_px": [
                1890,
                1890
            ],
            "dpi": 120,
            "file_mm": [
                405.0,
                405.0
            ],
            "file_px": [
                1914,
                1914
            ],
            "trim_mm": 2.5,
            "variant": 756
        },
        "ACP0600601HP": {
            "blueprint": 80,
            "cost": 5236,
            "design_mm": [
                600.0,
                600.0
            ],
            "design_px": [
                2835,
                2835
            ],
            "dpi": 120,
            "file_mm": [
                605.0,
                605.0
            ],
            "file_px": [
                2859,
                2859
            ],
            "trim_mm": 2.5,
            "variant": 760
        },
        "ALP0300301HP": {
            "blueprint": 46,
            "cost": 1465,
            "design_mm": [
                300.0,
                300.0
            ],
            "design_px": [
                1418,
                1418
            ],
            "dpi": 120,
            "file_mm": [
                305.0,
                305.0
            ],
            "file_px": [
                1441,
                1441
            ],
            "trim_mm": 2.5,
            "variant": 773
        },
        "ALP0400401HP": {
            "blueprint": 46,
            "cost": 2428,
            "design_mm": [
                400.0,
                400.0
            ],
            "design_px": [
                1890,
                1890
            ],
            "dpi": 120,
            "file_mm": [
                405.0,
                405.0
            ],
            "file_px": [
                1914,
                1914
            ],
            "trim_mm": 2.5,
            "variant": 775
        },
        "ALP0600601HP": {
            "blueprint": 46,
            "cost": 4843,
            "design_mm": [
                600.0,
                600.0
            ],
            "design_px": [
                2835,
                2835
            ],
            "dpi": 120,
            "file_mm": [
                605.0,
                605.0
            ],
            "file_px": [
                2859,
                2859
            ],
            "trim_mm": 2.5,
            "variant": 779
        },
        "CVS0400401LMF2HC": {
            "blueprint": 2,
            "cost": 1730,
            "design_mm": [
                400.0,
                400.0
            ],
            "design_px": [
                567,
                567
            ],
            "dpi": 36,
            "file_mm": [
                400.0,
                400.0
            ],
            "file_px": [
                567,
                567
            ],
            "trim_mm": 0.0,
            "variant": 13
        },
        "CVS0600601LMF2HC": {
            "blueprint": 2,
            "cost": 2638,
            "design_mm": [
                600.0,
                600.0
            ],
            "design_px": [
                851,
                851
            ],
            "dpi": 36,
            "file_mm": [
                600.0,
                600.0
            ],
            "file_px": [
                851,
                851
            ],
            "trim_mm": 0.0,
            "variant": 16
        },
        "KRR0050041": {
            "blueprint": 210,
            "cost": 299,
            "design_mm": [
                56.0,
                76.0
            ],
            "design_px": [
                265,
                360
            ],
            "dpi": 120,
            "file_mm": [
                56.0,
                76.0
            ],
            "file_px": [
                265,
                360
            ],
            "trim_mm": 0.0,
            "variant": 1269
        },
        "PSD0500501": {
            "blueprint": 47,
            "cost": 676,
            "design_mm": [
                500.0,
                500.0
            ],
            "design_px": [
                1418,
                1418
            ],
            "dpi": 72,
            "file_mm": [
                506.0,
                506.0
            ],
            "file_px": [
                1435,
                1435
            ],
            "trim_mm": 3.0,
            "variant": 442
        }
    }
}
