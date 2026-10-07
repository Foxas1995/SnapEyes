# Step 2 of the plates upload (the owner's machine, PowerShell): dry run, then the real upload, then a read-back of every plate.
#
#   .\upload_release1_plates.ps1 -Repo C:\kuriam\snapeyes -Plates D:\snapeyes-plates-4k            # dry run: reads nothing secret, writes nothing
#   .\upload_release1_plates.ps1 -Repo C:\kuriam\snapeyes -Plates D:\snapeyes-plates-4k -Yes       # uploads what is missing, then verifies all 109
#   .\upload_release1_plates.ps1 ... -LocalDir D:\rehearsal-store                                  # a rehearsal into a folder (no key needed)
#
# -Repo   a checkout of the RELEASE (it must hold scripts\upload_plates.py and api\_lib\plates_registry.py: after main has been
#         fast-forwarded to v3-release that is C:\kuriam\snapeyes; before, the v3-release worktree)
# -Plates the folder stage_release1_plates.py filled (<Plates>\plates_4k\<family>\<file>)
#
# The service key: asked once, hidden, kept only in this PowerShell process (never in a file, never printed); it must be the key of the
# SAME Supabase project and bucket as the Vercel variables SNAPEYES_SUPABASE_URL / SNAPEYES_SUPABASE_SERVICE_KEY / SNAPEYES_BUCKET.
param(
  [Parameter(Mandatory = $true)][string]$Repo,
  [Parameter(Mandatory = $true)][string]$Plates,
  [switch]$Yes,
  [string]$LocalDir = ""
)
$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
$script = Join-Path $Repo "scripts\upload_plates.py"
if (-not (Test-Path $script)) { throw "not a release checkout: $script is missing" }
if (-not (Test-Path (Join-Path $Plates "plates_4k"))) { throw "no plates_4k folder in $Plates (run stage_release1_plates.py first)" }

if ($LocalDir -eq "") {
  if (-not $env:SNAPEYES_SUPABASE_URL) { $env:SNAPEYES_SUPABASE_URL = (Read-Host "Supabase project URL (https://<ref>.supabase.co)").Trim() }
  if (-not $env:SNAPEYES_SUPABASE_SERVICE_KEY) {
    $sec = Read-Host "Supabase service key (hidden, not stored)" -AsSecureString
    $env:SNAPEYES_SUPABASE_SERVICE_KEY = [System.Net.NetworkCredential]::new("", $sec).Password.Trim()
  }
  if (-not $env:SNAPEYES_BUCKET) { $env:SNAPEYES_BUCKET = "snapeyes-private" }
  Write-Host "Bucket: $($env:SNAPEYES_BUCKET) (must be the bucket the Vercel project uses; private)"
}

$common = @($script, "--y2", $Plates, "--release1")
if ($LocalDir -ne "") { $common += @("--local-dir", $LocalDir) }

Write-Host "`n--- 1. dry run: what is there, what would be uploaded"
& python @common
if ($LASTEXITCODE -ne 0) { throw "dry run failed (exit $LASTEXITCODE): a source file is missing or a stored object is wrong; nothing was changed" }

if (-not $Yes) { Write-Host "`nDry run only. Run again with -Yes to upload."; return }

Write-Host "`n--- 2. upload (idempotent: an object that is already there is compared and left alone; a wrong one is reported, never overwritten)"
& python @common --yes
if ($LASTEXITCODE -ne 0) { throw "upload stopped (exit $LASTEXITCODE). Run the same command again: it continues where it stopped." }

Write-Host "`n--- 3. read-back: every plate is downloaded and its sha256 compared with the registry"
& python @common --yes
if ($LASTEXITCODE -ne 0) { throw "read-back failed (exit $LASTEXITCODE)" }
Write-Host "`nDone. Expect 109 present, 0 uploaded, 0 wrong above. Then: open https://snapeyes.com/api/health and look for plates_4k = true."
Remove-Item Env:\SNAPEYES_SUPABASE_SERVICE_KEY -ErrorAction SilentlyContinue
