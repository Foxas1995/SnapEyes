// wideFrame(): the customer's photo cut to the Reveal's frame, in the browser, from the photo the page still holds (TryApp.process
// calls it BEFORE releasePhoto()). One canvas, JPEG q85, kept in memory only, never uploaded and never stored (decision C10: no wide frame
// leaves the device, so there is no context crop and no card here; revealMath.contextBox is the unused twin of the prototype's). The pixels are the photo's own:
// a resample, no colour correction, no sharpening. Any part of the frame the photo does not cover is edge-clamped, blurred and
// darkened 50 % (4.1); the planner keeps that under 15 % of the frame or falls back to the tight frame.
//
// The crop that goes to /api/deglare and this frame must come from the SAME limbus fit with the same arithmetic (the crop is the
// square of side 2 r PAD centred on the fit; the frame is the window r / (2 rf) wide centred on the pupil): that is what makes the
// restored iris register with the photo by construction (TryApp.process derives both from the one `a.iris` it already holds).
import { revealGeometry, uncoveredShare, type Aspect, type Fit, type Geometry, type RevealParams } from './revealMath';

type Source = HTMLImageElement | ImageBitmap;

const dims = (img: Source): [number, number] => (img instanceof HTMLImageElement ? [img.naturalWidth, img.naturalHeight] : [img.width, img.height]);

function makeCanvas(w: number, h: number): HTMLCanvasElement {
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  return c;
}

/** Draw the source rectangle `box` of img into a W x H canvas; the part beyond the image is edge-clamped, blurred, darkened. */
export function drawFrame(img: Source, box: readonly [number, number, number, number], W: number, H: number): { canvas: HTMLCanvasElement; uncovered: number } {
  const [IW, IH] = dims(img);
  const [x0, y0, x1, y1] = box;
  const sx = W / (x1 - x0), sy = H / (y1 - y0);
  const ix0 = Math.max(0, x0), iy0 = Math.max(0, y0), ix1 = Math.min(IW, x1), iy1 = Math.min(IH, y1);
  const canvas = makeCanvas(W, H);
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('canvas');
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  const dx0 = (ix0 - x0) * sx, dy0 = (iy0 - y0) * sy, dx1 = (ix1 - x0) * sx, dy1 = (iy1 - y0) * sy;
  const uncovered = uncoveredShare(box, IW, IH);
  if (uncovered > 0.0005 && ix1 > ix0 && iy1 > iy0) {
    // edge replication: stretch the outermost pixel row / column of the photo into the margins
    const iw = ix1 - ix0, ih = iy1 - iy0;
    if (dx0 > 0) ctx.drawImage(img, ix0, iy0, 1, ih, 0, dy0, dx0, dy1 - dy0);
    if (dx1 < W) ctx.drawImage(img, ix1 - 1, iy0, 1, ih, dx1, dy0, W - dx1, dy1 - dy0);
    if (dy0 > 0) ctx.drawImage(img, ix0, iy0, iw, 1, dx0, 0, dx1 - dx0, dy0);
    if (dy1 < H) ctx.drawImage(img, ix0, iy1 - 1, iw, 1, dx0, dy1, dx1 - dx0, H - dy1);
    if (dx0 > 0 && dy0 > 0) ctx.drawImage(img, ix0, iy0, 1, 1, 0, 0, dx0, dy0);
    if (dx1 < W && dy0 > 0) ctx.drawImage(img, ix1 - 1, iy0, 1, 1, dx1, 0, W - dx1, dy0);
    if (dx0 > 0 && dy1 < H) ctx.drawImage(img, ix0, iy1 - 1, 1, 1, 0, dy1, dx0, H - dy1);
    if (dx1 < W && dy1 < H) ctx.drawImage(img, ix1 - 1, iy1 - 1, 1, 1, dx1, dy1, W - dx1, H - dy1);
    ctx.drawImage(img, ix0, iy0, iw, ih, dx0, dy0, dx1 - dx0, dy1 - dy0);
    // blur 0.02 W by a down/up pass (canvas filter is not everywhere), then darken 50 %, then the photo itself on top
    const k = Math.max(4, Math.round(0.02 * W * 1.5));
    const small = makeCanvas(Math.max(1, Math.round(W / k)), Math.max(1, Math.round(H / k)));
    const sctx = small.getContext('2d');
    if (sctx) {
      sctx.imageSmoothingQuality = 'high';
      sctx.drawImage(canvas, 0, 0, small.width, small.height);
      ctx.drawImage(small, 0, 0, W, H);
      ctx.fillStyle = 'rgba(0,0,0,0.5)';
      ctx.fillRect(0, 0, W, H);
      ctx.drawImage(img, ix0, iy0, iw, ih, dx0, dy0, dx1 - dx0, dy1 - dy0);
    }
  } else {
    ctx.drawImage(img, ix0, iy0, ix1 - ix0, iy1 - iy0, dx0, dy0, dx1 - dx0, dy1 - dy0);
  }
  return { canvas, uncovered };
}

export interface WideFrame { url: string; geometry: Geometry; uncovered: number; side: number }

/** The Reveal's photo layer: a data URL (JPEG q85, side px wide) plus the geometry it was cut with. */
export function wideFrame(img: Source, fit: Fit, params: Pick<RevealParams, 'pupil' | 'shift' | 'edge'> & { ia?: number }, side = 1024, aspect: Aspect = [1, 1], quality = 0.85): WideFrame {
  const g = revealGeometry(fit, params, aspect);
  const W = side, H = Math.round((side * aspect[1]) / aspect[0]);
  const { canvas, uncovered } = drawFrame(img, g.box, W, H);
  return { url: canvas.toDataURL('image/jpeg', quality), geometry: g, uncovered, side };
}
