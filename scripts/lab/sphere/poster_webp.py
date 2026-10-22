"""LAB: the two widths of each poster (src/lab/poster/<piece>.png from ./poster.mjs -> <piece>-1200.webp and <piece>-640.webp; the png is removed)."""
import os
from PIL import Image

DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src', 'lab', 'poster')
for piece in ('globe', 'ring'):
    src = os.path.join(DIR, f'{piece}.png')
    im = Image.open(src).convert('RGB')
    for w in (1200, 640):
        h = round(im.height * w / im.width)
        path = os.path.join(DIR, f'{piece}-{w}.webp')
        im.resize((w, h), Image.LANCZOS).save(path, 'WEBP', quality=70 if w == 1200 else 74, method=6)
        print(piece, w, 'x', h, os.path.getsize(path), 'bytes')
    os.remove(src)
