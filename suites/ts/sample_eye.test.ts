// The AI-generated sample eye of /try and the picker (QA of 2026-10-20): the page showed "Your eye needs a retake" and a greyed Universe tile for the demo eye, a picture
// the visitor did not take, because the first restoration file of the sample failed the fill rule of the restoration gate (fill_hard_edges). The two answers below are the
// REAL answers of the server's engine for the two files (api/_lib/catalogue.py tile_list and the eye's profile, run on this machine for the file shipped before and the
// file shipped now; the first one is kept here as the failing eye the picker must still handle): the picker's own functions turn them into what the visitor sees.
import { retakeView, tileState, type ServerEye, type ServerTile } from '../../src/try/picker';

type Row = [string, boolean, string?];
interface Answer { pick: string | null; reason: string | null; eyes: ServerEye[]; tiles: ServerTile[] }

// the shipped sample before 2026-10-20 (sha256 7e681ceca2195512...): lid rule ok, fill rule failed (fill_hard_edges, 127 sectors of 180 against the limit of 120)
const OLD: Answer = {"pick":null,"reason":null,"eyes":[{"eye":1,"eye_id":"7e681ceca2195512","cls":"own","pupil":"round","gate":{"lid":true,"fill":false},"why":["fill_hard_edges"]}],"tiles":[{"id":"solo.powder","name":"Powder Burst","slug":"powder-burst","group":"solo","legacy":0,"stage":"preview","available":true,"why":null,"layouts":["single"],"eyes":1,"price_class":"art","looks":{},"gate":"advisory","rule":"lid","pick":false},{"id":"solo.universe","name":"Universe","slug":"universe","group":"solo","legacy":0,"stage":"preview","available":false,"why":"gate","layouts":["single"],"eyes":1,"price_class":"art","looks":{"echo":"preview","vortex":"preview"},"gate":"hard","rule":"fill","pick":false},{"id":"solo.splash","name":"Splash","slug":"splash","group":"solo","legacy":0,"stage":"preview","available":true,"why":null,"layouts":["single"],"eyes":1,"price_class":"art","looks":{},"gate":"advisory","rule":"lid","pick":false},{"id":"solo.gold","name":"Celestial Gold","slug":"celestial-gold","group":"solo","legacy":0,"stage":"preview","available":true,"why":null,"layouts":["single"],"eyes":1,"price_class":"art","looks":{},"gate":"hard","rule":"lid","pick":false},{"id":"solo.radiance","name":"Radiance","slug":"radiance","group":"solo","legacy":0,"stage":"preview","available":true,"why":null,"layouts":["single"],"eyes":1,"price_class":"art","looks":{},"gate":"advisory","rule":"lid","pick":false},{"id":"solo.clean","name":"Clean Iris","slug":"clean-iris","group":"solo","legacy":0,"stage":"preview","available":true,"why":null,"layouts":["single"],"eyes":1,"price_class":"black","looks":{},"gate":"hard","rule":"lid","pick":false}]};
// the shipped sample now (sha256 4c4429b21f0d7d49...): both rules ok (fill n_step 95)
const NOW: Answer = {"pick":null,"reason":null,"eyes":[{"eye":1,"eye_id":"4c4429b21f0d7d49","cls":"own","pupil":"round","gate":{"lid":true,"fill":true},"why":[]}],"tiles":[{"id":"solo.powder","name":"Powder Burst","slug":"powder-burst","group":"solo","legacy":0,"stage":"preview","available":true,"why":null,"layouts":["single"],"eyes":1,"price_class":"art","looks":{},"gate":"advisory","rule":"lid","pick":false},{"id":"solo.universe","name":"Universe","slug":"universe","group":"solo","legacy":0,"stage":"preview","available":true,"why":null,"layouts":["single"],"eyes":1,"price_class":"art","looks":{"echo":"preview","vortex":"preview"},"gate":"hard","rule":"fill","pick":false},{"id":"solo.splash","name":"Splash","slug":"splash","group":"solo","legacy":0,"stage":"preview","available":true,"why":null,"layouts":["single"],"eyes":1,"price_class":"art","looks":{},"gate":"advisory","rule":"lid","pick":false},{"id":"solo.gold","name":"Celestial Gold","slug":"celestial-gold","group":"solo","legacy":0,"stage":"preview","available":true,"why":null,"layouts":["single"],"eyes":1,"price_class":"art","looks":{},"gate":"hard","rule":"lid","pick":false},{"id":"solo.radiance","name":"Radiance","slug":"radiance","group":"solo","legacy":0,"stage":"preview","available":true,"why":null,"layouts":["single"],"eyes":1,"price_class":"art","looks":{},"gate":"advisory","rule":"lid","pick":false},{"id":"solo.clean","name":"Clean Iris","slug":"clean-iris","group":"solo","legacy":0,"stage":"preview","available":true,"why":null,"layouts":["single"],"eyes":1,"price_class":"black","looks":{},"gate":"hard","rule":"lid","pick":false}]};

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  const view = (a: Answer) => retakeView({ tiles: a.tiles, eyes: a.eyes, selected: a.tiles[0] });
  const states = (a: Answer) => a.tiles.map((t) => `${t.id}:${tileState(t, a.eyes).kind}`);

  check('the sample eye of today: no retake card for a picture the visitor did not take (retakeView says none), and no tile is held back or greyed (every tile available, none in the gate, reseal or pupil state)',
    view(NOW) === null && NOW.tiles.every((t) => t.available && t.why === null) && NOW.tiles.every((t) => !['gate', 'reseal', 'pupil'].includes(tileState(t, NOW.eyes).kind)), JSON.stringify(states(NOW)));
  check('... the eye the server read says so: both rules pass and no reason code', NOW.eyes.length === 1 && NOW.eyes[0].gate.lid === true && NOW.eyes[0].gate.fill === true && NOW.eyes[0].why.length === 0, JSON.stringify(NOW.eyes));
  check('... and the Universe tile (the one that reads the fill rule) is one of them: available and ready for the demo eye',
    NOW.tiles.some((t) => t.id === 'solo.universe' && t.rule === 'fill' && t.gate === 'hard') && tileState(NOW.tiles.find((t) => t.id === 'solo.universe')!, NOW.eyes).kind !== 'gate', JSON.stringify(states(NOW)));

  // the failing eye is still handled as before: the file shipped before is exactly such an eye (it fails the fill rule only), so the card and the grey tile are what a visitor's
  // own eye with that defect gets
  const rv = view(OLD);
  // 2026-10-22: the page no longer shows the retake card or the held tile for such an eye (the tile is left out, src/try/picker.ts heldTile); the state below is what it reads
  check('an eye that fails the fill rule (the first sample file) still has a retake state for the eye and holds the Universe tile back, and no other tile (the gate is unchanged)',
    rv !== null && rv.eyes.join() === '1' && rv.holds === true && rv.why === 'fill_hard_edges' && rv.reasons.join() === 'lid'
    && OLD.tiles.filter((t) => !t.available).map((t) => t.id).join() === 'solo.universe' && tileState(OLD.tiles.find((t) => t.id === 'solo.universe')!, OLD.eyes).kind === 'gate', JSON.stringify([rv, states(OLD)]));
  return out;
}
