# -*- coding: utf-8 -*-
"""The QR codes of the landing's first screen on a computer (src/landing/HeroView.tsx, 2026-11-10): one per language, each the address
of the capture tool in that language (https://snapeyes.com/try?lang=xx), so a visitor at a desk opens it on the phone that will take
the photo. The market is not in the code: /try finds it as it does for every new visitor.
    python scripts/make_qr.py            writes public/assets/atelier/qr-try-<lang>.svg (needs the qrcode package)
    python scripts/make_qr.py --check    reads every file back with OpenCV and compares the address (needs opencv-python and Pillow)
Dark modules on white with a quiet zone of 3 modules inside the picture (the page puts it on its dark ground, so the white is part of the file)."""
import os, re, sys
import qrcode

LANGS = ["en", "de", "lt", "hu", "hr"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public", "assets", "atelier")
QUIET = 3
url = lambda l: "https://snapeyes.com/try?lang=%s" % l


def matrix(text):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=QUIET)
    q.add_data(text)
    q.make(fit=True)
    return q.get_matrix()


def svg(m):
    n = len(m)
    d = []
    for y, row in enumerate(m):
        x = 0
        while x < n:
            if row[x]:
                x0 = x
                while x < n and row[x]:
                    x += 1
                d.append("M%d %dh%dv1h-%dz" % (x0, y, x - x0, x - x0))
            else:
                x += 1
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" shape-rendering="crispEdges"><rect width="%d" height="%d" rx="2" fill="#fff"/>'
            '<path fill="#07090e" d="%s"/></svg>\n' % (n, n, n, n, "".join(d)))


def check():
    import cv2, numpy as np
    bad = 0
    for l in LANGS:
        s = open(os.path.join(OUT, "qr-try-%s.svg" % l), encoding="utf-8").read()
        n = int(re.search(r'viewBox="0 0 (\d+)', s).group(1))
        im = np.full((n, n), 255, np.uint8)
        for x, y, w in re.findall(r"M(\d+) (\d+)h(\d+)v1", s):
            im[int(y), int(x):int(x) + int(w)] = 0
        big = cv2.resize(im, (n * 8, n * 8), interpolation=cv2.INTER_NEAREST)
        got = cv2.QRCodeDetector().detectAndDecode(big)[0]
        ok = got == url(l)
        bad += not ok
        print("%s %s: %s" % ("ok " if ok else "BAD", l, got or "nothing read"))
    return bad


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(1 if check() else 0)
    for l in LANGS:
        s = svg(matrix(url(l)))
        open(os.path.join(OUT, "qr-try-%s.svg" % l), "w", encoding="utf-8", newline="\n").write(s)
        print("qr-try-%s.svg %d B, %s" % (l, len(s), url(l)))
