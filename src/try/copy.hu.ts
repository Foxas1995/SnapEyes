// Hungarian ("hu") copy for /try: every key of src/try/copy.ts `en`, in the same structure. Friendly "te", the
// landing page's words (src/landing/copy.hu.ts): hátsó kamera, szelfikamera, 2x-es zoom, felvétel (shot), fotó,
// előnézet, alkotás, helyreállít, rostok, mesterséges intelligencia / MI, művészi háttér. Decimal comma (3,7).
// Hungarian grammar the English helpers do not need:
//  - a noun stays singular after a number (2 szem, 5 fotó), so "eye/eyes" collapses to "szem";
//  - "Eye 3" is an ordinal, "3. szem";
//  - the article before a number depends on how the number is spoken: "az 1.", "az 5.", "az 50.", else "a" (az());
//  - "-szer/-szor/-ször" after a number follows how the number is spoken (szer()).
// Two deliberate differences from the English, for honesty in Hungary („íriszfotózás” means studio
// macro photography there): the "Studio macro" badge and step are „Részletes helyreállítás” / „Finom rostok
// helyreállítása”, so nothing here reads as a studio macro photo.
// The buy button carries only „Megrendelés fizetési kötelezettséggel” (the label of the owner's Hungarian launch plan: an "equivalent,
// unambiguous" wording under 45/2014. Korm. rendelet 15. § (2), whose own words are „fizetési kötelezettséggel járó
// megrendelés”; Art. 8(2) Directive 2011/83/EU), without the price: the card shows the price right above it. The
// click that binds is Stripe's pay button; api/_lib/pay_hu.py SUBMIT_NOTE_HU puts the decree's words right above it.
import type { BlockCopy, BlockReason, TryCopy } from './copy';
import type { Layout, LightAnswer } from './multi';
import { CONTACT_EMAIL } from '../landing/config';
import { CHECKOUT_LEGAL } from '../shared/legal';
import { TRANSPARENCY_HU } from '../landing/copy.hu';

/** "Az" or "A" before a number, as it is spoken: az 1., az 5., az 50-59., else a (numbers up to 99, all this page uses). */
export const Az = (n: number) => (n === 1 || n === 5 || (n >= 50 && n <= 59) ? 'Az' : 'A');
export const az = (n: number) => Az(n).toLowerCase();

/** The suffix of "n times" after a number written with digits, as the number is spoken. A decimal is read with
 *  "tized" or "fél" (3,7: három egész hét tized; 2,5: két és fél), so it always takes -szer: 3,7-szer, 2,5-szer.
 *  A whole number follows its last spoken word: 2-szer, 3-szor, 5-ször, 6-szor, 8-szor; a round number its tens or
 *  hundreds: 10-szer (tíz), 20-szor (húsz), 30-szor, 40-szer, 50-szer, 60-szor, 70-szer, 80-szor, 90-szer,
 *  100-szor (száz), 1000-szer (ezer). */
export function szer(num: string): string {
  const s = num.trim();
  if (/[.,]/.test(s)) return 'szer';
  const digits = s.replace(/\D/g, '');
  if (!digits) return 'szer';
  const last = digits.slice(-1);
  if (last !== '0') return last === '5' ? 'ször' : ['3', '6', '8'].includes(last) ? 'szor' : 'szer';
  if (/000$/.test(digits)) return 'szer';                                        // ezer
  if (/00$/.test(digits)) return 'szor';                                         // száz
  return ['2', '3', '6', '8'].includes(digits.slice(-2, -1)) ? 'szor' : 'szer';  // húsz, harminc, hatvan, nyolcvan
}

/** "4,0" -> "4": a whole ratio is written without its ",0" (4-szer, not 4,0-szer). */
const dropZero = (num: string) => num.trim().replace(/[.,]0$/, '');

/** "1.", "1. és 3.", "1., 2. és 4.": ordinals in a list. */
const ordList = (xs: number[]) => {
  const o = xs.map((x) => `${x}.`);
  return o.length < 2 ? (o[0] ?? '') : `${o.slice(0, -1).join(', ')} és ${o[o.length - 1]}`;
};

// the capture guide's steps, word for word the same on the capture screen and in the retake cards (src/try/copy.ts)
const LIGHT = 'Nappali fény egy ablakból, oldalról (nem szemből). Se lámpa, se vaku.';
const CAMERA = 'Hátsó kamera 2x-es zoommal, kb. 10 cm-re a szemtől.';
const FOCUS = 'Koppints az íriszre a képernyőn, hogy a kamera arra állítsa az élességet.';
const STEADY = 'Tartsd stabilan a telefont (támaszd meg a könyöködet), és készíts 3-5 felvételt.';
const DARK_LIGHT = 'Több fénynél a sötét írisz mintázata is előtűnik: nappal állj közel egy világos ablakhoz, úgy, hogy az ablak oldalt legyen (ne közvetlen napfényben). Se lámpa, se vaku.';
const HU_DECIMAL = new Intl.NumberFormat('hu-HU', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

export const hu: TryCopy = {
  lang: 'hu',
  meta: {
    title: 'SnapEyes Studio - Íriszalkotás a szemfotódból',
    description: 'Fotózd le a szemed a telefonoddal, és kb. egy perc alatt meglátod a saját íriszedet helyreállítva, kozmikus műalkotásként.',
  },
  switchLabel: 'Nyelv',
  dec1: (v: number) => HU_DECIMAL.format(v),

  header: {
    tag: 'Private Atelier · előnézet',
    study: 'Családi teszt',
  },

  errors: {
    tooLarge: 'Ez a fotó túl nagy. Próbáld újra egy szokásos kamerás fotóval.',
    timeout: 'Ez nálunk túl sokáig tartott. Kérjük, próbáld újra.',
    notResponding: 'A stúdió most nem válaszol. Kérjük, próbáld újra egy kicsit később.',
    requestFailed: (status: number) => `A kérés nem sikerült (${status})`,
    unreadable: 'Ezt a képet nem tudtuk beolvasni',
    noEyeAny: 'Egyik fotón sem találtunk szemet.',
    noEyeShot: 'Ezen a felvételen nem találtunk szemet.',
    noEye: 'Nem található szem',
    keepFailed: 'Hiba történt a felvételeid mentésekor. Kérjük, készítsd el újra a fotót.',
  },

  capture: {
    titleA: 'A TE SZEMED, ',
    titleB: 'TÉNYLEG.',
    lead: 'Fotózd le az egyik szemed. Megkeressük az íriszt, eltávolítjuk a tükröződéseket, helyreállítjuk a rostokat, és műalkotássá formáljuk. Kb. egy perc.',
    addTitle: (n: number) => `${n}. szem hozzáadása`,
    addLead: 'A párod, a gyermeked vagy a másik szemed. Ugyanazok a lépések, mint az előbb: készíts néhány felvételt, és a legjobbat megtartjuk.',
    takeTurns: 'Egymást fotózzátok? Felváltva csináljátok: az egyik tartja a telefont, a másik egyenesen előre néz. Aztán cseréljetek.',
    helper: 'Kettesben a legkönnyebb: az egyik tartja a telefont, a másik egyenesen előre néz.',
    retakeTitle: (n: number) => `${n}. szem újrafotózása`,
    retakeLead: 'Ugyanazok a lépések, mint az előbb. Az új felvételed lecseréli ezt a szemet az alkotáson; addig minden marad, ahogy van.',
    back: (n: number) => `Vissza az alkotásodhoz (${n} szem)`,
    sampleButton: 'MI által generált mintaszem',
    sampleLoadFailed: 'A mintaszemet nem sikerült betölteni.',
    thumbLabel: (i: number) => `${i}. szem`,
    sampleThumb: 'MI által generált minta',
    steps: [
      { title: '1. Hátsó kamera', text: '2x-es vagy 3x-os zoom, ne a szelfikamera.' },
      { title: '2. 10 cm távolság', text: 'Az írisz töltse ki a kép harmadát.' },
      { title: '3. Ablakfény', text: LIGHT },
      { title: '4. Élességállítás', text: 'Koppints az íriszre a képernyőn, maradj mozdulatlan, és fotózz.' },
    ],
    stepsOpen: 'Tágra nyitott szem. ',
    stepsOpenMore: 'Nézz egyenesen előre, és egy ujjheggyel óvatosan emeld meg a felső szemhéjadat, hogy se a szemhéj, se a szempillák ne takarják az íriszt.',
    stepsShots: 'Készíts 3-5 felvételt, és küldd el mindet.',
    stepsShotsMore: ' A felvételek között fordulj egy kicsit. Mindegyiket megmérjük, és a legélesebbet használjuk; egy valódi teszten a legjobb felvételen 3,7-szer annyi részlet volt, mint a leggyengébben.',
    takePhoto: 'Fotó készítése',
    pickShots: '3-5 fotó kiválasztása',
    consent: 'A szemfotóm és az eredmény mentése a SnapEyes tanító adattárába, hogy a helyreállítások idővel jobbak legyenek. Névtelenül, név és arc nélkül. Bármikor kérheted a törlésüket.',
  },

  working: {
    finding: 'Keressük az íriszed…',
    locating: 'Az írisz és a pupilla megkeresése',
    measuringSize: 'Méret és élesség mérése',
    checking: (n: number, done: number) => `${n} fotó ellenőrzése: ${done}/${n} kész`,
    measuringShot: (k: number, max: number) => `Felvétel mérése: ${k}/${max}`,
    restoring: 'Az íriszed helyreállítása…',
    restoringEye: (n: number) => `${n}. szem helyreállítása…`,
    cut: 'Az íriszed kivágása',
    reflections: 'Tükröződések eltávolítása',
    macro: 'Finom rostok helyreállítása (kb. 30 mp)',
    composing: (n: number) => (n > 1 ? `Az alkotásod összeállítása ${n} szemmel` : 'Az alkotásod összeállítása'),
    sampleCaption: 'MI által generált minta',
    yourIris: 'Az íriszed',
    elapsed: (s: number) => `${s} mp`,
  },

  quality: {
    retake: 'Újrafotózás',
    continueAnyway: 'Folytatás így is',
    notCentred: 'Ezen a fotón az írisz nincs középen, ezért nem állítható helyre. Kérjük, fotózd újra úgy, hogy az egyik szemed kitöltse a képet.',
    blocks: {
      too_blurry: {
        badge: 'Túl elmosódott',
        title: 'Túl elmosódott ahhoz, hogy a saját íriszedet helyreállítsuk',
        reason: 'Ezen a fotón nem látszik eléggé a saját íriszmintázatod ahhoz, hogy helyreállítsuk, ezért nem használjuk.',
        error: 'Ez a fotó túl elmosódott ahhoz, hogy a saját íriszedet helyreállítsuk. Kérjük, fotózd újra az alábbi lépések szerint.',
        retakeLine: 'Ez a felvétel túl elmosódott ahhoz, hogy a saját íriszedet helyreállítsuk. Fotózd újra nappali fénynél, oldalt lévő ablaknál, a hátsó kamerával 2x-es zoommal: koppints az íriszre az élességállításhoz, és tartsd stabilan a telefont.',
        thumb: 'elmosódott',
        steps: [LIGHT, CAMERA, FOCUS, STEADY],
      },
      too_dark: {
        badge: 'Túl sötét',
        title: 'Túl sötét ahhoz, hogy látsszon a saját íriszmintázatod',
        reason: 'Az íriszed sötét, és túl kevés volt a fény ahhoz, hogy a saját mintázata látsszon, ezért ezt a fotót nem használjuk.',
        error: 'Ez a fotó túl sötét ahhoz, hogy látsszon a saját íriszmintázatod. Kérjük, fotózd újra az alábbi lépések szerint.',
        retakeLine: 'Ez a felvétel túl sötét ahhoz, hogy látsszon a saját íriszmintázatod. Fotózd újra nappal, egy világos ablak közelében, úgy, hogy az ablak oldalt legyen. Se lámpa, se vaku.',
        thumb: 'sötét',
        steps: [DARK_LIGHT, CAMERA, FOCUS, STEADY],
      },
      pupil_too_large: {
        badge: 'Túl tág pupilla',
        title: 'A pupillád túl tág ahhoz, hogy az íriszedet helyreállítsuk',
        reason: 'Ezen a fotón annyira tág a pupillád, hogy túl kevés látszik körülötte az íriszedből, ezért nem használjuk.',
        error: 'Ezen a fotón túl tág a pupillád ahhoz, hogy a saját íriszedet helyreállítsuk. Kérjük, fotózd újra az alábbi lépések szerint.',
        retakeLine: 'Ezen a felvételen túl tág a pupillád. Több fénynél kisebb lesz: fotózd újra nappal, egy világos ablak közelében, ne vakuval.',
        thumb: 'pupilla',
        steps: [
          'Több fénynél kisebb lesz a pupillád: nappal állj közel egy világos ablakhoz, úgy, hogy az ablak oldalt legyen (ne közvetlen napfényben). Vakut ne használj.',
          'Fotózás előtt hagyj a szemednek egy percet ebben a fényben, hogy a pupilla összeszűkülhessen. Sötétedés után kapcsold fel az összes mennyezeti lámpát.',
          CAMERA,
          'Koppints az íriszre a képernyőn az élességállításhoz, tartsd stabilan a telefont, és készíts 3-5 felvételt.',
        ],
      },
      too_small: {
        badge: 'Túl kicsi',
        title: 'Az íriszed túl kicsi ezen a fotón',
        reason: 'Az íriszed olyan kicsi ezen a fotón, hogy túl kevés látszik a saját mintázatából, ezért nem használjuk.',
        error: 'Az íriszed túl kicsi ezen a fotón ahhoz, hogy helyreállítsuk. Kérjük, fotózd újra közelebbről, az alábbi lépések szerint.',
        retakeLine: 'Az íriszed túl kicsi ezen a felvételen. Menj közelebb: hátsó kamera 2x-es zoommal, kb. 10 cm-re a szemedtől, hogy az írisz a kép kb. harmadát kitöltse.',
        thumb: 'kicsi',
        steps: [
          'Menj közelebb: hátsó kamera 2x-es zoommal, kb. 10 cm-re a szemtől, hogy az írisz a kép kb. harmadát kitöltse.',
          LIGHT,
          FOCUS,
          STEADY,
        ],
      },
      // a lid over part of the iris (api/analyze.py EYELID_BLOCK_PCT): the studio would have to paint iris over it. The words
      // of the capture guide's open-eye step (stepsOpen, stepsOpenMore) and of api/_lib/analyze_hu.py TEXT_HU["eyelid"]
      eyelid: {
        badge: 'Takarja a szemhéj',
        title: 'A szemhéjad eltakarja az íriszed egy részét',
        reason: 'Ezen a fotón az íriszed egy részét a szemhéjad vagy a szempilláid takarják, ezért nem használjuk.',
        error: 'A szemhéjad ezen a fotón eltakarja az íriszed egy részét. Kérjük, fotózd újra az alábbi lépések szerint.',
        retakeLine: 'A szemhéjad ezen a felvételen eltakarja az íriszed egy részét. Nézz egyenesen a kamerába, nyisd tágra a szemed, és egy ujjheggyel óvatosan emeld meg a felső szemhéjadat.',
        thumb: 'szemhéj',
        steps: [
          'Nézz egyenesen a kamerába, ne ferdén: oldalra nézve a felső szemhéj rácsúszik az íriszre.',
          'Nyisd tágra a szemed, és egy ujjheggyel óvatosan emeld meg a felső szemhéjadat, hogy se bőr, se szempilla, se szempillaspirál ne lógjon az íriszre.',
          CAMERA,
          'Koppints az íriszre a képernyőn az élességállításhoz, tartsd stabilan a telefont, és készíts 3-5 felvételt.',
        ],
      },
    } satisfies Record<BlockReason, BlockCopy>,
    blockedOther: {
      badge: 'Kevés a részlet',
      title: 'Túl kevés a részlet ahhoz, hogy a saját íriszedet helyreállítsuk',
      reason: 'Ezen a fotón nem látszik eléggé a saját íriszmintázatod ahhoz, hogy helyreállítsuk, ezért nem használjuk.',
      error: 'Ezen a fotón nem látszik eléggé a saját íriszed ahhoz, hogy helyreállítsuk. Kérjük, fotózd újra az alábbi lépések szerint.',
      retakeLine: 'Ezen a felvételen nem látszik eléggé a saját íriszed ahhoz, hogy helyreállítsuk. Készíts egy újat a fotózási útmutató szerint.',
      thumb: 'újra',
      steps: [LIGHT, CAMERA, FOCUS, STEADY],
    } satisfies BlockCopy,
    guideTitle: 'Az újrafotózáshoz',
    noneUsable: (n: number) => (n === 2 ? 'Mindkét fotót ellenőriztük, de egyik sem használható.' : `Mind ${az(n)} ${n} fotót ellenőriztük, de egyik sem használható.`),
    shotUnusable: 'Ez a felvétel nem használható. Készíts egy újat a fenti tanácsok szerint.',
    shotsUnusable: 'Ezek közül még egyik felvétel sem használható. Készíts egy újat a fenti tanácsok szerint.',
    fullUnusable: (max: number) => `Ennek ${az(max)} ${max} felvételnek egyike sem használható. Egy újabb felvétellel új sorozatot kezdesz.`,
    verdicts: { good: 'Remek fotó', ok: 'Használható fotó', weak: 'Gyenge fotó' },
    detectedIris: 'Felismert írisz',
    detail: 'Részletesség',
    aimFor: (d: number) => `Cél: ${d}+`,
    fibresResolved: 'A rostok kivehetők',
    picked: (of: number, used: number) => `${of} fotót hasonlítottunk össze, és a legjobbat használtuk (${used}. fotó).`,
    pickedRatio: (ratio: string) => ` Ezen ${dropZero(ratio)}-${szer(dropZero(ratio))} annyi rostrészlet látszik, mint a legelmosódottabbon.`,
    tryRetake: 'Újrafotózás',
    pupilNote: 'A pupillán lévő tükröződés nem gond: a pupillát tiszta sötétként építjük újra.',
    lampFallback: 'A lámpafény elszínezi a szemfehérjédet, ezért a színek melegebbnek tűnhetnek, mint amilyenek valójában.',
    closer: 'Menj közelebb, vagy zoomolj rá, hogy az írisz nagyobb részt töltsön ki a képből.',
  },

  collector: {
    header: (n: number, max: number) => `Felvétel: ${n}/${max}`,
    headerDetail: (d: number) => ` · Részletesség ${d}`,
    shotAlt: (n: number) => `${n}. felvétel`,
    bestLabel: (k: number, d?: number) => `${k}. felvétel${d !== undefined ? ` (részletesség ${d})` : ''}`,
    full: (max: number, best: string) => `Ez már ${max} felvétel. A legjobbat használjuk: ${best}.`,
    more: (left: number) => `Még legfeljebb ${left} felvételt készíthetsz. Mindegyiket megmérjük, és a legjobbat tartjuk meg.`,
    sharpEnough: 'Ez elég éles ahhoz, hogy használjuk.',
    bestSoFar: 'Ez az eddigi legjobb felvételed.',
    lampSkipped: (n: number, best: string) => `A lámpafény elszínezte ${az(n)} ${n}. felvételt, ezért a legjobb, valódi színű felvételedet használjuk: ${best}.`,
    bestIs: (best: string) => `Az eddigi legjobb: ${best}. Ezt fogjuk használni.`,
    lastFailed: (note: string) => `Az utolsó felvétel nem használható. ${note} Az eddigi legjobb felvételed megmarad.`,
    takeAnother: 'Még egy felvétel',
    useBest: 'A legjobbat használom',
    useThis: 'Ezt használom',
    startOver: 'Újrakezdés',
  },

  result: {
    beforeAfter: 'Előtte / utána',
    eyes: 'Szemek ezen az alkotáson',
    eyeLabel: (i: number) => `${i}. szem`,
    sampleLabel: 'MI által generált minta',
    yourPhoto: 'A fotód',
    samplePhoto: 'MI által generált minta',
    after: 'Helyreállítva',
    sliderBefore: 'A fotód',
    sliderAfter: 'Helyreállítva',
    // src/landing/copy.hu.ts TRANSPARENCY_HU, word for word
    transparency: TRANSPARENCY_HU,
    sampleNote: 'Ez a szem az MI által generált minta, nem valódi fotó. A saját fotóddal a szín a te fotódból származik.',
    colourOff: 'A színellenőrzésünk szerint ez a helyreállítás eltért a fotódtól: világosabbnak vagy sötétebbnek tűnhet, mint a szemed. Egy újrafotózás lágy nappali fényben általában megoldja.',
    retakeEye: (i: number) => `${i}. szem újrafotózása`,
    retakeOnly: 'A szem újrafotózása',
    replaceSample: 'Használd inkább a saját szemed',
    removed: (i: number) => `${i}. szem eltávolítva.`,
    undo: 'Visszavonás',
    sampleArtwork: 'Mintaalkotás',
    sampleBadge: 'MI által generált minta',
    // baked into the preview image (the engine's caption title, at most 40 characters): 23 characters
    sampleTitle: 'MI által generált minta',
    sampleArtworkNote: 'Kizárólag az MI által generált mintaszemből készült, nem valódi fotóból.',
    mixedArtworkNote: 'Ez az alkotás tartalmazza az MI által generált mintaszemet, amely nem valódi fotó.',
    drag: 'Húzd el a csúszkát.',
    irisPx: (px: number) => `Írisz a fotódon: ${px} px.`,
    reflection: 'Tükröződés eltávolítva.',
    upscaled: 'Kis fotó: helyreállítás előtt felnagyítva.',
    badgeMacro: 'Részletes helyreállítás',
    badgeFallback: 'Csak hű nagyítás',
    artwork: 'Az alkotásod',
    composing: 'Összeállítás…',
    composeFailed: 'Ezt az előnézetet nem sikerült összeállítani.',
    previewReduced: 'Az előnézet kicsinyített és vízjeles.',
    previewFile: (square: boolean): string => (square
      ? 'A fájlod: 4096 px, elég éles a legfeljebb 50 x 50 cm-es nyomtatáshoz.'
      : 'A fájlod: 4096 px a hosszabbik oldalán, elég éles olyan nyomtatáshoz, amelynek hosszabbik oldala legfeljebb 50 cm.'),
    retry: 'Próbáld újra',
    layout: 'Elrendezés',
    layouts: {
      single: 'Egy szem', duo: 'Egymás mellett', fusion: 'Összeolvadás', triangle: 'Háromszög', row: 'Egy sorban', grid: 'Rács', galaxy: 'Galaxis',
    } satisfies Record<Layout, string>,
    style: 'Stílus',
    namesPlaceholder: 'Nevek vagy felirat (nem kötelező)',
    save: 'Előnézet mentése',
    // ASCII only, as the English and German names are
    fileName: (style: string, n: number, sample: boolean) => `snapeyes-elonezet-${style}-${n}-szem${sample ? '-mi-altal-generalt-minta' : ''}.jpg`,
    addSecond: 'Második szem hozzáadása',
    addAnother: 'Újabb szem hozzáadása',
    addHint: (left: number) => `A párod, a gyermeked vagy a másik szemed. Még ${left} szem fér el ezen az alkotáson.`,
    full: (max: number) => `Ez ${max} szem: ennél több nem fér el egy alkotáson.`,
    remove: (i: number) => `${i}. szem eltávolítása`,
    startOver: 'Újrakezdés',
    confirmStartOver: (n: number) => `Elveted mind ${az(n)} ${n} szemet, és újrakezded?`,
    stored: 'Mentve a tanító adattárba',
  },

  price: {
    title: 'Az alkotás ára',
    oneEye: (style: string) => `1 szem · ${style}`,
    duo: 'Couple Duo · 2 szem',
    many: (n: number) => `${n} szem · Couple Duo + ${n - 2} további`,
    oneEyeOther: (studioBlack: string, art: string) => `1 szem: ${studioBlack} Studio Black stílusban, ${art} művészi háttérrel.`,
    duoOffer: (duo: string) => `Egy második szemmel Couple Duo páros kép lesz belőle: ${duo} mindkettőért.`,
    extra: (duo: string, extra: string, max: number) => `Couple Duo ${duo}, utána +${extra} minden további szemért, legfeljebb ${max} szemig.`,
    // src/landing/copy.hu.ts pricing.notice, word for word
    notice: 'A rendelés hamarosan indul: az előnézeted már ma ingyenes.',
    footnote: 'Egy vízjel nélküli digitális fájlt kapnál, a hosszabbik oldalán 4096 px méretben. Az árak euróban értendők.',
    footnoteAud: 'Egy vízjel nélküli digitális fájlt kapnál, a hosszabbik oldalán 4096 px méretben. Az árak ausztrál dollárban (A$) értendők.',
    footnoteHuf: 'Egy vízjel nélküli digitális fájlt kapnál, a hosszabbik oldalán 4096 px méretben. Az árak forintban értendők.',
    demo: 'Ez egy bemutató az MI által generált mintaszemmel. Próbáld ki a saját szemeddel, hogy lásd az árat.',
    sampleNotCounted: (k: number) => (k === 1
      ? 'Az MI által generált mintaszem nem része a rendelésnek, ezért nem számoljuk bele.'
      : `${Az(k)} ${k} MI által generált mintaszem nem része a rendelésnek, ezért nem számoljuk bele.`),
  },

  buy: {
    // the label alone (see the header); the price stays in the card's head
    button: (_price: string) => CHECKOUT_LEGAL.hu.continueButton,
    next: `A „${CHECKOUT_LEGAL.hu.continueButton}” gomb a Stripe biztonságos fizetési oldalára visz. Ott megadod az e-mail-címed, és amikor a fizetési gombbal jóváhagyod a fizetést, a megrendelésed kötelező érvényűvé válik. A fájlod elkészítését azután kezdjük meg, hogy elküldtük a rendelésed visszaigazoló e-mailjét, ez általában a fizetés után egy percen belül megtörténik.`,
    waitPreview: 'Ennek a választásnak az előnézete még készül. Amint látod, rendelhetsz.',
    previewFailed: 'Kérjük, előbb töltsd be ennek a választásnak az előnézetét (fent: „Próbáld újra”), hogy lásd, mit rendelsz.',
    steps: {
      sync: 'A rendelésed ellenőrzése…',
      upload: (i: number, n: number) => (n > 1 ? `Szem feltöltése: ${i}/${n}…` : 'A szemed feltöltése…'),
      arrange: 'A szemek elrendezése…',
      checkout: 'A biztonságos fizetési oldal megnyitása…',
    },
    sample: (k: number): string => (k === 1
      ? 'Az MI által generált mintaszem nem rendelhető meg. Cseréld le a saját szemedre, hogy megrendelhesd ezt az alkotást.'
      : 'Az MI által generált mintaszemek nem rendelhetők meg. Cseréld le őket valódi szemekre, hogy megrendelhesd ezt az alkotást.'),
    replaceSampleEye: (i: number) => `${i}. szem cseréje a sajátodra`,
    // api/_lib/iris.py TICKET_TTL: an eye's draft is accepted only with its photo's 15-minute work ticket
    stale: (list: number[], total: number) => (total === 1
      ? 'A fotódat több mint 15 perce készítetted. Egy fotó az elkészítése után 15 percig rendelhető meg, ezért a rendeléshez kérjük, fotózd újra.'
      : `${Az(list[0] ?? 0)} ${ordList(list)} szemet több mint 15 perce fotóztad. Egy fotó az elkészítése után 15 percig rendelhető meg, ezért a rendeléshez kérjük, fotózd újra${list.length === 1 ? '' : ' őket'}.${list.length < total ? ' A többi szem marad, ahogy van.' : ''}`),
    cancelled: 'Fizetés megszakítva. Nem történt terhelés. Az alkotásod még itt van: módosíthatod, vagy újra megrendelheted.',
    cancelledLost: 'Fizetés megszakítva. Nem történt terhelés. Ez az oldal nem tudta megőrizni az előnézetedet, ezért kérjük, készítsd el újra a fotódat.',
    close: 'Bezárás',
    errors: {
      network: 'Nem sikerült elérni a SnapEyes szolgáltatást. Kérjük, ellenőrizd az internetkapcsolatodat, és próbáld újra.',
      busy: 'A fizetési szolgáltatás nem válaszolt. Kérjük, próbáld újra egy kicsit később.',
      payments: `Nem sikerült megnyitni a fizetési oldalt. Kérjük, próbáld újra később, vagy írj nekünk: ${CONTACT_EMAIL}.`,
      too_large: 'Az egyik szemedről készült felvétel túl nagy a feltöltéshez. Kérjük, fotózd újra azt a szemet.',
      paused: `Az új rendeléseket mára szüneteltetjük: elértük a napi feltöltési korlátot. Nem történt terhelés. Kérjük, próbáld újra holnap, vagy írj nekünk: ${CONTACT_EMAIL}.`,
      too_many: `Ez a rendelés mára elérte a feltöltési korlátját (30 feltöltés, az újrafotózásokkal együtt). Nem történt terhelés. Kérjük, próbáld újra holnap, vagy írj nekünk: ${CONTACT_EMAIL}.`,
      failed: `Hiba történt a rendelésed előkészítése közben. Kérjük, próbáld újra, vagy írj nekünk: ${CONTACT_EMAIL}.`,
      closed: 'A rendelés még nem indult el.',
    },
    footnote: 'Egy digitális fájl (JPEG), a hosszabbik oldalán 4096 px, vízjel nélkül. Ez a végső ár: nem vagyunk áfafizetőként nyilvántartásba véve, ezért áfát nem számítunk fel.',
    footnoteAud: 'Egy digitális fájl (JPEG), a hosszabbik oldalán 4096 px, vízjel nélkül. Ez a teljes ár: GST-t nem számítunk fel.',
  },

  study: {
    title: (shot: number, photos: number) => (photos > 1 ? `Családi teszt · ${shot - photos + 1}-${shot}. fotó` : `Családi teszt · ${shot}. felvétel`),
    light: 'A felvétel fénye',
    lights: {
      window_daylight: 'Nappali fény az ablaknál', room_lamp: 'Szobalámpa', phone_torch: 'A telefon zseblámpája', someone_helped: 'Valaki segített',
    } satisfies Record<LightAnswer, string>,
    comfort: 'Mennyire volt könnyű? 1 nehéz, 5 könnyű',
    skip: 'Kihagyás',
    thanks: 'Köszönjük! Ezeket a válaszokat a következő fotóddal küldjük el.',
    pending: (shots: number[]) => `Családi teszt: ${az(shots[0] ?? 0)} ${ordList(shots)} felvételre adott válaszaidat még nem küldtük el. A következő fotóddal mennek, például amikor újabb szemet adsz hozzá. Ha most bezárod az oldalt, elvesznek.`,
  },
};
