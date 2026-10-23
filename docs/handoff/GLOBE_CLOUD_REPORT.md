# Iris globe: cloud session report (branch v3-globe)

Date: 2026-10-23. Starting point: c596eeb (the unfinished work-in-progress commit). Scope: the hero's globe only; no change to prices, api/, the legal texts or /try.

## Summary

The work-in-progress state was more complete than its commit message said: it built, its page tests passed and every check that touches the hero passed without a change to the globe's code. What this session changed:

| Commit | What |
| --- | --- |
| fb363fa | `scripts/lib/cdp.mjs`: an optional `CHROME_FLAGS` environment variable (space-separated switches), so the browser checks run in a Linux container as root (`CHROME_PATH=/opt/pw-browsers/chromium CHROME_FLAGS=--no-sandbox`). Without it nothing changes; the Windows default stays first in the list after `CHROME_PATH`. |
| 232b964 | `README.md`: the motion line now names the one deliberate exception to "no 3D" (the hero globe), next to where `src/motion/motion.css` and `scripts/check_taste.mjs` (rule "3D", `ALLOW_3D`) already write it. |
| 1ecd437 | `scripts/check_budget.mjs`: `GLOBE` set to the measured numbers (JS +7,888 B, CSS +1,158 B; the work-in-progress commit had written +7,868 B before anything was built), with the breakdown in the comment, as the other constants do. |
| this commit | this report. |

The globe itself (`src/landing/globe/*`, `globeArt.ts`, `Hero.tsx`, `HeroScene.tsx`, `HeroView.tsx`, `css/hero.css`, `shell/hero.ts`, the copy in four languages, the pictures and the poster) is as c596eeb left it: no check found anything to fix in it.

What the brief asked for, and where it is proven:

* Phone order globe, headline, one line, gold button and "Tikra nuotrauka: prieš ir po" link; desktop copy left and globe right: `css/hero.css` (grid from 960 px, `display: contents` and `order` below it); `check:shell`, `check:landing overflow` and `check:slots` pass at 280 to 1280 px.
* The poster is the first paint and the LCP element, CLS 0: `check:landing vitals` (phone, slow 4G, CPU x4): LCP 964 to 980 ms on `poster_1200`, CLS 0.0002. `check:shell`: the live globe takes the poster's place with no box moved (stage mean pixel difference 2.6 to 3.3, 0.3 to 0.7 % of pixels far apart, within its limits).
* The chunk loads lazily, after the load, only while the hero is on screen: `check:landing globe` (asked for at 142 ms after a load at 94 ms; nothing asked for in 4 s when opened at #faq).
* Reduced motion: still, an artwork opens in place on a tap, Escape and a tap beside it close it: `check:landing globe`.
* Keyboard: one tab stop, arrows along and across the rows, Enter opens onto the button, Escape gives the focus back, Tab leaves: `check:landing globe` (also passed with a mouse emulated).
* Every artwork is a labelled button saying whose eyes it shows (32 of them), in four languages: `check:landing labels`.
* A vertical swipe scrolls the page, a sideways one turns the globe: `check:landing globe` (touch, 412 px).
* No "AI" wording in the hero or the globe (searched the four copy files and the globe's code); `check:texts` passes (four languages complete, no en or em dash).
* The honest line under the globe ("Mūsų pačių akis ir pavyzdinės nuotraukos, ne klientų" and the en, de, hu versions): `check:landing labels` checks it is under the stage in its own figure, in every language.
* The motion spec exception: `src/motion/motion.css` (header comment), `scripts/check_taste.mjs` (`ALLOW_3D` names only `src/landing/globe/globe.css` and `Globe.tsx`) and now the README. `check:taste` passes; its 3D rule matches `perspective:`, `perspective(`, `rotateX(`/`rotateY(`, `preserve-3d`, `translateZ(`, `backface-visibility` and not `translate3d(0,0,0)` or `perspective-origin`.

## Checks that ran here and their results

Environment: Linux container, Node 22.22.0, Python 3.13.16, headless Chromium 141 from Playwright (`/opt/pw-browsers/chromium`), run with `CHROME_PATH` and `CHROME_FLAGS=--no-sandbox`.

| Check | Result |
| --- | --- |
| `npm ci` | ok |
| `npm run build` (tsc and vite) | ok, no warnings |
| `node scripts/run_ts_tests.mjs` | 933 of 933 passed |
| `npm run check:texts` | ok |
| `npm run check:prices` | ok |
| `npm run check:styles` | ok |
| `npm run check:assets` | ok |
| `npm run check:budget` | ok: JS 262,028 B (-1,618 B against the base), CSS 37,793 B (+5,420 B; budget +7,000) |
| `npm run check:taste` | ok |
| `npm run lint` (oxlint) | exit 0; no warning in the globe or hero files |
| `python suites/compile_matrix.py` | ok under 3.12 and 3.13; 3.14 is not installed here |
| `bash suites/run_main.sh v3reg` | 225 of 226; the one failure is "the six legacy ids render the same pixels" (image hashes of the engine). The parent 8c253bf fails the same way on this machine (Pillow 12.3.0, numpy 2.5.3), so it is the environment, not this branch. The mutation test this branch adapted (the hero's alt text naming a style) passes. |
| `npm run check:landing` | every section ok except `guide` and `axe` (below); run one section at a time (`--only`) |
| `npm run check:states` | ok |
| `npm run check:slots` | ok |
| `npm run check:motion` | ok |
| `npm run check:motion:sections` | ok with a mouse emulated (see below) |
| `npm run check:motion:phone` | ok |
| `npm run check:reveal` | ok (rest: the globe's slow turn is the only thing that moves at rest, glows at most .22) |
| `npm run check:polish` | ok |
| `npm run check:tryheader` | ok |
| `npm run check:shell` | ok (16 language, market and size combinations; the globe takes the poster's place without a visible change) |

The three that need a word:

* `check:landing guide`: 3 failures, the guide video stays paused at 0 s. This Chromium build has no H.264 decoder (`canPlayType('video/mp4; codecs="avc1.42E01E"')` is empty) and the guide files are H.264. The guide video is not touched by this branch. It must be run in real Chrome locally.
* `check:landing axe` (axe-core 4.10.2 fetched into a scratch folder, not added to the repository): 8 findings, all two issues outside the hero. A colour contrast on the step number of "How it works" (`.lp-step:nth-child(2) .lp-num`, phones) and `image-redundant-alt` on the logo picture (`eye-dark-h34.png`). The parent 8c253bf gives exactly the same 8 findings, so they are older than the globe.
* `check:motion:sections`: on the first run 2 failures in its gallery part (the wall button not hidden at rest with a mouse, the hover zoom 1). The container has no pointer device, so Chromium answers `(hover: hover)` and `(pointer: fine)` with false. With a mouse emulated (`CHROME_FLAGS="--no-sandbox --blink-settings=primaryHoverType=2,availableHoverTypes=2,primaryPointerType=4,availablePointerTypes=4"`) the whole check passes. `check:landing globe,focus` also pass that way.

A first full `check:landing` run once stalled with no output for 10 minutes (Chrome's background requests to google.com are refused by this container's proxy); every section then passed or failed as above when run one at a time.

An indicative frame rate (headless, software rendering, so not a phone): at 412 px, pixel ratio 2.625, the globe's idle turn and a sideways drag with its fling ran at 60 fps with no frame over 33 ms, both at normal CPU and slowed 4x.

## Checks not run here

* The Python suites that need the private image fixtures (`suites/private/fixtures`, never in git): skipped. Of the guard suites only v3reg ran (above).
* `check:landing guide` in a browser that plays H.264 (see above).
* `check:langswitch`, `check:langheads`, `check:gate`, `check:legal`, `check:motion:close`, `check:motion:flow`: not asked for and not related to the hero; not run.

## Measured bytes

First load (what `dist/lp/lt.html` and `en.html` name, gzip level 6), this branch against its parent 8c253bf:

| | parent | globe | difference |
| --- | --- | --- | --- |
| HTML (lt / en) | 8,135 / 8,064 B | 7,745 / 7,680 B | -390 / -384 B |
| JavaScript named by the page | 133,866 B | 133,954 B | +88 B (entry +125 B for the watcher that fetches the globe, copy files -37 B) |
| CSS | 19,152 B | 18,675 B | -477 B |
| Hero picture | wall picture 34,138 B (900 px) and disc 13,790 B | poster 20,544 B (900 px) | -27,384 B |

The one first-load growth is the 125 B of JavaScript for the watcher (it has to live in the entry to fetch the lazy chunk); it is recorded in `scripts/check_budget.mjs` with the rest of `GLOBE`.

Lazy, only after the load while the hero is on screen:

* `Globe-*.js` 7,804 B gzip (21.1 kB raw), `Globe-*.css` 1,635 B gzip (6.1 kB raw).
* Disc pictures, 32 of each width: 160 px 79,416 B, 240 px 160,894 B (one width per visitor, picked by `sizes`), 480 px 638,172 B (only the opened artwork's own, one at a time).
* Poster: 600 px 12,628 B, 900 px 20,544 B, 1200 px 29,944 B (one of them, preloaded).

`check:budget` sum, all chunks the landing can request: JavaScript +7,888 B and CSS +1,158 B over the parent (that is `GLOBE`).

## What the local verification must look at

1. Run the browser checks on Windows in real Chrome (the default path, no variables): above all `check:landing` in full (guide and axe included) and `check:motion:sections` with a real mouse.
2. The axe findings (step number contrast, logo alt) are older than this branch; decide separately whether to fix them.
3. The poster was captured on the owner's machine. `check:shell` here (Linux Chromium) found the live globe within the limits (mean 2.6 to 3.3); look once at 375, 768 and 1280 px in Windows Chrome that the swap from poster to globe is not seen.
4. Feel on a real phone (iPhone Safari and an Android Chrome): the slow turn, a fling, a vertical swipe that must scroll the page, a tap that opens an artwork, its words and "Try it with your eye" on a short phone (the veil goes on below the stage there), Escape or a tap beside it.
5. Reduced motion on a phone (iOS: Reduce Motion): still, tidy, an artwork opens in place on a tap.
6. The v3reg pixel failure is the environment (same on the parent here); it should be green on the owner's machine as before.
7. The branch is not for main until the owner has looked at it.
