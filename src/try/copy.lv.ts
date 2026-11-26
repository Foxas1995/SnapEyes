// Latvian ("lv") copy for /try: every key of src/try/copy.ts `en`, in the same structure. Polite plural "jūs",
// lowercase inside sentences as Latvian web copy writes it, and the landing page's words
// (src/landing/copy/lv.json): aizmugurējā kamera, priekšējā kamera, 2x tuvinājums, kadrs (shot), fotogrāfija,
// priekšskatījums, mākslas darbs, atjaunot, šķiedras, mākslīgais intelekts (MI only in the shortest labels).
// Decimal comma (3,7). Buttons are infinitives ("Fotografēt"), instructions the polite imperative ("Nofotografējiet").
// Latvian grammar the English helpers do not need (src/shared/lv.ts):
//  - a noun after a number takes one of three forms: 1 acs, 2 acis, 10 acu; 1 kadrs, 3 kadri, 10 kadru (lvForm()),
//    and the sentence declines it (dative "vieta 3 acīm", accusative "vēl 1 kadru");
//  - "Eye 3" and "shot 2" are ordinals, "3. acs", "2. kadrs", and a list of them shares one noun: "1. un 3. acs".
// The server's own sentences (quality.message, tips) come from api/analyze.py in the request's language
// (api/_lib/analyze_lv.py TEXT_LV, the twin of TEXT_HR).
// The buy button carries only „Pasūtījums ar pienākumu maksāt” (the words of Art. 8(2) Directive 2011/83/EU in its
// official Latvian text), without the price: the card shows the price right above it. The click that binds is
// Stripe's pay button; api/_lib/pay_lv.py SUBMIT_NOTE_LV (the twin of SUBMIT_NOTE_HR) puts the statutory words right
// above it.
import type { BlockCopy, BlockReason, TryCopy } from './copy';
import type { LightAnswer } from './multi';
import { CONTACT_EMAIL } from '../landing/config';
import { CHECKOUT_LEGAL } from '../shared/legal';
import { TRANSPARENCY_LV } from '../landing/copy.lv';
import { acis, acisDat, burti, dec1Lv, fotografijasAcc, kadri, kadriAcc, lvForm, zimes } from '../shared/lv';

/** "1.", "1. un 3.", "1., 2. un 4.": ordinals in a list; the noun follows once ("1. un 3. acs"). */
const ordList = (xs: number[]) => {
  const o = xs.map((x) => `${x}.`);
  return o.length < 2 ? (o[0] ?? '') : `${o.slice(0, -1).join(', ')} un ${o[o.length - 1]}`;
};

// the capture guide's steps, word for word the same on the capture screen and in the retake cards (src/try/copy.ts)
const LIGHT = 'Dienasgaisma no loga vai lukturītis, no sāniem. Bez istabas lampas un bez zibspuldzes.';
const CAMERA = 'Aizmugurējā kamera ar 2x tuvinājumu, apmēram 10 cm no acs.';
const FOCUS = 'Pieskarieties varavīksnenei ekrānā, lai kamera to iefokusē.';
const STEADY = 'Turiet telefonu nekustīgi (atbalstiet elkoņus pret kaut ko) un uzņemiet 3-5 kadrus.';
// the first retake step for a dark iris: the same light, only closer to the window
const DARK_LIGHT = 'Vairāk gaismas izceļ tumšas varavīksnenes rakstu: dienā nostājieties tuvu gaišam logam tā, lai logs būtu sānos (ne tiešos saules staros), vai palūdziet kādam turēt lukturīti no sāniem. Bez istabas lampas un bez zibspuldzes.';

export const lv: TryCopy = {
  lang: 'lv',
  meta: {
    title: 'SnapEyes Studio - Varavīksnenes māksla no jūsu acs fotogrāfijas',
    description: 'Nofotografējiet savu aci ar telefonu un apmēram minūtes laikā ieraugiet savu varavīksneni, atjaunotu un jūsu izvēlētajā stilā.',
  },
  switchLabel: 'Valoda',
  /** One decimal, as Latvian writes it (3,7). */
  dec1: (v: number) => dec1Lv(v),

  header: {
    study: 'Ģimenes tests',
  },

  errors: {
    tooLarge: 'Šī fotogrāfija ir pārāk liela. Mēģiniet vēlreiz ar parastu kameras fotogrāfiju.',
    timeout: 'Mūsu pusē tas aizņēma pārāk ilgu laiku. Mēģiniet vēlreiz.',
    notResponding: 'Studija pašlaik neatbild. Mēģiniet vēlreiz pēc brīža.',
    requestFailed: (status: number) => `Pieprasījums neizdevās (${status})`,
    unreadable: 'Šo fotogrāfiju neizdevās atvērt. Ja tas ir HEIC fails no iPhone, šī pārlūkprogramma to nevar nolasīt: izvēlieties JPEG vai PNG vai atveriet snapeyes.com telefonā un nofotografējiet tur.',
    noEyeAny: 'Nevienā no šīm fotogrāfijām neatradām aci.',
    noEyeShot: 'Šajā kadrā neatradām aci.',
    noEye: 'Acs nav atrasta',
    keepFailed: 'Saglabājot jūsu kadrus, kaut kas nogāja greizi. Nofotografējiet vēlreiz.',
  },

  capture: {
    // the first screen's heading: the second part is set in gold
    titleA: 'NOFOTOGRAFĒJIET',
    titleB: ' SAVU ACI.',
    lead: 'Pēc minūtes redzēsiet to kā mākslas darbu. Bez maksas.',
    addTitle: (n: number) => `Pievienojiet ${n}. aci`,
    addLead: 'Jūsu partnera, jūsu bērna vai jūsu otra acs. Tie paši soļi kā iepriekš: uzņemiet dažus kadrus, un mēs paturēsim labāko.',
    takeTurns: 'Fotografējat viens otru? Mainieties: viens tur telefonu, otrs skatās taisni uz priekšu. Pēc tam samainieties.',
    retakeTitle: (n: number) => `Nofotografējiet ${n}. aci vēlreiz`,
    retakeLead: 'Tie paši soļi kā iepriekš. Jaunais kadrs aizstās šo aci mākslas darbā; līdz tam tā paliek, kāda ir.',
    back: (n: number) => `Atpakaļ pie jūsu mākslas darba (${acis(n)})`,
    sampleButton: 'Parauga acs',
    sampleLoadFailed: 'Parauga aci neizdevās ielādēt.',
    // the guide video's button and the four steps under it, one line each (copy.ts says why)
    videoPlay: 'Atskaņot pamācības video',
    videoPause: 'Apturēt pamācības video',
    steps: ['Aizmugurējā kamera, 2x tuvinājums', 'Apmēram 10 cm no acs', 'Gaisma no loga vai lukturīša, no sāniem', 'Pieskarieties varavīksnenei un nekustieties'],
    moreTips: 'Vairāk padomu',
    stepsOpen: 'Plaši atvērta acs. ',
    stepsOpenMore: 'Skatieties taisni uz priekšu un ar pirksta galu saudzīgi paceliet augšējo plakstiņu, lai plakstiņš un skropstas neaizsedz varavīksneni.',
    stepsShots: 'Uzņemiet 3-5 kadrus un nosūtiet visus.',
    stepsShotsMore: ' Starp kadriem nedaudz pagriezieties. Mēs izmērām katru un izmantojam asāko; īstā testā labākajā kadrā bija 3,7 reizes vairāk detaļu nekā sliktākajā.',
    cameraTip: 'Visasākā fotogrāfija sanāk ar telefona kameru (2x, pie loga): nofotografējiet un augšupielādējiet to šeit.',
    // the live camera of ?cam=1 (src/try/livecam): the hint inside the view, the torch button, the shutter's label for a screen reader
    liveHint: 'Turiet aci aplī',
    liveLight: 'Gaisma',
    liveShutter: 'Fotografēt',
    takePhoto: 'Fotografēt aci',
    pickShots: 'Augšupielādēt foto',
    consent: 'Saglabāt manas acs fotogrāfiju un rezultātu SnapEyes mācību atmiņā, lai atjaunošana ar laiku kļūtu arvien labāka. Anonīmi, bez vārda un sejas. Dzēšanu varat lūgt jebkurā brīdī.',
  },

  working: {
    finding: 'Meklējam jūsu varavīksneni…',
    // the waiting screens' slideshow (src/try/Slideshow.tsx): its one line
    slidesLine: 'Drīz arī jūsu acs izskatīsies tā.',
    locating: 'Atrodam varavīksneni un zīlīti',
    measuringSize: 'Mērām izmēru un asumu',
    checking: (n: number, done: number) => `Pārbaudām fotogrāfijas: gatavas ${done} no ${n}`,
    measuringShot: (k: number, max: number) => `Mērām ${k}. kadru no ${max}`,
    restoring: 'Atjaunojam jūsu varavīksneni…',
    restoringEye: (n: number) => `Atjaunojam ${n}. aci…`,
    cut: 'Izgriežam jūsu varavīksneni',
    reflections: 'Noņemam atspīdumus',
    macro: 'Studijas makro atjaunošana (apmēram 30 s)',
    composing: (n: number) => (n > 1 ? `Veidojam jūsu mākslas darbu (${acis(n)})` : 'Veidojam jūsu mākslas darbu'),
    sampleCaption: 'Mākslīgā intelekta radīts paraugs',
    yourIris: 'Jūsu varavīksnene',
    elapsed: (s: number) => `${s} s`,
  },

  quality: {
    retake: 'Fotografēt vēlreiz',
    notCentred: 'Varavīksnene nav šīs fotogrāfijas centrā, tāpēc to nevar atjaunot. Nofotografējiet vēlreiz tā, lai viena acs aizpilda kadru.',
    blocks: {
      too_blurry: {
        title: 'Pārāk izplūdis, lai atjaunotu jūsu varavīksneni',
        reason: 'Šajā fotogrāfijā nav redzams pietiekami daudz jūsu varavīksnenes raksta, lai to atjaunotu, tāpēc to neizmantojam.',
        error: 'Šī fotogrāfija ir pārāk izplūdusi, lai atjaunotu jūsu varavīksneni. Nofotografējiet vēlreiz, sekojot tālāk norādītajiem soļiem.',
        retakeLine: 'Šis kadrs ir pārāk izplūdis, lai atjaunotu jūsu varavīksneni. Uzņemiet to vēlreiz dienasgaismā no loga vai ar lukturīti, no sāniem, ar aizmugurējo kameru un 2x tuvinājumu: pieskarieties varavīksnenei, lai iefokusētu, un turiet telefonu nekustīgi.',
        thumb: 'izplūdis',
        steps: [LIGHT, CAMERA, FOCUS, STEADY],
      },
      too_dark: {
        title: 'Pārāk tumšs, lai redzētu jūsu varavīksnenes rakstu',
        reason: 'Jūsu varavīksnene ir tumša, un gaismas bija par maz, lai redzētu tās rakstu, tāpēc šo fotogrāfiju neizmantojam.',
        error: 'Šī fotogrāfija ir pārāk tumša, lai redzētu jūsu varavīksnenes rakstu. Nofotografējiet vēlreiz, sekojot tālāk norādītajiem soļiem.',
        retakeLine: 'Šis kadrs ir pārāk tumšs, lai redzētu jūsu varavīksnenes rakstu. Uzņemiet to vēlreiz dienasgaismā tuvu gaišam logam tā, lai logs būtu sānos, vai ar lukturīti no sāniem. Bez istabas lampas un bez zibspuldzes.',
        thumb: 'tumšs',
        steps: [DARK_LIGHT, CAMERA, FOCUS, STEADY],
      },
      pupil_too_large: {
        title: 'Zīlīte ir pārāk plata, lai atjaunotu jūsu varavīksneni',
        reason: 'Šajā fotogrāfijā jūsu zīlīte ir tik plata, ka ap to redzams pārāk maz varavīksnenes, tāpēc to neizmantojam.',
        error: 'Šajā fotogrāfijā jūsu zīlīte ir pārāk plata, lai atjaunotu jūsu varavīksneni. Nofotografējiet vēlreiz, sekojot tālāk norādītajiem soļiem.',
        retakeLine: 'Šajā kadrā jūsu zīlīte ir pārāk plata. Vairāk gaismas to samazina: uzņemiet vēlreiz dienasgaismā tuvu gaišam logam vai ar lukturīti no sāniem, nevis ar zibspuldzi.',
        thumb: 'zīlīte',
        steps: [
          'Vairāk gaismas samazina zīlīti: dienā nostājieties tuvu gaišam logam tā, lai logs būtu sānos (ne tiešos saules staros), vai palūdziet kādam turēt lukturīti no sāniem. Bez zibspuldzes.',
          'Pirms fotografēšanas ļaujiet acij minūti pabūt šajā gaismā, lai zīlīte paspēj sašaurināties. Kad ir tumšs, ieslēdziet visas griestu lampas un palūdziet kādam turēt lukturīti no sāniem.',
          CAMERA,
          'Pieskarieties varavīksnenei ekrānā, lai iefokusētu, turiet telefonu nekustīgi un uzņemiet 3-5 kadrus.',
        ],
      },
      too_small: {
        title: 'Jūsu varavīksnene šajā fotogrāfijā ir pārāk maza',
        reason: 'Jūsu varavīksnene šajā fotogrāfijā ir tik maza, ka redzams pārāk maz tās raksta, tāpēc to neizmantojam.',
        error: 'Jūsu varavīksnene šajā fotogrāfijā ir pārāk maza, lai to atjaunotu. Nofotografējiet vēlreiz no mazāka attāluma, sekojot tālāk norādītajiem soļiem.',
        retakeLine: 'Jūsu varavīksnene šajā kadrā ir pārāk maza. Pieejiet tuvāk: aizmugurējā kamera ar 2x tuvinājumu, apmēram 10 cm no acs, lai varavīksnene aizņem apmēram trešdaļu kadra.',
        thumb: 'maza',
        steps: [
          'Pieejiet tuvāk: aizmugurējā kamera ar 2x tuvinājumu, apmēram 10 cm no acs, lai varavīksnene aizņem apmēram trešdaļu kadra.',
          LIGHT,
          FOCUS,
          STEADY,
        ],
      },
      // a lid over part of the iris (api/analyze.py EYELID_BLOCK_PCT): the studio would have to paint iris over it. The words
      // of the capture guide's open-eye step (stepsOpen, stepsOpenMore) and of api/_lib/analyze_lv.py TEXT_LV["eyelid"]
      eyelid: {
        title: 'Plakstiņš aizsedz daļu jūsu varavīksnenes',
        reason: 'Šajā fotogrāfijā daļa jūsu varavīksnenes ir paslēpta zem plakstiņa vai skropstām, tāpēc to neizmantojam.',
        error: 'Šajā fotogrāfijā plakstiņš aizsedz daļu jūsu varavīksnenes. Nofotografējiet vēlreiz, sekojot tālāk norādītajiem soļiem.',
        retakeLine: 'Šajā kadrā plakstiņš aizsedz daļu jūsu varavīksnenes. Skatieties taisni objektīvā, plaši atveriet aci un ar pirksta galu saudzīgi paceliet augšējo plakstiņu.',
        thumb: 'plakstiņš',
        steps: [
          'Skatieties taisni objektīvā, nevis slīpi: kad skatiens novirzās sānis, augšējais plakstiņš noslīd pār varavīksneni.',
          'Plaši atveriet aci un ar pirksta galu saudzīgi paceliet augšējo plakstiņu, lai āda, skropstas un skropstu tuša neaizsedz varavīksneni.',
          CAMERA,
          'Pieskarieties varavīksnenei ekrānā, lai iefokusētu, turiet telefonu nekustīgi un uzņemiet 3-5 kadrus.',
        ],
      },
    } satisfies Record<BlockReason, BlockCopy>,
    // a reason this page does not know yet: neutral on purpose, it names no cause the server did not name
    blockedOther: {
      title: 'Par maz detaļu, lai atjaunotu jūsu varavīksneni',
      reason: 'Šajā fotogrāfijā nav redzams pietiekami daudz jūsu varavīksnenes raksta, lai to atjaunotu, tāpēc to neizmantojam.',
      error: 'Šajā fotogrāfijā nav redzams pietiekami daudz jūsu varavīksnenes, lai to atjaunotu. Nofotografējiet vēlreiz, sekojot tālāk norādītajiem soļiem.',
      retakeLine: 'Šajā kadrā nav redzams pietiekami daudz jūsu varavīksnenes, lai to atjaunotu. Uzņemiet jaunu kadru, sekojot fotografēšanas pamācībai.',
      thumb: 'vēlreiz',
      steps: [LIGHT, CAMERA, FOCUS, STEADY],
    } satisfies BlockCopy,
    guideTitle: 'Fotografējot vēlreiz',
    noneUsable: (n: number) => (n === 1
      ? 'Pārbaudījām fotogrāfiju, taču to nevar izmantot.'
      : n === 2
        ? 'Pārbaudījām abas fotogrāfijas, un nevienu nevar izmantot.'
        : `Pārbaudījām ${lvForm(n, 'visu', 'visas', 'visas')} ${fotografijasAcc(n)}, un nevienu nevar izmantot.`),
    shotUnusable: 'Šo kadru nevar izmantot. Uzņemiet jaunu, ņemot vērā padomus augstāk.',
    shotsUnusable: 'Nevienu no šiem kadriem pagaidām nevar izmantot. Uzņemiet jaunu, ņemot vērā padomus augstāk.',
    fullUnusable: (max: number) => `Nevienu no ${lvForm(max, 'šī', 'šiem', 'šiem')} ${max} ${lvForm(max, 'kadra', 'kadriem', 'kadriem')} nevar izmantot. Uzņemiet jaunu kadru, lai sāktu jaunu sēriju.`,
    detectedIris: 'Atrastā varavīksnene',
    pupilNote: 'Atspīdums uz zīlītes netraucē: zīlīti mēs atveidojam kā tīru tumsu.',
    lampFallback: 'Lampas gaisma iekrāso acs baltumu, tāpēc krāsas var iznākt siltākas, nekā tās patiesībā ir.',
    closer: 'Pieejiet tuvāk vai pietuviniet, lai varavīksnene aizņem lielāku kadra daļu.',
  },

  // the camera shot collector
  collector: {
    header: (n: number, max: number) => `${n}. kadrs no ${max}`,
    shotAlt: (n: number) => `${n}. kadrs`,
    // best is printed in the nominative, after a colon ("Pagaidām labākais: 2. kadrs")
    bestLabel: (k: number, d?: number) => `${k}. kadrs${d !== undefined ? ` (detaļas ${d})` : ''}`,
    full: (max: number, best: string) => `Tie jau ir ${kadri(max)}. Izmantosim labāko: ${best}.`,
    more: (left: number) => `Varat uzņemt vēl ne vairāk kā ${kadriAcc(left)}. Mēs izmērām katru kadru un paturam labāko.`,
    sharpEnough: 'Šis kadrs ir pietiekami ass, lai to izmantotu.',
    bestSoFar: 'Šis pagaidām ir jūsu labākais kadrs.',
    lampSkipped: (n: number, best: string) => `Lampas gaisma iekrāsoja ${n}. kadru, tāpēc izmantosim jūsu labāko kadru īstajās krāsās: ${best}.`,
    bestIs: (best: string) => `Pagaidām labākais: ${best}. To arī izmantosim.`,
    lastFailed: (note: string) => `Pēdējo kadru nevar izmantot: ${note} Jūsu līdz šim labākais kadrs ir saglabāts.`,
    takeAnother: 'Vēl viens kadrs',
    useBest: 'Izmantot labāko kadru',
    useThis: 'Izmantot šo kadru',
    startOver: 'Sākt no sākuma',
  },

  result: {
    beforeAfter: 'Pirms / pēc',
    eyes: 'Acis šajā mākslas darbā',
    eyeLabel: (i: number) => `${i}. acs`,
    sampleLabel: 'Mākslīgā intelekta radīts paraugs',
    yourPhoto: 'Jūsu fotogrāfija',
    samplePhoto: 'MI paraugs',
    after: 'Studijas makro',
    sliderBefore: 'Jūsu fotogrāfija',
    sliderAfter: 'Atjaunots',
    sliderLabel: 'Salīdziniet savu fotogrāfiju un atjaunoto varavīksneni',
    sliderValue: 'fotogrāfija {n} procenti',
    // announced once, by a polite live region, when the studio has made the preview (release review, perf-a11y M3)
    previewReady: 'Jūsu priekšskatījums ir gatavs. Izvēlieties stilu zemāk.',
    // src/landing/copy.lv.ts TRANSPARENCY_LV, word for word. Shown for a real eye only.
    transparency: TRANSPARENCY_LV,
    // src/shared/aiMaterial.ts AI_MATERIAL_PAGE.lv, word for word as the landing's FAQ answer (src/landing/copy/lv.json)
    aiMaterial: 'Dažos stilos pulveris, šķidrums, liesma vai putekļi ap jūsu varavīksneni ir mākslīgā intelekta radīts materiāls no kopīgas bibliotēkas, tāpēc cita klienta mākslas darbā var būt tas pats elements. Jūsu varavīksnene saglabā jūsu fotogrāfijas krāsas, rakstu un izvietojumu; vissmalkākās šķiedras, kā aprakstīts iepriekš, atjauno mākslīgais intelekts.',
    sampleNote: 'Šī acs ir mākslīgā intelekta radīts paraugs, nevis īsta fotogrāfija. Ja izmantosiet savu fotogrāfiju, krāsa nāks no tās.',
    // new sentences of 2026-10-20 (colourOff, pupilWide, how, did)
    colourOff: 'Krāsas var nedaudz atšķirties no jūsu acs. Visprecīzākās tās ir dienasgaismā vai ar lukturīti no sāniem, bez zibspuldzes; ja jums patīk, turpiniet.',
    pupilWide: 'Vairāk gaismas samazina zīlīti un parāda vairāk jūsu varavīksnenes.',
    pupilLarge: 'Zīlīte ir liela: pie loga tā sašaurināsies, un būs redzams vairāk varavīksnenes raksta.',
    how: 'Kā tas notiek',
    did: {
      title: 'Ko mēs izdarījām',
      glare: 'Noņēmām atspīdumus.',
      sharp: 'Uzlabojām asumu un smalkās šķiedras.',
      colour: 'Izlīdzinājām gaismu.',
      lid: 'Turpinājām jūsu pašu varavīksneni zem plakstiņa.',
      nothing: 'Neko neuzzīmējām pa virsu: ne jaunas krāsas, ne citas acs rakstu.',
      quality: (crop: number) => `Fotogrāfiju pilnā kvalitātē uzņem jūsu telefona kamera. No tās izgriežam jūsu acs tuvplānu (ne vairāk kā ${crop} px) un to atjaunojam; pilna izmēra 4096 px fails tiktu veidots no šīs atjaunošanas, nevis izstiepjot jūsu fotogrāfiju.`,
    },
    retakeEye: (i: number) => `Nofotografēt ${i}. aci vēlreiz`,
    retakeOnly: 'Nofotografēt šo aci vēlreiz',
    replaceSample: 'Tā vietā izmantot savu aci',
    removed: (i: number) => `${i}. acs noņemta.`,
    undo: 'Atsaukt',
    sampleArtwork: 'Mākslas darba paraugs',
    sampleBadge: 'Mākslīgā intelekta radīts paraugs',
    // baked into the preview image itself (the engine's caption title, at most 40 characters: this is 33; Cinzel has
    // every Latvian letter)
    sampleTitle: 'Mākslīgā intelekta radīts paraugs',
    sampleArtworkNote: 'Veidots tikai no mākslīgā intelekta radītas parauga acs, nevis no īstas fotogrāfijas.',
    mixedArtworkNote: 'Šajā mākslas darbā ir mākslīgā intelekta radīta parauga acs, kas nav īsta fotogrāfija.',
    upscaled: 'Maza fotogrāfija: pirms atjaunošanas palielināta.',
    badgeMacro: 'Studijas makro',
    badgeFallback: 'Tikai precīzs palielinājums',
    artwork: 'Jūsu mākslas darbs',
    composing: 'Veidojam…',
    composeFailed: 'Šo priekšskatījumu neizdevās izveidot.',
    previewReduced: 'Priekšskatījums ir samazināts un ar ūdenszīmi.',
    previewFile: (square: boolean): string => (square
      ? 'Jūsu fails: 4096 px, pietiekami ass izdrukai līdz 60 x 60 cm.'
      : 'Jūsu fails: 4096 px garākajā malā, pietiekami ass izdrukai līdz 60 cm šajā malā.'),
    retry: 'Mēģināt vēlreiz',
    layout: 'Izkārtojums',
    style: 'Stils',
    save: 'Saglabāt priekšskatījumu',
    // the saved preview's file name (ASCII, as the English and German ones); a sample preview says so in its name too
    fileName: (style: string, n: number, sample: boolean) => `snapeyes-prieksskatijums-${style}-${n}-${lvForm(n, 'acs', 'acis', 'acu')}${sample ? '-mi-paraugs' : ''}.jpg`,
    addSecond: 'Pievienot otru aci',
    addAnother: 'Pievienot vēl vienu aci',
    addHint: (left: number) => `Partnera, bērna vai jūsu otra acs. Šajā mākslas darbā vēl ir vieta ${acisDat(left)}.`,
    full: (max: number) => `Tās ir ${acis(max)}: vairāk vienā mākslas darbā neietilpst.`,
    quota: (left: number, max: number) => `Bezmaksas priekšskatījumi šodien: atlikuši ${left} no ${max}.`,
    remove: (i: number) => `Noņemt ${i}. aci`,
    startOver: 'Sākt no sākuma',
    confirmStartOver: (n: number) => `Atmest visas acis (${n}) un sākt no sākuma?`,
    stored: 'Saglabāts mācību atmiņā',

    reveal: {
      photo: 'Jūsu fotogrāfija',
      iris: 'Jūsu varavīksnene',
      slider: 'Salīdziniet savu fotogrāfiju ar atjaunoto varavīksneni',
      valueText: 'fotogrāfija {n} procenti',
      promise: 'Atjaunota, nekad nepārzīmēta: mēs nekad nepārkrāsojam jūsu varavīksneni un neaizstājam to ar citu aci.',
      softTip: 'Jūsu fotogrāfija ir maza, tāpēc tās puse izskatās neasa. Pieejiet tuvāk vai izmantojiet 2x tuvinājumu, lai salīdzinājums būtu asāks.',
    },
  },

  // the style picker (src/try/picker.ts)
  picker: {
    groups: { one: 'Tikai jūs', two: 'Jūs abi', family: 'Ģimene' },
    groupIntro: {
      one: 'Viena varavīksnene, viena pati uz melna fona vai savā visumā.',
      two: 'Partnerim: divas varavīksnenes, kas satiekas.',
      family: 'Ģimenei: katra varavīksnene saglabā savu krāsu.',
    },
    groupSoon: 'Bezmaksas priekšskatījums pieejams jau tagad. Šai grupai pasūtījumus pieņemsim drīz.',
    countSoon: (n: number) => `Pasūtījumus ${acisDat(n)} pieņemsim drīz.`,
    soonBuy: 'Šis stils būs pieejams drīzumā. Izvēlieties citu, lai pasūtītu tagad.',
    retakeBuy: (total: number): string => (total === 1
      ? 'Ar šo fotogrāfiju pagaidām neko nevar pasūtīt. Lai pasūtītu, nofotografējiet aci vēlreiz.'
      : 'Ar šīm fotogrāfijām pagaidām neko nevar pasūtīt. Lai pasūtītu, nofotografējiet vēlreiz zemāk norādītās acis.'),
    soonNote: 'Šis stils būs pieejams drīzumā.',
    soonLookBuy: (look: string) => `Variants ${look} būs pieejams drīzumā. Izvēlieties citu variantu vai stilu, lai pasūtītu tagad.`,
    soonLookNote: (look: string) => `Variants ${look} būs pieejams drīzumā.`,
    listLabel: 'Stili jūsu acīm',
    soon: 'Drīzumā',
    recommended: 'Ieteicams',
    reasons: {
      'reason.solo_powder.own': 'Jūsu pašu krāsas, pārvērstas pulverī',
      'reason.solo_gold.dark_brown': 'Zelts liek tumši brūnām acīm mirdzēt',
      'reason.solo_radiance.grey': 'Sudrabaina gaisma pelēkām acīm',
      'reason.duo_collision_infinity.own': 'Divas varavīksnenes, viena bezgalība',
      'reason.duo_kiss_collision.own': 'Divas pasaules, viens uzliesmojums',
      'reason.duo_kiss_collision.dark_brown': 'Divas pasaules, viens uzliesmojums',
      'reason.duo_kiss_collision.grey': 'Divas pasaules, viens uzliesmojums',
      'reason.grp_collision.own': 'Katrs savā krāsā',
      'reason.grp_collision.dark_brown': 'Katrs savā krāsā',
      'reason.grp_collision.grey': 'Katrs savā krāsā',
    },
    lines: {
      'line.solo_clean': 'Jūsu atjaunotā varavīksnene viena pati uz tīri melna fona.',
      'line.solo_powder': 'Mala sabirst graudiņos jūsu acs krāsās.',
      'line.solo_universe': 'Jūsu asā varavīksnene tās pašas varavīksnenes priekšā, palielinātas un maigi izplūdušas.',
      'line.solo_splash': 'Mala paceļas šķidruma kronī.',
      'line.solo_gold': 'Smalks zelta gredzens un oreols ap varavīksneni.',
      'line.solo_radiance': 'Smalki gaismas stari jūsu pašu varavīksnenes krāsās.',
      'line.solo_supernova': 'Zvaigžņu putekļi izšaujas no malas jūsu acs krāsās.',
      'line.solo_nebula': 'Jūsu varavīksnene mirdz miglāja sirdī.',
      'line.solo_sparks': 'Dzirksteles ceļas no malas jūsu acs krāsās.',
      'line.solo_halo': 'Jūsu varavīksnene, no aizmugures izgaismota tās pašas krāsā.',
      'line.solo_aurora': 'Ziemeļblāzmas aizkari ap jūsu varavīksneni.',
      'line.solo_echo': 'Jūsu varavīksnene pašas atbalsī, šķiedras stiepjas kā tunelis.',
      'line.solo_galaxy': 'Zvaigžņu spirāles zari vijas ārā no jūsu varavīksnenes tās pašas krāsās.',
      'line.duo_galaxy': 'Divas varavīksnenes vienas spirālveida galaktikas sirdī, katrs zars savās krāsās.',
      'line.grp_galaxy': 'Viena galaktika visai ģimenei, pa vienam zaram katra cilvēka krāsās.',
      'line.grp_powder': 'Katra varavīksnene pārtop putekļos savās krāsās, un vidū tie sajaucas.',
    },
    tileAlt: (name: string) => `${name} ar jūsu acīm: samazināts priekšskatījums ar ūdenszīmi`,
    tileMaking: (name: string) => `${name}: priekšskatījums tiek veidots`,
    tileFailed: 'Priekšskatījums nav izveidots',
    changed: {
      eyes: (from: string, to: string, n: number) => `${from} nav pieejams ${acisDat(n)}, tāpēc izvēlējāmies ${to}.`,
      gate: (from: string, to: string, i: number) => `Stilam ${from} vajag tīrāku varavīksneni, tāpēc pagaidām izvēlējāmies ${to}. Nofotografējiet ${i}. aci vēlreiz, lai izmantotu ${from}.`,
      reseal: (from: string, to: string, i: number) => `Lai izmantotu ${from}, izveidojiet ${i}. acs priekšskatījumu vēlreiz. Pagaidām izvēlējāmies ${to}.`,
      pupil: (from: string, to: string) => `${from} nav piemērots šādai zīlītes formai, tāpēc izvēlējāmies ${to}.`,
    },
    chipRetake: 'Vēlreiz',
    chipLabel: (i: number) => `${i}. acs: jāfotografē vēlreiz`,
    advisory: (list: number[], total: number) => (total === 1
      ? 'Jūsu varavīksnenes gredzenā joprojām ir plakstiņš vai skropsta. Nofotografējiet vēlreiz, lai rezultāts būtu tīrāks.'
      : `${ordList(list)} acs: gredzenā joprojām ir plakstiņš vai skropsta. Nofotografējiet vēlreiz, lai rezultāts būtu tīrāks.`),
    retake: {
      calm: 'Lai parādītu stilus, mums vajag vēl vienu fotogrāfiju.',
      manual: 'Joprojām neizdodas? Atsūtiet savas labākās fotogrāfijas uz {link}, un mēs tās apskatīsim.',
      noStyles: 'Šādam acu skaitam pagaidām nevaram parādīt nevienu stilu. Noņemiet vienu aci vai rakstiet mums.',
    },
    stack: 'Jūsu abas varavīksnenes krāsā stipri atšķiras, tāpēc viena ir otrai priekšā.',
    widePupil: 'Jūsu zīlītes ir platas, tāpēc varavīksnenes saskaras, nevis pārklājas.',
    options: {
      swap: 'Samainīt vietām',
      rotate: 'Mainīt vietas pa apli',
      earlier: 'Pārvietot uz priekšu',
      later: 'Pārvietot atpakaļ',
      earlierLabel: (i: number) => `Pārvietot ${i}. aci mākslas darbā uz priekšu`,
      laterLabel: (i: number) => `Pārvietot ${i}. aci mākslas darbā atpakaļ`,
      centre: 'Likt centrā',
      centreLabel: (i: number) => `Likt ${i}. aci mākslas darba centrā`,
      centreNote: 'Pirmā acs ir centrā, pārējās izvietotas ap to. Izvēlieties aci augstāk un lieciet to centrā.',
      look: 'Variants',
    },
    names: {
      // the one quiet button that opens the words on the artwork (closed until pressed, open while a word is typed)
      open: '+ Pievienot vārdu vai datumu',
      title: 'Vārdi mākslas darbā (nav obligāti)',
      nameFor: (i: number, total: number) => (total === 1 ? 'Vārds (nav obligāti)' : `Vārds ${i}. acij`),
      date: 'Datums (nav obligāti)',
      datePlaceholder: 'Piemēram, 14.06.2026.',
      family: 'Ģimenes uzvārds (nav obligāti)',
      problem: {
        nameLong: (i: number, max: number) => `Vārds ${i}. acij ir pārāk garš: ne vairāk kā ${burti(max)}.`,
        namesLong: (max: number) => `Vārdi kopā ir pārāk gari: ne vairāk kā ${burti(max)}.`,
        glyph: (chars: string) => `Mākslas darba fonts nevar attēlot ${chars}. Izmantojiet citu burtu.`,
        dateLong: (max: number) => `Datums ir pārāk garš: ne vairāk kā ${zimes(max)}.`,
        familyLong: (max: number) => `Ģimenes uzvārds ir pārāk garš: ne vairāk kā ${burti(max)}.`,
      },
    },
  },

  price: {
    title: 'Šī mākslas darba cena',
    eyes: (n: number, style: string) => `${acis(n)} · ${style}`,
    black: (name: string, black: string, art: string) => `1 acs: ${black} stilam ${name}, ${art} jebkuram citam stilam.`,
    duoOffer: (two: string) => `Pievienojiet otru aci: ${two} par abām.`,
    extra: (two: string, further: string, max: number) => `Divas acis ${two}, pēc tam +${further} par katru nākamo aci, līdz ${acisDat(max)}.`,
    // the landing's pricing.notice (src/landing/copy/lv.json), then the same second half as in English
    notice: 'Pasūtījumus sāksim pieņemt drīz - šodien jūsu priekšskatījums ir bez maksas.',
    footnote: 'Jūs saņemtu vienu digitālu failu bez ūdenszīmes, 4096 px garākajā malā. Cenas ir eiro.',
    footnoteAud: 'Jūs saņemtu vienu digitālu failu bez ūdenszīmes, 4096 px garākajā malā. Cenas ir Austrālijas dolāros (A$).',
    footnoteHuf: 'Jūs saņemtu vienu digitālu failu bez ūdenszīmes, 4096 px garākajā malā. Cenas ir Ungārijas forintos (Ft).',
    footnoteUsd: 'Jūs saņemtu vienu digitālu failu bez ūdenszīmes, 4096 px garākajā malā. Cenas ir ASV dolāros (US$).',
    demo: 'Šī ir demonstrācija ar mākslīgā intelekta radītu parauga aci. Izmēģiniet ar savu aci, lai redzētu savu cenu.',
    sampleNotCounted: (k: number) => (k === 1
      ? 'Mākslīgā intelekta radītā parauga acs nav pasūtījuma daļa, tāpēc to neskaitām.'
      : `Mākslīgā intelekta radītās parauga acis (${k}) nav pasūtījuma daļa, tāpēc tās neskaitām.`),
  },

  // ordering from the result screen. The waiver and the links under it are src/shared/legal.ts CHECKOUT_LEGAL.lv, word
  // for word the text the server records (api/_lib/pay.py CONSENT_TEXT["lv"]).
  buy: {
    // the label alone (see the header); the price stays in the card's head
    button: (_price: string) => CHECKOUT_LEGAL.lv.continueButton,
    waitPreview: 'Priekšskatījums šai izvēlei vēl tiek veidots. Pasūtīt varēsiet, tiklīdz to redzēsiet.',
    previewFailed: 'Vispirms ielādējiet priekšskatījumu šai izvēlei (augstāk: „Mēģināt vēlreiz”), lai redzat, ko pasūtāt.',
    steps: {
      sync: 'Pārbaudām jūsu pasūtījumu…',
      upload: (i: number, n: number) => (n > 1 ? `Augšupielādējam ${i}. aci no ${n}…` : 'Augšupielādējam jūsu aci…'),
      arrange: 'Izkārtojam jūsu acis…',
      checkout: 'Atveram drošo maksājuma lapu…',
    },
    // the card shows its own replace button(s) right under this line, so the line names none
    sample: (k: number): string => (k === 1
      ? 'Mākslīgā intelekta radīto parauga aci nevar pasūtīt. Aizstājiet to ar savu aci, lai pasūtītu šo mākslas darbu.'
      : 'Mākslīgā intelekta radītās parauga acis nevar pasūtīt. Aizstājiet tās ar savām acīm, lai pasūtītu šo mākslas darbu.'),
    replaceSampleEye: (i: number) => `Aizstāt ${i}. aci ar savu`,
    // api/order.py draft: an eye is accepted with its photo's work ticket (15 minutes) or its sealed preview (api/_lib/preview.py SEAL_TTL, 48 hours)
    stale: (list: number[], total: number) => (total === 1
      ? 'Jūsu fotogrāfija uzņemta pirms vairāk nekā 2 dienām. Fotogrāfiju var pasūtīt 2 dienu laikā pēc uzņemšanas, tāpēc, lai pasūtītu, nofotografējiet vēlreiz.'
      : `${list.length === 1 ? `${list[0]}. acs fotografēta` : `${ordList(list)} acs fotografētas`} pirms vairāk nekā 2 dienām. Fotogrāfiju var pasūtīt 2 dienu laikā pēc uzņemšanas, tāpēc, lai pasūtītu, nofotografējiet ${list.length === 1 ? 'to' : 'tās'} vēlreiz.${list.length < total ? ' Pārējās jūsu acis paliek, kādas ir.' : ''}`),
    cancelled: 'Maksājums atcelts. Nekas nav iekasēts. Jūsu mākslas darbs joprojām ir šeit: varat to mainīt vai pasūtīt vēlreiz.',
    cancelledLost: 'Maksājums atcelts. Nekas nav iekasēts. Šī lapa nevarēja saglabāt jūsu priekšskatījumu, tāpēc nofotografējiet vēlreiz.',
    close: 'Aizvērt',
    errors: {
      network: 'Neizdevās sasniegt SnapEyes. Pārbaudiet interneta savienojumu un mēģiniet vēlreiz.',
      busy: 'Maksājumu pakalpojums neatbildēja. Mēģiniet vēlreiz pēc brīža.',
      payments: `Neizdevās atvērt maksājuma lapu. Mēģiniet vēlreiz vēlāk vai rakstiet uz ${CONTACT_EMAIL}.`,
      too_large: 'Vienas jūsu acs fotogrāfija ir pārāk liela augšupielādei. Nofotografējiet šo aci vēlreiz.',
      // api/order.py draft: 503 uploads_paused and 429 too_many_uploads, both until the next day (UTC)
      paused: `Jauni pasūtījumi šodien ir apturēti: sasniegts dienas augšupielāžu limits. Nekas nav iekasēts. Mēģiniet vēlreiz rīt vai rakstiet uz ${CONTACT_EMAIL}.`,
      too_many: `Šis pasūtījums šodien ir sasniedzis augšupielāžu limitu (30 augšupielādes, ieskaitot atkārtotu fotografēšanu). Nekas nav iekasēts. Mēģiniet vēlreiz rīt vai rakstiet uz ${CONTACT_EMAIL}.`,
      failed: `Sagatavojot jūsu pasūtījumu, kaut kas nogāja greizi. Mēģiniet vēlreiz vai rakstiet uz ${CONTACT_EMAIL}.`,
      closed: 'Pasūtījumus vēl nepieņemam.',
      plan_changed: 'Jūsu mākslas darbs tikko mainījās, tāpēc izveidojām priekšskatījumu vēlreiz. Apskatiet to un pēc tam nospiediet pogu vēlreiz.',
      unavailable: 'Šo stilu jūsu acīm pašlaik nevar pasūtīt. Izvēlieties citu vai nofotografējiet aci vēlreiz.',
      print_unavailable: 'Izdrukas pašlaik nevar pasūtīt. Varat pasūtīt tikai digitālo failu.',
      print_changed: 'Izdrukas cena tikko mainījās. Apskatiet to vēlreiz un pēc tam nospiediet pogu.',
      voucher: 'Jūsu dāvanu karti neizdevās izmantot: iespējams, tā jau ir izmantota vai tai beidzies derīguma termiņš. Pārbaudiet to vēlreiz.',
    },
    namesBlocked: 'Vispirms izlabojiet vārdus mākslas darbā (skatiet augstāk).',
    footnote: 'Digitāls fails, 4096 px, bez ūdenszīmes.',
  },

  gift: {
    open: 'Man ir dāvanu karte',
    label: 'Dāvanu kartes kods',
    apply: 'Izmantot',
    checking: 'Pārbaudām kodu',
    applied: (value: string) => `Dāvanu karte: −${value}`,
    remove: 'Noņemt',
    toPay: (value: string) => `Jāmaksā: ${value}`,
    note: 'Karte tiek izmantota, kad pabeidzat maksājumu. Atlikums paliek kartē.',
    errors: {
      format: 'Tas nav kartes kods. Kodā ir 12 burti un cipari, piemēram, ABCD-EFGH-JKLM.',
      unknown: 'Šādu kodu nezinām. Pārbaudiet to.',
      used: 'Šī karte jau ir izmantota.',
      expired: 'Šīs kartes derīguma termiņš ir beidzies.',
      currency: 'Šo karti var izmantot tikai pasūtījumiem eiro.',
      failed: 'Pašlaik nevaram pārbaudīt kodu. Mēģiniet vēlreiz.',
    },
  },

  // the anonymous feedback box (src/try/Feedback.tsx, api/_lib/feedback.py)
  feedback: {
    title: { result: 'Kā jums tas izskatās?', retake: 'Vai tas palīdzēja?' },
    hint: { result: 'Viens pieskāriens un, ja vēlaties, daži vārdi. Tas nonāk pie cilvēka, kurš šos darbus veido.', retake: 'Ar vienu pieskārienu pasakiet, kas jums traucēja.' },
    chips: {
      result: { love: 'Man ļoti patīk', likeness: 'Neizskatās pēc manas acs', colour: 'Krāsas nešķiet pareizas', style: 'Es gribēju citu stilu', price: 'Cena ir pārāk augsta', other: 'Kaut kas cits' },
      retake: { unclear: 'Nesaprotu, kas nav kārtībā', fine: 'Manuprāt, mana fotogrāfija ir laba', device: 'Mans telefons labāk nevar', only: 'Tā ir mana vienīgā fotogrāfija', effort: 'Tas prasa pārāk daudz pūļu', other: 'Kaut kas cits' },
    },
    textLabel: 'Vai vēlaties ko piebilst? (nav obligāti)',
    textHint: 'Lūdzu, nerakstiet vārdus, e-pasta adreses un tālruņa numurus.',
    count: (n: number, max: number) => `${n} no ${max}`,
    send: 'Nosūtīt',
    sending: 'Sūtām',
    thanks: 'Paldies. Tas nonāca pie cilvēka, kurš šos darbus veido.',
    textDropped: 'Paldies. Jūsu atbildi ieskaitījām, bet tekstu nesaglabājām, jo šķita, ka tajā ir kontaktinformācija vai saite.',
    textLost: 'Paldies. Jūsu atbilde mūs sasniedza, bet tekstu neizdevās saglabāt.',
    failed: 'Nosūtīt neizdevās. Mēģiniet vēlreiz pēc brīža.',
    privacy: 'Anonīmi: bez vārda, bez e-pasta. Teksts tiek dzēsts pēc 90 dienām.',
  },

  study: {
    title: (shot: number, photos: number) => (photos > 1 ? `Ģimenes tests · fotogrāfijas ${shot - photos + 1}-${shot}` : `Ģimenes tests · ${shot}. kadrs`),
    light: 'Gaisma šim kadram',
    lights: {
      window_daylight: 'Dienasgaisma no loga', room_lamp: 'Istabas lampa', phone_torch: 'Telefona lukturītis', someone_helped: 'Kāds palīdzēja',
    } satisfies Record<LightAnswer, string>,
    comfort: 'Cik viegli tas bija? 1 grūti, 5 viegli',
    skip: 'Izlaist',
    // the engine logs the answers only with an analyze request, so they wait for the next photo
    thanks: 'Paldies. Šīs atbildes tiks nosūtītas kopā ar jūsu nākamo fotogrāfiju.',
    pending: (shots: number[]) => `Ģimenes tests: jūsu atbildes par ${shots.length === 1 ? `${shots[0]}. kadru` : `kadriem ${shots.join(', ')}`} vēl nav nosūtītas. Tās tiks nosūtītas kopā ar jūsu nākamo fotogrāfiju, piemēram, kad pievienosiet vēl vienu aci. Ja aizvērsiet lapu tagad, tās pazudīs.`,
  },
};
