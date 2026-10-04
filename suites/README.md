# The guard suites

The regression net of the payments, ordering, admin, price, legal-text and (from the v3 work) style code: twenty Python suites and
the page-code tests, run against a checkout of this repository with a fake Stripe, a fake mail service, a local store folder and the
image model stubbed. No real key is used, no network is needed, no image model is called. They used to live in a session scratch
folder (a temp path that disappears); since 2026-10-04 they live here, versioned with the code they guard.

    bash suites/run_main.sh              # every suite and the page-code tests, three at a time (about 4 minutes)
    bash suites/run_main.sh pay au ts    # only these
    python suites/compile_matrix.py      # compileall api under Python 3.12, 3.13 and 3.14, and 3.12 syntax of every file
    node scripts/run_ts_tests.mjs        # the page-code tests alone

`run_main.sh` tests the checkout it sits in (`SNAPEYES_REPO` overrides), builds the site first when `dist/legal/order-mail.json` is
missing (the admin suites read the legal pack), prints one table (`summary.py`) and exits 1 when a suite is red, passes fewer
checks than `baseline.json` records, or did not run at all (SKIPPED: see below). Results and the prepared copy go to
`suites/out/` (not in git).

## What is where

| Path | What |
|---|---|
| `run_main.sh`, `run_all.sh` | the runner: prepare, run three at a time, then the page-code tests |
| `suites.list` | one `name:dir:script[:needs]` line per suite; a new suite is one more line |
| `mksp.py` | prepares one run: copies `tree/`, the repository's own `scripts/styles_tests/`, the private fixtures and the built legal pack |
| `tree/` | the suite sources, in the folder names the suites use among themselves (`wave-pv/tests/harness.py` is the harness of the fake Stripe and Resend). The names are the historic scratch names: renaming them would break the suites' relative references |
| `ts/` | the page-code tests (`*.test.ts`, run by `scripts/run_ts_tests.mjs` together with any `src/**/*.test.ts`) |
| `summary.py`, `baseline.json`, `baseline.md` | the result table, the recorded green list with the number of checks per suite, and the measurements of the first baseline |
| `compile_matrix.py`, `check_fixtures.py`, `fixtures.sha256` | the interpreter matrix and the check of the private fixtures |

The suites find the checkout through `SNAPEYES_REPO` and their own prepared tree through `SNAPEYES_SP` (both set by `run_main.sh`);
nothing in the tree names a path of this machine, and run by hand without `SNAPEYES_REPO` a suite stops with a message.

## The private fixtures (not in git)

The two admin suites (`admin`, `oldadmin`) replay the replies of the image model that were recorded from the owner's own photos
(`suites/private/fixtures`, 20 files, 3 MB). A real eye is biometric data, so they are **never committed** (`.gitignore`,
`suites/private/`); `fixtures.sha256` lists their hashes so that a copy kept elsewhere can be verified
(`python suites/check_fixtures.py [folder]`). `SNAPEYES_FIXTURES` points the runner at another folder. When they are missing the two
suites are reported SKIPPED (exit 77), not green, and the run ends with `INCOMPLETE: admin, oldadmin did not run` and **exits 1**,
so that a gate reading the exit code of `run_main.sh` in a fresh clone cannot take a run without the 372 admin checks for a green
one. A machine that cannot have the fixtures says so on purpose: `--allow-skipped` for `summary.py`, or `SNAPEYES_ALLOW_SKIPPED=1`
for `run_main.sh` (the last lines still name what did not run). The v3 style suites use a synthetic iris generator (work package WP4) and need none.
Keep a copy of `suites/private/` somewhere safe outside the repository: the only other copy is in a session scratch folder.

## Adding a suite

1. Put it in `scripts/styles_tests/` (Python, a `PASS name` / `FAIL name   <- detail` line per check, exit 1 on a failure). It reads
   `SNAPEYES_REPO` and takes its fake services from `wave-pv/tests/harness.py` (see `scripts/styles_tests/test_wp0.py`).
2. Add `name:scripts/styles_tests:test_file.py` to `suites.list`.
3. Add its check count to `baseline.json` in the same commit.

Rules that the build enforces on the files of `scripts/` and `src/`: no written price (amounts in minor units, taken from
`api/_lib/markets.py`), no en or em dash, Lithuanian and Hungarian strings by `scripts/check_texts.mjs`. This folder is not scanned
by those checks, but its files hold no dash either (`test_wp0.py` checks it).

## Not in a function

`suites/` is in `excludeFiles` of every `vercel.json` entry and in `.vercelignore`, so none of it is bundled or uploaded
(`node scripts/bundle_report.mjs --check` fails when a folder besides `api/` would ride into a function).
