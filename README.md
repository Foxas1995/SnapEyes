# SnapEyes

Iris art from a phone photo. Marketing page at `/` (React + Vite + Tailwind) and the real studio at `/try`.

## How `/try` works

1. **Capture** (`src/try/TryApp.tsx`): native camera via `<input capture>`, gallery upload, or live camera with hardware zoom where the browser supports it (Android Chrome). The photo never leaves the browser at full size: a 1600 px copy goes to analysis, then only the iris square (max 1400 px) is sent on.
2. **`POST /api/analyze`**: Gemini vision returns iris/pupil/glare boxes as JSON, a Daugman-style limbus fit refines the circle, size and sharpness are measured. Verdict: `good` (iris >= 500 px and sharp), `ok`, `weak`, with concrete tips.
3. **`POST /api/deglare`**: disk mask, Real-ESRGAN x4 (ONNX, CPU) when the iris is small, glare mask (relative brightness + vision boxes), and a Gemini image edit that rebuilds only the reflection area, blended back through a feathered mask.
4. **`POST /api/enhance`**: `faithful` = conservative restoration prompt with `thinking_level: high` plus a fidelity guard (low-frequency SSIM against the input; below 0.75 falls back to the faithful upscale). `artistic` = macro re-interpretation for weak photos. With consent the crop, result and metrics are stored to Vercel Blob (`eyes/<session>/…`) as training memory.
5. **`POST /api/compose`**: PIL composition on the style backgrounds in `api/_assets/bg` with Cinzel/Plus Jakarta typography and a preview watermark.

`GET /api/health` reports what is configured on a deployment.

## Environment variables (Vercel)

- `GEMINI_API_KEY` (required)
- `BLOB_READ_WRITE_TOKEN` (optional, enables the training memory)
- `SNAPEYES_VISION_MODEL` / `SNAPEYES_IMAGE_MODEL` (optional overrides; defaults `gemini-3.8-flash` / `gemini-3.1-flash-image`)

## Local development

```bash
npm install
python scripts/dev_api.py          # Python stand-in for the Vercel functions on :5050 (reads C:\kuriam\.gemini-key locally)
npx vite --port 5175               # frontend, proxies /api to :5050
python scripts/test_flow.py photo.jpg [--artistic]   # end-to-end API test, writes ./flowtest next to the photo
npm run build                      # tsc + vite build (both pages)
```

Python deps for local runs: `pip install -r requirements.txt`.
