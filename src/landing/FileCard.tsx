import { asset } from './assets';
import { useCopy } from './copy/useCopy';

/** Step 3 of "How it works": the file itself, as a card (thumbnail of an engine artwork, the file name, "4096 x 4096 px, JPEG").
 *  It shows what you receive: a file, not a print, so it needs no label; the texts stay readable to a screen reader because they
 *  describe the product (the size and the format). The tag "Digital file" under them went in the lean pass of 2026-10-22: the price
 *  list says it. */
export function FileCard() {
  const { c, fmt } = useCopy();
  const pic = asset('art/gold_own_480');
  return (
    <div className="lp-filecard">
      <img src={pic.src} width={pic.w} height={pic.h} loading="lazy" decoding="async" alt="" />
      <div>
        <b>{c.how.fileName}</b>
        <span>{fmt(c.how.fileMeta)}</span>
      </div>
    </div>
  );
}
