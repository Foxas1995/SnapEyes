import { useEffect, useMemo, useState } from 'react';
import { parseReveal, revealView, tightFit, type RevealParams, type RevealView } from './revealMath';
import { wideFrame, type WideFrame } from './wideFrame';

/** What the hook reads of an eye (src/try/multi.ts Eye has all of it). */
export interface FrameEye {
  id: string;
  before: string;                  // data URL: the client crop /api/deglare took (the photo the page keeps for the eye)
  image: string;                   // base64 JPEG: the display copy /api/enhance returned (the restored half)
  pad: number;
  sample?: boolean;
  reveal?: unknown;                // /api/enhance's "reveal" field as the page stored it (parseReveal checks it)
  wide?: WideFrame;                // the photo's frame, cut in the browser while the page still held the photo (kept in memory only)
}

const loadImg = (src: string): Promise<HTMLImageElement> => new Promise((res, rej) => {
  const i = new Image();
  i.onload = () => res(i);
  i.onerror = () => rej(new Error('image'));
  i.src = src;
});

export interface RevealState {
  rv: RevealParams | null;         // the checked numbers (null: none, or not what the server sends)
  view: RevealView;                // 'cut', 'strip' or 'plain': what to show for this eye (plain also when its frame could not be built)
  frame: WideFrame | null;         // the photo's frame; null while it is being built
  restored: string;                // the display copy as an image source
  ready: boolean;                  // both layers decoded: the arrival sweep may start
}

/** The Reveal's photo frame for an eye, and whether both layers are decoded. A fresh eye brings its frame (cut from the full photo before the page
 *  let it go). An eye that has none (brought back from Stripe's page: the frame is memory only and is not kept) gets the tight frame of the client crop
 *  it still holds: nothing is invented around the iris, nothing is stored or uploaded. If even that fails the view is 'plain': the old slider. */
export function useRevealFrame(eye: FrameEye | undefined): RevealState {
  const rv = useMemo(() => parseReveal(eye?.reveal), [eye?.reveal]);
  const wanted = !!eye && revealView(rv, eye.sample) !== 'plain';
  const [built, setBuilt] = useState<{ id: string; frame: WideFrame | null } | null>(null);
  const id = eye?.id ?? '';
  const before = eye?.before;
  const pad = eye?.pad ?? 1.12;
  const given = eye?.wide;
  useEffect(() => {
    if (!wanted || given || !rv || !before) return;
    let live = true;
    loadImg(before)
      .then((img) => { if (live) setBuilt({ id, frame: wideFrame(img, tightFit(img.naturalWidth, pad), rv) }); })
      .catch(() => { if (live) setBuilt({ id, frame: null }); });
    return () => { live = false; };
  }, [wanted, given, rv, before, pad, id]);
  const frame = given ?? (built && built.id === id ? built.frame : null);
  const failed = !given && !!built && built.id === id && built.frame === null;

  const restored = eye ? `data:image/jpeg;base64,${eye.image}` : '';
  const [decoded, setDecoded] = useState('');
  useEffect(() => {
    if (!wanted || !restored) return;
    let live = true;
    const i = new Image();
    i.onload = () => { if (live) setDecoded(restored); };
    i.src = restored;
    return () => { live = false; };
  }, [wanted, restored]);

  const view: RevealView = failed ? 'plain' : revealView(rv, eye?.sample);
  return { rv, view, frame, restored, ready: !!frame && decoded === restored };
}
