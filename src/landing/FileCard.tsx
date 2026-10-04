import { asset } from './assets';
import { useCopy } from './copy/useCopy';

/** Step 3 of "How it works": the file itself, as a card (thumbnail of an engine artwork, the file name, "4096 x 4096 px, JPEG",
 *  "Digital file"). It shows what you receive: a file, not a print, so it needs no label; the texts stay readable to a
 *  screen reader because they describe the product (the size and the format). */
export function FileCard() {
  const { c, fmt } = useCopy();
  const pic = asset('art/radiance_own_480');
  return (
    <div className="lp-filecard">
      <img src={pic.src} width={pic.w} height={pic.h} loading="lazy" decoding="async" alt="" />
      <div>
        <b>{c.how.fileName}</b>
        <span>{fmt(c.how.fileMeta)}</span>
        <em>{c.how.fileTag}</em>
      </div>
    </div>
  );
}
