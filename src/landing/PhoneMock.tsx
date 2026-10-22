import { asset } from './assets';
import { useCopy } from './copy/useCopy';

/** The phone drawn in the second step of "How it works" (the first step shows the guide video, src/shared/GuideVideo.tsx: the
 *  owner, 2026-10-22, the camera phone drawn there before showed the eye far too close). It is a picture of a screen, not of a
 *  print, a room or an example, so it carries no label (the picture chip is for prints, rooms and artwork); it is illustration
 *  only, which is why a screen reader skips it: the step's own text and the caption under it say the same in words.
 *  The free preview screen with its watermark, and the button under it ("Your file, next" while ordering is not open,
 *  "Continue to payment" once it is: only the open state names payment). */
export function PhoneMock({ open }: { open: boolean }) {
  const { c } = useCopy();
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
