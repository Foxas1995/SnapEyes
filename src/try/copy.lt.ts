// Lithuanian /try copy: the twin of `en` in src/try/copy.ts same keys, same order, same function
// signatures. Polite "Jūs" (capitalised in every form) and the landing page's words (src/landing/copy.lt.ts):
// galinė kamera, priekinė kamera, 2x priartinimas, kadras (shot), peržiūra, kūrinys, atkurti,
// skaidulos, DI, meninis fonas. Numbers with a decimal comma.
// The server's own sentences (quality.message, tips) come from api/analyze.py in the request's language:
// api/_lib/analyze_lt.py TEXT_LT. src/try/shots.ts recognises three of those tips by words (see the header of that file).
import type { BlockCopy, BlockReason, TryCopy } from './copy';
import type { LightAnswer } from './multi';
import { CONTACT_EMAIL } from '../landing/config';
import { CHECKOUT_LEGAL } from '../shared/legal';
import { akiuWord, akys, akysWord, dec1Lt, kadrai, kadruWord, ltForm, nuotraukasAcc } from '../shared/lt';

// "1", "1 ir 3", "1, 2 ir 4"
const andList = (xs: number[], and: string) => (xs.length < 2 ? String(xs[0] ?? '') : `${xs.slice(0, -1).join(', ')} ${and} ${xs[xs.length - 1]}`);

// The capture guide's steps, word for word the same on the capture screen and in the retake cards (the English
// file's rule): daylight from the side, never a lamp or the flash.
const LIGHT = 'Dienos šviesa pro langą, iš šono (ne tiesiai iš priekio). Ne lempa ir ne blykstė.';
const CAMERA = 'Galinė kamera su 2x priartinimu, maždaug 10 cm nuo akies.';
const FOCUS = 'Bakstelėkite rainelę ekrane, kad kamera ją sufokusuotų.';
const STEADY = 'Laikykite telefoną stabiliai (alkūnes atremkite į ką nors tvirto) ir padarykite 3-5 kadrus.';
// the first retake step for a dark iris: the same light, only closer to the window
const DARK_LIGHT = 'Daugiau šviesos išryškina tamsią rainelę: dieną atsistokite arti šviesaus lango, kad langas būtų iš šono (ne tiesioginiai saulės spinduliai). Ne lempa ir ne blykstė.';

export const lt: TryCopy = {
  lang: 'lt',
  meta: {
    title: 'SnapEyes Studio - rainelės menas iš Jūsų akies nuotraukos',
    description: 'Nufotografuokite savo akį telefonu ir maždaug per minutę pamatykite savo rainelę atkurtą ir paverstą kosminiu meno kūriniu.',
  },
  switchLabel: 'Kalba',
  /** One decimal, as Lithuanian writes it (3,7). */
  dec1: (v: number) => dec1Lt(v),

  header: {
    tag: 'Private Atelier · peržiūra',
    study: 'Šeimos testas',
  },

  errors: {
    tooLarge: 'Ši nuotrauka per didelė. Pabandykite dar kartą su įprasta kameros nuotrauka.',
    timeout: 'Mūsų pusėje tai užtruko per ilgai. Pabandykite dar kartą.',
    notResponding: 'Studija šiuo metu neatsako. Po akimirkos pabandykite dar kartą.',
    requestFailed: (status: number) => `Užklausa nepavyko (${status})`,
    unreadable: 'Nepavyko nuskaityti šio vaizdo',
    noEyeAny: 'Nė vienoje iš šių nuotraukų neradome akies.',
    noEyeShot: 'Šiame kadre neradome akies.',
    noEye: 'Akis nerasta',
    keepFailed: 'Išsaugant Jūsų kadrus kažkas nepavyko. Nufotografuokite dar kartą.',
  },

  capture: {
    // the first screen's heading: the second part is set in gold
    titleA: 'JŪSŲ AKIS. ',
    titleB: 'TIKRAI.',
    lead: 'Nufotografuokite vieną akį. Surasime rainelę, pašalinsime atspindžius, atkursime skaidulas ir perteiksime ją meno kūrinyje. Maždaug minutė.',
    addTitle: (n: number) => `Pridėti akį ${n}`,
    addLead: 'Partnerio, vaiko arba kita Jūsų akis. Tie patys žingsniai kaip anksčiau: padarykite kelis kadrus, o mes pasiliksime geriausią.',
    takeTurns: 'Fotografuojate vienas kitą? Darykite tai paeiliui: vienas laiko telefoną, kitas žiūri tiesiai į priekį. Tada apsikeiskite.',
    helper: 'Lengviausia dviese: vienas laiko telefoną, kitas žiūri tiesiai į priekį.',
    retakeTitle: (n: number) => `Fotografuoti akį ${n} iš naujo`,
    retakeLead: 'Tie patys žingsniai kaip anksčiau. Naujas kadras pakeis šią akį kūrinyje; iki tol ji lieka tokia, kokia yra.',
    back: (n: number) => `Grįžti prie kūrinio (${akys(n)})`,
    sampleButton: 'DI sugeneruota pavyzdinė akis',
    sampleLoadFailed: 'Nepavyko įkelti pavyzdinės akies.',
    thumbLabel: (i: number) => `Akis ${i}`,
    sampleThumb: 'DI sugeneruotas pavyzdys',
    // the capture guide on the first screen. Step 3 is the retake guide's first step, word for word (LIGHT).
    steps: [
      { title: '1. Galinė kamera', text: '2x arba 3x priartinimas, ne priekinė kamera.' },
      { title: '2. 10 cm atstumu', text: 'Rainelė turėtų užpildyti trečdalį kadro.' },
      { title: '3. Šviesa pro langą', text: LIGHT },
      { title: '4. Sufokusuokite bakstelėdami', text: 'Bakstelėkite rainelę ekrane, nejudėkite, fotografuokite.' },
    ],
    stepsOpen: 'Plačiai atmerkta akis. ',
    stepsOpenMore: 'Žiūrėkite tiesiai į priekį ir piršto galiuku švelniai pakelkite viršutinį voką, kad nei vokas, nei blakstienos nedengtų rainelės.',
    stepsShots: 'Padarykite 3-5 kadrus ir siųskite visus.',
    stepsShotsMore: ' Tarp kadrų šiek tiek pasisukite. Įvertiname kiekvieną ir naudojame ryškiausią; tikrame bandyme geriausias kadras turėjo 3,7 karto daugiau detalių nei prasčiausias.',
    takePhoto: 'Fotografuoti',
    pickShots: 'Pasirinkti 3-5 kadrus',
    consent: 'Išsaugoti mano akies nuotrauką ir rezultatą SnapEyes mokymosi atmintyje, kad atkūrimas laikui bėgant gerėtų. Anonimiškai, be vardo ir veido. Bet kada galite paprašyti juos ištrinti.',
  },

  working: {
    finding: 'Ieškome Jūsų rainelės…',
    locating: 'Ieškome rainelės ir vyzdžio',
    measuringSize: 'Matuojame dydį ir ryškumą',
    checking: (n: number, done: number) => `Tikriname nuotraukas: ${done} iš ${n}`,
    measuringShot: (k: number, max: number) => `Matuojame kadrą ${k} iš ${max}`,
    restoring: 'Atkuriame Jūsų rainelę…',
    restoringEye: (n: number) => `Atkuriame akį ${n}…`,
    cut: 'Iškerpame Jūsų rainelę',
    reflections: 'Šaliname atspindžius',
    macro: 'Studijinis makro atkūrimas (apie 30 s)',
    composing: (n: number) => (n > 1 ? `Kuriame Jūsų kūrinį (${akys(n)})` : 'Kuriame Jūsų kūrinį'),
    sampleCaption: 'DI sugeneruotas pavyzdys',
    yourIris: 'Jūsų rainelė',
    elapsed: (s: number) => `${s} s`,
  },

  quality: {
    retake: 'Fotografuoti iš naujo',
    continueAnyway: 'Vis tiek tęsti',
    notCentred: 'Šios nuotraukos centre nėra rainelės, todėl jos atkurti negalime. Nufotografuokite iš naujo taip, kad viena akis užpildytų kadrą.',
    blocks: {
      too_blurry: {
        badge: 'Per neryški',
        title: 'Nuotrauka per neryški, kad atkurtume Jūsų rainelę',
        reason: 'Šioje nuotraukoje matyti per mažai Jūsų rainelės rašto, kad galėtume jį atkurti, todėl jos nenaudojame.',
        error: 'Ši nuotrauka per neryški, kad atkurtume Jūsų rainelę. Nufotografuokite iš naujo pagal toliau pateiktus žingsnius.',
        retakeLine: 'Šis kadras per neryškus, kad atkurtume Jūsų rainelę. Fotografuokite iš naujo dienos šviesoje prie lango iš šono, galine kamera su 2x priartinimu: bakstelėkite rainelę, kad kamera ją sufokusuotų, ir laikykite telefoną stabiliai.',
        thumb: 'neryški',
        steps: [LIGHT, CAMERA, FOCUS, STEADY],
      },
      too_dark: {
        badge: 'Per tamsi',
        title: 'Per tamsu, kad būtų matomas Jūsų rainelės raštas',
        reason: 'Jūsų rainelė tamsi, o šviesos buvo per mažai, kad būtų matomas jos raštas, todėl šios nuotraukos nenaudojame.',
        error: 'Ši nuotrauka per tamsi, kad būtų matomas Jūsų rainelės raštas. Nufotografuokite iš naujo pagal toliau pateiktus žingsnius.',
        retakeLine: 'Šis kadras per tamsus, kad būtų matomas Jūsų rainelės raštas. Fotografuokite iš naujo arti šviesaus lango dienos šviesoje, kad langas būtų iš šono. Ne lempa ir ne blykstė.',
        thumb: 'tamsi',
        steps: [DARK_LIGHT, CAMERA, FOCUS, STEADY],
      },
      pupil_too_large: {
        badge: 'Per platus vyzdys',
        title: 'Vyzdys per platus, kad atkurtume Jūsų rainelę',
        reason: 'Šioje nuotraukoje Jūsų vyzdys taip išsiplėtęs, kad aplink jį matyti per mažai rainelės, todėl jos nenaudojame.',
        error: 'Šioje nuotraukoje Jūsų vyzdys per platus, kad atkurtume Jūsų rainelę. Nufotografuokite iš naujo pagal toliau pateiktus žingsnius.',
        retakeLine: 'Šiame kadre Jūsų vyzdys per platus. Daugiau šviesos jį sumažina: fotografuokite iš naujo arti šviesaus lango dienos šviesoje, ne su blykste.',
        thumb: 'vyzdys',
        steps: [
          'Daugiau šviesos sumažina vyzdį: dieną atsistokite arti šviesaus lango, kad langas būtų iš šono (ne tiesioginiai saulės spinduliai). Ne blykstė.',
          'Prieš fotografuojant leiskite akiai minutę pabūti toje šviesoje, kad vyzdys spėtų susiaurėti. Sutemus įjunkite visas lubų lempas.',
          CAMERA,
          'Bakstelėkite rainelę ekrane, kad kamera ją sufokusuotų, laikykite telefoną stabiliai ir padarykite 3-5 kadrus.',
        ],
      },
      too_small: {
        badge: 'Per maža',
        title: 'Šioje nuotraukoje Jūsų rainelė per maža',
        reason: 'Šioje nuotraukoje Jūsų rainelė tokia maža, kad matyti per mažai jos rašto, todėl nuotraukos nenaudojame.',
        error: 'Šioje nuotraukoje Jūsų rainelė per maža, kad ją atkurtume. Nufotografuokite iš naujo iš arčiau pagal toliau pateiktus žingsnius.',
        retakeLine: 'Šiame kadre Jūsų rainelė per maža. Fotografuokite iš arčiau: galinė kamera su 2x priartinimu, maždaug 10 cm nuo akies, kad rainelė užpildytų maždaug trečdalį kadro.',
        thumb: 'maža',
        steps: [
          'Fotografuokite iš arčiau: galinė kamera su 2x priartinimu, maždaug 10 cm nuo akies, kad rainelė užpildytų maždaug trečdalį kadro.',
          LIGHT,
          FOCUS,
          STEADY,
        ],
      },
      // a lid over part of the iris (api/analyze.py EYELID_BLOCK_PCT): the studio would have to paint iris over it. The words
      // of the capture guide's open-eye step (stepsOpen, stepsOpenMore) and of api/_lib/analyze_lt.py TEXT_LT["eyelid"]
      eyelid: {
        badge: 'Vokas dengia rainelę',
        title: 'Vokas dengia dalį Jūsų rainelės',
        reason: 'Šioje nuotraukoje dalį Jūsų rainelės dengia vokas arba blakstienos, todėl jos nenaudojame.',
        error: 'Šioje nuotraukoje vokas dengia dalį Jūsų rainelės. Nufotografuokite iš naujo pagal toliau pateiktus žingsnius.',
        retakeLine: 'Šiame kadre vokas dengia dalį Jūsų rainelės. Žiūrėkite tiesiai į kamerą, plačiai atmerkite akį ir piršto galiuku švelniai pakelkite viršutinį voką.',
        thumb: 'vokas',
        steps: [
          'Žiūrėkite tiesiai į kamerą, ne įstrižai: žvelgiant į šoną viršutinis vokas užslenka ant rainelės.',
          'Plačiai atmerkite akį ir piršto galiuku švelniai pakelkite viršutinį voką, kad nei oda, nei blakstienos, nei blakstienų tušas nepatektų ant rainelės.',
          CAMERA,
          'Bakstelėkite rainelę ekrane, kad kamera ją sufokusuotų, laikykite telefoną stabiliai ir padarykite 3-5 kadrus.',
        ],
      },
    } satisfies Record<BlockReason, BlockCopy>,
    // a reason this page does not know yet: neutral on purpose, it names no cause the server did not name
    blockedOther: {
      badge: 'Per mažai detalių',
      title: 'Per mažai detalių, kad atkurtume Jūsų rainelę',
      reason: 'Šioje nuotraukoje matyti per mažai Jūsų rainelės rašto, kad galėtume jį atkurti, todėl jos nenaudojame.',
      error: 'Šioje nuotraukoje matyti per mažai Jūsų rainelės, kad ją atkurtume. Nufotografuokite iš naujo pagal toliau pateiktus žingsnius.',
      retakeLine: 'Šiame kadre matyti per mažai Jūsų rainelės, kad ją atkurtume. Padarykite kitą kadrą pagal fotografavimo patarimus.',
      thumb: 'iš naujo',
      steps: [LIGHT, CAMERA, FOCUS, STEADY],
    } satisfies BlockCopy,
    guideTitle: 'Fotografuojant iš naujo',
    noneUsable: (n: number) => (n === 2 ? 'Patikrinome abi nuotraukas, bet nė vienos negalima panaudoti.' : `Patikrinome visas ${nuotraukasAcc(n)}, bet nė vienos iš jų negalima panaudoti.`),
    shotUnusable: 'Šio kadro panaudoti negalima. Padarykite kitą pagal aukščiau pateiktus patarimus.',
    shotsUnusable: 'Kol kas nė vieno iš šių kadrų panaudoti negalima. Padarykite kitą pagal aukščiau pateiktus patarimus.',
    fullUnusable: (max: number) => `Nė vieno iš šių ${max} ${kadruWord(max)} panaudoti negalima. Padarykite dar vieną ir pradėkite naują seriją.`,
    verdicts: { good: 'Puiki nuotrauka', ok: 'Tinkama nuotrauka', weak: 'Silpna nuotrauka' },
    detectedIris: 'Rasta rainelė',
    detail: 'Detalumas',
    aimFor: (d: number) => `Siekite ${d}+`,
    fibresResolved: 'Matomos skaidulos',
    // "geriausią", not "ryškiausią": the verdict ranks first, so a photo with a reflection can be sharper and still lose
    picked: (of: number, used: number) => `Palyginome ${nuotraukasAcc(of)} ir panaudojome geriausią (nuotrauka ${used}).`,
    pickedRatio: (ratio: string) => ` Joje ${ratio} karto daugiau skaidulų detalių nei neryškiausioje.`,
    tryRetake: 'Fotografuoti iš naujo',
    pupilNote: 'Atspindys vyzdyje netrukdo: vyzdį atkuriame kaip švarią tamsą.',
    lampFallback: 'Lempos šviesa nuspalvina Jūsų akies baltymą, todėl spalvos gali atrodyti šiltesnės, nei yra iš tikrųjų.',
    closer: 'Fotografuokite iš arčiau arba priartinkite vaizdą, kad rainelė užpildytų didesnę kadro dalį.',
  },

  // the camera shot collector
  collector: {
    header: (n: number, max: number) => `Kadras ${n} iš ${max}`,
    headerDetail: (d: number) => ` · Detalumas ${d}`,
    shotAlt: (n: number) => `Kadras ${n}`,
    // best is printed in the nominative after a colon or as a subject ("Kol kas geriausias: kadras 2")
    bestLabel: (k: number, d?: number) => `kadras ${k}${d !== undefined ? ` (detalumas ${d})` : ''}`,
    full: (max: number, best: string) => `Tai jau ${kadrai(max)}. Panaudosime geriausią: ${best}.`,
    more: (left: number) => `Galite padaryti dar iki ${left} ${kadruWord(left)}. Įvertiname kiekvieną kadrą ir pasiliekame geriausią.`,
    sharpEnough: 'Šis kadras pakankamai ryškus.',
    bestSoFar: 'Kol kas tai geriausias Jūsų kadras.',
    lampSkipped: (n: number, best: string) => `Lempos šviesa nuspalvino kadrą ${n}, todėl naudosime geriausią kadrą tikromis spalvomis: ${best}.`,
    bestIs: (best: string) => `Kol kas geriausias: ${best}. Būtent jį ir panaudosime.`,
    lastFailed: (note: string) => `Paskutinio kadro panaudoti negalima: ${note} Geriausias iki šiol kadras išsaugotas.`,
    takeAnother: 'Dar vienas kadras',
    useBest: 'Naudoti geriausią',
    useThis: 'Naudoti šį kadrą',
    startOver: 'Pradėti iš naujo',
  },

  result: {
    beforeAfter: 'Prieš ir po',
    eyes: 'Akys šiame kūrinyje',
    eyeLabel: (i: number) => `Akis ${i}`,
    sampleLabel: 'DI sugeneruotas pavyzdys',
    yourPhoto: 'Jūsų nuotrauka',
    samplePhoto: 'DI pavyzdys',
    after: 'Studijinis makro',
    sliderBefore: 'Jūsų nuotrauka',
    sliderAfter: 'Atkurta',
    // src/landing/copy.lt.ts TRANSPARENCY_LT, word for word. Shown for a real eye only.
    transparency: 'Spalva paimta iš Jūsų pačių nuotraukos. Kur telefonas neužfiksavo smulkiausių skaidulų, jas atkuria mūsų DI.',
    sampleNote: 'Ši akis yra DI sugeneruotas pavyzdys, ne tikra nuotrauka. Su Jūsų nuotrauka spalva paimama iš Jūsų nuotraukos.',
    colourOff: 'Mūsų spalvų patikra rodo, kad šis atkūrimas nukrypo nuo Jūsų nuotraukos: jis gali atrodyti šviesesnis arba tamsesnis nei Jūsų akis. Paprastai padeda naujas kadras švelnioje dienos šviesoje.',
    retakeEye: (i: number) => `Fotografuoti akį ${i} iš naujo`,
    retakeOnly: 'Fotografuoti šią akį iš naujo',
    replaceSample: 'Naudoti savo akį',
    removed: (i: number) => `Akis ${i} pašalinta.`,
    undo: 'Atšaukti',
    sampleArtwork: 'Pavyzdinis kūrinys',
    sampleBadge: 'DI sugeneruotas pavyzdys',
    // baked into the preview image itself (the engine's caption title, at most 40 characters: this is 24)
    sampleTitle: 'DI sugeneruotas pavyzdys',
    sampleArtworkNote: 'Sukurta tik iš DI sugeneruotos pavyzdinės akies, ne iš tikros nuotraukos.',
    mixedArtworkNote: 'Šiame kūrinyje yra DI sugeneruota pavyzdinė akis, kuri nėra tikra nuotrauka.',
    drag: 'Tempkite rankenėlę.',
    irisPx: (px: number) => `Rainelė Jūsų nuotraukoje: ${px} px.`,
    reflection: 'Atspindys pašalintas.',
    upscaled: 'Maža nuotrauka: prieš atkuriant padidinta.',
    badgeMacro: 'Studijinis makro',
    badgeFallback: 'Tik tikslus padidinimas',
    artwork: 'Jūsų kūrinys',
    composing: 'Kuriama…',
    composeFailed: 'Nepavyko sukurti šios peržiūros.',
    previewReduced: 'Peržiūra sumažinta ir su vandens ženklu.',
    previewFile: (square: boolean): string => (square
      ? 'Jūsų failas: 4096 px, pakankamai ryškus spausdinti iki 50 x 50 cm.'
      : 'Jūsų failas: 4096 px ilgiausioje kraštinėje, pakankamai ryškus spaudai, kurios ilgiausia kraštinė iki 50 cm.'),
    retry: 'Bandyti dar kartą',
    layout: 'Išdėstymas',
    style: 'Stilius',
    namesPlaceholder: 'Vardai arba užrašas (nebūtina)',
    save: 'Išsaugoti peržiūrą',
    // the saved preview's file name (ASCII, as the German one); a sample preview says so in its name too
    fileName: (style: string, n: number, sample: boolean) => `snapeyes-perziura-${style}-${n}-${ltForm(n, 'akis', 'akys', 'akiu')}${sample ? '-di-sugeneruotas-pavyzdys' : ''}.jpg`,
    addSecond: 'Pridėti antrą akį',
    addAnother: 'Pridėti dar vieną akį',
    addHint: (left: number) => `Partnerio, vaiko arba kita Jūsų akis. Šiame kūrinyje telpa dar ${left} ${akysWord(left)}.`,
    full: (max: number) => `Tai jau ${akys(max)}: daugiau viename kūrinyje netelpa.`,
    remove: (i: number) => `Pašalinti akį ${i}`,
    startOver: 'Pradėti iš naujo',
    confirmStartOver: (n: number) => `Pašalinti visas akis (${n}) ir pradėti iš naujo?`,
    stored: 'Išsaugota mokymosi atmintyje',

    reveal: {
      photo: 'Jūsų nuotrauka',
      iris: 'Jūsų rainelė',
      art: 'Jūsų kūrinys',
      slider: 'Palyginkite nuotrauką su atkurta rainele',
      valueText: 'nuotrauka {n} %',
      drag: 'Tempkite liniją arba naudokite rodykles. Enter grąžina į vyzdžio pjūvį.',
      promise: 'Atkurta, niekada neperpiešta: niekada nekeičiame Jūsų rainelės spalvos ir nepakeičiame jos kita akimi.',
      stripTitle: 'Nuo nuotraukos iki meno',
      stripIntro: 'Ta pati akis tris kartus: kaip nufotografavote, atkurta ir kaip kūrinys, kurį jai siūlome.',
      stripIntroPair: 'Ta pati akis du kartus: kaip nufotografavote ir atkurta.',
      noCut: 'Šiai akiai pjūvio parodyti nepavyko, todėl Jūsų nuotrauka ir atkurta rainelė rodomos greta.',
      softTip: 'Jūsų nuotrauka maža, todėl jos pusė atrodo minkšta. Prisiartinkite arba naudokite 2x priartinimą, kad palyginimas būtų ryškesnis.',
      frameWide: 'Platus kadras',
      frameTight: 'Siauras kadras: Jūsų nuotrauka yra artimas iškarpymas, aplink rainelę nieko nepiešiama',
    },
  },

  price: {
    title: 'Šio kūrinio kaina',
    oneEye: (style: string) => `1 akis · ${style}`,
    duo: 'Couple Duo · 2 akys',
    many: (n: number) => `${akys(n)} · Couple Duo + dar ${n - 2}`,
    oneEyeOther: (studioBlack: string, art: string) => `1 akis: ${studioBlack} Studio Black stiliumi, ${art} su meniniu fonu.`,
    duoOffer: (duo: string) => `Pridėkite antrą akį ir gausite Couple Duo: ${duo} už abi.`,
    extra: (duo: string, extra: string, max: number) => `Couple Duo ${duo}, toliau +${extra} už kiekvieną papildomą akį, iki ${max} ${akiuWord(max)}.`,
    // src/landing/copy.lt.ts pricing.notice, word for word
    notice: 'Užsakymus pradėsime priimti netrukus - peržiūra jau šiandien nemokama.',
    footnote: 'Gautumėte vieną skaitmeninį failą be vandens ženklo, kurio ilgoji kraštinė yra 4096 px. Kainos nurodytos eurais.',
    footnoteAud: 'Gautumėte vieną skaitmeninį failą be vandens ženklo, kurio ilgoji kraštinė yra 4096 px. Kainos nurodytos Australijos doleriais (A$).',
    footnoteHuf: 'Gautumėte vieną skaitmeninį failą be vandens ženklo, kurio ilgoji kraštinė yra 4096 px. Kainos nurodytos Vengrijos forintais (Ft).',
    demo: 'Tai demonstracija su DI sugeneruota pavyzdine akimi. Išbandykite su savo akimi ir pamatysite savo kainą.',
    sampleNotCounted: (k: number) => (k === 1
      ? 'DI sugeneruota pavyzdinė akis nėra užsakymo dalis, todėl ji neskaičiuojama.'
      : `DI sugeneruotos pavyzdinės akys (${k}) nėra užsakymo dalis, todėl jos neskaičiuojamos.`),
  },

  // ordering from the result screen. The waiver and the links under it are src/shared/legal.ts
  // CHECKOUT_LEGAL.lt, word for word the text the server records (api/_lib/pay_lt.py CONSENT_TEXT_LT). The
  // button only opens Stripe's page, so it carries continueButton, never "pirkti" or "užsakyti"; the binding order is
  // Stripe's own pay button ("užsakymas su prievole sumokėti", CK 6.228(8) straipsnio 3 dalis).
  buy: {
    button: (price: string) => `${CHECKOUT_LEGAL.lt.continueButton} · ${price}`,
    next: 'Toliau atsidarys saugus Stripe mokėjimo puslapis. Ten įvesite savo el. pašto adresą ir pateiksite užsakymą su prievole sumokėti, kai patvirtinsite mokėjimą mokėjimo mygtuku. Jūsų failą pradedame kurti, kai tik išsiunčiamas užsakymo patvirtinimo el. laiškas, paprastai per minutę nuo apmokėjimo.',
    waitPreview: 'Šio pasirinkimo peržiūra dar kuriama. Užsisakyti galėsite, kai tik ją pamatysite.',
    previewFailed: 'Pirmiausia įkelkite šio pasirinkimo peržiūrą (aukščiau: „Bandyti dar kartą“), kad matytumėte, ką užsisakote.',
    steps: {
      sync: 'Tikriname Jūsų užsakymą…',
      upload: (i: number, n: number) => (n > 1 ? `Įkeliame akį ${i} iš ${n}…` : 'Įkeliame Jūsų akį…'),
      arrange: 'Išdėstome Jūsų akis…',
      checkout: 'Atidarome saugų mokėjimo puslapį…',
    },
    // the card shows its own replace button(s) right under this line, so the line names none
    sample: (k: number): string => (k === 1
      ? 'DI sugeneruotos pavyzdinės akies užsisakyti negalima. Pakeiskite ją savo akimi, kad galėtumėte užsisakyti šį kūrinį.'
      : 'DI sugeneruotų pavyzdinių akių užsisakyti negalima. Pakeiskite jas savo akimis, kad galėtumėte užsisakyti šį kūrinį.'),
    replaceSampleEye: (i: number) => `Pakeisti akį ${i} savo akimi`,
    // api/_lib/iris.py TICKET_TTL: a photo can be ordered within 15 minutes of taking it
    stale: (list: number[], total: number) => (total === 1
      ? 'Jūsų nuotrauka padaryta daugiau nei prieš 15 minučių. Nuotrauką galima užsisakyti per 15 minučių nuo jos padarymo, todėl, kad galėtumėte užsisakyti, nufotografuokite dar kartą.'
      : `${list.length === 1 ? `Akis ${list[0]} nufotografuota` : `Akys ${andList(list, 'ir')} nufotografuotos`} daugiau nei prieš 15 minučių. Nuotrauką galima užsisakyti per 15 minučių nuo jos padarymo, todėl, kad galėtumėte užsisakyti, ${list.length === 1 ? 'ją' : 'jas'} nufotografuokite dar kartą.${list.length < total ? ' Kitos Jūsų akys lieka tokios, kokios yra.' : ''}`),
    cancelled: 'Mokėjimas atšauktas. Pinigai nenuskaityti. Jūsų kūrinys vis dar čia: galite jį pakeisti arba užsisakyti dar kartą.',
    cancelledLost: 'Mokėjimas atšauktas. Pinigai nenuskaityti. Šis puslapis neišsaugojo Jūsų peržiūros, todėl nufotografuokite dar kartą.',
    close: 'Uždaryti',
    errors: {
      network: 'Nepavyko susisiekti su SnapEyes. Patikrinkite interneto ryšį ir bandykite dar kartą.',
      busy: 'Mokėjimų paslauga neatsakė. Po akimirkos bandykite dar kartą.',
      payments: `Nepavyko atidaryti mokėjimo puslapio. Bandykite vėliau arba parašykite mums adresu ${CONTACT_EMAIL}.`,
      too_large: 'Vienos iš Jūsų akių nuotrauka per didelė, kad ją įkeltume. Nufotografuokite tą akį dar kartą.',
      // api/order.py draft: 503 uploads_paused and 429 too_many_uploads, both until the next day (UTC)
      paused: `Nauji užsakymai šiandien sustabdyti: pasiektas dienos įkėlimų limitas. Pinigai nenuskaityti. Bandykite rytoj arba parašykite mums adresu ${CONTACT_EMAIL}.`,
      too_many: `Šis užsakymas šiandien pasiekė įkėlimų limitą (30 įkėlimų, įskaitant pakartotinius kadrus). Pinigai nenuskaityti. Bandykite rytoj arba parašykite mums adresu ${CONTACT_EMAIL}.`,
      failed: `Ruošiant Jūsų užsakymą kažkas nepavyko. Bandykite dar kartą arba parašykite mums adresu ${CONTACT_EMAIL}.`,
      closed: 'Užsakymų dar nepriimame.',
    },
    footnote: 'Vienas skaitmeninis failas (JPEG), ilgoji kraštinė 4096 px, be vandens ženklo. Tai galutinė kaina: MB „Portretizuokis“ nėra PVM mokėtoja, todėl PVM netaikomas.',
    footnoteAud: 'Vienas skaitmeninis failas (JPEG), ilgoji kraštinė 4096 px, be vandens ženklo. Tai bendra kaina: GST netaikomas.',
  },

  study: {
    title: (shot: number, photos: number) => (photos > 1 ? `Šeimos testas · nuotraukos ${shot - photos + 1}-${shot}` : `Šeimos testas · kadras ${shot}`),
    light: 'Šviesa šiam kadrui',
    lights: {
      window_daylight: 'Dienos šviesa pro langą', room_lamp: 'Kambario lempa', phone_torch: 'Telefono žibintuvėlis', someone_helped: 'Padėjo kitas žmogus',
    } satisfies Record<LightAnswer, string>,
    comfort: 'Ar buvo lengva? 1 sunku, 5 lengva',
    skip: 'Praleisti',
    // the engine logs the answers only with an analyze request, so they wait for the next photo
    thanks: 'Ačiū. Šie atsakymai bus išsiųsti su kita Jūsų nuotrauka.',
    pending: (shots: number[]) => `Šeimos testas: Jūsų atsakymai apie ${shots.length === 1 ? `kadrą ${shots[0]}` : `kadrus ${shots.join(', ')}`} dar neišsiųsti. Jie bus išsiųsti su kita nuotrauka, pavyzdžiui, kai pridėsite dar vieną akį. Jei dabar uždarysite puslapį, jie bus prarasti.`,
  },
};
