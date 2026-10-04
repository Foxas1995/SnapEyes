"""The pictures of the landing page: copies exactly the files the page uses into public/assets/landing with content hashed
names and writes the manifest the code imports (src/landing/assets.ts and src/landing/assets.data.ts).

    python scripts/build_landing_assets.py --src <folder of rendered pictures>     write (or update) the files and the manifest
    python scripts/build_landing_assets.py --check                                  verify the committed files against the manifest

What is used is decided by scripts/landing_assets.json: the picture families the wall, the style gallery, the rooms, the
Reveal and the wall thumbnails name, plus "extras" (files a component names itself). Nothing else is copied, and files in
public/assets/landing that are not in that set are deleted, so the repository holds only what the page uses. The pictures
themselves are rendered elsewhere (the mock-up library, the style renders and the Reveal layers of the design waves; their
sources and rights are in scripts/landing_assets_provenance.json); --src is the folder with the finished webp files in
m/, art/, reveal/ and ui/ (the prototype's assets folder). The page never loads a file from there, only the copies.

A name is <dir>/<base>_<width>; its file is public/assets/landing/<dir>/<base>_<width>.<hash>.webp where <hash> is the first
ten hex characters of the SHA-256 of the file. vercel.json serves /assets/landing/* with "immutable" for a year: a changed
picture has another hash, so another address. No price, no text and no secret is in any of this.
"""
import argparse, hashlib, json, os, re, shutil, sys

sys.dont_write_bytecode = True
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST = os.path.join(ROOT, "scripts", "landing_assets.json")
OUT_DEFAULT = os.path.join(ROOT, "public", "assets", "landing")
TS_FILES = os.path.join(ROOT, "src", "landing", "assets.ts")
TS_DATA = os.path.join(ROOT, "src", "landing", "assets.data.ts")
IRIS = os.path.join(ROOT, "api", "_lib", "iris.py")
BASE_URL = "/assets/landing/"
HASH_LEN = 10
WIDTH_RE = re.compile(r"^(.*)_(\d+)$")


def collect(spec, available):
    """The used file names. A family's widths are the ones that exist in `available` (name -> path), so a width that was never
    rendered is simply not offered; a family with no file at all is an error."""
    used = set(spec["extras"])
    problems = []

    def fam(base, only=None):
        ws = sorted(int(m.group(2)) for n in available for m in [WIDTH_RE.match(n)] if m and m.group(1) == base)
        if only is not None:
            ws = [w for w in ws if w in only]
        if not ws:
            problems.append(f"no picture for the family {base}")
        for w in ws:
            used.add(f"{base}_{w}")

    for mat in spec["stage"].values():
        for a in mat.values():
            fam(a["base"])
            if "de" in a:
                fam(a["de"])
    for grp in spec["gallery"]["groups"]:
        for it in spec["gallery"][grp]:
            for k in ("wall", "wallOwn"):
                if it.get(k):
                    fam(it[k]["base"])
            if "design" in it:
                for e in spec["gallery"]["eyes"]:
                    fam(f"art/{it['design']}_{e['id']}", {480, 900})
            else:
                fam(f"art/{it['file']}", {480, 900})
    for e in spec["gallery"]["eyes"]:
        used.add(e["thumb"])
    for r in spec["more"]:
        fam(r["base"])
    for e in spec["reveal"]["eyes"]:
        fam(e["photo"], {900, 1200})
        fam(e["iris"], {900, 1200})
        used.add(e["art"])
    used.update(spec["wallThumbs"].values())
    return used, problems


def sha10(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:HASH_LEN]


def dims(path):
    from PIL import Image
    with Image.open(path) as im:
        if im.format != "WEBP":
            raise SystemExit(f"{path}: not a webp file")
        return im.width, im.height


def scan_src(src):
    found = {}
    for d in ("m", "art", "reveal", "ui"):
        base = os.path.join(src, d)
        if not os.path.isdir(base):
            continue
        for f in os.listdir(base):
            if f.endswith(".webp"):
                found[f"{d}/{f[:-5]}"] = os.path.join(base, f)
    return found


def live_engine_styles():
    """The styles api/_lib/iris.py can make today (the keys of STYLES)."""
    try:
        text = open(IRIS, encoding="utf-8").read()
        body = text[text.index("STYLES = {"):]
        body = body[:body.index("\n}\n")]
        return sorted(set(re.findall(r'^[ ]{4}"([a-z_]+)":[ ]*\{', body, re.M)))
    except (OSError, ValueError):
        return []


def release_gate(spec):
    """One row per tile: can the order flow make what the tile shows, today? It can when the engine has the style (STYLES of iris.py),
    the style LOOKS like the tile (look) and the terms of sale, /try and the order e-mail call it by the tile's name (name). A style
    that shares only a name with a tile, or only a look, does not count."""
    live = live_engine_styles()
    rows = []
    for grp in spec["gallery"]["groups"]:
        for it in spec["gallery"][grp]:
            eng = spec["engine"].get(it["id"])
            ok = bool(eng and eng["style"] in live and eng["look"] and eng["name"])
            rows.append({"tile": it["id"], "group": grp, "engine_style": eng["style"] if eng else None, "in_engine_today": ok})
    return live, rows


def ts_literal(v, indent=0):
    return json.dumps(v, indent=2, ensure_ascii=False).replace("\n", "\n" + " " * indent)


def write_manifest(spec, files, ts_files_path, ts_data_path):
    names = sorted(files)
    fam = {}
    for n in names:
        m = WIDTH_RE.match(n)
        if m:
            fam.setdefault(m.group(1), []).append(int(m.group(2)))
    fam = {k: sorted(v) for k, v in sorted(fam.items())}
    lines = [f"  '{n}': ['{files[n]['hash']}', {files[n]['w']}, {files[n]['h']}, {files[n]['bytes']}]," for n in names]
    widths = [f"  '{k}': [{', '.join(str(w) for w in v)}]," for k, v in fam.items()]
    text = f"""// GENERATED by scripts/build_landing_assets.py from scripts/landing_assets.json. Do not edit by hand: change the list and run
// the script (python scripts/build_landing_assets.py --src <folder of rendered pictures>).
//
// Every picture of the landing page has a content hash in its name (public/assets/landing/<dir>/<name>.<hash>.webp), so
// vercel.json serves it with "Cache-Control: immutable" for a year; a changed picture is another address. This file is the
// only place that knows the addresses: components ask for a name and get the address, the srcset and the size.
//
//   asset('m/lounge_acrylic__eye__tight')     the family: every width as a srcset, one of them as src (pick, default 900)
//   asset('reveal/gd_iris_900')               one file
//   asset('m/dining_metal__eye__wide', 2000)  the family with the 2000 px file as the src
//   asset('m/lounge_acrylic__eye__tight', {{ max: 1200 }})   the family without its widest files
// A name that is not here does not compile. The structures that name pictures (wall, gallery, rooms, Reveal) are in
// ./assets.data.ts, which only the sections below the first screen load.

export const ASSET_BASE = '{BASE_URL}';

/** name (folder and file name without the extension) -> [content hash, width, height, bytes] */
const FILES = {{
{chr(10).join(lines)}
}} as const satisfies Record<string, readonly [string, number, number, number]>;

/** family (the name without _<width>) -> the widths that exist, ascending */
const WIDTHS = {{
{chr(10).join(widths)}
}} as const satisfies Record<string, readonly number[]>;

export type AssetFile = keyof typeof FILES;
export type AssetFamily = keyof typeof WIDTHS;
export type AssetName = AssetFile | AssetFamily;

/** What a picture needs: the address, the srcset of a family with several widths, the size of the src (every width of a
 *  family has the same shape, so width and height reserve the right space). Same shape as PictureAsset in ./ui.tsx. */
export interface PictureAsset {{ src: string; srcset?: string; w: number; h: number }}

/** The address of one file. */
export function assetUrl(file: AssetFile): string {{
  const slash = file.lastIndexOf('/');
  return `${{ASSET_BASE}}${{file.slice(0, slash + 1)}}${{file.slice(slash + 1)}}.${{FILES[file][0]}}.webp`;
}}

/** The widths a family has, ascending. */
export function assetWidths(family: AssetFamily): readonly number[] {{
  return WIDTHS[family];
}}

/** How a family becomes a srcset: pick = the width whose file is the src (nearest to it, default 900); max = the widest file the
 *  srcset offers (the first screen offers 600, 900 and 1200 only, so a phone with a dense screen does not fetch the 2000 px file). */
export type AssetOptions = number | {{ pick?: number; max?: number }};

/** A file by name, or a family as a srcset. */
export function asset(name: AssetName, options: AssetOptions = {{}}): PictureAsset {{
  if (name in FILES) {{
    const f = name as AssetFile;
    return {{ src: assetUrl(f), w: FILES[f][1], h: FILES[f][2] }};
  }}
  const o = typeof options === 'number' ? {{ pick: options }} : options;
  const pick = o.pick ?? 900;
  const all = WIDTHS[name as AssetFamily];
  const ws = all.filter((w) => w <= (o.max ?? Infinity));
  if (ws.length === 0) throw new Error(`asset ${{name}}: no file up to ${{o.max}} px`);
  let best: number = ws[0];
  for (const w of ws) if (Math.abs(w - pick) < Math.abs(best - pick)) best = w;
  const file = (w: number) => `${{name}}_${{w}}` as AssetFile;
  return {{
    src: assetUrl(file(best)),
    srcset: ws.length > 1 ? ws.map((w) => `${{assetUrl(file(w))}} ${{w}}w`).join(', ') : undefined,
    w: FILES[file(best)][1],
    h: FILES[file(best)][2],
  }};
}}

/** Every address of the manifest (the build's check and the service of the preload list read it). */
export const ALL_ASSET_FILES = Object.keys(FILES) as AssetFile[];
export const ASSET_HASH = FILES as Readonly<Record<AssetFile, readonly [string, number, number, number]>>;
"""
    open(ts_files_path, "w", encoding="utf-8", newline="\n").write(text)

    data = f"""// GENERATED by scripts/build_landing_assets.py from scripts/landing_assets.json. Do not edit by hand.
//
// What the sections below the first screen need to know about the pictures: which family is which wall scene (material x
// artwork), which flat artworks the gallery shows, the rooms of "More ways to see it", the Reveal's layers, the wall
// thumbnails and the close-up crop. Every name is checked against the manifest (./assets.ts) by the compiler. No price and
// no text is here: the words are the copy's (src/landing/copy), the prices come from src/landing/prices.ts.
import type {{ AssetFamily, AssetFile }} from './assets';

export type Material = 'acrylic' | 'metal' | 'canvas' | 'framed' | 'block' | 'phone';
export type WallArt = 'eye' | 'universe' | 'family4' | 'collision';
export type EyeId = 'own' | 'yg' | 'br' | 'gr';
export type GalleryGroup = 'one' | 'two' | 'family';

/** The wall stage: the scene of a material with an artwork in it. sizeOk: the drawn size was estimated at 40 to 55 cm, so
 *  the page may print "about 50 cm" next to it. de: the German version of the scene (the phone shows text). */
export interface StageScene {{ base: AssetFamily; sizeOk: boolean; de?: AssetFamily }}
export const STAGE: Readonly<Record<Material, Readonly<Partial<Record<WallArt, StageScene>>>>> = {ts_literal(spec["stage"])};

/** A tile of the style gallery. design: a single-eye style, its flat art is art/<design>_<eye> (two widths); file: a two-eye
 *  or family artwork, art/<file> (two widths). wallOwn / wall: the tile shown on the wall (Mantas's eye, or a fixed scene).
 */
export interface GalleryTile {{
  id: string;
  design?: string;
  file?: string;
  price: 'art' | 'black' | 'two' | 'n';
  src?: 'mixed';
  n?: number;
  square?: boolean;
  wallOwn?: {{ base: AssetFamily; ratio: string }};
  wall?: {{ base: AssetFamily; ratio: string }};
}}
export const GALLERY: {{
  readonly groups: readonly GalleryGroup[];
  readonly eyes: readonly {{ id: EyeId; thumb: AssetFile }}[];
  readonly one: readonly GalleryTile[];
  readonly two: readonly GalleryTile[];
  readonly family: readonly GalleryTile[];
}} = {ts_literal(spec["gallery"])};

/** "More ways to see it": the rooms that are not on the wall stage. */
export const MORE: readonly {{ id: string; base: AssetFamily }}[] = {ts_literal(spec["more"])};

/** The Reveal's eyes: two registered layers (photo, restored iris; 900 and 1200 px) and the artwork of the strip. phone: the left half
 *  IS a phone photo (the owner's own phone, rights confirmed); false for a photograph from elsewhere (the brown eye is a web photograph),
 *  whose left half the page calls "Photo", never "Phone photo" (src/landing/RevealSlider.tsx, copy reveal.beforeWeb). */
export const REVEAL: {{ readonly eyes: readonly {{ id: 'gd' | 'br' | 'own'; phone: boolean; photo: AssetFamily; iris: AssetFamily; art: AssetFile }}[] }} = {ts_literal(spec["reveal"])};

/** The 96 px thumbnail of each wall artwork (the chips of the wall stage). */
export const WALL_THUMBS: Readonly<Record<WallArt, AssetFile>> = {ts_literal(spec["wallThumbs"])};

/** The close-up: a square of crop_px = [left, top, right, bottom] cut from the 4096 px file. */
export const FIBRE: {{ readonly crop_px: readonly [number, number, number, number]; readonly of: number }} = {ts_literal(spec["fibre"])};

/** The gallery tile -> the engine style that could make it today. The release gate (scripts/check_landing_assets.mjs) counts a tile as
 *  orderable only when ALL of these hold: the engine really has the style (STYLES of api/_lib/iris.py), the style looks like the tile
 *  (look), and the terms of sale, /try and the order e-mail call it by the tile's name (name). A tile that is not in this table, or
 *  whose style shares only a name or only a look with it, cannot be ordered yet. Update it in scripts/landing_assets.json, in the
 *  same change that ships the engine styles (BUILD_PLAN section 3, item 1). */
export interface EngineStyle {{ style: string; look: boolean; name: boolean }}
export const ENGINE_STYLE: Readonly<Record<string, EngineStyle>> = {ts_literal(spec["engine"])};
"""
    open(ts_data_path, "w", encoding="utf-8", newline="\n").write(data)


def main():
    ap = argparse.ArgumentParser(description="Copy the landing page's pictures with content hashed names and write the manifest.")
    ap.add_argument("--src", default=os.environ.get("LANDING_ASSETS_SRC"), help="folder with m/, art/, reveal/, ui/ (finished webp files)")
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--check", action="store_true", help="verify the committed files against assets.ts, change nothing")
    args = ap.parse_args()
    spec = json.load(open(LIST, encoding="utf-8"))

    if args.check:
        ts = open(TS_FILES, encoding="utf-8").read()
        listed = {}
        for m in re.finditer(r"'([A-Za-z0-9_/.-]+)': \['([0-9a-f]{10})', (\d+), (\d+), (\d+)\],", ts):
            listed[m.group(1)] = (m.group(2), int(m.group(5)))
        bad = []
        for n, (h, size) in listed.items():
            d, f = n.rsplit("/", 1)
            p = os.path.join(args.out, d, f"{f}.{h}.webp")
            if not os.path.exists(p):
                bad.append(f"missing {os.path.relpath(p, ROOT)}")
            elif os.path.getsize(p) != size or sha10(p) != h:
                bad.append(f"changed {os.path.relpath(p, ROOT)}")
        on_disk = set()
        for dp, _, fs in os.walk(args.out):
            for f in fs:
                on_disk.add(os.path.relpath(os.path.join(dp, f), args.out).replace(os.sep, "/"))
        want = {f"{n.rsplit('/', 1)[0]}/{n.rsplit('/', 1)[1]}.{h}.webp" for n, (h, _) in listed.items()}
        for extra in sorted(on_disk - want):
            bad.append(f"not in the manifest: {extra}")
        if bad:
            print("landing assets NOT in order:\n  " + "\n  ".join(bad[:40]))
            return 1
        print(f"landing assets ok: {len(listed)} files match assets.ts, none extra")
        return 0

    if not args.src or not os.path.isdir(args.src):
        print("give --src <folder with m/, art/, reveal/, ui/> (or set LANDING_ASSETS_SRC)")
        return 2
    available = scan_src(args.src)
    used, problems = collect(spec, available)
    missing = sorted(u for u in used if u not in available)
    if problems or missing:
        print("cannot build:\n  " + "\n  ".join(problems + [f"missing {m}.webp in {args.src}" for m in missing]))
        return 1

    files = {}
    for n in sorted(used):
        p = available[n]
        w, h = dims(p)
        files[n] = {"hash": sha10(p), "w": w, "h": h, "bytes": os.path.getsize(p), "path": p}
    os.makedirs(args.out, exist_ok=True)
    keep = set()
    for n, f in files.items():
        d, base = n.rsplit("/", 1)
        os.makedirs(os.path.join(args.out, d), exist_ok=True)
        name = f"{base}.{f['hash']}.webp"
        keep.add(f"{d}/{name}")
        target = os.path.join(args.out, d, name)
        if not os.path.exists(target):
            shutil.copyfile(f["path"], target)
    removed = 0
    for dp, _, fs in os.walk(args.out):
        for fn in fs:
            rel = os.path.relpath(os.path.join(dp, fn), args.out).replace(os.sep, "/")
            if rel not in keep:
                os.remove(os.path.join(dp, fn))
                removed += 1
    for dp, dn, fs in os.walk(args.out, topdown=False):
        if not os.listdir(dp) and dp != args.out:
            os.rmdir(dp)
    write_manifest(spec, files, TS_FILES, TS_DATA)
    total = sum(f["bytes"] for f in files.values())
    print(f"{len(files)} files, {total / 1e6:.2f} MB into {os.path.relpath(args.out, ROOT)} ({removed} stale removed); manifest in src/landing/assets.ts and assets.data.ts")
    live, rows = release_gate(spec)
    not_live = [r["tile"] for r in rows if not r["in_engine_today"]]
    print(f"RELEASE GATE: the engine makes {live} today; tiles it cannot make yet: {len(not_live)} of {len(rows)} ({', '.join(not_live)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
