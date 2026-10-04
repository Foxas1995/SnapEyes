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
| v3wp0 | 0 | 61 | GREEN |

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
build log shows a missing wheel, `.python-version` 3.13 is the fallback (the pins support it) and the suites must be re-run on it.

## 3. Function size (V1) and `excludeFiles` (V2)

`node scripts/bundle_report.mjs --pypi` computes, without a Linux machine and without `vercel build` (a local Windows build would
install Windows wheels): the files each function bundles (git's files minus `excludeFiles` minus `.vercelignore`) and the size of
the Linux wheels PyPI lists for the pinned versions, read from the zip directories of the wheels (about 100 KB each; no wheel is
downloaded). MiB = 2^20 bytes.

| Part | MiB | Note |
|---|---:|---|
| Files of the repository in each function | 16.5 | all of it `api/`: `_assets` 16 (11 backgrounds, the ONNX model, 2 fonts), `_lib` and the handlers 1.4 |
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
at the peak, which could run a 1 GB function out of memory), this one in float32 (the probe peaks near 350 MB), and the other six
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
