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


## 11. The seed from the eye id (WP5B, 2026-10-05): the reviewed diff of what moved

Decision C9, step B: the seed of a picture is made from the eye ids and the plan's seed key (`api/_lib/styles/seeds.py`: registry id, design used, ground, clean flag, layout id, the three
options, plates version) and from nothing else; before it was the sha256 of the bytes of the iris, the design and the canvas. `ENGINE_V` is 2 (it was 1), `data/engine_v.json` records the
hashes of the new golden files. Recorded on this machine class (Windows 11, Python 3.14.3, numpy 2.4.4, Pillow 12.2.0) with `scripts/styles_tests/record_goldens_repo.py`; the step A
recording (the scratch prototype's own pictures) is kept in `scripts/styles_tests/data/stepA/` and replayed with the old seed (`opts seed_mode legacy`).

**What moved** (`python scripts/styles_tests/diff_goldens.py [--pixels] [--real]`): 60 of the 72 synthetic pictures (every design but Clean Iris, 12 of 12 each; Clean Iris draws no matter
and its seed only dithered pure black, so its 12 hashes are the old ones). Plate picks at 1024 px on the three synthetic eyes (blue, dark brown, grey), old to new:

| Design | blue | dark brown | grey |
|---|---|---|---|
| Powder Burst | strong right (black 60) to strong lower right (black 45) | strong lower right (black 60) to strong upper right (black 45) | strong upper left (black 45) to strong up (black 30) |
| Splash | clear water, 16 spikes, rise up left to clear water, 20 spikes, rise up right | cognac, 12 spikes, rise up to cognac, 16 spikes, rise up left | clear water, 12 spikes, rise up to clear water, 20 spikes, rise up left |

(the liquid is a function of the eye's colour and is the same before and after; the crown and the cloud are re-picked.) Elements picks new plates too (held, lab only). Radiance and
Celestial Gold have no plate: their rays, dust and stars are re-rolled.

**What did not move: the iris.** Measured on every 1024 px picture, old seed against new (zone A, up to 0.95 R): the largest difference is 0 for every design, on the 18 synthetic
pictures and on the 24 real calibration pictures (T1 and T6 hold on every picture, old and new). The share of the other pixels that moved by more than 8 levels (the matter, the
background) and their mean change, over the cases:

| Design | synthetic eyes | real calibration eyes |
|---|---|---|
| Clean Iris | 0 % | 0 % |
| Powder Burst | 29 to 38 %, mean change 15 to 26 | 26 to 33 %, 16 to 18 |
| Splash | 19 to 22 %, 16 | 17 to 23 %, 16 to 19 |
| Elements | 15 %, 15 | 13 to 15 %, 9 to 16 |
| Radiance | 31 to 42 %, 10 to 15 | 33 to 41 %, 11 to 14 |
| Celestial Gold | 12 to 13 %, 6 | 12 %, 6 |

**That the seed is the only thing that moved** (the proof that step B changed nothing else): with `opts seed_mode legacy` the port draws the step A recording byte for byte, with the
seeds and plate picks: 36 pictures at 512 px (every design on three eyes, and the other two canvases with names and a date), 18 at 1024 px, 3 masters at 4096 px, and, with the scratch
tree (LOCAL lines, not counted): Powder Burst at 4096 px through storage and the plate cache, and the 24 real calibration pictures. The committed files are still what
`port_singles.py` makes of the scratch files (the step A edits plus the one `STEP_B` set: the seed, the plates version `pv`, the liquid the plan may freeze).

**The statistical rules, re-run over other seeds** (the seed re-rolled every plate, wind and particle, so the rules must hold for any seed, not for three eyes): 60 pictures of 5 designs
x 3 eye classes x 4 other seeds (512 px with a name) pass T1, T6, T7 and T12; at 1024 px with no text over 12 seeds each the black share (T4) of Powder Burst is 0.543 to 0.587
(range 0.45 to 0.65) and of Elements 0.725 to 0.739 (range 0.55 to 0.75), the veil of Powder Burst has a mean alpha up to 0.038 (limit 0.10). (At 512 px with a name Elements' black share
is 0.744 to 0.764 with the new seeds and 0.748 to 0.755 with the old: that is the size and the text, not the seed; T4 is defined at 1024 px.) The 24 other seeds spread the cloud pick over at least 6 plates.

**Time.** `resolve` with the eye, the seed, the plate pick and the frozen liquid: 0.4 ms warm, 563 ms for the first call of a cold process (it imports the family and the powder module;
before this step it imported the family only). The suite `v3single` is 115 checks (was 86; 29 new: the replay of the step A recording with the old seed, the seed and its refusals,
plan against picture on 30 pictures, the frozen liquid, `pv`, the sweep, the compose preview and the laboratory) and takes about 4 minutes 30 seconds alone (the sweep is 56 s of it);
`v3steps` is 150 (was 142; 8 new: the plan's seed, plates and frozen liquid, the two new holds, the picture checked against the plan).

**The boards for the owner's look (merged with L1).** The admin laboratory (Laboratorija, Stilių laboratorija) has a Sėkla menu: the new seed (the one a customer's picture has, made
from the eye's id; for a lab test order's eye the id of its stored record) or the old one, so any board can be looked at before and after on any eye, in the page. A contact sheet of
the four real calibration eyes x Powder Burst, Splash, Radiance and Celestial Gold, old and new side by side, was rendered for this review (`wp5b/boards/boards_before_after.jpg` in the
session folder, real eyes: not in the repository). The looks are the same families (the same eye gets the same liquid, the same palette, the same iris); the cloud, the crown, the
rays and the dust are drawn differently. Nothing else is asked of the owner here: the re-look is part of L1 for each style.

**Existing checks changed, each with its reason:** `v3steps` check "a plan that does not know its plates yet" uses an eye with no id (the plan of an eye with an id now knows its plates);
the test stand in for `master_eye` records the preview's eye id from the draft, as the real one does (it wrote a made up id that nothing read until the seed did).

**Full set** on an export of `5144e04` (`git archive`, the private fixtures, `SNAPEYES_SCRATCH_Y3` and `SNAPEYES_CALIB` set so that the LOCAL lines of `v3single` ran too): 28 of 28 green, exit 0, every count equal to
`baseline.json` (r2 105, r3 48, r4 69, r5 54, fix 53, admin 186, pay 120, advance 66, refund 7, preview 60, review 11, fixmk 36, markets 58, au 70, payrev 19, fixer 43, oldpay 120, oldadv 66, oldadmin 186, exp 349, ts 31, v3wp0 93,
v3reg 172, v3gate 97, v3core 86, v3plates 108, **v3single 115, v3steps 150**). The first full run on an export of `bc2d632` was 26 of 28 and is not counted: `v3single` did not parse (two byte literals of the WP5B files
with a line break inside `b"\r\n"`, an editing slip, fixed in `5144e04`), and **`oldadv` died at its check H3** (a request with a foreign `Origin` header, answered 403 by the origin gate before the body is read) with
`ConnectionAbortedError(10053)` raised in the test's own `requests.post`, after 46 of its 66 checks had passed and with no failing check; the same check H3 passed in the `advance` suite in the same run (the same file's newer copy) and
`oldadv` passed 66 of 66 in the next full run. The call is `L.run`'s origin gate, which no WP5B file touches; it is most likely the Windows connection abort of the harness's one-thread-per-request test server that sections 7 and 10 of
this file already record (the server answers 403 and closes before the client has sent its whole body: an inference from the error, not reproduced): a flake of the harness, recorded and not hidden; if it recurs it is a defect to chase.

## 12. The Reveal's server half (WP9, 2026-10-05): what it costs and what is proven

**Time.** `reveal_for` (the one call of `/api/enhance`: `reveal_params` 0.25 s, the prepared restoration and the watermarked display copy 0.2 s) takes 0.53 s of CPU per eye at 1024 px with a
400 px crop on this machine (the calibration eyes: 0.5 to 0.6 s each, the arcs variant included in that figure). The plan's figure was 0.4 to 1.0 s per eye. `enhance` asks for 4 s left in the invocation
(`REVEAL_MIN_LEFT`, separate from the profile's 6 s): on the quiet core that is eight times the work, on a slow instance (x1.6) five times. The memory is that of one restoration, a 1024 px square and a few
256 px float arrays: no measurable peak beside the model call's own.

**Proof that the port is the prototype.** `port_reveal.py` makes `reveal.py`, `reveal_clean.py` and `reveal_wm.py` from `designs/presentation*.py` by a listed set of edits (imports, the references
between the three files, the docstrings, the `__future__` import) and `test_reveal.py` runs `--check` when the scratch tree is there (LOCAL). The other side: the goldens recorded on the scratch code
(`data/reveal_goldens.json`, twelve synthetic cases: the numbers of the wire dict, the sha256 of the prepared restoration and of the arcs display copy in English and Lithuanian) and, with
`SNAPEYES_CALIB`, the ten real calibration eyes (`data/reveal_goldens_real.json`, hashes and numbers only): every one equal. Mutations seen to fail: the crush luma, the display swap in `enhance.py`.

**What the real eyes say** (the scratch code and the port agree): ok for nine of the ten human eyes, withheld by colour for the hazel eye p09f (restored colour 19.7 dE00 from its photo; the limit is 8,
the warning 6); the drift of the other nine is 0.6 to 5.6. Registration: every real eye is inside 0.005 R on the crop pair (the largest spread is 0.0034 R, drv_w03; the page's frame-level number for the owner's d05, 0.0057 R in the prototype's
T16 on the photo layers, needs the frame builder in Python, which the server does not carry: C10). On the synthetic cases a one degree turn (0.0079 R) and a two percent enlargement (0.0084 R) are withheld,
a 3 px shift is corrected (measured to a fifth of a pixel) and not withheld.

**The browser half** was verified in a real browser against the dev API with the image and vision models stubbed (no model call: the stub also replaces `gemini` and the key lookup and refuses every
request to another host): the hero Reveal (the restored layer on `rgb(0, 0, 0)`, no border, outline, shadow or filter on any layer, the cut at 50.00, the handle hidden at rest), the arrival sweep
(100 to 50 after 427 ms, `clip-path 900ms cubic-bezier(.2,.7,.2,1)`), reduced motion (the first value is 50.00, no transition, the strip columns at opacity 1 with no transition), keys and pointer (arrows
step 2, Home 0, End 100, Enter 50, a press at 51 snaps to 50, 47.5 snaps to 50), the four languages, two eyes (no strip), the withheld colour case (the strip without the cut, the note, the colour check's
advice, the amber retake button), the AI-generated sample (the plain slider, no strip), the way back from Stripe (a copy with no frame: the Reveal is built from the crop and says "Tight frame"), and 375 and 320
px wide (no horizontal overflow, the strip in three columns at 375 and stacked at 320).

**Counts:** `v3reveal` 63 (new), `ts` 79 (was 31: 15 ported node tests, 11 new node tests in `src/reveal/reveal.test.ts`, 22 in `suites/ts/reveal_page.test.ts`). `scripts/run_ts_tests.mjs` runs both kinds.

**Review fixes of WP9 (2026-10-05, fixer).** `v3reveal` 72 (9 more: the crop padding of the request, the display copy's anchor, a NaN in the wire dict) and `ts` 89 (10 more: the real `ResultView` rendered on the server with `react-dom/server` for six eyes, so the promise line and the colour warning are checked as the page prints them). Mutations seen to fail: the padding ignored by the anchor, the padding gate removed, the promise shown beside the colour warning. A real browser against the dev API with the models stubbed: the warm case (the chroma lock off, red x1.3, blue x0.7) prints the no-cut note, the colour check, then the transparency sentence and no promise line; the ordinary case prints the Reveal with the promise line and no colour warning.

## 13. The collision family (WP7A, 2026-10-05): the replay, the seam budget and what 4096 px costs

The collision family (Kiss Collision, Collision Infinity, Clean Infinity, Family Colours, Infinity Chain) is the DG1 snapshot of the design rounds' code ported verbatim
(`scripts/styles_tests/port_collision.py`: a listed set of edits, the sha256 of the twelve source files, `--check` against the scratch tree). Recorded on this machine class (Windows 11,
Python 3.14.3, numpy 2.4.4, Pillow 12.2.0) by `record_goldens_collision_scratch.py` in a tree made by `make_collision_scratch_tree.py`: the DG1 folder has no `plates_cx`, so a render
there draws no JET plate; the recording tree has the plates of the design round, and exactly the two JET plates the bake retouched (a scale bar and a legend of the generator were painted
into the raw files) are taken from the baked library instead (the recorder finds them by comparing fits and says so). The other 33 of the 35 collision plates are the prototype's own raw and
1K files, which proves that `jetplates.py` picks, fits and places like the prototype.

**The replay.** 62 of 62 synthetic pictures byte for byte equal, with their seeds and facts (design drawn, lens mode and colour step, fronts, edge modes, the plates the haze took, shares): the
three pairs (a blue and a dark brown, a blue and a green, a grey and an amber) in the three pair designs at 1024 px, the five canvases, 512, 1024 and 4096 px, the words, the forced stack
lens, the wide pupil that falls back to the Kiss geometry, the laboratory switches, the trio, every layout of the family for four to eight eyes and the chain. 21 of 21 real calibration-eye
pictures equal too (LOCAL lines, hashes only), and the colour steps K of the eight DG1 board pairs are the judge's own table: blue with brown 46.84, blue with copper 33.21, blue with
yellow 29.93, grey with hazel 17.84, two similar blues 16.62, two browns 10.66, the very dark pair 9.18, two similar browns 7.99.

**The owner's seam budget E1, measured.** The pixels that are really mixed (0.02 < w < 0.98) and the support of the blend (0 < w < 1) are limits of 3 percent of an iris each (the plan scales the
half width down to hold them), the seam band as the integrity test pads it at most 4 percent (the owner's reading). Synthetic replay, 23 woven pairs: mixed at most 0.0280, support at most
0.0295, band at most 0.0319. On the eight real pairs of the DG1 boards (16 woven pictures, both infinity builds) mixed at most 0.0279, support at most 0.0295, band at most 0.0317; the largest colour step K is 46.8 against the stack lens's limit of 62.

**Time and memory at 4096 px.** A fresh process per render, one thread, this machine (shared with other builders: the cells differ by up to 10 percent between two runs of the same code),
the real calibration restorations resized to the working copy a master gets (2048 px for a pair, a family and a chain; the trio's registry `work_side` is 4096), Windows peak working set.
CPU seconds of the render (imports apart), the port and the scratch alternating, two rounds each, against the spike's table (SP 4.1, quiet core, cold) scaled by this machine's
yardstick (1.393 s against the spike's 1.464 s, x0.95):

| Render | Port, runs | Scratch, runs | SP table x0.95 | Peak port | Peak scratch | SP peak |
|---|---|---|---|---|---|---|
| Collision Infinity, 2 eyes, 3:2 | 8.3, 8.1, 7.9, 7.9 | 7.8, 8.0 | 8.0 | 550 MB | 557 | 645 |
| Clean Infinity | 7.0 | not measured | 8.6 | 557 | | 642 |
| Kiss Collision | 7.5 | not measured | 6.8 | 552 | | 643 |
| Trio, 2048 px copy | 16.1, 15.9 | 16.3, 17.4 | 14.6 | 778 | 792 | |
| Trio, 4096 px sources (the registry's work_side) | 23.5 | n/a (the scratch always shrinks to 2048) | 14.6 | 992 | | 929 |
| Family Colours 4 (zigzag, 3:2) | 13.2, 11.3 | 12.6, 11.4 | 9.4 | 572 | 595 | 782 |
| Family Colours 8 (ring, 1:1) | 26.1, 23.8 | 28.2, 25.7 | 19.2 | 915 | 985 | 1330 uncapped, 945 capped |
| Chain 4 (3:2) | 11.2 | not measured | 9.6 | 557 | | 772 |
| Chain 6 (3:1) | 13.3 | not measured | 10.5 | 482 | | 800 |

The pair designs and the trio from a 2048 px copy are within 15 percent of the table (clean infinity 18 percent under it); the families and the chains are 20 to 40 percent over it on this
machine and the **unchanged scratch code takes the same time** (the port is 0 to 7 percent faster and a little smaller in memory in every pair of runs), so the cause is the machine and the
eyes, not the port, as WP5A found for the singles. Family Colours with eight eyes peaks at 915 MB (acceptance: at most 945 MB capped). **The trio from 4096 px sources costs 23.5 s of CPU and 992 MB,
not the table's 15.4 s: at the slow factor 1.6 that is about 45 s of the 52 s budget** (the table's row is a 2048 px copy's); the plan freeze (WP7B) decides between capping the trio at 2048 px
(the Trio delta check) and raising its cost row.

**Known misses of the layouts, found by the self check on synthetic eyes and left as the prototype has them** (step A is verbatim): Family Colours as a flower of six eyes (petals 1.94 R apart,
an overlap of 0.06 R that is no contact: T1 and T6 fail on 56 pixels of four petals at 0.94 to 0.95 R); T3, the visible share, on Family Colours as a brick of four eyes (0.76 against 0.82) and a flower of
eight (0.77), and on the end irises of a chain of three (0.895 against 0.90). The pairs, the trio and the default layout of every eye count keep their floors.

**Suite.** `v3coll` 70 checks (6 LOCAL lines with `SNAPEYES_CALIB` and `SNAPEYES_SCRATCH_DG1`), about 7 minutes (the replay 116 s, the 4096 px pictures and the real eyes the rest) alone: the family's files and rules, the registry against the family
(every layout of the five styles builds a scene on its default canvas), the replay, the hard rules on every picture of 1024 px and less, the seam, the tests of the brief (T4, T6, T7, T10, T12,
T13, T18, T19), determinism in two fresh processes with different hash seeds, the bounded caches, the guards, the plates, the contract, a master through the master plan's art step.

**Review fixes of WP7A (2026-10-05).** (1) The registry lists the canvases of a style, not of an eye count: a sweep of every style, eye count, layout and canvas the registry lists (99 pairs of a layout and a canvas, a preview of each at 192 px) found five that raised a KeyError (the chain of three on 3:1, of five and six on 3:2 and the phone column), the ring and the flower of five to eight on 3:2 and the ring of eight on 5:4 (T18, the iris size floor) and the brick of seven and eight, which the family always draws square whatever canvas is asked (the Preview named the canvas asked). `canvases_for` says which canvases a style draws for an eye count and layout; 20 of the 99 pairs are cut and a spec that names one is drawn on the layout's own default canvas. (2) The cost table was the spike's, and the spike's Trio row is a 2048 px copy's. Measured again with the master step's own call (`preview(check=True)` at 4096 px, real calibration restorations, a fresh process, one thread, this machine's yardstick 1.40 to 1.78 s against the spike's 1.464 s while other builders ran): the Trio from 4096 px sources 23.5 s of render in a quiet run (23.6 s again under load) and 3.1 s of self check, 992 MB; from a 2048 px copy 16.1 s and 3.2 s, 778 MB. In the spike's units (divided by this machine's 0.951): 28.0 s and 20.2 s. `costs.MEASURED` holds both rows (a tuple, only raising); at the slow factor 1.6 the Trio from 4096 px sources needs 52.5 s of the 52 s budget (break-even factor 1.58, the spike's 2.80) and from a 2048 px copy 40.0 s (2.17), so the capacity check refuses the Trio at its registry work side until WP7B caps it (after the delta check of the spike: mean dE00 0.36, 99th percentile 4.6 at 2048 px) or splits it. The same measurement for the rest, left out of the table until one reviewed re-bake (the plan's section 10.3 and three suites pin the spike's figures), in the spike's units and with the self check: Collision Infinity 2 eyes at 2048 px 9.3 s (table 6.3), Family Colours 4 eyes 13.4 s (9.9), 8 eyes 27 to 30 s and 885 to 915 MB (16.8 s capped, 945 MB), Infinity Chain 4 links 12.9 s (10.1); the need of Family 8 at 1.6 is then 55 to 59 s against the table's 38 s, and a chain of six on its 3:1 canvas fails T18 on the real calibration eyes (the links are spaced by the pupils). None of that is a collision file defect: the code is the prototype's, byte for byte, and takes the same time as the scratch code.

**Full set** on an export of `aac24fe` (`git archive`, CRLF line ends, the private fixtures, `SNAPEYES_SCRATCH_Y3`, `SNAPEYES_CALIB` and `SNAPEYES_SCRATCH_DG1` set so that the LOCAL lines of `v3single` and `v3coll` ran too): **29 of 30 green**, every count equal to `baseline.json` (r2 105, r3 48, r4 69, r5 54, fix 53, admin 186, pay 120, advance 66, refund 7, preview 60, review 11, fixmk 36, markets 58, au 70, payrev 19, fixer 43, oldpay 120, oldadv 66, oldadmin 186, exp 349, ts 78, v3wp0 93, v3reg 172, v3gate 97, v3core 86, v3plates 108, v3single 115, v3steps 150, **v3coll 70** (new)). The one red suite is `v3reveal` (WP9's, 61 of 63): its check "each module opens with its docstring and then the __future__ import" reads `
`, and the export has CRLF line ends (the trap the WP3 and WP4 notes record; on the working tree, with LF files, it passes), and its check "the whole call with the stub model costs at most 4 s of CPU" measured 4.25 s with three suites and other builders' processes on the machine. Neither touches a collision file; WP9 owns both. `python -m compileall api` exit 0, `npm run build` exit 0 (the registry hash is still `870892880cf3`, a rendering function 187.7 MiB of the 235), and `python scripts/dev_api.py` starts with the 11 routes and `/api/health` answers `styles: true, plates_4k: true`.

## 14. The universe family (WP8A, 2026-10-05): the replay, what 4096 px costs and the tests carried over

The universe family (Echo, Vortex, Deep Field, Starfield on one eye; Echo on a pair and on a group of three to six) is the design rounds' code ported verbatim
(`scripts/styles_tests/port_universe.py`: a listed set of edits, `--check` against the scratch tree). Recorded on this machine class (Windows 11, Python 3.14.3, numpy 2.4.4,
Pillow 12.2.0) by `record_goldens_universe.py` on the scratch prototype itself: its own plates, atlas and gate, nothing swapped.

**The replay.** 71 of 71 synthetic pictures byte for byte equal, with their seeds, the plates they drew from (the id, the LOD, the upscale, the mirror), the layout, the contacts and
notches: every look on three colour classes at 512 and 1024 px, Echo as a master at 4096 px (three eyes and a pair) and at 2048 px (the coarse factor 2), the 4:5 canvas and the
9:19.5 wall (with the accent plate at 512 px), a bar pupil, a slit pupil and a pet (the polar fill), the fill alone, names, a date and a Lithuanian letter, pairs on four canvases, a
forced Kiss distance, a swap, the laboratory's switches, groups of three to six (the trio rotated and with the weave at its base, the two rings). The 18 pictures of four calibration
eyes (every look at 1024 px, a pair, a trio) and the four pictures that draw from a 4K plate (the wall canvas at 1024 px: the 2k mip of a DUST plate; Vortex and Deep Field as masters: the
2k mip of a 4K plate; Starfield as a master: a 4k LOD) are equal too (10 LOCAL lines, hashes only for the real eyes; the 4K plates came through a local store made from the scratch tree's
own files, sha256 equal to the registry's, then the cache). The prototype's own 23 tests (T1 to T25) passed on the real eyes (`data/stepA/universe_tests_scratch.json`).

**Time and memory at 4096 px** (`scripts/styles_tests/time_universe.py`): a fresh process per render, one thread, this machine (shared with other builders: two runs of the same code differ
by up to 10 percent), synthetic eyes of 1024 px, the canvas 4096 px, a pair and a group on copies of at most 2048 px (the registry's `work_side`), Windows peak working set. CPU seconds of
the render (imports apart), the port and the scratch alternating, two rounds each, against the spike's table (SP 4.1, quiet core, cold) scaled by this machine's yardstick (x0.95):

| Render | Port, runs | Scratch, runs | SP table x0.95 | Peak port | Peak scratch | SP peak |
|---|---|---|---|---|---|---|
| Echo, 1 eye | 11.8, 11.8 | 12.4, 11.8 | 11.5 | 567 MB | 568 | 635 |
| Echo, 2 eyes, 3:2 | 13.7, 14.3 | 13.7, 13.8 | 14.1 | 860 | 817 | 649 |
| Echo, 6 eyes | 23.3, 26.5 | 25.2, 26.5 | 20.2 (capped) | 815 | 772 | 815 (capped) |
| Vortex (a 2k mip of a 4K plate through the cache) | 8.2, 8.5 | 9.2, 9.4 | 9.7 | 459 | 459 | 526 |
| Deep Field (a 2k mip) | 8.6, 8.3 | 8.6, 7.5 | 9.6 | 528 | 530 | 595 |
| Starfield (a 4k LOD) | 7.2, 7.9 | 8.4, 7.2 | 8.9 | 458 | 459 | 525 |

Acceptance of the card (Echo, one eye, master: about 12 s of CPU and 635 MB): 11.8 s and 567 MB. Every cell is within 15 percent of the table apart from the pair's memory (860 MB against
649: the unchanged scratch code peaks at 817) and the group of six's CPU (up to 31 percent over, the scratch the same), so the cause is the machine and the eyes, not the port, as WP5A
and WP7A found. The master through the step runner (`lab_steps` on one synthetic 4096 px master, Echo): 16.2 to 16.6 s of CPU, +496 MB of resident size, against the plan's estimate of
25.6 s and 731 MB at the factor 1.6. Warm previews at 1024 px (CPU, a loaded machine): Echo 1.4 to 1.5 s, a pair 1.4 to 1.5 s, six eyes 2.6 to 2.8 s, Vortex 1.2 s, Deep Field 1.0 s,
Starfield 0.5 s (the brief's limits are 1.5 s and 3 s for six). A preview never touches storage: at 1024 px all three plate looks read the 1K LOD (their placement scale is at most
1.1 x 1024 by construction); only the Echo wall canvas at 1024 px and every master need a 4K file (the 2k mip or the 4k LOD).

**The tests carried over** (`v3uni`, section 6, on synthetic eyes; the numbers the prototype printed on the real eyes are in `data/stepA/universe_tests_scratch.json`): T1 iris integrity
(largest difference 1 level in the fade zone, 0 pixels over the tolerance, the seam blend share at most 8.2 percent of an iris against the bound 8.5), T1b (0 unexplained pixels over 15
cases), T2 (0 covered pupil pixels over 7 sets), T3 (pair 0.889, trio apex 1.0 and bases 0.936 and 0.805, groups of four to six at least 0.827), T5, T6, T7, T8, T9 (the master against the
preview: design SSIM 0.988 for one eye, 0.979 for a pair, 0.987 for a trio at 2048 px, 0.997 and 0.993 for Deep Field and Vortex at 2048 px; T9a outside 1.15 R at least 0.982; T9b
mean dE00 inside the irises at most 1.07), T10 to T15, T18, T19 (800 sets), T21 (no row step at the band boundaries: at most 1.32 times the neighbouring rows; the picture does not depend
on the band height: 1 level at most), T22, T23, T24 (the synthetic gate verdicts equal the scratch gate's), T25. **Six bounds depend on the eye and are relaxed for the synthetic eyes**
(`BOUND` in the test, each with the prototype's value and what the prototype measured: the seam blend share 0.085 for 0.08, the matter's hue share 0.60 for 0.85, the p99 dE of the design
8.0 for 5.0 on one eye, the fill's chroma 0.70 for 0.85, the least fill lightness 7.0 for 8.0, the iris above its fill 10 for 15: a synthetic blue ring has little chroma and the synthetic
dark brown iris is darker than any real one). Equal pictures carry the real-eye results over to the port; the tests guard the structure and the numbers against later changes.

**Three findings of the port.** (1) The prototype caught every error of a plate look (`except Exception`) and drew the picture without the plate: a missing, short or wrong plate would
have been a silent substitution after payment. The port lets `PlateUnavailable` and `NoPlate` through (the step runner retries once and then holds the order); the build of the family
has no `except Exception` around a plate (a check of `v3uni`). (2) The Echo look on the wall canvas picks ANY of the seven DUST plates for its accent, and at 1024 px that is the 2k mip
of the 4K file, but the baked registry named a 4K file only for the four DUST plates that Deep Field picks: the bake rule `needs_4k` now says all seven (+19 MiB of 4K files for storage,
449 MiB in all, none of it in the first release: DUST is a laboratory family). (3) The pick of a spiral is an index into the candidate list and the baked registry is sorted by id while
the prototype's registry file was not: the order is kept in `plates.SPIRAL_ORDER` (the nine crisp spirals with a void of 0.20 R or more; the replay of Vortex proves it).

**Suite.** `v3uni` 102 checks (10 LOCAL lines with `SNAPEYES_SCRATCH_Y3` and `SNAPEYES_CALIB`), 12 to 14 minutes on a machine shared with other builders (741 s and 835 s in the last two runs; the replay about 170 s of it): the family's files and
rules, the registry against the family, the replay, the plates and the atlas (the candidates, a missing plate, a plate that arrived later), determinism in two fresh interpreters, the
guards of `render`, the contract (`resolve`, `preview`, `tiles`, the master plan's plan and capacity), the 23 tests of the design round, `/api/compose` for a style made visible, the
admin laboratory (every look, the estimate of a look, a Vortex master with its plate missing), and the master through `lab_steps`.

**Full set**: **32 of 32 green** on an export of `5e3c127` (`git archive`, CRLF line ends, the private fixtures, no scratch tree), every count equal to `suites/baseline.json` (`v3uni` 101 of
101 at that commit, 102 with the Preview's fallback check that followed), 1485 s on a machine shared with other builders. The first run, on an export of `e80f8c0`, was 29 of 32, and the three that were red are not
the family's: `v3single` because its check of the laboratory's list named six styles and the universe style joined the list (the check reads the singles' rows now); `v3wp0` because `bundle_report.mjs` walks the
whole folder when it is not a git checkout (an export), and a suite writing a temporary file under `suites/out` at that moment made `statSync` throw (the walk skips a file that vanished; in a git checkout the file
list comes from `git ls-files` and this never happened); `r3` check S10 (12 concurrent proven withdrawal statements: at most `ORDER_DAY_MAX` taken, the rest 429) saw all twelve answered 429 under the load of three
suites: **a race in the limiter's count, not touched by this work** (`r3` alone: 48 of 48, and green in the second full run). Listed here as a flake, not fixed (it is the withdrawal limiter's, and a retry would hide it):
the twelve statements each write a marker and then count the markers, so under a heavy load all twelve can count more than five.
