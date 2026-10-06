import { asset } from './assets';
import { useCopy } from './copy/useCopy';

/** The phone drawn in the first two steps of "How it works". Both are pictures of a screen, not of a print, a room or an
 *  example, so they carry no label (the picture chip is for prints, rooms and artwork); they are illustration only, which is
 *  why a screen reader skips them: the step's own text and the caption under it say the same in words.
 *   camera:  the viewfinder of a phone held at an eye (the founder's own 315 px phone crop, not retouched), the gold ring,
 *            the corner marks, "2x" and the shutter;
 *   preview: the free preview screen with its watermark, and the button under it ("Your file, next" while ordering is not
 *            open, "Continue to payment" once it is: only the open state names payment). */
export function PhoneMock({ kind, open }: { kind: 'camera' | 'preview'; open: boolean }) {
  const { c } = useCopy();
  if (kind === 'camera') {
    const pic = asset('ui/before-phone-crop-315');
    return (
      <div className="lp-phone" aria-hidden="true">
        <div className="lp-cam">
          <img src={pic.src} width={pic.w} height={pic.h} loading="lazy" alt="" />
          <span className="lp-ring" />
          <span className="lp-br lp-a" />
          <span className="lp-br lp-b" />
          <span className="lp-br lp-c" />
          <span className="lp-br lp-d" />
          <span className="lp-zoom">{c.how.phoneZoom}</span>
          <span className="lp-shutter" />
        </div>
      </div>
    );
  }
  const pic = asset('ui/preview_wm_360');
  return (
    <div className="lp-phone" aria-hidden="true">
      <div className={open ? 'lp-prev lp-open' : 'lp-prev'}>
        <b>{c.how.previewTitle}</b>
        <img src={pic.src} width={pic.w} height={pic.h} loading="lazy" alt="" />
        <span>{open ? c.how.previewButton : c.how.previewSoon}</span>
      </div>
    </div>
  );
}
