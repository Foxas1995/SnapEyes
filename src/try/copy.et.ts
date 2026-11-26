// Estonian ("et") copy for /try: every key of src/try/copy.ts `en`, in the same structure. Informal singular "sina",
// as Estonian consumer web shops write, and the landing page's words (src/landing/copy/et.json): tagakaamera,
// esikaamera, 2x suurendus, võte (shot), foto, eelvaade, kunstiteos, taastama, kiud, tehisintellekt ("AI" only in the
// two shortest labels, where the full word does not fit). Decimal comma (3,7).
// Estonian grammar the English helpers do not need (src/shared/et.ts):
//  - a noun after a number takes one of two forms: 1 silm, 2 silma; 1 võte, 3 võtet; 1 foto, 3 fotot (etForm());
//  - an eye is numbered after the noun, as in English: "silm 3", and a list shares the plural: "silmad 1 ja 3";
//  - a style name is not declined, so a sentence puts "stiil" or "variant" before it and declines that word.
// The server's own sentences (quality.message, tips) come from api/analyze.py in the request's language
// (api/_lib/analyze_et.py TEXT_ET, the twin of TEXT_HR).
// The buy button carries only „Tellimus koos maksekohustusega“ (the words of Art. 8(2) Directive 2011/83/EU as
// Võlaõigusseadus § 62¹ lg 3 has them), without the price: the card shows the price right above it. The click that
// binds is Stripe's pay button; api/_lib/pay_et.py SUBMIT_NOTE_ET (the twin of SUBMIT_NOTE_HR) puts the statutory
// words right above it.
import type { BlockCopy, BlockReason, TryCopy } from './copy';
import type { LightAnswer } from './multi';
import { CONTACT_EMAIL } from '../landing/config';
import { CHECKOUT_LEGAL } from '../shared/legal';
import { TRANSPARENCY_ET } from '../landing/copy.et';
import { dec1Et, etForm, fotod, margid, silmaGen, silmad, tahed, votted, vottedEla } from '../shared/et';

/** "1", "1 ja 3", "1, 2 ja 4": the numbers of a list; the noun stands before it once ("silmad 1 ja 3"). */
const jaList = (xs: number[]) => (xs.length < 2 ? String(xs[0] ?? '') : `${xs.slice(0, -1).join(', ')} ja ${xs[xs.length - 1]}`);

// the capture guide's steps, word for word the same on the capture screen and in the retake cards (src/try/copy.ts)
const LIGHT = 'Päevavalgus aknast või taskulamp, küljelt. Ilma toalambi ja välguta.';
const CAMERA = 'Tagakaamera 2x suurendusega, umbes 10 cm kaugusel silmast.';
const FOCUS = 'Puuduta ekraanil iirist, et kaamera sellele teravustaks.';
const STEADY = 'Hoia telefoni paigal (toeta küünarnukid millelegi) ja tee 3-5 võtet.';
// the first retake step for a dark iris: the same light, only closer to the window
const DARK_LIGHT = 'Rohkem valgust toob tumeda iirise esile: seisa päevavalguses heleda akna lähedal, nii et aken jääb küljele (mitte otsese päikese käes), või palu kellelgi hoida taskulampi küljelt. Ilma toalambi ja välguta.';
// the two steps the pupil and the eyelid cards share
const FOCUS_STEADY = 'Puuduta teravustamiseks ekraanil iirist, hoia telefoni paigal ja tee 3-5 võtet.';
// src/shared/aiMaterial.ts AI_MATERIAL_PAGE.et, word for word as the landing's FAQ answer (src/landing/copy/et.json)
const AI_MATERIAL_ET = 'Mõnes stiilis on pulber, vedelik, leek või tolm sinu iirise ümber tehisintellekti loodud materjal ühisest kogust, seega võib teise kliendi kunstiteos sisaldada sama tükki. Sinu iiris säilitab sinu foto värvid, mustri ja paigutuse; kõige peenemad kiud taastab tehisintellekt, nagu eespool kirjeldatud.';
const WOULD_ET = 'Saaksid ühe digitaalse faili ilma vesimärgita, 4096 px pikimal küljel.';

export const et: TryCopy = {
  lang: 'et',
  meta: {
    title: 'SnapEyes Studio: iirisekunst sinu silmafotost',
    description: 'Pildista oma silma telefoniga ja umbes minuti pärast näed oma iirist, taastatuna ja sinu valitud stiilis.',
  },
  switchLabel: 'Keel',
  /** One decimal, as Estonian writes it (3,7). */
  dec1: (v: number) => dec1Et(v),

  header: {
    study: 'Peretest',
  },

  errors: {
    tooLarge: 'See foto on liiga suur. Proovi uuesti tavalise kaamerafotoga.',
    timeout: 'See võttis meie poolel liiga kaua aega. Palun proovi uuesti.',
    notResponding: 'Stuudio ei vasta praegu. Palun proovi hetke pärast uuesti.',
    requestFailed: (status: number) => `Päring ebaõnnestus (${status})`,
    unreadable: 'Me ei saanud seda fotot avada. Kui see on iPhone’i HEIC-fail, ei oska see brauser seda lugeda: palun vali JPEG või PNG või ava snapeyes.com oma telefonis ja tee foto seal.',
    noEyeAny: 'Me ei leidnud ühelgi neist fotodest silma.',
    noEyeShot: 'Me ei leidnud sellelt võttelt silma.',
    noEye: 'Silma ei leitud',
    keepFailed: 'Sinu võtete salvestamisel läks midagi valesti. Palun tee foto uuesti.',
  },

  capture: {
    // the first screen's heading: the second part is set in gold
    titleA: 'PILDISTA',
    titleB: ' OMA SILMA.',
    lead: 'Minuti pärast näed seda kunstiteosena. Tasuta.',
    addTitle: (n: number) => `Lisa silm ${n}`,
    addLead: 'Sinu partner, sinu laps või sinu teine silm. Samad sammud mis enne: tee paar võtet ja me jätame alles parima.',
    takeTurns: 'Pildistate teineteist? Tehke seda kordamööda: üks hoiab telefoni, teine vaatab otse ette. Siis vahetage.',
    retakeTitle: (n: number) => `Pildista silm ${n} uuesti`,
    retakeLead: 'Samad sammud mis enne. Uus võte asendab kunstiteosel selle silma; seni jääb see nii, nagu on.',
    back: (n: number) => `Tagasi sinu kunstiteose juurde (${silmad(n)})`,
    sampleButton: 'Näidissilm',
    sampleLoadFailed: 'Näidissilma ei õnnestunud laadida.',
    // the guide video's button and the four steps under it, one line each (copy.ts says why)
    videoPlay: 'Esita juhendvideo',
    videoPause: 'Peata juhendvideo',
    steps: ['Üksi? Peeglist näed ekraani', 'Tagakaamera, 2x suurendus, 10 cm silmast', 'Akna- või taskulambivalgus, küljelt', 'Puuduta teravustamiseks iirist, hoia paigal'],
    moreTips: 'Veel nõuandeid',
    stepsOpen: 'Silm pärani lahti. ',
    stepsOpenMore: 'Vaata otse ette ja tõsta ülemist laugu õrnalt sõrmeotsaga, et laug ega ripsmed ei ulatuks iirise peale.',
    stepsShots: 'Tee 3-5 võtet ja saada kõik.',
    stepsShotsMore: ' Pööra end võtete vahel veidi. Mõõdame iga võtet ja kasutame kõige teravamat; päris katses oli parimal võttel 3,7 korda rohkem detaile kui kõige nõrgemal.',
    cameraTip: 'Kõige teravam foto tuleb telefoni kaameraga (2x, akna juures): pildista ja laadi see siia üles.',
    // the live camera of ?cam=1 (src/try/livecam): the hint inside the view, the torch button, the shutter's label for a screen reader
    liveHint: 'Hoia silm ringi sees',
    liveLight: 'Valgus',
    liveShutter: 'Tee foto',
    // the live camera's burst (2026-11-26): under the hint before the tap (n is the number of pictures one tap takes), during it, and at its end
    liveBurst: (n: number) => `Teeme ${n} fotot. Ära liiguta.`,
    liveStill: 'Ära liiguta',
    liveDone: 'Valmis',
    // the tips' second line in a tab with the live camera (?cam=1): it zooms by itself, so only the distance (closer than about 10 cm no phone focuses)
    liveStep: 'Tagakaamera, umbes 15 cm silmast',
    // the live camera's second line while the middle of the picture is too dark (it never blocks the shutter)
    liveDark: 'Liiga pime. Mine akna juurde või lülita valgus sisse.',
    takePhoto: 'Pildista silma',
    pickShots: 'Laadi foto üles',
    consent: 'Salvesta minu silmafoto ja tulemus SnapEyesi õppemällu, et taastamine muutuks ajaga paremaks. Anonüümselt, ilma nime ja näota. Võid igal ajal paluda meil selle kustutada.',
  },

  working: {
    finding: 'Otsime sinu iirist…',
    // the waiting screens' slideshow (src/try/Slideshow.tsx): its one line
    slidesLine: 'Varsti näeb ka sinu silm nii välja.',
    locating: 'Leiame iirise ja pupilli',
    measuringSize: 'Mõõdame suurust ja teravust',
    checking: (n: number, done: number) => `Kontrollime fotosid: valmis ${done}/${n}`,
    measuringShot: (k: number, max: number) => `Mõõdame võtet ${k}/${max}`,
    restoring: 'Taastame sinu iirist…',
    restoringEye: (n: number) => `Taastame silma ${n}…`,
    cut: 'Lõikame sinu iirise välja',
    reflections: 'Eemaldame peegeldusi',
    macro: 'Stuudio makrotaastamine (umbes 30 s)',
    composing: (n: number) => (n > 1 ? `Paneme kokku sinu kunstiteost (${silmad(n)})` : 'Paneme kokku sinu kunstiteost'),
    sampleCaption: 'Tehisintellekti loodud näidis',
    yourIris: 'Sinu iiris',
    elapsed: (s: number) => `${s} s`,
  },

  quality: {
    retake: 'Pildista uuesti',
    notCentred: 'Iiris ei ole selle foto keskel, seega ei saa seda taastada. Palun pildista uuesti nii, et üks silm täidab kaadri.',
    blocks: {
      too_blurry: {
        title: 'Liiga udune, et sinu enda iirist taastada',
        reason: 'Me ei näinud sellel fotol sinu enda iirise mustrit piisavalt, et seda taastada, seega me seda ei kasuta.',
        error: 'See foto on liiga udune, et sinu enda iirist taastada. Palun pildista uuesti allolevate sammude järgi.',
        retakeLine: 'See võte on liiga udune, et sinu enda iirist taastada. Pildista uuesti akna päevavalguses või taskulambiga, küljelt, tagakaamera 2x suurendusega: puuduta teravustamiseks iirist ja hoia telefoni paigal.',
        thumb: 'udune',
        steps: [LIGHT, CAMERA, FOCUS, STEADY],
      },
      too_dark: {
        title: 'Liiga tume, et sinu enda iirise mustrit näha',
        reason: 'Sinu iiris on tume ja valgust oli liiga vähe, et selle mustrit näha, seega me seda fotot ei kasuta.',
        error: 'See foto on liiga tume, et sinu enda iirise mustrit näha. Palun pildista uuesti allolevate sammude järgi.',
        retakeLine: 'See võte on liiga tume, et sinu enda iirise mustrit näha. Pildista uuesti päevavalguses heleda akna lähedal, nii et aken jääb küljele, või taskulambiga küljelt. Ilma toalambi ja välguta.',
        thumb: 'tume',
        steps: [DARK_LIGHT, CAMERA, FOCUS, STEADY],
      },
      pupil_too_large: {
        title: 'Pupill on liiga lai, et sinu iirist taastada',
        reason: 'Sinu pupill on sellel fotol nii laialt lahti, et selle ümber on näha liiga vähe iirist, seega me seda ei kasuta.',
        error: 'Sinu pupill on sellel fotol liiga lai, et sinu enda iirist taastada. Palun pildista uuesti allolevate sammude järgi.',
        retakeLine: 'Sinu pupill on sellel võttel liiga lai. Rohkem valgust teeb selle väiksemaks: pildista uuesti päevavalguses heleda akna lähedal või taskulambiga küljelt, mitte välguga.',
        thumb: 'pupill',
        steps: [
          'Rohkem valgust teeb pupilli väiksemaks: seisa päevavalguses heleda akna lähedal, nii et aken jääb küljele (mitte otsese päikese käes), või palu kellelgi hoida taskulampi küljelt. Ilma välguta.',
          'Anna silmale enne pildistamist minut aega selles valguses olla, et pupill jõuaks aheneda. Pimedal ajal pane põlema kõik laelambid ja palu kellelgi hoida taskulampi küljelt.',
          CAMERA,
          FOCUS_STEADY,
        ],
      },
      too_small: {
        title: 'Sinu iiris on sellel fotol liiga väike',
        reason: 'Sinu iiris on sellel fotol nii väike, et selle mustrit on näha liiga vähe, seega me seda ei kasuta.',
        error: 'Sinu iiris on sellel fotol liiga väike, et seda taastada. Palun pildista uuesti lähemalt, allolevate sammude järgi.',
        retakeLine: 'Sinu iiris on sellel võttel liiga väike. Tule lähemale: tagakaamera 2x suurendusega, umbes 10 cm kaugusel silmast, nii et iiris täidab umbes kolmandiku kaadrist.',
        thumb: 'väike',
        steps: [
          'Tule lähemale: tagakaamera 2x suurendusega, umbes 10 cm kaugusel silmast, nii et iiris täidab umbes kolmandiku kaadrist.',
          LIGHT,
          FOCUS,
          STEADY,
        ],
      },
      // a lid over part of the iris (api/analyze.py EYELID_BLOCK_PCT): the studio would have to paint iris over it. The words
      // of the capture guide's open-eye step (stepsOpen, stepsOpenMore) and of api/_lib/analyze_et.py TEXT_ET["eyelid"]
      eyelid: {
        title: 'Silmalaug katab osa sinu iirisest',
        reason: 'Osa sinu iirisest on sellel fotol silmalau või ripsmete all peidus, seega me seda ei kasuta.',
        error: 'Silmalaug katab sellel fotol osa sinu iirisest. Palun pildista uuesti allolevate sammude järgi.',
        retakeLine: 'Silmalaug katab sellel võttel osa sinu iirisest. Vaata otse objektiivi, ava silm pärani ja tõsta ülemist laugu õrnalt sõrmeotsaga.',
        thumb: 'laug',
        steps: [
          'Vaata otse objektiivi, mitte viltu: kui pilk läheb kõrvale, libiseb ülemine laug iirise peale.',
          'Ava silm pärani ja tõsta ülemist laugu õrnalt sõrmeotsaga, et nahk, ripsmed ega ripsmetušš ei ulatuks iirise peale.',
          CAMERA,
          FOCUS_STEADY,
        ],
      },
    } satisfies Record<BlockReason, BlockCopy>,
    // a reason this page does not know yet: neutral on purpose, it names no cause the server did not name
    blockedOther: {
      title: 'Liiga vähe detaile, et sinu enda iirist taastada',
      reason: 'Me ei näinud sellel fotol sinu enda iirise mustrit piisavalt, et seda taastada, seega me seda ei kasuta.',
      error: 'Sellel fotol on sinu enda iirist näha liiga vähe, et seda taastada. Palun pildista uuesti allolevate sammude järgi.',
      retakeLine: 'Sellel võttel on sinu enda iirist näha liiga vähe, et seda taastada. Tee uus võte pildistamisjuhendi järgi.',
      thumb: 'uuesti',
      steps: [LIGHT, CAMERA, FOCUS, STEADY],
    } satisfies BlockCopy,
    guideTitle: 'Uuesti pildistamiseks',
    noneUsable: (n: number) => (n === 1
      ? 'Kontrollisime foto üle, aga seda ei saa kasutada.'
      : n === 2
        ? 'Kontrollisime mõlemad fotod üle ja kumbagi ei saa kasutada.'
        : `Kontrollisime kõik ${fotod(n)} üle ja ühtki neist ei saa kasutada.`),
    shotUnusable: 'Seda võtet ei saa kasutada. Tee uus võte ülaltoodud nõuannete järgi.',
    shotsUnusable: 'Ühtki neist võtetest ei saa veel kasutada. Tee uus võte ülaltoodud nõuannete järgi.',
    fullUnusable: (max: number) => (max === 1
      ? 'Seda võtet ei saa kasutada. Tee uus võte, et alustada uut seeriat.'
      : `Ühtki neist ${vottedEla(max)} ei saa kasutada. Tee uus võte, et alustada uut seeriat.`),
    detectedIris: 'Tuvastatud iiris',
    pupilNote: 'Peegeldus pupillil ei sega: rekonstrueerime pupilli puhta tumedusena.',
    lampFallback: 'Lambivalgus annab sinu silmavalgele tooni, seega võivad värvid tulla soojemad, kui need tegelikult on.',
    closer: 'Tule lähemale või suurenda, et iiris täidaks suurema osa kaadrist.',
  },

  // the camera shot collector
  collector: {
    header: (n: number, max: number) => `Võte ${n}/${max}`,
    shotAlt: (n: number) => `Võte ${n}`,
    // best is printed after a colon or as the subject ("Sinu seni parim on võte 2")
    bestLabel: (k: number, d?: number) => `võte ${k}${d !== undefined ? ` (detailsus ${d})` : ''}`,
    full: (max: number, best: string) => `See on juba ${votted(max)}. Kasutame sinu parimat: ${best}.`,
    more: (left: number) => `${left === 1 ? 'Võid teha veel ühe võtte' : `Võid teha veel kuni ${votted(left)}`}. Mõõdame iga võtet ja jätame alles parima.`,
    sharpEnough: 'See võte on kasutamiseks piisavalt terav.',
    bestSoFar: 'See on seni sinu parim võte.',
    lampSkipped: (n: number, best: string) => `Lambivalgus andis võttele ${n} tooni, seega kasutame sinu parimat õigetes värvides võtet: ${best}.`,
    bestIs: (best: string) => `Sinu seni parim on ${best}. Seda me kasutamegi.`,
    lastFailed: (note: string) => `Viimast võtet ei saanud kasutada: ${note} Sinu seni parim võte jääb alles.`,
    takeAnother: 'Tee veel üks võte',
    useBest: 'Kasuta parimat võtet',
    useThis: 'Kasuta seda võtet',
    startOver: 'Alusta otsast',
  },

  result: {
    beforeAfter: 'Enne / pärast',
    eyes: 'Silmad sellel kunstiteosel',
    eyeLabel: (i: number) => `Silm ${i}`,
    sampleLabel: 'Tehisintellekti loodud näidis',
    yourPhoto: 'Sinu foto',
    samplePhoto: 'AI-näidis',
    after: 'Stuudio makro',
    sliderBefore: 'Sinu foto',
    sliderAfter: 'Taastatud',
    sliderLabel: 'Võrdle oma fotot ja taastatud iirist',
    sliderValue: 'foto {n} protsenti',
    // announced once, by a polite live region, when the studio has made the preview (release review, perf-a11y M3)
    previewReady: 'Sinu eelvaade on valmis. Vali allpool stiil.',
    // src/landing/copy.et.ts TRANSPARENCY_ET, word for word. Shown for a real eye only.
    transparency: TRANSPARENCY_ET,
    // src/shared/aiMaterial.ts AI_MATERIAL_PAGE.et, word for word as the landing's FAQ answer (src/landing/copy/et.json)
    aiMaterial: AI_MATERIAL_ET,
    sampleNote: 'See silm on tehisintellekti loodud näidis, mitte päris foto. Sinu enda foto puhul tuleb värv sinu fotolt.',
    // new sentences of 2026-10-20 (colourOff, pupilWide, how, did)
    colourOff: 'Värvid võivad sinu silmast veidi erineda. Kõige tõetruum on päevavalgus või taskulamp küljelt, ilma välguta; kui tulemus sulle meeldib, jätka julgelt.',
    pupilWide: 'Rohkem valgust teeb pupilli väiksemaks ja näitab sinu iirisest rohkem.',
    pupilLarge: 'Su pupill on suur: akna juures see aheneb ja iirise mustrit paistab rohkem.',
    how: 'Kuidas see käib',
    did: {
      title: 'Mida me tegime',
      glare: 'Eemaldasime peegeldused.',
      sharp: 'Teravdasime fookust ja peeneid kiude.',
      colour: 'Tasakaalustasime valgust.',
      lid: 'Jätkasime sinu enda iirist silmalau all.',
      nothing: 'Me ei maalinud midagi peale: ei uusi värve ega mustrit teisest silmast.',
      quality: (crop: number) => `Foto teeb sinu telefoni enda kaamera täiskvaliteedis. Lõikame sellest välja lähivaate sinu silmast (kuni ${crop} px) ja taastame selle; täissuuruses 4096 px fail joonistataks selle taastatud pildi põhjal, mitte sinu fotot venitades.`,
    },
    retakeEye: (i: number) => `Pildista silm ${i} uuesti`,
    retakeOnly: 'Pildista see silm uuesti',
    replaceSample: 'Kasuta selle asemel oma silma',
    removed: (i: number) => `Silm ${i} on eemaldatud.`,
    undo: 'Võta tagasi',
    sampleArtwork: 'Näidiskunstiteos',
    sampleBadge: 'Tehisintellekti loodud näidis',
    // baked into the preview image itself (the engine's caption title, at most 40 characters: this is 29)
    sampleTitle: 'Tehisintellekti loodud näidis',
    sampleArtworkNote: 'Tehtud ainult tehisintellekti loodud näidissilmast, mitte päris fotost.',
    mixedArtworkNote: 'See kunstiteos sisaldab tehisintellekti loodud näidissilma, mis ei ole päris foto.',
    upscaled: 'Väike foto: enne taastamist suurendatud.',
    badgeMacro: 'Stuudio makro',
    badgeFallback: 'Ainult tõetruu suurendus',
    artwork: 'Sinu kunstiteos',
    composing: 'Paneme kokku…',
    composeFailed: 'Meil ei õnnestunud seda eelvaadet kokku panna.',
    previewReduced: 'Eelvaade on vähendatud ja vesimärgiga.',
    previewFile: (square: boolean): string => (square
      ? 'Sinu fail: 4096 px, piisavalt terav, et trükkida kuni 60 x 60 cm.'
      : 'Sinu fail: 4096 px pikimal küljel, piisavalt terav, et trükkida sellel küljel kuni 60 cm.'),
    retry: 'Proovi uuesti',
    layout: 'Paigutus',
    style: 'Stiil',
    save: 'Salvesta eelvaade',
    // the saved preview's file name (ASCII, as the English and German ones); a sample preview says so in its name too
    fileName: (style: string, n: number, sample: boolean) => `snapeyes-eelvaade-${style}-${n}-${etForm(n, 'silm', 'silma')}${sample ? '-ai-naidis' : ''}.jpg`,
    addSecond: 'Lisa teine silm',
    addAnother: 'Lisa veel üks silm',
    addHint: (left: number) => `Partner, laps või sinu teine silm. Sellel kunstiteosel on ruumi veel ${silmaGen(left)} jaoks.`,
    full: (max: number) => `See on ${silmad(max)}, rohkem ühele kunstiteosele ei mahu.`,
    quota: (left: number, max: number) => `Tasuta eelvaateid täna alles: ${left}/${max}.`,
    remove: (i: number) => `Eemalda silm ${i}`,
    startOver: 'Alusta otsast',
    confirmStartOver: (n: number) => (n === 1 ? 'Kas visata see silm ära ja alustada otsast?' : `Kas visata kõik ${silmad(n)} ära ja alustada otsast?`),
    stored: 'Salvestatud õppemällu',

    reveal: {
      photo: 'Sinu foto',
      iris: 'Sinu iiris',
      slider: 'Võrdle oma fotot oma taastatud iirisega',
      valueText: 'foto {n} protsenti',
      promise: 'Taastatud, mitte kunagi üle maalitud: me ei värvi sinu iirist kunagi ümber ega vaheta seda teise silma vastu.',
      softTip: 'Sinu foto on väike, seega paistab selle pool pehme. Tule lähemale või kasuta 2x suurendust, et võrdlus oleks teravam.',
    },
  },

  // the style picker (src/try/picker.ts)
  picker: {
    groups: { one: 'Ainult sina', two: 'Teie kaks', family: 'Pere' },
    groupIntro: {
      one: 'Üks iiris, üksi mustal taustal või omaenda universumis.',
      two: 'Partnerile: kaks iirist, mis kohtuvad.',
      family: 'Perele: iga iiris säilitab oma värvi.',
    },
    groupSoon: 'Tasuta eelvaade on olemas. Selle rühma stiile saab tellida peagi.',
    countSoon: (n: number) => `Tellimine ${silmaGen(n)} jaoks avaneb peagi.`,
    soonBuy: 'See stiil avaneb peagi. Kohe tellimiseks vali mõni teine.',
    retakeBuy: (total: number) => (total === 1
      ? 'Selle fotoga ei saa veel midagi tellida. Tellimiseks pildista oma silm uuesti.'
      : 'Nende fotodega ei saa veel midagi tellida. Tellimiseks pildista allpool nimetatud silmad uuesti.'),
    soonNote: 'See stiil avaneb peagi.',
    soonLookBuy: (look: string) => `Variant ${look} avaneb peagi. Kohe tellimiseks vali mõni teine variant või stiil.`,
    soonLookNote: (look: string) => `Variant ${look} avaneb peagi.`,
    listLabel: 'Stiilid sinu silmadele',
    soon: 'Peagi',
    recommended: 'Soovitatud',
    reasons: {
      'reason.solo_powder.own': 'Sinu enda värvid, pulbriks muudetud',
      'reason.solo_gold.dark_brown': 'Kuld paneb tumepruunid silmad särama',
      'reason.solo_radiance.grey': 'Hõbedane valgus hallidele silmadele',
      'reason.duo_collision_infinity.own': 'Kaks iirist, üks lõpmatus',
      'reason.duo_kiss_collision.own': 'Kaks maailma, üks plahvatus',
      'reason.duo_kiss_collision.dark_brown': 'Kaks maailma, üks plahvatus',
      'reason.duo_kiss_collision.grey': 'Kaks maailma, üks plahvatus',
      'reason.grp_collision.own': 'Igaüks oma värvis',
      'reason.grp_collision.dark_brown': 'Igaüks oma värvis',
      'reason.grp_collision.grey': 'Igaüks oma värvis',
    },
    lines: {
      'line.solo_clean': 'Sinu taastatud iiris üksi puhtal mustal taustal.',
      'line.solo_powder': 'Serv laguneb teradeks sinu silma enda värvides.',
      'line.solo_universe': 'Sinu terav iiris sama iirise ees, mis on suurendatud ja pehmelt hägune.',
      'line.solo_splash': 'Serv kerkib vedelikust krooniks.',
      'line.solo_gold': 'Peen kuldne rõngas ja kuma iirise ümber.',
      'line.solo_radiance': 'Peened valguskiired sinu enda iirise värvides.',
      'line.solo_supernova': 'Servast paiskub tähetolm sinu silma enda värvides.',
      'line.solo_nebula': 'Sinu iiris helendab udukogu südames.',
      'line.solo_sparks': 'Servast tõusevad sädemed sinu silma enda värvides.',
      'line.solo_halo': 'Sinu iiris, mida valgustab tagant tema enda värv.',
      'line.solo_aurora': 'Virmaliste kardinad sinu iirise ümber.',
      'line.solo_echo': 'Sinu iiris omaenda kaja sees, kiud sirutuvad välja nagu tunnel.',
      'line.solo_galaxy': 'Tähtede spiraalharud keerduvad sinu iirisest välja selle enda värvides.',
      'line.duo_galaxy': 'Kaks iirist ühe spiraalgalaktika südames, kumbki haru oma värvides.',
      'line.grp_galaxy': 'Üks galaktika kogu perele, üks haru iga inimese värvides.',
      'line.grp_powder': 'Iga iiris muutub oma värvides tolmuks ja keskel need segunevad.',
    },
    tileAlt: (name: string) => `${name} sinu silmadega: vähendatud vesimärgiga eelvaade`,
    tileMaking: (name: string) => `${name}: eelvaade on valmimas`,
    tileFailed: 'Eelvaadet ei tehtud',
    changed: {
      eyes: (from: string, to: string, n: number) => `Stiil ${from} ei ole ${silmaGen(n)} jaoks saadaval, seega valisime stiili ${to}.`,
      gate: (from: string, to: string, i: number) => `Stiil ${from} vajab puhtamat iirist, seega valisime praegu stiili ${to}. Stiili ${from} kasutamiseks pildista silm ${i} uuesti.`,
      reseal: (from: string, to: string, i: number) => `Stiili ${from} kasutamiseks tee palun silma ${i} eelvaade uuesti. Praegu valisime stiili ${to}.`,
      pupil: (from: string, to: string) => `Stiil ${from} ei sobi selle pupillikujuga, seega valisime stiili ${to}.`,
    },
    chipRetake: 'Uuesti',
    chipLabel: (i: number) => `Silm ${i}: vaja on uuesti pildistada`,
    advisory: (list: number[], total: number) => (total === 1
      ? 'Sinu iirise rõnga sees on veel silmalaugu või ripsmeid. Puhtama tulemuse saamiseks pildista uuesti.'
      : `${list.length === 1 ? `Silm ${list[0]}` : `Silmad ${jaList(list)}`}: rõnga sees on veel silmalaugu või ripsmeid. Puhtama tulemuse saamiseks pildista uuesti.`),
    retake: {
      calm: 'Stiilide näitamiseks vajame veel üht fotot.',
      manual: 'Ikka ei õnnestu? Saada oma parimad fotod aadressile {link} ja me vaatame need üle.',
      noStyles: 'Nii mitme silma jaoks ei saa veel ühtki stiili näidata. Eemalda üks silm või kirjuta meile.',
    },
    stack: 'Sinu kaks iirist erinevad värvilt tugevalt, seega on üks teise ees.',
    widePupil: 'Sinu pupillid on laiad, seega iirised puudutavad teineteist, mitte ei kattu.',
    options: {
      swap: 'Vaheta kohad',
      rotate: 'Liiguta kohti ringi',
      earlier: 'Nihuta ettepoole',
      later: 'Nihuta tahapoole',
      earlierLabel: (i: number) => `Nihuta silm ${i} kunstiteosel ettepoole`,
      laterLabel: (i: number) => `Nihuta silm ${i} kunstiteosel tahapoole`,
      centre: 'Pane keskele',
      centreLabel: (i: number) => `Pane silm ${i} kunstiteose keskele`,
      centreNote: 'Esimene silm on keskel, teised tiirlevad selle ümber. Vali ülalt silm ja pane see keskele.',
      look: 'Variant',
    },
    names: {
      // the one quiet button that opens the words on the artwork (closed until pressed, open while a word is typed)
      open: '+ Lisa nimi või kuupäev',
      title: 'Sõnad kunstiteosel (valikuline)',
      nameFor: (i: number, total: number) => (total === 1 ? 'Nimi (valikuline)' : `Nimi silmale ${i}`),
      date: 'Kuupäev (valikuline)',
      datePlaceholder: 'Näiteks 14. juuni 2026',
      family: 'Perekonnanimi (valikuline)',
      problem: {
        nameLong: (i: number, max: number) => `Silma ${i} nimi on liiga pikk: kuni ${tahed(max)}.`,
        namesLong: (max: number) => `Nimed on kokku liiga pikad: kuni ${tahed(max)}.`,
        glyph: (chars: string) => `Kunstiteose kirjatüübis puudub ${chars}. Palun kasuta teist tähte.`,
        dateLong: (max: number) => `Kuupäev on liiga pikk: kuni ${margid(max)}.`,
        familyLong: (max: number) => `Perekonnanimi on liiga pikk: kuni ${tahed(max)}.`,
      },
    },
  },

  price: {
    title: 'Selle kunstiteose hind',
    eyes: (n: number, style: string) => `${silmad(n)} · ${style}`,
    black: (name: string, black: string, art: string) => `1 silm: ${black} stiili ${name} eest, ${art} mis tahes muu stiili eest.`,
    duoOffer: (two: string) => `Lisa teine silm: ${two} mõlema eest.`,
    extra: (two: string, further: string, max: number) => `Kaks silma ${two}, seejärel +${further} iga järgmise silma eest, kuni ${silmad(max)}.`,
    // the landing's pricing.notice (src/landing/copy/et.json), with today's free preview
    notice: 'Tellimine avaneb peagi: sinu eelvaade on täna tasuta.',
    footnote: `${WOULD_ET} Hinnad on eurodes.`,
    footnoteAud: `${WOULD_ET} Hinnad on Austraalia dollarites (A$).`,
    footnoteHuf: `${WOULD_ET} Hinnad on Ungari forintides (Ft).`,
    footnoteUsd: `${WOULD_ET} Hinnad on USA dollarites (US$).`,
    demo: 'See on demo tehisintellekti loodud näidissilmaga. Proovi oma silmaga, et näha oma hinda.',
    sampleNotCounted: (k: number) => (k === 1
      ? 'Tehisintellekti loodud näidissilm ei ole tellimuse osa, seega seda ei arvestata.'
      : `Tehisintellekti loodud näidissilmad (${k}) ei ole tellimuse osa, seega neid ei arvestata.`),
  },

  // ordering from the result screen. The waiver and the links under it are src/shared/legal.ts CHECKOUT_LEGAL.et, word
  // for word the text the server records (api/_lib/pay.py CONSENT_TEXT["et"]).
  buy: {
    // the label alone (see the header); the price stays in the card's head
    button: (_price: string) => CHECKOUT_LEGAL.et.continueButton,
    waitPreview: 'Selle valiku eelvaade on veel valmimas. Tellida saad kohe, kui seda näed.',
    previewFailed: 'Palun laadi esmalt selle valiku eelvaade (ülal „Proovi uuesti“), et näeksid, mida tellid.',
    steps: {
      sync: 'Kontrollime sinu tellimust…',
      upload: (i: number, n: number) => (n > 1 ? `Laadime üles silma ${i}/${n}…` : 'Laadime sinu silma üles…'),
      arrange: 'Paigutame sinu silmi…',
      checkout: 'Avame turvalise makselehe…',
    },
    // the card shows its own replace button(s) right under this line, so the line names none
    sample: (k: number): string => (k === 1
      ? 'Tehisintellekti loodud näidissilma ei saa tellida. Selle kunstiteose tellimiseks asenda see oma silmaga.'
      : 'Tehisintellekti loodud näidissilmi ei saa tellida. Selle kunstiteose tellimiseks asenda need oma silmadega.'),
    replaceSampleEye: (i: number) => `Asenda silm ${i} enda omaga`,
    // api/order.py draft: an eye is accepted with its photo's work ticket (15 minutes) or its sealed preview (api/_lib/preview.py SEAL_TTL, 48 hours)
    stale: (list: number[], total: number) => (total === 1
      ? 'Sinu foto on tehtud rohkem kui 2 päeva tagasi. Fotot saab tellida 2 päeva jooksul pärast pildistamist, seega pildista tellimiseks palun uuesti.'
      : `${list.length === 1 ? `Silm ${list[0]} on pildistatud` : `Silmad ${jaList(list)} on pildistatud`} rohkem kui 2 päeva tagasi. Fotot saab tellida 2 päeva jooksul pärast pildistamist, seega pildista ${list.length === 1 ? 'see' : 'need'} tellimiseks palun uuesti.${list.length < total ? ' Sinu teised silmad jäävad nii, nagu on.' : ''}`),
    cancelled: 'Makse tühistati. Raha ei võetud. Sinu kunstiteos on endiselt siin: võid seda muuta või uuesti tellida.',
    cancelledLost: 'Makse tühistati. Raha ei võetud. See leht ei saanud sinu eelvaadet alles hoida, seega tee palun foto uuesti.',
    close: 'Sulge',
    errors: {
      network: 'Me ei saanud SnapEyesiga ühendust. Palun kontrolli internetiühendust ja proovi uuesti.',
      busy: 'Makseteenus ei vastanud. Palun proovi hetke pärast uuesti.',
      payments: `Me ei saanud makselehte avada. Palun proovi hiljem uuesti või kirjuta aadressile ${CONTACT_EMAIL}.`,
      too_large: 'Ühe sinu silma foto on üleslaadimiseks liiga suur. Palun pildista see silm uuesti.',
      // api/order.py draft: 503 uploads_paused and 429 too_many_uploads, both until the next day (UTC)
      paused: `Uued tellimused on tänaseks peatatud: päevane üleslaadimiste piir on täis. Raha ei võetud. Palun proovi homme uuesti või kirjuta aadressile ${CONTACT_EMAIL}.`,
      too_many: `See tellimus on jõudnud tänase üleslaadimiste piirini (30 üleslaadimist, kaasa arvatud uuesti pildistamised). Raha ei võetud. Palun proovi homme uuesti või kirjuta aadressile ${CONTACT_EMAIL}.`,
      failed: `Sinu tellimuse ettevalmistamisel läks midagi valesti. Palun proovi uuesti või kirjuta aadressile ${CONTACT_EMAIL}.`,
      closed: 'Tellimine ei ole veel avatud.',
      plan_changed: 'Sinu kunstiteos muutus äsja, seega tegime eelvaate uuesti. Palun vaata see üle ja vajuta siis nuppu uuesti.',
      unavailable: 'Seda stiili ei saa sinu silmadega praegu tellida. Palun vali mõni teine või pildista silm uuesti.',
      print_unavailable: 'Trükitud pilte ei saa praegu tellida. Digitaalse faili saad tellida eraldi.',
      print_changed: 'Trükitud pildi hind muutus äsja. Palun vaata see uuesti üle ja vajuta siis nuppu.',
      voucher: 'Sinu kinkekaarti ei saanud kasutada: see võib olla juba kasutatud või aegunud. Palun kontrolli seda uuesti.',
    },
    namesBlocked: 'Palun paranda esmalt sõnad kunstiteosel (vt ülal).',
    footnote: 'Digitaalne fail, 4096 px, ilma vesimärgita.',
  },

  gift: {
    open: 'Mul on kinkekaart',
    label: 'Kinkekaardi kood',
    apply: 'Kasuta',
    checking: 'Kontrollime koodi',
    applied: (value: string) => `Kinkekaart: \u2212${value}`,
    remove: 'Eemalda',
    toPay: (value: string) => `Maksta: ${value}`,
    note: 'Kinkekaarti kasutatakse siis, kui viid makse lõpule. Ülejäänud summa jääb kinkekaardile.',
    errors: {
      format: 'See ei ole kinkekaardi kood. Koodis on 12 tähte ja numbrit, näiteks ABCD-EFGH-JKLM.',
      unknown: 'Me ei tunne seda koodi. Palun kontrolli seda.',
      used: 'See kinkekaart on juba kasutatud.',
      expired: 'See kinkekaart on aegunud.',
      currency: 'Seda kinkekaarti saab kasutada ainult eurodes tehtud tellimuste puhul.',
      failed: 'Me ei saanud koodi praegu kontrollida. Palun proovi uuesti.',
    },
  },

  // the anonymous feedback box (src/try/Feedback.tsx, api/_lib/feedback.py)
  feedback: {
    title: { result: 'Kuidas see sulle tundub?', retake: 'Kas sellest oli abi?' },
    hint: { result: 'Üks puudutus ja soovi korral paar sõna. See jõuab inimeseni, kes neid kunstiteoseid teeb.', retake: 'Üks puudutus ütleb meile, mis sind takistas.' },
    chips: {
      result: { love: 'Mulle väga meeldib', likeness: 'See ei näe välja nagu minu silm', colour: 'Värvid tunduvad valed', style: 'Tahtsin teist stiili', price: 'Hind on liiga kõrge', other: 'Midagi muud' },
      retake: { unclear: 'Ma ei saa aru, mis on valesti', fine: 'Minu arvates on mu foto korras', device: 'Mu telefon ei suuda paremini', only: 'See on mu ainus foto', effort: 'See on liiga suur vaev', other: 'Midagi muud' },
    },
    textLabel: 'Kas soovid midagi lisada? (valikuline)',
    textHint: 'Palun ära kirjuta nimesid, e-posti aadresse ega telefoninumbreid.',
    count: (n: number, max: number) => `${n} / ${max}`,
    send: 'Saada',
    sending: 'Saadame',
    thanks: 'Aitäh. See jõudis inimeseni, kes neid kunstiteoseid teeb.',
    textDropped: 'Aitäh. Arvestasime sinu vastust, kuid teksti me alles ei jätnud, sest selles paistis olevat kontaktandmeid või link.',
    textLost: 'Aitäh. Sinu vastus jõudis meieni, kuid teksti ei õnnestunud salvestada.',
    failed: 'Saatmine ei õnnestunud. Palun proovi hetke pärast uuesti.',
    privacy: 'Anonüümne: ilma nime ja e-posti aadressita. Tekst kustutatakse 90 päeva pärast.',
  },

  study: {
    title: (shot: number, photos: number) => (photos > 1 ? `Peretest · fotod ${shot - photos + 1}-${shot}` : `Peretest · võte ${shot}`),
    light: 'Valgus selle võtte ajal',
    lights: {
      window_daylight: 'Päevavalgus aknast', room_lamp: 'Toalamp', phone_torch: 'Telefoni taskulamp', someone_helped: 'Keegi aitas',
    } satisfies Record<LightAnswer, string>,
    comfort: 'Kui lihtne see oli? 1 raske, 5 lihtne',
    skip: 'Jäta vahele',
    // the engine logs the answers only with an analyze request, so they wait for the next photo
    thanks: 'Aitäh. Need vastused saadetakse koos sinu järgmise fotoga.',
    pending: (shots: number[]) => `Peretest: sinu vastuseid ${shots.length === 1 ? `võtte ${shots[0]}` : `võtete ${shots.join(', ')}`} kohta ei ole veel saadetud. Need lähevad teele koos sinu järgmise fotoga, näiteks kui lisad veel ühe silma. Kui sulged lehe praegu, lähevad need kaotsi.`,
  },
};
