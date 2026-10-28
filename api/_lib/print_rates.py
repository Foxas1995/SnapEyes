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
    "fetched": "2026-10-28",
    "shipping": {
        "AT": {
            "ACP0300301HP": 550,
            "ACP0400401HP": 550,
            "ACP0600601HP": 550,
            "CVS0400401LMSBF2HC": 550,
            "PSD0500501": 550
        },
        "BE": {
            "ACP0300301HP": 550,
            "ACP0400401HP": 550,
            "ACP0600601HP": 550,
            "CVS0400401LMSBF2HC": 550,
            "PSD0500501": 550
        },
        "BG": {
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "CVS0400401LMSBF2HC": 699,
            "PSD0500501": 699
        },
        "CY": {
            "ACP0300301HP": 799,
            "ACP0400401HP": 799,
            "ACP0600601HP": 799,
            "CVS0400401LMSBF2HC": 799,
            "PSD0500501": 799
        },
        "CZ": {
            "ACP0300301HP": 550,
            "ACP0400401HP": 550,
            "ACP0600601HP": 550,
            "CVS0400401LMSBF2HC": 550,
            "PSD0500501": 550
        },
        "DE": {
            "ACP0300301HP": 399,
            "ACP0400401HP": 399,
            "ACP0600601HP": 550,
            "CVS0400401LMSBF2HC": 399,
            "PSD0500501": 399
        },
        "DK": {
            "ACP0300301HP": 550,
            "ACP0400401HP": 550,
            "ACP0600601HP": 550,
            "CVS0400401LMSBF2HC": 550,
            "PSD0500501": 550
        },
        "EE": {
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "CVS0400401LMSBF2HC": 699,
            "PSD0500501": 699
        },
        "ES": {
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "CVS0400401LMSBF2HC": 699,
            "PSD0500501": 699
        },
        "FI": {
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "CVS0400401LMSBF2HC": 699,
            "PSD0500501": 699
        },
        "FR": {
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "CVS0400401LMSBF2HC": 699,
            "PSD0500501": 699
        },
        "GR": {
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "CVS0400401LMSBF2HC": 699,
            "PSD0500501": 699
        },
        "HR": {
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "CVS0400401LMSBF2HC": 699,
            "PSD0500501": 699
        },
        "HU": {
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "CVS0400401LMSBF2HC": 699,
            "PSD0500501": 699
        },
        "IE": {
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "CVS0400401LMSBF2HC": 699,
            "PSD0500501": 699
        },
        "IT": {
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "CVS0400401LMSBF2HC": 699,
            "PSD0500501": 699
        },
        "LT": {
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "CVS0400401LMSBF2HC": 699,
            "PSD0500501": 699
        },
        "LU": {
            "ACP0300301HP": 550,
            "ACP0400401HP": 550,
            "ACP0600601HP": 550,
            "CVS0400401LMSBF2HC": 550,
            "PSD0500501": 550
        },
        "LV": {
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "CVS0400401LMSBF2HC": 699,
            "PSD0500501": 699
        },
        "MT": {
            "ACP0300301HP": 799,
            "ACP0400401HP": 799,
            "ACP0600601HP": 799,
            "CVS0400401LMSBF2HC": 799,
            "PSD0500501": 799
        },
        "NL": {
            "ACP0300301HP": 550,
            "ACP0400401HP": 550,
            "ACP0600601HP": 550,
            "CVS0400401LMSBF2HC": 550,
            "PSD0500501": 550
        },
        "PL": {
            "ACP0300301HP": 550,
            "ACP0400401HP": 550,
            "ACP0600601HP": 550,
            "CVS0400401LMSBF2HC": 550,
            "PSD0500501": 550
        },
        "PT": {
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "CVS0400401LMSBF2HC": 699,
            "PSD0500501": 699
        },
        "RO": {
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "CVS0400401LMSBF2HC": 699,
            "PSD0500501": 699
        },
        "SE": {
            "ACP0300301HP": 799,
            "ACP0400401HP": 799,
            "ACP0600601HP": 799,
            "CVS0400401LMSBF2HC": 799,
            "PSD0500501": 799
        },
        "SI": {
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "CVS0400401LMSBF2HC": 699,
            "PSD0500501": 699
        },
        "SK": {
            "ACP0300301HP": 699,
            "ACP0400401HP": 699,
            "ACP0600601HP": 699,
            "CVS0400401LMSBF2HC": 699,
            "PSD0500501": 699
        }
    },
    "skus": {
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
        "CVS0400401LMSBF2HC": {
            "blueprint": 2,
            "cost": 3002,
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
