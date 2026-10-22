// The calm flow of /try (the owner, 2026-10-22, on his own Android phone on the live site): "someone photographs under a lamp, it is really not bad, and still it
// does not fit? ... we exist to RAISE the iris quality, not to tell every customer what does not fit", "maybe the slider should not vibrate and snap in the middle",
// "what is that Private Atelier?", "everything must be extremely simple and extremely clear". What this holds:
//   1. a photo the studio can restore goes straight on, whatever its verdict, Detail or lamp colour (src/try/shots.ts autoContinue); only what the engine cannot
//      restore stops (a circle that did not lock, a shot it blocked), and the numbers stay in the answer for the ranking and the server's log;
//   2. at most one calm line while the iris is restored (calmNote): the lamp colour, else the pupil reflection, else none;
//   3. no verdict pill, no Detail meter and no tips list on the page any more (the copy has no words for them), no tagline in the header of /try;
//   4. a drag of the Reveal never vibrates the phone (the snap itself is held by src/reveal/*.test.ts);
//   5. a style the gate holds back for these eyes is not a tile (src/try/picker.ts heldTile).
// The quality answer below is the REAL one the live server gave for the owner's own photo d01 on 2026-10-12 (verdict weak, Detail 29: "Silpna nuotrauka", "siekite 70+"
// on the old page), trimmed to the fields the page reads; the lamp answer is the same photo with the lamp's own words of api/analyze.py.
import { readFileSync } from 'node:fs';
import { COPY, T, setCopyLang } from '../../src/try/copy';
import { LANGS } from '../../src/shared/lang';
import { autoContinue, bestIndex, blockOf, calmNote, usable, type Analysis, type Quality } from '../../src/try/shots';
import { heldTile, type ServerEye, type ServerTile } from '../../src/try/picker';

type Row = [string, boolean, string?];
const read = (p: string) => readFileSync(new URL(`../../${p}`, import.meta.url), 'utf8');

const D01: Quality = {
  diameter_px: 337, sharpness: 97.7, fibre: 2.47, sharpness_label: 'sharp', occlusion_pct: 0, glare: true, locked: true, detail: 29, fibre_score: 3.36, glare_on_fibres_pct: 1.3,
  pupil_reflection: true, lamp_cast: false, lamp_message: null, verdict: 'weak', blocked: false, block_reason: null, pupil_size: 0.411,
  message: 'Small or soft, so more of the fine detail gets rebuilt. Closer and steadier gives a truer artwork.',
  tips: ['Move closer or use 2x zoom: the iris is 337 px, we want 420 px or more.', 'This came out soft. Use the back camera at 2x, tap the iris to focus, and keep the phone steady; front cameras cannot focus at this distance at all.'],
};
const LAMP_WORDS = {
  en: 'Lamp light is tinting your eye colour. Daylight from a window gives truer colour.',
  de: 'Lampenlicht verfälscht Ihre Augenfarbe. Tageslicht von einem Fenster gibt die Farbe echter wieder.',
  lt: 'Lempos šviesa iškraipo Jūsų akių spalvą. Dienos šviesa pro langą perteikia tikresnę spalvą.',
  hu: 'A lámpafény elszínezi a szemed színét. Egy ablakon beeső nappali fény valódibb színt ad.',
};
const shot = (q: Partial<Quality>): Analysis => ({ ok: true, ticket: 'work.x', iris: { cx: 0.5, cy: 0.5, r: 0.3 }, quality: { ...D01, ...q } });

export async function run(): Promise<Row[]> {
  const out: Row[] = [];
  const check = (name: string, ok: boolean, detail = '') => out.push([name, ok, detail]);
  setCopyLang('en');

  // ---- 1. the decision
  const weak = shot({});
  const lamp = shot({ verdict: 'good', lamp_cast: true, lamp_message: LAMP_WORDS.en, words: Object.fromEntries(LANGS.map((l) => [l, { message: D01.message, tips: [], lamp_message: LAMP_WORDS[l] }])) });
  check('a usable photo goes straight on to the restoration whatever its verdict: the owner\'s own d01 (weak, Detail 29), an ok one, a good one, and a lamp-tinted good one',
    autoContinue(weak) && autoContinue(shot({ verdict: 'ok', detail: 55 })) && autoContinue(shot({ verdict: 'good', detail: 88 })) && autoContinue(lamp));
  check('... a photo the studio cannot restore still stops: the circle did not lock, or the engine blocked it (each of its reasons)',
    !autoContinue(shot({ locked: false })) && ['too_blurry', 'too_dark', 'pupil_too_large', 'too_small', 'eyelid', 'something_new'].every((r) => !autoContinue(shot({ blocked: true, block_reason: r }))));
  check('... "goes on" and "can be restored" are one rule now (autoContinue is usable), so nothing else can park a usable photo on a screen of its own',
    [weak, lamp, shot({ verdict: 'ok' }), shot({ locked: false }), shot({ blocked: true })].every((a) => autoContinue(a) === usable(a)));
  check('... the numbers stay in the answer: the best of several shots is still the one with the better verdict and Detail (the ranking reads them, the page does not show them)',
    bestIndex([shot({ verdict: 'weak', detail: 20 }), shot({ verdict: 'good', detail: 80 }), shot({ verdict: 'ok', detail: 50 })]) === 1
    && bestIndex([shot({ verdict: 'good', detail: 90, lamp_cast: true }), shot({ verdict: 'ok', detail: 60 })]) === 1);

  // ---- 2. the one calm line while the iris is restored
  check('the lamp gets one calm line while the iris is restored: the server\'s own words in the page\'s language, else the page\'s fallback',
    LANGS.every((l) => { setCopyLang(l); return calmNote(lamp.quality) === LAMP_WORDS[l]; }) && (() => { setCopyLang('en'); return calmNote({ ...D01, lamp_cast: true, lamp_message: null, words: undefined }) === COPY.en.quality.lampFallback; })());
  setCopyLang('en');
  check('... the lamp line comes before the pupil note (at most ONE line), the pupil note alone when there is no lamp, and nothing at all otherwise',
    calmNote({ ...D01, lamp_cast: true, pupil_reflection: true, lamp_message: LAMP_WORDS.en }) === LAMP_WORDS.en && calmNote(D01) === T.quality.pupilNote
    && calmNote({ ...D01, pupil_reflection: false }) === null && calmNote(undefined) === null);

  // ---- 3. no verdict, no meter, no tips list, no tagline
  const tryApp = read('src/try/TryApp.tsx');
  check('the quality step and the shot collector show no verdict pill, no Detail meter and no tips list (the components are gone from the page)',
    !/\b(Verdict|DetailMeter|ShotNotes)\b/.test(tryApp) && !/visibleTips\(|meterBand\(|shownDetail\(/.test(tryApp) && !/T\.quality\.(verdicts|detail|aimFor|fibresResolved|continueAnyway)\b/.test(tryApp));
  check('... and the four dictionaries have no words for them any more ("Silpna nuotrauka", "Detalumas", "Siekite 70+", "Continue anyway" and their twins), nor a badge per block reason',
    LANGS.every((l) => {
      const q = COPY[l].quality as Record<string, unknown>;
      return !('verdicts' in q) && !('detail' in q) && !('aimFor' in q) && !('fibresResolved' in q) && !('continueAnyway' in q) && !('picked' in q)
        && Object.values(COPY[l].quality.blocks).every((b) => !('badge' in b)) && !('badge' in COPY[l].quality.blockedOther) && !('headerDetail' in COPY[l].collector);
    }) && !/Silpna nuotrauka|Siekite \$\{|Weak photo|Schwaches Foto|Gyenge fotó/.test(read('src/try/copy.ts') + read('src/try/copy.lt.ts') + read('src/try/copy.hu.ts')));
  check('the header of /try holds the logo and the language switch and no tagline: no "Private Atelier" in /try\'s dictionaries or its page, no header.tag',
    LANGS.every((l) => !('tag' in COPY[l].header)) && !/Private Atelier/.test(read('src/try/copy.ts') + read('src/try/copy.lt.ts') + read('src/try/copy.hu.ts') + tryApp) && !/T\.header\.tag/.test(tryApp));
  check('a blocked photo keeps its one reason line and its retake steps (the engine\'s hard blocks are the only stop), in every language',
    LANGS.every((l) => { setCopyLang(l); const b = blockOf(shot({ blocked: true, block_reason: 'too_blurry' })); return !!b && b.reason.length > 30 && b.steps.length === 4 && b.title.length > 10; }));
  setCopyLang('en');

  // ---- 4. the Reveal's drag
  const reveal = read('src/reveal/Reveal.tsx');
  check('a drag of the Reveal never vibrates the phone and never snaps (no navigator.vibrate, no snapCut, no entersSnap); it reads dragCut', !/vibrate|snapCut|entersSnap/.test(reveal) && /dragCut\(/.test(reveal));

  // ---- 5. a held style is not a tile
  const tile = (id: string, o: Partial<ServerTile> = {}): ServerTile => ({ id, name: id, slug: id, group: 'solo', legacy: 0, stage: 'preview', available: true, why: null, layouts: ['single'], eyes: 1, price_class: 'art', looks: {}, gate: 'advisory', rule: 'lid', pick: false, ...o });
  const eyes: ServerEye[] = [{ eye: 1, eye_id: 'a', cls: 'own', pupil: 'round', gate: { lid: true, fill: false }, why: ['fill_rim_sector'] }];
  check('a style the gate holds back for these eyes (Universe and its fill rule, the owner\'s case), a reseal and a pupil shape are held tiles; an available one, a Soon one and an advisory one that warns are not',
    heldTile(tile('solo.universe', { available: false, why: 'gate', gate: 'hard', rule: 'fill' }), eyes) && heldTile(tile('solo.clean', { available: false, why: 'reseal', gate: 'hard' }), eyes)
    && heldTile(tile('duo.kiss', { available: false, why: 'bar_pupil' }), eyes) && !heldTile(tile('solo.powder'), eyes) && !heldTile(tile('solo.gold', { stage: 'live', gate: 'hard' }), eyes)
    && !heldTile(tile('solo.splash', { gate: 'advisory' }), [{ ...eyes[0], gate: { lid: false, fill: true } }]));
  return out;
}
