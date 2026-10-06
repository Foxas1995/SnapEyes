// The eyes of a group laboratory request: what the browser makes of a picked file or of the site's own restored sample before it goes to the server (api/_lib/ops.py a_styles_lab_group:
// 1 to 8 restored iris squares, each sent as the base64 of a JPEG, together at most about 4.3 MB, so each is cut to its centre square and shrunk to 1024 px: the size of a preview).
// Pure browser code (canvas, FileReader), no React.

export const GROUP_SAMPLE = '/assets/sample_eye_blue_restored.jpg';
export const GROUP_SIDE = 1024;

function blobB64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const fr = new FileReader();
    fr.onload = () => resolve(String(fr.result).split(',')[1] || '');
    fr.onerror = () => reject(new Error('Failo nepavyko perskaityti.'));
    fr.readAsDataURL(blob);
  });
}

/** The centre square of an image as JPEG base64, at most GROUP_SIDE px on a side. */
export async function squareB64(blob: Blob, side = GROUP_SIDE): Promise<string> {
  const url = URL.createObjectURL(blob);
  try {
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const el = new Image();
      el.onload = () => resolve(el);
      el.onerror = () => reject(new Error('Nuotraukos nepavyko perskaityti.'));
      el.src = url;
    });
    const s = Math.min(img.naturalWidth, img.naturalHeight);
    const out = Math.min(side, s);
    const c = document.createElement('canvas');
    c.width = out; c.height = out;
    c.getContext('2d')!.drawImage(img, (img.naturalWidth - s) / 2, (img.naturalHeight - s) / 2, s, s, 0, 0, out, out);
    return c.toDataURL('image/jpeg', 0.93).split(',')[1] || '';
  } finally {
    URL.revokeObjectURL(url);
  }
}

/** The site's own restored sample, as the eyes of a group (the same eye n times: a check that the sheet draws, not a look at a real group). */
export async function sampleEyes(n: number): Promise<string[]> {
  const one = await blobB64(await (await fetch(GROUP_SAMPLE)).blob());
  return Array.from({ length: n }, () => one);
}

/** The picked files as eyes. */
export async function fileEyes(files: File[]): Promise<string[]> {
  const out: string[] = [];
  for (const f of files) out.push(await squareB64(f));
  return out;
}

/** Are these eye numbers 1 to n with no gap (the shape lab_steps asks for: the stored masters of a lab test order, eyes 1 to n)? */
export function isFirstN(ns: number[]): boolean {
  const s = [...ns].sort((a, b) => a - b);
  return s.length > 0 && s.every((v, i) => v === i + 1);
}
