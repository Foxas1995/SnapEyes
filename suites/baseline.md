# Baseline of the v3 engine work (work package WP0)

Recorded 2026-10-04 on main `1d58fbf` (branch `v3-engine`), Windows 11, Python 3.14.3, Node 24.14. Later work packages append dated
sections below (WP4: the real function sizes; WP17a: the slow factor of the real instance). **Everything that needs Vercel access
this machine does not have is marked "unverified" with the plan step that closes it (V1 to V4, VE3 of WP17 and WP17a): nothing here
is guessed.** The only measurements taken here are local ones, and each says what it measured.

## 1. The green list: the full set of 21 on `1d58fbf`

Taken twice, with the same result: first through the original scratch tools (`wave-exp/tools/run_main.sh` with `mksp.py`, before
anything moved), then from this folder (`bash suites/run_main.sh`), which is the one that counts from now on. Twenty Python suites,
all exit 0, no failing check, and the page-code tests `ts`, which are red by construction in the old runner (it imported Vite from a
folder of the old scratch tree that does not exist: `ERR_MODULE_NOT_FOUND`, and it ran one hard-coded file) and green in
`scripts/run_ts_tests.mjs` (20 of 20). The last row is the first suite of the v3 work, added by WP0 (the 22nd entry).

| suite | exit | checks (PASS lines) | state |
|---|---:|---:|---|
| r2 | 0 | 105 | GREEN |
| r3 | 0 | 48 | GREEN |
| r4 | 0 | 69 | GREEN |
| r5 | 0 | 54 | GREEN |
| fix | 0 | 53 | GREEN |
| admin | 0 | 186 | GREEN |
| pay | 0 | 120 | GREEN |
| advance | 0 | 66 | GREEN |
| refund | 0 | 7 | GREEN |
| preview | 0 | 60 | GREEN |
| review | 0 | 11 | GREEN |
| fixmk | 0 | 36 | GREEN |
| markets | 0 | 58 | GREEN |
| au | 0 | 70 | GREEN |
| payrev | 0 | 19 | GREEN |
| fixer | 0 | 43 | GREEN |
| oldpay | 0 | 120 | GREEN |
| oldadv | 0 | 66 | GREEN |
| oldadmin | 0 | 186 | GREEN |
| exp | 0 | 349 | GREEN |
| ts | 0 | 20 | GREEN |
| v3wp0 | 0 | 93 | GREEN |

(`v3wp0` was 61 checks when WP0 was first committed and is 93 after the review fixes of section 7.)

**Determinism: this list was NOT deterministic when it was first recorded, and is now (section 7).** The suite `fix` (check
`A2 six parallel drafts with one ticket`) failed on Windows in 3 of 8 serial runs on main `1d58fbf` and 2 of 8 on the WP0 branch
(the review's loop), and the first record above happened to be a green draw. The cause was in the local-folder store, not in the
checkout code under test: see section 7. Since that fix the same suite is green in every run of the loops recorded there.

The counts are in `baseline.json`; `summary.py` flags a suite that passes fewer checks than recorded. Around them: `npm run build`
(tsc, the price check with the experiments' ladders, the text check, Vite) exits 0; `python -m compileall api` exits 0 under Python
3.12.13, 3.13 and 3.14.3 and every file parses as Python 3.12 (`python suites/compile_matrix.py`); `python scripts/dev_api.py`
starts and serves the eleven routes.

Two things the old runner hid: (1) the `exp` suite and the page-code test found their code through paths of the scratch tree, so
they could only run there; (2) `mksp.py` copied everything from the scratch root, so a suite in the repository (the planned
`scripts/styles_tests`) was unreachable. Both are fixed (`suites/mksp.py` has `REPO_DIRS`).

**Not in git:** the two admin suites replay model replies recorded from the owner's own photos (20 files, 3 MB). A real eye is
biometric data, so they stay in `suites/private/fixtures` (ignored by git); `fixtures.sha256` lists their hashes. The only other
copy is in the session scratch folder: **the owner should keep a copy of `suites/private/` outside the repository (decision DE4).**

## 2. Pins

| What | Value | Basis |
|---|---|---|
| Interpreter | `.python-version` = `3.14` | the development machine and the scratch goldens run 3.14.3; Vercel's default is 3.12 and 3.13 and 3.14 are available (plan 3.1 rule 9, decision DE2) |
| numpy | `==2.4.4` | the version of the suites and the scratch goldens |
| Pillow | `==12.2.0` | same |
| requests | `==2.33.1` | same |
| onnxruntime | `==1.26.0` | same |
| Pulled in, not pinned | charset-normalizer 3.4.7, idna 3.14, urllib3 2.7.0, certifi 2026.4.22, flatbuffers 25.12.19, packaging 26.2, protobuf 7.34.1 | the full set these suites ran with |

Checked on PyPI (metadata only, 2026-10-04): numpy, Pillow and onnxruntime list `cp314` `manylinux_2_27`/`manylinux_2_28` x86_64
wheels for exactly these versions, and requests is a pure wheel, so a Linux build for Python 3.14 has all four.
**Unverified (closing step VE3, decision DE2): the Python version and the onnxruntime wheel in a real Vercel build log.** The
deployed versions of the last Vercel build are not in the repository, so the pin is the pair both the development machine and a
Linux build can run, not a copy of production's. The pin changes the interpreter of the next deploy (3.12 to 3.14): if the Preview
build log shows a missing wheel, `.python-version` 3.13 is the fallback and the suites must be re-run on it. **Measured in the review
fix (2026-10-04, a throwaway 3.13.1 venv with the same four pins): the fallback renders the same bytes.** The legacy compose path
(6 styles x 1, 2 and 3 eyes through `compose.compose`, 18 pixel hashes, and 12 clean engine renders) gives identical hashes on 3.13.1
and 3.14.3 with these pins. The libraries matter more than the interpreter: numpy 2.3.5 with Pillow 11.3.0 (what 3.13 had installed
on this machine without the pins) gives the same QA flags, the same layouts and the same 12 clean engine renders, but **different
preview pixels in all 18 compose outputs** (one measured case, celestial_gold with one eye: 6.9 percent of the pixels differ, 0.4
percent by more than 32 levels, in blocks spread over the picture; the preview path adds the watermark and a JPEG encode). So the
byte-level goldens hold only on the pinned versions, and the first deploy with the pins may change the preview pixels of the
legacy styles slightly against whatever versions production resolves today (not knowable here: the last build log is not in the
repository). Not measured: which of the two libraries causes it, and the paid master path (it was not run: it needs the image model).

## 3. Function size (V1) and `excludeFiles` (V2)

`node scripts/bundle_report.mjs --pypi` computes, without a Linux machine and without `vercel build` (a local Windows build would
install Windows wheels): the files each function bundles (git's files minus `excludeFiles` minus `.vercelignore`) and the size of
the Linux wheels PyPI lists for the pinned versions, read from the zip directories of the wheels (about 100 KB each; no wheel is
downloaded). MiB = 2^20 bytes.

| Part | MiB | Note |
|---|---:|---|
| Files of the repository in each function | 16.5 | all of it `api/`: `_assets` 15.4 (11 backgrounds, the ONNX model, 2 fonts), `_lib` and the handlers 1.1 |
| numpy (Linux wheel, unpacked) | 53.9 | Windows 39.3 |
| Pillow | 18.6 | Windows 14.0 |
| onnxruntime | 49.3 | Windows 36.8 |
| the other 8 packages | 3.8 | requests, charset-normalizer, idna, urllib3, certifi, flatbuffers, packaging, protobuf |
| **Python packages together** | **125.6** | Windows 93.8: Linux is 1.34 times larger, inside the plan's guess of 1.2 to 1.75 |
| **Estimate per function (all 11 are alike today)** | **142.2** | against the 235 MiB tripwire: 92.8 MiB of room; the plan's earlier estimate was 165 to 225 MB |

Looking ahead with the plan's own figures (not a measurement): the plates (44 MiB with the atlases) and the engine code (0.8 MiB)
go into the four rendering functions only (WP4), about 187 MiB for those, still under the tripwire; the legacy backgrounds
(11 MB) go at WP19.

The two readings of `excludeFiles` (strict: a pattern without a slash such as `*.json` matches the project root only; loose: any
depth, dotfiles too) give the same 16.5 MiB today, because nothing under `api/` is a `.json`, `.html`, `.ts` or `.md` file. The
report fails (`--check`) when a folder other than `api/` would ride into a function, which is how `suites/` was found missing from
`excludeFiles` and added (it is also in `.vercelignore`).

**Unverified, closing steps V1 and V2 in WP17a:** the real unzipped size of each of the 11 functions on a Preview deployment
(`node scripts/bundle_report.mjs --sizes <json>` records the dashboard figures next to these estimates, `--func-dir` reads a Linux
`vercel build`); whether `excludeFiles` reaches installed packages (so that the nine functions without a model could drop
onnxruntime, about 49 MiB each); how overlapping `functions` globs resolve; whether `.vercelignore` is honoured for Git deployments
(`excludeFiles` is the one that does not depend on it).

## 4. The slow factor (V3)

`api/_lib/cpu_probe.py` holds the workload (blur by cumulative sums, float32 trigonometry and exp, a 4096 px RGB frame, a LANCZOS
reduction, a bincount scatter, a JPEG q95 4:4:4 encode and decode: no engine code), the admin action `cpu_probe`
(`{mode: cold|warm, runs, baseline}`) returns seconds per phase, `slow_factor`, the configured `STYLE_SLOW_CPU` (environment,
default 1.6, `style_slow_cpu()`) and the instance's own facts (memory, CPUs, `/tmp`, versions); `scripts/cpu_probe.py` runs the same
workload locally and, with `--remote URL --key-file F`, measures the baseline here and asks the deployment to run it.

Local baseline of the development machine on 2026-10-04 (median of three invocations of `python scripts/cpu_probe.py --runs 5`),
seconds: blur 0.303, float32 math 0.060, RGB frame 0.203, LANCZOS 0.158, scatter 0.083, JPEG encode 0.275, JPEG decode 0.311,
**total 1.393**. The planning spike's own probe took 1.464 on a pinned quiet core; its RGB frame was built in float64 (about 800 MB
at the peak, which could run a 1 GB function out of memory), this one in float32 (the probe peaks near 420 MB of working set, measured on Windows; the commit charge there reads 920 MB, which is
not resident memory), and the other six
phases agree within 5 percent. Sanity check of the action against the local dev server on the same machine: slow factor 0.99.

**Unverified, closing step V3 (WP17a, VE1):** the slow factor cold and warm on a real instance. The action is not deployed (it is
in this branch only); it needs a Preview deployment with the admin secret and, if the Preview is protected, the bypass header
(`--header`). Until then `STYLE_SLOW_CPU` stays 1.6 (measured 1.58, range 1.44 to 1.73, on a 1024 px compose; 4096 px work has no
Vercel measurement).

## 5. Project settings and the instance (V4, VE3)

**Unverified, closing steps V4 and VE3:** the project's function memory, Fluid compute, maximum duration, the size of `/tmp`, the
vCPU count, whether in-function concurrency is on, and the plan (Hobby or Pro, decision 23). What the repository says: `vercel.json`
`maxDuration` 60, `iris.BUDGET` 52 s, `iris.py` assumes a 1024 MB function; the platform documentation read for the plan says 2 GB
and 1 vCPU with Fluid on Hobby. The `cpu_probe` reply carries the instance's own view (`instance.mem_total_mb`, `cgroup_memory_max`,
`cpus_usable`, `tmp_total_mb`, `process_age_s`), which settles memory, vCPU and `/tmp` as far as an instance can know them; the
project settings themselves (Fluid, maximum duration) are read in the Vercel dashboard.

## 6. Open

| Step | What | Who |
|---|---|---|
| V1, V2 | real function sizes, `excludeFiles` semantics | WP17a, needs a Preview |
| V3 | slow factor cold and warm | WP17a (VE1), needs a Preview with the admin secret |
| V4, VE3 | memory, Fluid, duration, `/tmp`, Python version and onnxruntime wheel of the real build | owner reads the project settings, WP17a reads the build log |
| DE4 | a safe copy of `suites/private/` outside the repository | owner |

## 7. Review of WP0 and its fixes (2026-10-04)

An independent review re-ran everything on throwaway clones. No blocker. What it found, and what was done:

**The regression net was not deterministic (major).** `fix` is the one suite that failed on both main and the branch: serial runs
of the same suite on the same checkout, red 3 of 8 times on main `1d58fbf` and 2 of 8 on the WP0 branch, always the check
`A2 six parallel drafts with one ticket: all answered, ONE order`. Root cause, reproduced with a traceback: the local-folder store
(`api/_lib/store.py`, the stand-in for the bucket that `STORE_LOCAL_DIR` switches on in the tests and the dev server) writes with
`os.replace` and reads with `read_bytes`. On Windows a file that another thread has open, or is just replacing, refuses open,
rename and delete with `PermissionError` for a few milliseconds (POSIX does not, and neither does the bucket). Six parallel drafts
of one work ticket all write the same `orders/<order>/draft/eye_1.json`, so one of them got `PermissionError(13)`, which the API
turns into 403 "This session expired". In an isolated loop of the six-thread draft (a script, 100 rounds on the unfixed code):
8 rounds failed, 6 in `os.replace` and 2 in `read_bytes`. The fix: `store._retry_busy`, used by the local branches of `put`
(replace), `get`, `delete` and `delete_many`; it retries `PermissionError` up to 40 times with a few milliseconds between tries,
only on Windows (`os.name == "nt"`), and re-raises after the last try or for any other error; nothing changes on Linux or against
the bucket. After it: the same loop, 400 rounds, 0 failures and 0 `PermissionError`; **the `fix` suite, 30 serial runs, 30 green
(53 of 53 checks each)**; the full harness is green (the table of section 1). A thread stress test of the store that fails on the
unfixed code in every round (20 of 20) and passes on the fixed code in every round (20 of 20) is part of `v3wp0` (section 7a of the
suite). **Rule for later packages: a suite that goes red once is investigated, never rerun until green; a flake found is fixed or
listed here.**

**Fixed minors:** `cpu_probe` with a whole number too big for a float as the baseline answered 500 and now 400
(`math.isfinite(10 ** 400)` raised `OverflowError`); `suites/run_all.sh` called with fewer than three arguments expanded
`rm -f "$OUT"/*` to `/*` and now refuses with a usage message (exit 2) and clears only plain files of a non-trivial folder;
`scripts/cpu_probe.py` followed a 301, 302 or 303 on its POST and sent the admin key to the Location host, now no redirect is
followed (the 3xx is reported); a duplicate `shutil.copy` in `test_fixer.py` is gone (the commit that moved the suites says
nothing else was changed); a run without the private fixtures (a fresh clone) exited 0 with the two admin suites SKIPPED, it now
exits 1 and says `INCOMPLETE` unless `--allow-skipped` or `SNAPEYES_ALLOW_SKIPPED=1` says the skip is on purpose; the cold-mode
import timings of the probe always read "already loaded" in the admin function (which imports numpy and Pillow at start), so the
probe now also times the two imports in a fresh child interpreter (`imports_fresh_interpreter`); the probe's memory note read
"near 350 MB" and the measured working set is 420 MB (the commit charge reads 920 MB, not resident memory);
`bundle_report.mjs --check` treated `.vercelignore` as authoritative, it now judges the folders that would ride into a function
without it (Git deployments may not honour it: V2); `.vercelignore` repeats the entries of `.gitignore` (the CLI may read it
instead of `.gitignore`: not verified); `run_ts_tests.mjs` counted a `node:test` file as one pass whatever it held, it now prints
one line per test, and a file with no test, a skipped test or a failing one is a FAIL; `bundle_report.mjs` no longer reads a
missing Python interpreter as a report; the comment in `requirements.txt` named four wheels for Python 3.14 where `requests` is
pure Python; the file breakdown in section 3 is 15.4 plus 1.1 MiB (it read 16 plus 1.4).

**Not fixed, and why (all recorded as unverified in sections 3 to 6, each with its closing step):** V1 to V4 and VE3 (real function
sizes, `excludeFiles` semantics, the slow factor, memory, Fluid, duration, `/tmp`, the Python version of a real build log) need a
Preview deployment and the admin secret, and this machine has no Vercel access. Nothing else of the review is open.

## 8. The plates land (WP4, 2026-10-05): V1 and V2 with the plates in

What changed in the bundle: `api/_assets/plates` (the 1K files of 169 usable plates), `api/_assets/atlas` (two sprite atlases), the baked
registry `api/_lib/plates_registry.py` and the foundation modules of `api/_lib/styles/` (core, layouts, text, plates, atlas, costs,
selfcheck, 0.3 MiB of source). `vercel.json` now has one entry per function (11), and the seven that never render exclude the plates and
atlases. All figures from `node scripts/bundle_report.mjs --pypi` (Linux wheels as in section 3), MiB = 2^20 bytes:

| Function | Files of the repository | Of which plates and atlases | Python packages (Linux wheels) | Estimate | Room under 235 |
|---|---:|---:|---:|---:|---:|
| compose, master_compose, order, admin (4) | 60.8 | 43.8 (plates 37.0, atlases 6.8) | 125.6 | **186.4** | 48.6 |
| the other seven | 17.0 | 0 | 125.6 | **142.6** | 92.4 |

The 60.8 MiB are `api/_assets/plates` 37.0, `bg` 10.5 (the legacy backgrounds, gone at WP19: 175.9 MiB then), `atlas` 6.8, `models` 4.6,
`_lib` 1.3, `fonts` 0.3, handlers 0.2. The registry's recorded dependency size is 126 MiB (an estimate until V1 reads a Preview);
`check_styles` item 9 fails the build when files plus that figure pass 235 MiB for a rendering function.

The library, by family (plates / usable / 1K MiB of the usable ones / 4K MiB of the plates an engine can fetch):

| Family | Plates | Usable | 1K MiB | 4K MiB | Note |
|---|---:|---:|---:|---:|---|
| P-SN-CLOUD | 47 | 47 | 9.52 | 237.64 | 4K only for the Powder Burst filter (black 30, 45, 60, a direction, void 0.40 or more) |
| P-SP-CROWN | 60 | 60 | 6.36 | 59.68 | Splash and Elements |
| P-DN-SPIRAL | 16 | 10 | 1.80 | 72.48 | the crisp ones (Vortex, void 0.20 or more) |
| P-EL-FLAME | 14 | 6 | 0.28 | 3.43 | the v3 flames; Elements stays in the laboratory |
| P-UV-DUST, P-UV-MILKY | 14 | 11 | 4.96 | 56.71 | Deep Field and Starfield (laboratory); three milky ways vetoed |
| P-CX-JET, P-CX-RIVER | 70 | 35 | 14.07 | 0 | collision plates are used at 1K only |
| **all** | **221** | **169** | **36.99** | **429.95** | |

Storage for V6: the first release's three families (CLOUD, CROWN, SPIRAL) are **369.8 MiB** of 4K files (`upload_plates.py --release1`, a dry run
prints it); all families together 430 MiB. The plan's estimate was 415 MB for release 1 and 675 MB as an upper bound: the engines' own filters
decide which CLOUD plates are ever fetched at 4K, so the figure is lower. The project's real storage plan is still unread (V6).

V2, what the explicit entries settle and what they do not: with one `functions` entry per file, no file matches two patterns, so the question
of how overlapping globs resolve no longer arises (`check_styles` item 10 refuses a glob). Whether `excludeFiles` reaches the installed
packages (so that nine functions could drop onnxruntime, about 49 MiB each) and whether it reads `api/_assets/plates/**` as a path from the
project root are still unverified: a Preview's function list answers both, and the four rendering functions' sizes against the table above
are how the plates exclusion is confirmed (the seven others should be 43.8 MiB smaller).

## 9. The singles family (WP5A, 2026-10-05): time and memory of the six designs

Measured on this machine (the CPU yardstick of `scripts/cpu_probe.py` is 1.373 s against the planning spike's 1.464 s, so this core is 0.94 of the
spike's), Python 3.14.3, numpy 2.4.4, Pillow 12.2.0, one thread, synthetic 1024 px eyes (`scripts/styles_tests/synth_iris.py`), a fresh process per
design and the best of three. "Spike" is `costs.PREVIEW` (the planning spike's table) times 0.94, the figure the same code was expected to give here.
The scratch prototype's own code, timed the same way on the same machine the same hour, is the third column of each pair: the port is
byte-identical to it, so the difference between the port and the table is the machine and the eyes, not the port.

1024 px preview (seconds): cold = the first preview of a process (imports, plate and atlas loads), same eye = the design alone, new eye = a second eye.

| Design | Cold: port / scratch / spike x 0.94 | Same eye: port / scratch / spike | New eye: port / scratch / spike |
|---|---|---|---|
| Clean Iris | 0.68 / 0.80 / 0.68 | 0.08 / 0.09 / 0.05 | 0.70 / 0.79 / 0.54 |
| Powder Burst | 1.91 / 2.08 / 1.61 | 1.06 / 1.16 / 0.83 | 1.70 / 1.79 / 1.31 |
| Splash | 1.41 / 1.46 / 1.09 | 0.71 / 0.78 / 0.48 | 1.31 / 1.45 / 0.88 |
| Elements | 1.78 / 1.82 / 1.42 | 1.05 / 1.15 / 0.78 | 1.70 / 1.74 / 1.26 |
| Radiance | 1.05 / 1.14 / 1.00 | 0.46 / 0.54 / 0.38 | 1.07 / 1.16 / 0.83 |
| Celestial Gold (variant A) | 0.96 / 1.28 (the old design) / 1.04 | 0.33 / 0.61 (old) / 0.40 | 1.00 / 1.30 (old) / 0.89 |

(Correction below: a repeat that alternates the two shows the port and the scratch equal, not the port faster. The Gold row's scratch column is the old design.) Against the spike's table the cold previews are +0 percent (Clean), +19 (Powder),
+29 (Splash), +26 (Elements), +5 (Radiance), -8 (Gold); the acceptance line of the work package ("within 10 percent of the table") is therefore met
for Clean, Radiance and Gold and not for Powder Burst, Splash and Elements, by the same margin that the unchanged scratch code misses it on this
machine. The cause is not in the port; V3 and V11 (WP17a) measure the real instance, and the cost table is not touched by this package.

4096 px master from a 1024 px eye (the real masters start from a 4096 px eye and add its grade, 2 to 3 seconds more), seconds of one process and
peak working set in MiB (Windows; the table's cold peaks in brackets): Clean 3.0 s, 554 (620); Radiance 6.7 s, 836 (900); Celestial Gold 6.9 s, 565
(734: the table is the old design); Powder Burst 10.5 s, 659 (729); Splash 11.7 s, 729 (801); Elements 16.2 s, 815 (890). Every peak is under the
table's, so `costs.est_mb` is a safe bound for the family. The row of Celestial Gold in `costs.MASTER` (12.4 s, 734 MB) is the old design's: variant A
is cheaper, and the row is left as it is (conservative) until V11 measures a real 4096 px master of it.

The golden replay (`v3single`): 54 pictures at 512 and 1024 px (every design, three eye classes, three canvases, the text lockup) and 9 at 4096 px (the non-plate designs) are counted; with the scratch tree the 9
plate-style pictures at 4096 px, 24 real-eye pictures and the check of the port's edits run as LOCAL lines (all equal). `v3single` takes about 2.5 minutes alone.

Correction (review of WP5A, 2026-10-05). The first table said the port is up to 16 percent faster than the scratch code. The review could not reproduce it
(Powder Burst cold 2.2 s for both, Splash 1.6 s for both, in fresh processes), and a repeat that alternates the two in fresh processes (one design per process,
the port and the scratch swapping places each round, five rounds, this machine, one thread, a synthetic 1024 px eye, no other heavy process; best of five and
median, seconds, cold = the first preview of a process) gives the same speed within noise:

| Design | Cold, best (median): port | scratch |
|---|---|---|
| Clean Iris | 0.74 (0.75) | 0.74 (0.77) |
| Powder Burst | 2.00 (2.04) | 1.99 (2.08) |
| Splash | 1.38 (1.40) | 1.39 (1.41) |
| Elements | 1.74 (1.82) | 1.76 (1.79) |
| Radiance | 1.11 (1.15) | 1.16 (1.20) |
| Celestial Gold (variant A) | 1.01 (1.04) | (the scratch's own Gold is the old design) |

The port is the same code, so the same speed is the expected result. Why the first table showed the port faster is not established (most likely the two were timed one
after the other while the load of the machine changed); the repeat is the figure to use. Against the spike's table (x 0.94, the figures of the first table) this repeat gives Powder Burst +24 percent, Splash +27, Elements +23, Radiance +11,
Clean +9, Celestial Gold -3: the acceptance line "within 10 percent of the table" is met for Clean and Gold and not for Powder Burst, Splash, Elements and (by one
point, where the first table said +5) Radiance, by the same margin that the unchanged scratch code shows. Nothing in the cost table moved.


## 10. The master plan (WP6a, 2026-10-05): what a real 4096 px step takes, and the suite

**The steps measured through the step runner** (`steps.lab_run`, the admin action `lab_steps` without the HTTP: one fresh Python process per design, so the memory is the design's
own; this machine, Windows 11, Python 3.14.3, numpy 2.4.4, Pillow 12.2.0, one thread, a synthetic blue eye of 4096 px as the stored master, the customer's names and a date drawn,
`STYLE_SLOW_CPU` unset; nothing else heavy of mine running). `need` and `est` are what the plan says (the cost table at the factor 1.6, with the 15 percent Linux allowance on the
memory), `table` the spike's own cold figures for the design:

| Design | wall time | CPU | memory increase (VmRSS) | plan need / est | table (cold CPU, cold peak) |
|---|---:|---:|---:|---:|---|
| Clean Iris | 7.0 s | 6.7 s | +486 MB | 16.4 s / 713 MB | 6.3 s, 620 MB |
| Radiance | 10.7 s | 10.3 s | +807 MB | 21.2 s / 1035 MB | 9.3 s, 900 MB |
| Celestial Gold (variant A) | 10.2 s | 9.8 s | +460 MB | 26.1 s / 845 MB | 12.4 s, 734 MB (the old design's row) |

Every self check of the three passed (T1, T6, T7, T12), each picture is one JPEG q95 4:4:4 of 4096 x 4096. The wall time includes decoding the 4096 px master, the grade (the
largest part, 4.7 s of Clean's 6.6 s), the finish, the checks and the encode, and is a fraction of the plan's need on every design, as the table's own model says (the need is
the factor 1.6 times the CPU, plus the cold start the real instance pays and this machine does not). The `hwm_mb` of those runs (about 1.84 GB) is the process's high-water mark
and includes the test script's own making of the 4096 px synthetic master: this is why the events and records carry the INCREASE of the resident size over the step
(`peak_mb`) and the instance's high-water mark only beside it, labelled as that. Powder Burst, Splash and Elements are not measured here: their 4K plates are not in a local
store (the release-1 upload needs the owner's service key). Celestial Gold's cost row is still the old design's (12.4 s, 734 MB): variant A measures less (10.2 s, +460 MB), so the
row stays a safe bound until V11 reads a real master on the instance.

**What the plan costs a legacy order**: the step runner adds a few small storage calls to a composition (the plan, the claim, the try record twice, the done record, three reads
for the order's state), about a second on a real bucket; the artwork's file and digest are those of `master_compose` as before (the suite `v3steps` holds the real legacy composer
to the old digest rule on a real 4096 px master). The watchdog costs one self-call of at most `KICK_READ` (1.5 s) at the start of a step, and two relay invocations that wait
40 s each and then find the order ready (they do no work: a relay that wakes to a finished order stops after four reads).

**The suite** `v3steps` (136 checks, about 1 minute 50 seconds alone) drives the real handlers over HTTP with the image model stubbed (the fake master writes a procedural iris
of 4096 px for the single styles) and scripted executors for the state machine. It joins the list in `suites/suites.list` and `baseline.json` (v3steps 136); the page-code
count went from 20 to 29 (the order page's driver, `suites/ts/order_driver.test.ts`). Existing checks changed, each with its reason (in the commit): the two admin suites expect
one more master event for a composed order (the step's `art` event beside the legacy composer's own `compose` event), `v3single` no longer expects `master_compose` to answer 400
for a style of the v3 engine (the master plan makes it: with no stored eye it answers 409 `eyes_not_ready`), and one label of `v3reg`.

**Full set** on the work tree after the last code change: 28 of 28 green, every count equal to the baseline (r2 105, r3 48, r4 69, r5 54, fix 53, admin 186, pay 120, advance 66,
refund 7, preview 60, review 11, fixmk 36, markets 58, au 70, payrev 19, fixer 43, oldpay 120, oldadv 66, oldadmin 186, exp 349, ts 29, v3wp0 93, v3reg 172, v3gate 97, v3core 86,
v3plates 108, v3single 86, v3steps 136).

**Review fix of WP6a (a render that waits behind another heavy render).** A step that found the instance's CPU or memory held by another render was answered `busy_retry` and asked again
at once, so a second paid order spent its ten busy hops in about 4 to 25 s (the guard's wait is 2 s a hop) and stopped `busy` with a note that blames the image model, while the first
order's 26 to 46 s step was still drawing. It is now answered 503 `room_retry` with `retry_after` = the holder's remaining estimate (5 to 40 s); the chain and the order page wait that long.
`v3steps` 142 (six checks added: the guard's `eta_s`, the bounds of the back-off, the chain's decision, two paid orders at once end to end with the gaps between the refusals asserted),
`ts` 31 (two: the page waits the server's time and stops `busy` after twelve waits); five existing `v3steps` checks that expected `busy_retry` from a full guard expect `room_retry`.
Measured with the real constants (guard wait 2 s, back-off 5 to 40 s): a first order that holds the slot 22 s (its plan says 16.4 s), the second order's two refusals waited 13 s and
5 s and it was ready at 25.4 s with no note. Full set after the fix: 28 of 28 green, every count the baseline's (`ts` 31, `v3steps` 142, the rest as above).

**A flake of the harness under load, recorded and not hidden.** In one full run (the first, with three suites in parallel and another agent's node processes on the machine) the
`pay` suite died at its third checkout with `ConnectTimeout` to its own loopback API server (60 s), after 87 of its 120 checks, with no failing check; `pay` alone passes 120 of 120
(and did in three other runs, among them the next full run). The call that timed out is `/api/checkout`, which none of this package's code touches (it is the same kind of death
the WP5A review saw as `ConnectionAbortedError` with three suites in parallel). It is a property of the harness's one-thread-per-request test server on a loaded Windows machine,
not of the code under test; if it recurs on a quiet machine it is a defect to be chased, not a flake.
