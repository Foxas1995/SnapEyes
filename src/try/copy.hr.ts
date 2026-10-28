// Croatian ("hr") copy for /try: every key of src/try/copy.ts `en`, in the same structure. Polite plural "vi",
// lowercase inside sentences as modern Croatian web copy writes it, and the landing page's words
// (src/landing/copy.hr.ts): stražnja kamera, prednja kamera, zum 2x, snimka (shot), fotografija, pregled,
// umjetničko djelo, obnoviti, vlakna, umjetna inteligencija (UI only in the shortest labels). Decimal comma (3,7).
// Croatian grammar the English helpers do not need (src/shared/hr.ts):
//  - a noun after a number takes one of three forms: 1 oko, 2 oka, 5 očiju; 1 snimka, 3 snimke, 5 snimaka (hrForm());
//  - "Eye 3" and "shot 2" are ordinals, "3. oko", "2. snimka", and a list of them shares one noun: "1. i 3. oko";
//  - "oko" is also the word for "about", so "about" is always "otprilike" here and an eye is never written "oko 3".
// The server's own sentences (quality.message, tips) come from api/analyze.py in the request's language
// (api/_lib/analyze_hr.py TEXT_HR, the twin of TEXT_HU).
// The buy button carries only „Narudžba s obvezom plaćanja“ (the words of Art. 8(2) Directive 2011/83/EU in its
// official Croatian text, as Zakon o zaštiti potrošača transposes it), without the price: the card shows the price
// right above it. The click that binds is Stripe's pay button; api/_lib/pay_hr.py SUBMIT_NOTE_HR (the twin of
// SUBMIT_NOTE_HU) puts the statutory words right above it.
import type { BlockCopy, BlockReason, TryCopy } from './copy';
import type { LightAnswer } from './multi';
import { CONTACT_EMAIL } from '../landing/config';
import { CHECKOUT_LEGAL } from '../shared/legal';
import { TRANSPARENCY_HR } from '../landing/copy.hr';
import { dec1Hr, fotografijeAcc, hrForm, oci, slova, snimke, snimkeAcc, znakova } from '../shared/hr';

/** "1.", "1. i 3.", "1., 2. i 4.": ordinals in a list; the noun follows once ("1. i 3. oko"). */
const ordList = (xs: number[]) => {
  const o = xs.map((x) => `${x}.`);
  return o.length < 2 ? (o[0] ?? '') : `${o.slice(0, -1).join(', ')} i ${o[o.length - 1]}`;
};

// the capture guide's steps, word for word the same on the capture screen and in the retake cards (src/try/copy.ts)
const LIGHT = 'Dnevno svjetlo s prozora ili svjetiljka, sa strane. Bez sobne lampe i bez bljeskalice.';
const CAMERA = 'Stražnja kamera sa zumom 2x, otprilike 10 cm od oka.';
const FOCUS = 'Dodirnite šarenicu na zaslonu kako bi je kamera izoštrila.';
const STEADY = 'Držite mobitel mirno (oslonite laktove na nešto) i napravite 3-5 snimaka.';
// the first retake step for a dark iris: the same light, only closer to the window
const DARK_LIGHT = 'Više svjetla otkriva uzorak tamne šarenice: danju stanite blizu svijetlog prozora, tako da je prozor sa strane (ne na izravnom suncu), ili zamolite nekoga da drži svjetiljku sa strane. Bez sobne lampe i bez bljeskalice.';

export const hr: TryCopy = {
  lang: 'hr',
  meta: {
    title: 'SnapEyes Studio - Umjetnost šarenice iz fotografije vašeg oka',
    description: 'Fotografirajte svoje oko mobitelom i za otprilike minutu vidjet ćete vlastitu šarenicu, obnovljenu i u stilu koji odaberete.',
  },
  switchLabel: 'Jezik',
  /** One decimal, as Croatian writes it (3,7). */
  dec1: (v: number) => dec1Hr(v),

  header: {
    study: 'Obiteljski test',
  },

  errors: {
    tooLarge: 'Ova je fotografija prevelika. Pokušajte ponovno s običnom fotografijom iz kamere.',
    timeout: 'To je kod nas trajalo predugo. Pokušajte ponovno.',
    notResponding: 'Studio trenutačno ne odgovara. Pokušajte ponovno za trenutak.',
    requestFailed: (status: number) => `Zahtjev nije uspio (${status})`,
    unreadable: 'Ovu fotografiju nismo uspjeli otvoriti. Ako je riječ o HEIC datoteci s iPhonea, ovaj je preglednik ne može pročitati: odaberite JPEG ili PNG ili otvorite snapeyes.com na mobitelu i ondje snimite fotografiju.',
    noEyeAny: 'Ni na jednoj od tih fotografija nismo pronašli oko.',
    noEyeShot: 'Na toj snimci nismo pronašli oko.',
    noEye: 'Oko nije pronađeno',
    keepFailed: 'Pri spremanju vaših snimaka nešto je pošlo po zlu. Snimite fotografiju ponovno.',
  },

  capture: {
    // the first screen's heading: the second part is set in gold
    titleA: 'VAŠE OKO, ',
    titleB: 'KAO UMJETNOST.',
    lead: 'Fotografirajte jedno oko i za otprilike minutu vidjet ćete ga obnovljeno.',
    addTitle: (n: number) => `Dodajte ${n}. oko`,
    addLead: 'Oko vašeg partnera, vašeg djeteta ili vaše drugo oko. Isti koraci kao i prije: napravite nekoliko snimaka, a mi zadržavamo najbolju.',
    takeTurns: 'Fotografirate jedno drugo? Izmjenjujte se: jedno drži mobitel, drugo gleda ravno naprijed. Zatim se zamijenite.',
    helper: 'Najlakše je udvoje, s laktovima na stolu: jedno drži mobitel blizu oka, drugo naslanja bradu na dlan, gleda ravno naprijed i drži svjetiljku sa strane.',
    retakeTitle: (n: number) => `Ponovno snimite ${n}. oko`,
    retakeLead: 'Isti koraci kao i prije. Nova snimka zamijenit će ovo oko na umjetničkom djelu; do tada ono ostaje kakvo jest.',
    back: (n: number) => `Natrag na vaše umjetničko djelo (${oci(n)})`,
    sampleButton: 'Uzorak oka',
    sampleLoadFailed: 'Uzorak oka nije se mogao učitati.',
    thumbLabel: (i: number) => `${i}. oko`,
    sampleThumb: 'UI uzorak',
    // the guide video's button and the four steps under it, one line each (copy.ts says why)
    videoPlay: 'Pokrenite video s uputama',
    videoPause: 'Pauzirajte video s uputama',
    steps: ['Stražnja kamera, zum 2x', 'Otprilike 10 cm od oka', 'Svjetlo s prozora ili svjetiljka, sa strane', 'Dodirnite šarenicu i ne mičite se'],
    moreTips: 'Više savjeta',
    stepsOpen: 'Širom otvoreno oko. ',
    stepsOpenMore: 'Gledajte ravno naprijed i vrhom prsta nježno podignite gornji kapak, tako da ni kapak ni trepavice ne prelaze preko šarenice.',
    stepsShots: 'Napravite 3-5 snimaka i pošaljite sve.',
    stepsShotsMore: ' Između snimaka se malo okrenite. Mjerimo svaku i koristimo najoštriju; u pravom testu najbolja je snimka imala 3,7 puta više detalja od najslabije.',
    takePhoto: 'Snimite fotografiju',
    pickShots: 'Odaberite 3-5 snimaka',
    consent: 'Spremiti fotografiju mojeg oka i rezultat u SnapEyes memoriju za učenje kako bi obnove s vremenom bile sve bolje. Anonimno, bez imena i lica. Brisanje možete zatražiti u bilo kojem trenutku.',
  },

  working: {
    finding: 'Tražimo vašu šarenicu…',
    locating: 'Pronalazimo šarenicu i zjenicu',
    measuringSize: 'Mjerimo veličinu i oštrinu',
    checking: (n: number, done: number) => `Provjeravamo fotografije: ${done} od ${n} gotovo`,
    measuringShot: (k: number, max: number) => `Mjerimo snimku ${k} od ${max}`,
    restoring: 'Obnavljamo vašu šarenicu…',
    restoringEye: (n: number) => `Obnavljamo ${n}. oko…`,
    cut: 'Izrezujemo vašu šarenicu',
    reflections: 'Uklanjamo odraze',
    macro: 'Studijska makro obnova (otprilike 30 s)',
    composing: (n: number) => (n > 1 ? `Slažemo vaše umjetničko djelo (${oci(n)})` : 'Slažemo vaše umjetničko djelo'),
    sampleCaption: 'Uzorak izrađen umjetnom inteligencijom',
    yourIris: 'Vaša šarenica',
    elapsed: (s: number) => `${s} s`,
  },

  quality: {
    retake: 'Snimite ponovno',
    notCentred: 'Šarenica nije u središtu ove fotografije, pa je ne možemo obnoviti. Snimite je ponovno tako da jedno oko ispuni kadar.',
    blocks: {
      too_blurry: {
        title: 'Premutno da bismo obnovili vašu šarenicu',
        reason: 'Na ovoj se fotografiji ne vidi dovoljno uzorka vaše šarenice da bismo ga obnovili, pa je ne koristimo.',
        error: 'Ova je fotografija premutna da bismo obnovili vašu šarenicu. Snimite je ponovno prema koracima u nastavku.',
        retakeLine: 'Ova je snimka premutna da bismo obnovili vašu šarenicu. Snimite je ponovno uz dnevno svjetlo s prozora ili uz svjetiljku, sa strane, stražnjom kamerom sa zumom 2x: dodirnite šarenicu za izoštravanje i držite mobitel mirno.',
        thumb: 'mutno',
        steps: [LIGHT, CAMERA, FOCUS, STEADY],
      },
      too_dark: {
        title: 'Pretamno da bi se vidio uzorak vaše šarenice',
        reason: 'Vaša je šarenica tamna, a svjetla je bilo premalo da bi se vidio njezin uzorak, pa ovu fotografiju ne koristimo.',
        error: 'Ova je fotografija pretamna da bi se vidio uzorak vaše šarenice. Snimite je ponovno prema koracima u nastavku.',
        retakeLine: 'Ova je snimka pretamna da bi se vidio uzorak vaše šarenice. Snimite je ponovno blizu svijetlog prozora uz dnevno svjetlo, s prozorom sa strane, ili uz svjetiljku sa strane. Bez sobne lampe i bez bljeskalice.',
        thumb: 'tamno',
        steps: [DARK_LIGHT, CAMERA, FOCUS, STEADY],
      },
      pupil_too_large: {
        title: 'Zjenica je preširoka da bismo obnovili vašu šarenicu',
        reason: 'Na ovoj je fotografiji vaša zjenica toliko raširena da se oko nje vidi premalo šarenice, pa je ne koristimo.',
        error: 'Na ovoj je fotografiji vaša zjenica preširoka da bismo obnovili vašu šarenicu. Snimite je ponovno prema koracima u nastavku.',
        retakeLine: 'Na ovoj je snimci vaša zjenica preširoka. Više svjetla je smanjuje: snimite ponovno blizu svijetlog prozora uz dnevno svjetlo ili uz svjetiljku sa strane, ne s bljeskalicom.',
        thumb: 'zjenica',
        steps: [
          'Više svjetla smanjuje zjenicu: danju stanite blizu svijetlog prozora, tako da je prozor sa strane (ne na izravnom suncu), ili zamolite nekoga da drži svjetiljku sa strane. Bez bljeskalice.',
          'Prije snimanja dajte svom oku minutu na tom svjetlu, kako bi se zjenica stigla suziti. Kad padne mrak, upalite sva stropna svjetla i zamolite nekoga da drži svjetiljku sa strane.',
          CAMERA,
          'Dodirnite šarenicu na zaslonu za izoštravanje, držite mobitel mirno i napravite 3-5 snimaka.',
        ],
      },
      too_small: {
        title: 'Vaša je šarenica premalena na ovoj fotografiji',
        reason: 'Vaša je šarenica na ovoj fotografiji toliko malena da se vidi premalo njezina uzorka, pa fotografiju ne koristimo.',
        error: 'Vaša je šarenica na ovoj fotografiji premalena da bismo je obnovili. Snimite fotografiju ponovno izbliza, prema koracima u nastavku.',
        retakeLine: 'Vaša je šarenica na ovoj snimci premalena. Približite se: stražnja kamera sa zumom 2x, otprilike 10 cm od oka, tako da šarenica ispuni otprilike trećinu kadra.',
        thumb: 'malo',
        steps: [
          'Približite se: stražnja kamera sa zumom 2x, otprilike 10 cm od oka, tako da šarenica ispuni otprilike trećinu kadra.',
          LIGHT,
          FOCUS,
          STEADY,
        ],
      },
      // a lid over part of the iris (api/analyze.py EYELID_BLOCK_PCT): the studio would have to paint iris over it. The words
      // of the capture guide's open-eye step (stepsOpen, stepsOpenMore) and of api/_lib/analyze_hr.py TEXT_HR["eyelid"]
      eyelid: {
        title: 'Kapak prekriva dio vaše šarenice',
        reason: 'Na ovoj je fotografiji dio vaše šarenice skriven ispod kapka ili trepavica, pa je ne koristimo.',
        error: 'Na ovoj fotografiji kapak prekriva dio vaše šarenice. Snimite je ponovno prema koracima u nastavku.',
        retakeLine: 'Na ovoj snimci kapak prekriva dio vaše šarenice. Gledajte ravno u objektiv, širom otvorite oko i vrhom prsta nježno podignite gornji kapak.',
        thumb: 'kapak',
        steps: [
          'Gledajte ravno u objektiv, ne ukoso: kad pogled skrene u stranu, gornji kapak klizne preko šarenice.',
          'Širom otvorite oko i vrhom prsta nježno podignite gornji kapak, tako da ni koža, ni trepavice, ni maskara ne prelaze preko šarenice.',
          CAMERA,
          'Dodirnite šarenicu na zaslonu za izoštravanje, držite mobitel mirno i napravite 3-5 snimaka.',
        ],
      },
    } satisfies Record<BlockReason, BlockCopy>,
    // a reason this page does not know yet: neutral on purpose, it names no cause the server did not name
    blockedOther: {
      title: 'Premalo detalja da bismo obnovili vašu šarenicu',
      reason: 'Na ovoj se fotografiji ne vidi dovoljno uzorka vaše šarenice da bismo ga obnovili, pa je ne koristimo.',
      error: 'Na ovoj se fotografiji ne vidi dovoljno vaše šarenice da bismo je obnovili. Snimite fotografiju ponovno prema koracima u nastavku.',
      retakeLine: 'Na ovoj se snimci ne vidi dovoljno vaše šarenice da bismo je obnovili. Napravite novu snimku prema uputama za snimanje.',
      thumb: 'ponovno',
      steps: [LIGHT, CAMERA, FOCUS, STEADY],
    } satisfies BlockCopy,
    guideTitle: 'Za ponovno snimanje',
    noneUsable: (n: number) => (n === 1
      ? 'Provjerili smo fotografiju, ali ne može se upotrijebiti.'
      : n === 2
        ? 'Provjerili smo obje fotografije i nijedna se ne može upotrijebiti.'
        : `Provjerili smo ${hrForm(n, 'sve', 'sve', 'svih')} ${fotografijeAcc(n)} i nijedna se ne može upotrijebiti.`),
    shotUnusable: 'Ova se snimka ne može upotrijebiti. Napravite novu prema savjetima iznad.',
    shotsUnusable: 'Nijedna od ovih snimaka zasad se ne može upotrijebiti. Napravite novu prema savjetima iznad.',
    fullUnusable: (max: number) => `Nijedna od ${hrForm(max, 'ove', 'ove', 'ovih')} ${max} ${hrForm(max, 'snimke', 'snimke', 'snimaka')} ne može se upotrijebiti. Napravite novu snimku i započnite novi niz.`,
    detectedIris: 'Prepoznata šarenica',
    pupilNote: 'Odraz na zjenici nije problem: zjenicu iznova gradimo kao čistu tamu.',
    lampFallback: 'Svjetlo lampe oboji bjeloočnicu, pa boje mogu ispasti toplije nego što zaista jesu.',
    closer: 'Približite se ili zumirajte kako bi šarenica ispunila veći dio kadra.',
  },

  // the camera shot collector
  collector: {
    header: (n: number, max: number) => `Snimka ${n} od ${max}`,
    shotAlt: (n: number) => `${n}. snimka`,
    // best is printed in the nominative, after a colon ("Dosad najbolja: 2. snimka")
    bestLabel: (k: number, d?: number) => `${k}. snimka${d !== undefined ? ` (detalji ${d})` : ''}`,
    full: (max: number, best: string) => `To je već ${snimke(max)}. Koristit ćemo najbolju: ${best}.`,
    more: (left: number) => `Možete napraviti najviše još ${snimkeAcc(left)}. Mjerimo svaku snimku i zadržavamo najbolju.`,
    sharpEnough: 'Ova je snimka dovoljno oštra za upotrebu.',
    bestSoFar: 'Ovo je zasad vaša najbolja snimka.',
    lampSkipped: (n: number, best: string) => `Svjetlo lampe obojilo je ${n}. snimku, pa koristimo vašu najbolju snimku u pravim bojama: ${best}.`,
    bestIs: (best: string) => `Dosad najbolja: ${best}. Nju ćemo koristiti.`,
    lastFailed: (note: string) => `Zadnja se snimka ne može upotrijebiti: ${note} Vaša dosad najbolja snimka ostaje sačuvana.`,
    takeAnother: 'Još jedna snimka',
    useBest: 'Koristite najbolju snimku',
    useThis: 'Koristite ovu snimku',
    startOver: 'Počnite ispočetka',
  },

  result: {
    beforeAfter: 'Prije / poslije',
    eyes: 'Oči na ovom umjetničkom djelu',
    eyeLabel: (i: number) => `${i}. oko`,
    sampleLabel: 'Uzorak izrađen umjetnom inteligencijom',
    yourPhoto: 'Vaša fotografija',
    samplePhoto: 'UI uzorak',
    after: 'Studijski makro',
    sliderBefore: 'Vaša fotografija',
    sliderAfter: 'Obnovljeno',
    sliderLabel: 'Usporedite svoju fotografiju i obnovljenu šarenicu',
    sliderValue: 'fotografija {n} posto',
    // announced once, by a polite live region, when the studio has made the preview (release review, perf-a11y M3)
    previewReady: 'Vaš je pregled spreman. Odaberite stil u nastavku.',
    // src/landing/copy.hr.ts TRANSPARENCY_HR, word for word. Shown for a real eye only.
    transparency: TRANSPARENCY_HR,
    // src/shared/aiMaterial.ts AI_MATERIAL_PAGE.hr, word for word as the landing's FAQ answer (src/landing/copy/hr.json)
    aiMaterial: 'U nekim stilovima prah, tekućina, plamen ili prašina oko vaše šarenice materijal je koji je izradila umjetna inteligencija, iz zajedničke biblioteke, pa slika drugog kupca može sadržavati isti komad. Vaša šarenica zadržava boje, uzorak i raspored s vaše fotografije; najfinija vlakna obnavlja umjetna inteligencija, kako je gore opisano.',
    sampleNote: 'Ovo je oko uzorak koji je izradila umjetna inteligencija, a ne prava fotografija. Kad koristite vlastitu fotografiju, boja dolazi iz nje.',
    // new sentences of 2026-10-20 (colourOff, pupilWide, how, did)
    colourOff: 'Boje se mogu malo razlikovati od vašeg oka. Najvjernije su uz dnevno svjetlo ili svjetiljku sa strane, bez bljeskalice; ako vam se sviđa, slobodno nastavite.',
    pupilWide: 'Uz više svjetla zjenica je manja i vidi se više vaše šarenice.',
    how: 'Kako to funkcionira',
    did: {
      title: 'Što smo napravili',
      glare: 'Uklonili smo odraze.',
      sharp: 'Izoštrili smo fokus i fina vlakna.',
      colour: 'Ujednačili smo svjetlo.',
      lid: 'Nastavili smo vašu vlastitu šarenicu ispod kapka.',
      nothing: 'Ništa nismo docrtali: ni nove boje ni uzorak drugog oka.',
      quality: (crop: number) => `Fotografiju snima kamera vašeg mobitela u punoj kvaliteti. Iz nje izrežemo uski isječak vašeg oka (najviše ${crop} px) i njega obnovimo; datoteka pune veličine od 4096 px nastala bi iz te obnove, a ne razvlačenjem vaše fotografije.`,
    },
    retakeEye: (i: number) => `Ponovno snimite ${i}. oko`,
    retakeOnly: 'Ponovno snimite ovo oko',
    replaceSample: 'Umjesto toga koristite svoje oko',
    removed: (i: number) => `${i}. oko je uklonjeno.`,
    undo: 'Poništite',
    sampleArtwork: 'Primjer umjetničkog djela',
    sampleBadge: 'Uzorak izrađen umjetnom inteligencijom',
    // baked into the preview image itself (the engine's caption title, at most 40 characters: this is 38)
    sampleTitle: 'Uzorak izrađen umjetnom inteligencijom',
    sampleArtworkNote: 'Izrađeno samo od uzorka oka koji je izradila umjetna inteligencija, a ne od prave fotografije.',
    mixedArtworkNote: 'Ovo umjetničko djelo sadrži uzorak oka koji je izradila umjetna inteligencija i koji nije prava fotografija.',
    upscaled: 'Mala fotografija: povećana prije obnove.',
    badgeMacro: 'Studijski makro',
    badgeFallback: 'Samo vjerno povećanje',
    artwork: 'Vaše umjetničko djelo',
    composing: 'Slažemo…',
    composeFailed: 'Ovaj pregled nismo uspjeli složiti.',
    previewReduced: 'Pregled je smanjen i ima vodeni žig.',
    previewFile: (square: boolean): string => (square
      ? 'Vaša datoteka: 4096 px, dovoljno oštra za ispis do 50 x 50 cm.'
      : 'Vaša datoteka: 4096 px na duljoj stranici, dovoljno oštra za ispis do 50 cm na toj stranici.'),
    retry: 'Pokušajte ponovno',
    layout: 'Raspored',
    style: 'Stil',
    save: 'Spremite pregled',
    // the saved preview's file name (ASCII, as the English and German ones); a sample preview says so in its name too
    fileName: (style: string, n: number, sample: boolean) => `snapeyes-pregled-${style}-${n}-${hrForm(n, 'oko', 'oka', 'ociju')}${sample ? '-ui-uzorak' : ''}.jpg`,
    addSecond: 'Dodajte drugo oko',
    addAnother: 'Dodajte još jedno oko',
    addHint: (left: number) => `Partner, dijete ili vaše drugo oko. Na ovom umjetničkom djelu ima mjesta za još ${oci(left)}.`,
    full: (max: number) => `To je ${oci(max)}, najviše što stane na jedno umjetničko djelo.`,
    remove: (i: number) => `Uklonite ${i}. oko`,
    startOver: 'Počnite ispočetka',
    confirmStartOver: (n: number) => `Odbaciti sve oči (${n}) i početi ispočetka?`,
    stored: 'Spremljeno u memoriju za učenje',

    reveal: {
      photo: 'Vaša fotografija',
      iris: 'Vaša šarenica',
      slider: 'Usporedite svoju fotografiju s obnovljenom šarenicom',
      valueText: 'fotografija {n} posto',
      promise: 'Obnovljeno, nikad iznova naslikano: nikad ne mijenjamo boju vaše šarenice niti je zamjenjujemo drugim okom.',
      softTip: 'Vaša je fotografija mala, pa njezina polovica djeluje neoštro. Približite se ili koristite zum 2x za oštriju usporedbu.',
    },
  },

  // the style picker (src/try/picker.ts): not yet read by a native speaker
  picker: {
    groups: { one: 'Samo vi', two: 'Vas dvoje', family: 'Obitelj' },
    groupIntro: {
      one: 'Jedna šarenica, sama na crnom ili u vlastitom svemiru.',
      two: 'Za partnera: dvije šarenice koje se susreću.',
      family: 'Za obitelj: svaka šarenica zadržava svoju boju.',
    },
    groupSoon: 'Besplatni pregled već sada. Naručivanje za ovu skupinu otvara se uskoro.',
    countSoon: (n: number) => `Naručivanje za ${oci(n)} otvara se uskoro.`,
    soonBuy: 'Ovaj stil stiže uskoro. Odaberite drugi ako želite naručiti sada.',
    retakeBuy: (total: number) => (total === 1
      ? 'S ovom fotografijom zasad se ništa ne može naručiti. Za narudžbu ponovno snimite svoje oko.'
      : 'S ovim fotografijama zasad se ništa ne može naručiti. Za narudžbu ponovno snimite oči navedene u nastavku.'),
    soonNote: 'Ovaj stil stiže uskoro.',
    soonLookBuy: (look: string) => `Varijanta ${look} stiže uskoro. Odaberite drugu varijantu ili stil ako želite naručiti sada.`,
    soonLookNote: (look: string) => `Varijanta ${look} stiže uskoro.`,
    listLabel: 'Stilovi za vaše oči',
    soon: 'Uskoro',
    recommended: 'Preporučeno',
    reasons: {
      'reason.solo_powder.own': 'Vaše vlastite boje, pretvorene u prah',
      'reason.solo_gold.dark_brown': 'Zlato daje sjaj tamnosmeđim očima',
      'reason.solo_radiance.grey': 'Srebrnasto svjetlo za sive oči',
      'reason.duo_collision_infinity.own': 'Dvije šarenice, jedna beskonačnost',
      'reason.duo_kiss_collision.own': 'Dva svijeta, jedan prasak',
      'reason.duo_kiss_collision.dark_brown': 'Dva svijeta, jedan prasak',
      'reason.duo_kiss_collision.grey': 'Dva svijeta, jedan prasak',
      'reason.grp_collision.own': 'Svatko u svojoj boji',
      'reason.grp_collision.dark_brown': 'Svatko u svojoj boji',
      'reason.grp_collision.grey': 'Svatko u svojoj boji',
    },
    lines: {
      'line.solo_clean': 'Vaša obnovljena šarenica, sama na čistoj crnoj podlozi.',
      'line.solo_powder': 'Rub se raspada u zrnca u bojama vašeg oka.',
      'line.solo_universe': 'Vaša vlastita šarenica, uvećana, ispunjava cijelo platno.',
      'line.solo_splash': 'Rub se uzdiže u krunu od tekućine.',
      'line.solo_gold': 'Tanki zlatni prsten i aureola oko šarenice.',
      'line.solo_radiance': 'Tanke zrake svjetla u bojama vaše šarenice.',
      'line.solo_supernova': 'Zvjezdana prašina izbija iz ruba u bojama vašeg oka.',
      'line.solo_nebula': 'Vaša šarenica sja u srcu maglice.',
      'line.solo_sparks': 'Iskre se dižu s ruba u bojama vašeg oka.',
      'line.solo_halo': 'Vaša šarenica, osvijetljena straga vlastitom bojom.',
      'line.solo_aurora': 'Zastori polarne svjetlosti oko vaše šarenice.',
      'line.solo_echo': 'Vaša šarenica u vlastitoj jeci, vlakna se pružaju poput tunela.',
    },
    tileAlt: (name: string) => `${name} na vašim očima: smanjeni pregled s vodenim žigom`,
    tileMaking: (name: string) => `${name}: pregled se izrađuje`,
    tileFailed: 'Pregled nije izrađen',
    changed: {
      eyes: (from: string, to: string, n: number) => `${from} nije dostupan za ${oci(n)}, pa smo odabrali ${to}.`,
      gate: (from: string, to: string, i: number) => `Za ${from} potrebna je čišća šarenica, pa smo zasad odabrali ${to}. Ponovno snimite ${i}. oko kako biste mogli koristiti ${from}.`,
      reseal: (from: string, to: string, i: number) => `Da biste koristili ${from}, ponovno izradite pregled ${i}. oka. Zasad smo odabrali ${to}.`,
      pupil: (from: string, to: string) => `${from} ne odgovara ovom obliku zjenice, pa smo odabrali ${to}.`,
    },
    chipRetake: 'Ponovno',
    chipLabel: (i: number) => `${i}. oko: potrebno je ponovno snimanje`,
    advisory: (list: number[], total: number) => (total === 1
      ? 'U prstenu vaše šarenice još je kapak ili trepavica. Ponovno snimanje dat će čišći rezultat.'
      : `${ordList(list)} oko: u prstenu je još kapak ili trepavica. Ponovno snimanje dat će čišći rezultat.`),
    retake: {
      calm: 'Da bismo prikazali stilove, trebamo još jednu fotografiju.',
      manual: 'I dalje ne ide? Pošaljite svoje najbolje fotografije na {link} i pogledat ćemo ih.',
      noStyles: 'Za ovoliko očiju zasad ne možemo prikazati nijedan stil. Uklonite jedno oko ili nam pišite.',
    },
    stack: 'Vaše se dvije šarenice jako razlikuju po boji, pa je jedna ispred druge.',
    widePupil: 'Vaše su zjenice široke, pa se šarenice dodiruju umjesto da se preklapaju.',
    options: {
      swap: 'Zamijenite mjesta',
      rotate: 'Zarotirajte mjesta',
      earlier: 'Pomaknite naprijed',
      later: 'Pomaknite natrag',
      earlierLabel: (i: number) => `Pomaknite ${i}. oko naprijed na umjetničkom djelu`,
      laterLabel: (i: number) => `Pomaknite ${i}. oko natrag na umjetničkom djelu`,
      centre: 'Stavite u središte',
      centreLabel: (i: number) => `Stavite ${i}. oko u središte umjetničkog djela`,
      centreNote: 'Prvo je oko u središtu, ostala kruže oko njega. Odaberite oko iznad i stavite ga u središte.',
      look: 'Varijanta',
    },
    names: {
      title: 'Riječi na umjetničkom djelu (nije obavezno)',
      nameFor: (i: number, total: number) => (total === 1 ? 'Ime (nije obavezno)' : `Ime za ${i}. oko`),
      date: 'Datum (nije obavezno)',
      datePlaceholder: 'Na primjer 14. 6. 2026.',
      family: 'Prezime obitelji (nije obavezno)',
      problem: {
        nameLong: (i: number, max: number) => `Ime za ${i}. oko predugo je: najviše ${slova(max)}.`,
        namesLong: (max: number) => `Imena su zajedno preduga: najviše ${slova(max)}.`,
        glyph: (chars: string) => `Font umjetničkog djela ne može prikazati ${chars}. Upotrijebite drugo slovo.`,
        dateLong: (max: number) => `Datum je predug: najviše ${znakova(max)}.`,
        familyLong: (max: number) => `Prezime obitelji predugo je: najviše ${slova(max)}.`,
      },
    },
  },

  price: {
    title: 'Cijena ovog umjetničkog djela',
    eyes: (n: number, style: string) => `${oci(n)} · ${style}`,
    black: (name: string, black: string, art: string) => `1 oko: ${black} za ${name}, ${art} za svaki drugi stil.`,
    duoOffer: (two: string) => `Dodajte drugo oko: ${two} za oba.`,
    extra: (two: string, further: string, max: number) => `Dva oka ${two}, zatim +${further} za svako sljedeće oko, do ${max} ${hrForm(max, 'oka', 'oka', 'očiju')}.`,
    // src/landing/copy.hr.ts pricing.notice, word for word
    notice: 'Naručivanje se otvara uskoro - vaš je pregled danas besplatan.',
    footnote: 'Dobili biste jednu digitalnu datoteku bez vodenog žiga, 4096 px na duljoj stranici. Cijene su u eurima.',
    footnoteAud: 'Dobili biste jednu digitalnu datoteku bez vodenog žiga, 4096 px na duljoj stranici. Cijene su u australskim dolarima (A$).',
    footnoteHuf: 'Dobili biste jednu digitalnu datoteku bez vodenog žiga, 4096 px na duljoj stranici. Cijene su u mađarskim forintama (Ft).',
    footnoteUsd: 'Dobili biste jednu digitalnu datoteku bez vodenog žiga, 4096 px na duljoj stranici. Cijene su u američkim dolarima (US$).',
    demo: 'Ovo je demonstracija s uzorkom oka koji je izradila umjetna inteligencija. Isprobajte sa svojim okom da vidite svoju cijenu.',
    sampleNotCounted: (k: number) => (k === 1
      ? 'Uzorak oka koji je izradila umjetna inteligencija nije dio narudžbe, pa se ne računa.'
      : `Uzorci očiju koje je izradila umjetna inteligencija (${k}) nisu dio narudžbe, pa se ne računaju.`),
  },

  // ordering from the result screen. The waiver and the links under it are src/shared/legal.ts CHECKOUT_LEGAL.hr, word
  // for word the text the server records (api/_lib/pay.py CONSENT_TEXT["hr"]).
  buy: {
    // the label alone (see the header); the price stays in the card's head
    button: (_price: string) => CHECKOUT_LEGAL.hr.continueButton,
    next: `Gumb „${CHECKOUT_LEGAL.hr.continueButton}“ vodi vas na Stripeovu sigurnu stranicu za plaćanje. Ondje upisujete svoju adresu e-pošte, a narudžba postaje obvezujuća kada plaćanje potvrdite gumbom za plaćanje. Izradu vaše datoteke počinjemo nakon što vam pošaljemo e-poruku s potvrdom narudžbe, obično unutar minute od plaćanja.`,
    waitPreview: 'Pregled za ovaj odabir još se izrađuje. Naručiti možete čim ga vidite.',
    previewFailed: 'Najprije učitajte pregled za ovaj odabir (gore: „Pokušajte ponovno“), da vidite što naručujete.',
    steps: {
      sync: 'Provjeravamo vašu narudžbu…',
      upload: (i: number, n: number) => (n > 1 ? `Prenosimo ${i}. oko od ${n}…` : 'Prenosimo vaše oko…'),
      arrange: 'Raspoređujemo vaše oči…',
      checkout: 'Otvaramo sigurnu stranicu za plaćanje…',
    },
    // the card shows its own replace button(s) right under this line, so the line names none
    sample: (k: number): string => (k === 1
      ? 'Uzorak oka koji je izradila umjetna inteligencija ne može se naručiti. Zamijenite ga svojim okom da biste naručili ovo umjetničko djelo.'
      : 'Uzorci očiju koje je izradila umjetna inteligencija ne mogu se naručiti. Zamijenite ih svojim očima da biste naručili ovo umjetničko djelo.'),
    replaceSampleEye: (i: number) => `Zamijenite ${i}. oko svojim`,
    // api/_lib/iris.py TICKET_TTL: an eye's draft is accepted only with its photo's 15-minute work ticket
    stale: (list: number[], total: number) => (total === 1
      ? 'Vaša je fotografija snimljena prije više od 15 minuta. Fotografija se može naručiti u roku od 15 minuta od snimanja, pa je za narudžbu snimite ponovno.'
      : `${list.length === 1 ? `${list[0]}. oko snimljeno je` : `${ordList(list)} oko snimljena su`} prije više od 15 minuta. Fotografija se može naručiti u roku od 15 minuta od snimanja, pa ${list.length === 1 ? 'ga' : 'ih'} za narudžbu snimite ponovno.${list.length < total ? ' Vaše ostale oči ostaju kakve jesu.' : ''}`),
    cancelled: 'Plaćanje je otkazano. Ništa nije naplaćeno. Vaše je umjetničko djelo još ovdje: možete ga promijeniti ili ponovno naručiti.',
    cancelledLost: 'Plaćanje je otkazano. Ništa nije naplaćeno. Ova stranica nije mogla sačuvati vaš pregled, pa ponovno snimite fotografiju.',
    close: 'Zatvorite',
    errors: {
      network: 'Nismo uspjeli doći do SnapEyesa. Provjerite internetsku vezu i pokušajte ponovno.',
      busy: 'Usluga plaćanja nije odgovorila. Pokušajte ponovno za trenutak.',
      payments: `Nismo uspjeli otvoriti stranicu za plaćanje. Pokušajte ponovno kasnije ili nam pišite na ${CONTACT_EMAIL}.`,
      too_large: 'Fotografija jednog od vaših očiju prevelika je za prijenos. Ponovno snimite to oko.',
      // api/order.py draft: 503 uploads_paused and 429 too_many_uploads, both until the next day (UTC)
      paused: `Nove su narudžbe za danas pauzirane: dosegnuto je dnevno ograničenje prijenosa. Ništa nije naplaćeno. Pokušajte ponovno sutra ili nam pišite na ${CONTACT_EMAIL}.`,
      too_many: `Ova je narudžba za danas dosegnula ograničenje prijenosa (30 prijenosa, uključujući ponovna snimanja). Ništa nije naplaćeno. Pokušajte ponovno sutra ili nam pišite na ${CONTACT_EMAIL}.`,
      failed: `Pri pripremi vaše narudžbe nešto je pošlo po zlu. Pokušajte ponovno ili nam pišite na ${CONTACT_EMAIL}.`,
      closed: 'Naručivanje još nije otvoreno.',
      plan_changed: 'Vaše se umjetničko djelo upravo promijenilo, pa smo ponovno izradili pregled. Pogledajte ga, a zatim ponovno pritisnite gumb.',
      unavailable: 'Ovaj se stil trenutačno ne može naručiti za vaše oči. Odaberite drugi ili ponovno snimite oko.',
    },
    namesBlocked: 'Najprije ispravite riječi na umjetničkom djelu (vidi gore).',
    footnote: 'Jedna digitalna datoteka (JPEG), 4096 px na duljoj stranici, bez vodenog žiga. Ovo je konačna cijena: nismo u sustavu PDV-a, pa se PDV ne obračunava.',
    footnoteAud: 'Jedna digitalna datoteka (JPEG), 4096 px na duljoj stranici, bez vodenog žiga. Ovo je ukupna cijena: GST se ne naplaćuje.',
    footnoteUsd: 'Jedna digitalna datoteka (JPEG), 4096 px na duljoj stranici, bez vodenog žiga. Ovo je ukupna cijena: američki porez na promet ne naplaćuje se.',
  },

  // the anonymous feedback box (src/try/Feedback.tsx, api/_lib/feedback.py)
  feedback: {
    title: { result: 'Kako vam se čini?', retake: 'Je li vam ovo pomoglo?' },
    hint: { result: 'Jedan dodir i, ako želite, nekoliko riječi. Stiže do osobe koja izrađuje ove slike.', retake: 'Jednim dodirom recite nam što vam je zasmetalo.' },
    chips: {
      result: { love: 'Sviđa mi se', likeness: 'Ne izgleda kao moje oko', colour: 'Boje ne izgledaju točno', style: 'Više bi mi odgovarao drugi stil', price: 'Cijena mi je previsoka', other: 'Nešto drugo' },
      retake: { unclear: 'Ne razumijem što ne valja', fine: 'Mislim da mi je fotografija dobra', device: 'Moj mobitel ne može bolje', only: 'To mi je jedina fotografija', effort: 'Previše je truda', other: 'Nešto drugo' },
    },
    textLabel: 'Želite li nešto dodati? (nije obavezno)',
    textHint: 'Molimo vas da ne pišete imena, adrese e-pošte ni brojeve telefona.',
    count: (n: number, max: number) => `${n} / ${max}`,
    send: 'Pošaljite',
    sending: 'Šaljemo',
    thanks: 'Hvala vam. Stiglo je do osobe koja izrađuje ove slike.',
    textDropped: 'Hvala vam. Vaš smo odgovor ubrojili, ali tekst nismo zadržali jer se činilo da sadrži podatke za kontakt ili poveznicu.',
    textLost: 'Hvala vam. Vaš je odgovor stigao, ali tekst se nije mogao spremiti.',
    failed: 'Slanje nije uspjelo. Pokušajte ponovno za trenutak.',
    privacy: 'Anonimno: bez imena, bez e-pošte. Tekst se briše nakon 90 dana.',
  },

  study: {
    title: (shot: number, photos: number) => (photos > 1 ? `Obiteljski test · fotografije ${shot - photos + 1}-${shot}` : `Obiteljski test · ${shot}. snimka`),
    light: 'Svjetlo za ovu snimku',
    lights: {
      window_daylight: 'Dnevno svjetlo s prozora', room_lamp: 'Sobna lampa', phone_torch: 'Svjetiljka mobitela', someone_helped: 'Netko je pomogao',
    } satisfies Record<LightAnswer, string>,
    comfort: 'Koliko je bilo lako? 1 teško, 5 lako',
    skip: 'Preskočite',
    // the engine logs the answers only with an analyze request, so they wait for the next photo
    thanks: 'Hvala vam. Ovi se odgovori šalju s vašom sljedećom fotografijom.',
    pending: (shots: number[]) => `Obiteljski test: vaši odgovori o ${shots.length === 1 ? `${shots[0]}. snimci` : `snimkama ${shots.join(', ')}`} još nisu poslani. Šalju se s vašom sljedećom fotografijom, na primjer kada dodate još jedno oko. Ako sada zatvorite stranicu, bit će izgubljeni.`,
  },
};
