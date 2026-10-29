// The order detail says WHY a 4K eye needs the owner's review (2026-10-28): the codes of the check record's "fail" list (api/_lib/iris.py preview_qa) in words, among them
// pupil_shape, the delivered pupil that is not one round dark disc (the lab order lab-261027-9c1f1d48: a blob with arms and black spots). Pure page code, loaded through
// Vite's module runner by scripts/run_ts_tests.mjs; returns its results.
import { readFileSync } from 'node:fs';
import { QA_FAIL_LT, qaFailText } from '../../src/admin/format';

type Row = [string, boolean, string?];

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const shape = qaFailText(['pupil_shape']);
  check('qaFailText: the pupil shape failure in words, after "priežastis:"', shape.startsWith('priežastis: vyzdys netaisyklingas') && shape.includes('pažiūrėk prieš siunčiant'), shape);
  check('qaFailText: several codes in the record\'s order, an unknown code as itself', qaFailText(['dl', 'pupil_shape', 'new_code']) === `priežastis: ${QA_FAIL_LT.dl}; ${QA_FAIL_LT.pupil_shape}; new_code`, qaFailText(['dl', 'pupil_shape', 'new_code']));
  check('qaFailText: nothing failed, no list, or no codes: no words', qaFailText([]) === '' && qaFailText(undefined) === '' && qaFailText('pupil_shape') === '' && qaFailText([3, null, '']) === '');
  check('every code preview_qa can write has its words (ring_de00, dl, follow, pupil, photo, pupil_shape, qa_error)',
    ['ring_de00', 'dl', 'follow', 'pupil', 'photo', 'pupil_shape', 'qa_error'].every((c) => typeof QA_FAIL_LT[c] === 'string' && QA_FAIL_LT[c].length > 3));
  const dash = new RegExp('[' + String.fromCharCode(0x2012, 0x2013, 0x2014, 0x2015) + ']');
  check('the words hold no dash, no straight quote and no double space', Object.values(QA_FAIL_LT).every((w) => !dash.test(w) && !w.includes('"') && !/ {2}/.test(w)));
  const src = readFileSync('src/admin/OrderDetail.tsx', 'utf8');
  check('the order detail\'s check line prints the reason (QaLine reads qa.fail through qaFailText)', /qaFailText\(qa\.fail\)/.test(src));
  return out;
}
