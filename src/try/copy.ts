// Every string /try shows, in English and German (formal "Sie", the landing page's words: src/landing/copy.ts),
// in one place. T is the copy of the page's current language: TryApp sets it with setCopyLang() before it
// renders, and again when the visitor switches, so every component and helper reads T at render time.
// The server's own sentences (quality.message, tips, errors) come in the language the request asked for
// (the "lang" field every request carries).
import type { Layout, LightAnswer } from './multi';
import type { Lang } from './lang';
import { CONTACT_EMAIL } from '../landing/config';
import { CHECKOUT_LEGAL } from '../shared/legal';

/** The reasons api/analyze.py gives for blocking a shot (quality.block_reason). A blocked shot gets no work
 *  ticket, so the page offers only a retake. */
export type BlockReason = 'too_blurry' | 'too_dark' | 'pupil_too_large' | 'too_small';

/** What the page says about a blocked shot. badge: the verdict pill; title: the retake card's heading; reason:
 *  why, in one line, on the single-photo card (the steps follow in the retake card, so the server's own message,
 *  which lists them too, is not shown next to them); error: when the studio is asked for it anyway; retakeLine:
 *  one self-contained line for a shot collector whose best shot is still usable (no retake card there), used
 *  only when the server sends no message; thumb: under its thumbnail instead of a Detail number; steps: the
 *  retake card's list. */
export interface BlockCopy { badge: string; title: string; reason: string; error: string; retakeLine: string; thumb: string; steps: string[] }

// ---------------------------------------------------------------------------------------------------- English

const eyes = (n: number) => `${n} ${n === 1 ? 'eye' : 'eyes'}`;
// "1", "1 and 3", "1, 2 and 4"
const andList = (xs: number[], and: string) => (xs.length < 2 ? String(xs[0] ?? '') : `${xs.slice(0, -1).join(', ')} ${and} ${xs[xs.length - 1]}`);

// The capture guide's steps, word for word the same on the capture screen and in the retake guide of a shot the
// engine blocked, so "Retake" never leads to advice that contradicts the screen it came from. Daylight from the
// side: straight-on light washes over the iris (04 in the test set), and a lamp tints it (api/analyze.py
// LAMP_MESSAGE).
const LIGHT = 'Daylight from a window, off to one side (not straight in front). Not a lamp or the flash.';
const CAMERA = 'Back camera at 2x zoom, about 10 cm from the eye.';
const FOCUS = 'Tap the iris on the screen so the camera focuses on it.';
const STEADY = 'Hold the phone steady (rest your elbows on something) and take 3-5 shots.';
// the first retake step for a dark iris: the same light as LIGHT, only closer to the window, since more light is
// what brings a dark iris's pattern out (api/analyze.py DARK_IRIS_TIP)
const DARK_LIGHT = 'More light brings out a dark iris: stand close to a bright window in daylight, with the window off to one side (not direct sun). Not a lamp or the flash.';

const en = {
  lang: 'en' as Lang,
  meta: {
    title: 'SnapEyes Studio - Turn your eye photo into iris art',
    description: 'Take a photo of your eye with your phone and see your own iris restored and turned into cosmic art in about a minute.',
  },
  switchLabel: 'Language',
  /** One decimal, as this language writes it (3.7 / 3,7). */
  dec1: (v: number) => v.toFixed(1),

  header: {
    tag: 'Private Atelier · preview',
    study: 'Family test',
  },

  errors: {
    tooLarge: 'That photo is too large. Try again with a normal camera photo.',
    timeout: 'That took too long on our side. Please try again.',
    notResponding: 'The studio is not responding right now. Please try again in a moment.',
    requestFailed: (status: number) => `Request failed (${status})`,
    unreadable: 'Could not read this image',
    noEyeAny: 'We could not find an eye in any of those photos.',
    noEyeShot: 'We could not find an eye in that shot.',
    noEye: 'No eye found',
    keepFailed: 'Something went wrong keeping your shots. Please take the photo again.',
  },

  capture: {
    // the first screen's heading: the second part is set in gold
    titleA: 'YOUR EYE, ',
    titleB: 'FOR REAL.',
    lead: 'Photograph one eye. We find the iris, remove reflections, restore the fibres and set it in art. About a minute.',
    addTitle: (n: number) => `Add eye ${n}`,
    addLead: 'Your partner, your child, or your other eye. Same steps as before: take a few shots and we keep the best one.',
    // a couple with one phone: the back camera cannot be aimed at your own eye while you watch the screen
    takeTurns: 'Photographing each other? Take turns: one holds the phone, the other looks straight ahead. Then swap.',
    helper: 'Easiest in pairs: one holds the phone, the other looks straight ahead.',
    retakeTitle: (n: number) => `Retake eye ${n}`,
    retakeLead: 'Same steps as before. Your new shot replaces this eye on the artwork; until then it stays as it is.',
    back: (n: number) => `Back to your artwork (${eyes(n)})`,
    sampleLink: 'or try with an AI-generated sample eye',
    sampleButton: 'AI-generated sample eye',
    sampleLoadFailed: 'The sample eye could not be loaded.',
    thumbLabel: (i: number) => `Eye ${i}`,
    sampleThumb: 'AI-generated sample',
    // the capture guide on the first screen. Step 3 is the retake guide's first step, word for word (LIGHT).
    steps: [
      { title: '1. Back camera', text: '2x or 3x zoom, not the selfie camera.' },
      { title: '2. 10 cm away', text: 'The iris should fill a third of the frame.' },
      { title: '3. Window light', text: LIGHT },
      { title: '4. Tap to focus', text: 'Tap the iris on screen, hold still, shoot.' },
    ],
    // lashes that hang over the iris cannot be removed by the engine (they come out as dark streaks), so the guide
    // asks for an open eye before the first shot
    stepsOpen: 'Eye wide open. ',
    stepsOpenMore: 'Look straight ahead and lift the upper lid gently with a fingertip, so no lid or lashes cross the iris.',
    stepsShots: 'Take 3-5 shots and send them all.',
    stepsShotsMore: ' Turn a little between shots. We measure every one and use the sharpest; on a real test the best shot had 3.7x the detail of the worst.',
    takePhoto: 'Take a photo',
    pickShots: 'Pick 3-5 shots',
    liveCamera: 'Live camera + zoom',
    consent: "Save my eye photo and result to SnapEyes' training memory so restorations get better over time. Anonymous, no name or face. You can ask us to delete it any time.",
  },

  working: {
    finding: 'Finding your iris…',
    locating: 'Locating the iris and pupil',
    measuringSize: 'Measuring size and sharpness',
    checking: (n: number, done: number) => `Checking ${n} photos: ${done} of ${n} done`,
    measuringShot: (k: number, max: number) => `Measuring shot ${k} of ${max}`,
    restoring: 'Restoring your iris…',
    restoringEye: (n: number) => `Restoring eye ${n}…`,
    cut: 'Cutting out your iris',
    reflections: 'Removing reflections',
    macro: 'Studio macro restoration (about 30 s)',
    composing: (n: number) => (n > 1 ? `Composing your artwork with ${n} eyes` : 'Composing your artwork'),
    sampleCaption: 'AI-generated sample',
    yourIris: 'Your iris',
    elapsed: (s: number) => `${s}s`,
  },

  quality: {
    retake: 'Retake',
    continueAnyway: 'Continue anyway',
    notCentred: 'This photo is not centred on an iris, so it cannot be restored. Please retake it with one eye filling the frame.',
    // shots the engine blocked (api/analyze.py quality.blocked + block_reason): no work ticket, so never a way
    // forward from them. One entry per reason the server gives; blockOf() in shots.ts picks it.
    blocks: {
      // blur_blocked: too little of the customer's own iris pattern to restore it, the studio would invent one
      too_blurry: {
        badge: 'Too blurry',
        title: 'Too blurry to restore your own iris',
        reason: 'We could not see enough of your own iris pattern in this photo to restore it, so it is not used.',
        error: 'This photo is too blurry to restore your own iris. Please retake it following the steps below.',
        retakeLine: 'This shot is too blurry to restore your own iris. Retake it in daylight from a window off to one side, with the back camera at 2x: tap the iris to focus and hold the phone steady.',
        thumb: 'blurry',
        steps: [LIGHT, CAMERA, FOCUS, STEADY],
      },
      // blocked for the same reason, but the photo is sharp and the iris dark: light is the fix, not focus
      too_dark: {
        badge: 'Too dark',
        title: 'Too dark to see your own iris pattern',
        reason: 'Your iris is dark and there was too little light to see its own pattern, so this photo is not used.',
        error: 'This photo is too dark to see your own iris pattern. Please retake it following the steps below.',
        retakeLine: 'This shot is too dark to see your own iris pattern. Retake it close to a bright window in daylight, with the window off to one side. Not a lamp or the flash.',
        thumb: 'dark',
        steps: [DARK_LIGHT, CAMERA, FOCUS, STEADY],
      },
      // a pupil so wide that too little iris shows around it. Light is the fix: the pupil narrows in bright
      // light, while the flash comes too late to narrow it and puts a reflection on the iris
      pupil_too_large: {
        badge: 'Pupil too wide',
        title: 'Your pupil is too wide to restore your iris',
        reason: 'Your pupil is open so wide in this photo that too little of your iris shows around it, so it is not used.',
        error: 'Your pupil is too wide in this photo to restore your own iris. Please retake it following the steps below.',
        retakeLine: 'Your pupil is too wide in this shot. More light makes it smaller: retake it close to a bright window in daylight, not with the flash.',
        thumb: 'pupil',
        steps: [
          'More light makes your pupil smaller: stand close to a bright window in daylight, with the window off to one side (not direct sun). Not the flash.',
          'Give your eye a minute in that light before you shoot, so the pupil has time to narrow. After dark, switch on all the ceiling lights.',
          CAMERA,
          'Tap the iris on the screen to focus, hold the phone steady and take 3-5 shots.',
        ],
      },
      // an iris too small in the photo (BLOCK_DIAMETER_PX): the model would draw a pattern the photo does not have
      too_small: {
        badge: 'Too small',
        title: 'Your iris is too small in this photo',
        reason: 'Your iris is so small in this photo that too little of its own pattern shows, so it is not used.',
        error: 'Your iris is too small in this photo to restore it. Please retake it closer, following the steps below.',
        retakeLine: 'Your iris is too small in this shot. Come closer: back camera at 2x, about 10 cm from your eye, so the iris fills about a third of the frame.',
        thumb: 'small',
        steps: [
          'Come closer: back camera at 2x zoom, about 10 cm from the eye, so the iris fills about a third of the frame.',
          LIGHT,
          FOCUS,
          STEADY,
        ],
      },
    } satisfies Record<BlockReason, BlockCopy>,
    // a reason this page does not know yet (a newer server, or none sent): still never a way forward, and still
    // the guide. Neutral on purpose: it must not claim a cause (blur, darkness) the server did not name
    blockedOther: {
      badge: 'Not enough detail',
      title: 'Not enough detail to restore your own iris',
      reason: 'We could not see enough of your own iris pattern in this photo to restore it, so it is not used.',
      error: 'This photo does not show enough of your own iris to restore it. Please retake it following the steps below.',
      retakeLine: 'This shot does not show enough of your own iris to restore it. Take another following the capture guide.',
      thumb: 'retake',
      steps: [LIGHT, CAMERA, FOCUS, STEADY],
    } satisfies BlockCopy,
    guideTitle: 'For the retake',
    // a gallery pick where the best photo is still one we cannot use
    noneUsable: (n: number) => (n === 2 ? 'We checked both photos and neither can be used.' : `We checked all ${n} photos and none of them can be used.`),
    // the camera shot collector when its best shot cannot be used
    shotUnusable: 'This shot cannot be used. Take another with the advice above.',
    shotsUnusable: 'None of these shots can be used yet. Take another with the advice above.',
    fullUnusable: (max: number) => `None of these ${max} shots can be used. Take another to start a fresh set.`,
    verdicts: { good: 'Great photo', ok: 'Usable photo', weak: 'Weak photo' },
    detectedIris: 'Detected iris',
    detail: 'Detail',
    aimFor: (d: number) => `Aim for ${d}+`,
    fibresResolved: 'Fibres resolved',
    // "best", not "sharpest": the verdict ranks first, so a glared photo can be sharper and still lose
    picked: (of: number, used: number) => `We compared ${of} photos and used the best one (photo ${used}).`,
    pickedRatio: (ratio: string) => ` It carries ${ratio}x the fibre detail of the softest.`,
    tryRetake: 'Try a retake',
    pupilNote: 'A reflection on the pupil is fine: we rebuild the pupil as clean darkness.',
    lampFallback: 'Lamp light is tinting the white of your eye, so the colours may come out warmer than they really are.',
    // topTip() when the iris is too small and the server sent no tip of its own for it
    closer: 'Move closer or zoom in so the iris fills more of the frame.',
  },

  // the camera shot collector
  collector: {
    header: (n: number, max: number) => `Shot ${n} of ${max}`,
    headerDetail: (d: number) => ` · Detail ${d}`,
    shotAlt: (n: number) => `Shot ${n}`,
    bestLabel: (k: number, d?: number) => `shot ${k}${d !== undefined ? ` (Detail ${d})` : ''}`,
    full: (max: number, best: string) => `That is ${max} shots. We will use your best one, ${best}.`,
    more: (left: number) => `Take up to ${left} more. We measure every shot and keep the best one.`,
    sharpEnough: 'This one is sharp enough to use.',
    bestSoFar: 'This is your best shot so far.',
    lampSkipped: (n: number, best: string) => `Lamp light tinted shot ${n}, so we will use ${best}, your best shot in true colour.`,
    bestIs: (best: string) => `Your best so far is ${best}. That is the one we will use.`,
    lastFailed: (note: string) => `That last shot could not be used: ${note} Your best shot so far is kept.`,
    takeAnother: 'Take another',
    useBest: 'Use best shot',
    useThis: 'Use this shot',
    startOver: 'Start over',
  },

  live: {
    guide: 'iris fills this circle · 12-15 cm · 2x',
    sharp: 'Sharp ✓',
    holdStill: 'Hold still / tap to focus',
    close: 'Close',
    zoom: (v: string) => `Zoom ${v}x`,
    noZoom: 'This browser does not expose camera zoom. Use "Take a photo" and pinch to 2x in your camera app instead.',
    lowRes: 'This browser can only grab a low-resolution frame here. For a sharp result use "Take a photo" instead, which opens the real camera.',
    capture: 'Capture',
    unavailable: 'Camera not available',
  },

  result: {
    beforeAfter: 'Before / after',
    eyes: 'Eyes on this artwork',
    eyeLabel: (i: number) => `Eye ${i}`,
    sampleLabel: 'AI-generated sample',
    yourPhoto: 'Your photo',
    samplePhoto: 'AI-generated sample',
    after: 'Studio macro',
    // CompareSlider's own labels, when a caller passes none
    sliderBefore: 'Your photo',
    sliderAfter: 'Restored',
    // owner decision 5, word for word. Shown for a real eye only: the sample has no photo of its own.
    transparency: 'Colour from your own photo. Where your phone could not capture the finest fibres, our AI restores them.',
    sampleNote: 'This eye is the AI-generated sample, not a real photo. With your own photo, the colour comes from your photo.',
    // the engine's colour check (api/enhance qa) failed for this eye: say so next to the promise above
    colourOff: 'Our colour check says this restoration drifted from your photo: it may look lighter or darker than your eye. A retake in soft daylight usually fixes it.',
    retakeEye: (i: number) => `Retake eye ${i}`,
    retakeOnly: 'Retake this eye',
    replaceSample: 'Use your own eye instead',
    removed: (i: number) => `Eye ${i} removed.`,
    undo: 'Undo',
    sampleArtwork: 'Sample artwork',
    sampleBadge: 'AI-generated sample',
    // baked into the preview image itself (the engine's caption title, at most 40 characters), so a saved
    // sample preview carries its label wherever it goes
    sampleTitle: 'AI-generated sample',
    sampleArtworkNote: 'Made only from the AI-generated sample eye, not from a real photo.',
    mixedArtworkNote: 'This artwork contains the AI-generated sample eye, which is not a real photo.',
    drag: 'Drag the handle.',
    irisPx: (px: number) => `Iris in your photo: ${px}px.`,
    reflection: 'Reflection removed.',
    upscaled: 'Small photo: upscaled before restoration.',
    badgeMacro: 'Studio macro',
    badgeFallback: 'Faithful upscale only',
    artwork: 'Your artwork',
    composing: 'Composing…',
    composeFailed: 'We could not compose this preview.',
    retry: 'Try again',
    layout: 'Layout',
    layouts: {
      single: 'Single', duo: 'Side by side', fusion: 'Fusion', triangle: 'Triangle', row: 'In a row', grid: 'Grid', galaxy: 'Galaxy',
    } satisfies Record<Layout, string>,
    style: 'Style',
    namesPlaceholder: 'Names or inscription (optional)',
    save: 'Save preview',
    // the saved preview's file name; a sample preview says so in its name too
    fileName: (style: string, n: number, sample: boolean) => `snapeyes-preview-${style}-${n}-${n === 1 ? 'eye' : 'eyes'}${sample ? '-ai-generated-sample' : ''}.jpg`,
    addSecond: 'Add a second eye',
    addAnother: 'Add another eye',
    addHint: (left: number) => `Partner, child, or your other eye. Room for ${left} more ${left === 1 ? 'eye' : 'eyes'} on this artwork.`,
    full: (max: number) => `That is ${max} eyes, the most one artwork holds.`,
    remove: (i: number) => `Remove eye ${i}`,
    startOver: 'Start over',
    confirmStartOver: (n: number) => `Discard all ${n} eyes and start over?`,
    stored: 'Saved to training memory',
  },

  price: {
    title: 'Price for this artwork',
    oneEye: (style: string) => `1 eye · ${style}`,
    duo: 'Couple Duo · 2 eyes',
    many: (n: number) => `${n} eyes · Couple Duo + ${n - 2} extra`,
    oneEyeOther: (studioBlack: string, art: string) => `1 eye: ${studioBlack} in Studio Black, ${art} with an art background.`,
    duoOffer: (duo: string) => `Add a second eye for the Couple Duo: ${duo} for both.`,
    extra: (duo: string, extra: string, max: number) => `Couple Duo ${duo}, then +${extra} for each extra eye, up to ${max} eyes.`,
    notice: 'Ordering opens soon - your preview is free today.',
    footnote: 'You would receive one digital file, 4096 px on its longest side, without watermark. Prices in euros.',
    demo: 'This is a demo with the AI-generated sample eye. Try your own eye to see your price.',
    sampleNotCounted: (k: number) => (k === 1
      ? 'The AI-generated sample eye is not part of an order, so it is not counted.'
      : `The ${k} AI-generated sample eyes are not part of an order, so they are not counted.`),
  },

  // ordering from the result screen (./BuyCard.tsx, ./checkout.ts). The withdrawal waiver and the links under it are
  // src/shared/legal.ts CHECKOUT_LEGAL, word for word the text the server records. The button only opens Stripe's
  // payment page: the binding order is Stripe's own pay button (src/legal/docs/terms.ts "contract", § 312j Abs. 3
  // BGB), so it carries CHECKOUT_LEGAL's continueButton, never "buy" or "order"; "next" says the same as the terms
  // (binding on Stripe's pay button; making starts once the order confirmation email has gone out).
  buy: {
    button: (price: string) => `${CHECKOUT_LEGAL.en.continueButton} · ${price}`,
    next: "Next is Stripe's secure payment page. There you enter your email and place your binding order when you confirm the payment with the pay button. We start making your file once your order confirmation email has gone out, normally within a minute of your payment.",
    waitPreview: 'The preview for this choice is still being made. You can order as soon as you see it.',
    previewFailed: 'Please load the preview for this choice first (Try again above), so you see what you order.',
    steps: {
      sync: 'Checking your order…',
      upload: (i: number, n: number) => (n > 1 ? `Uploading eye ${i} of ${n}…` : 'Uploading your eye…'),
      arrange: 'Arranging your eyes…',
      checkout: 'Opening the secure payment page…',
    },
    // the card shows its own replace button(s) right under this line (./BuyCard.tsx), so the line names none
    sample: (k: number): string => (k === 1
      ? 'The AI-generated sample eye cannot be ordered. Replace it with your own eye to order this artwork.'
      : 'The AI-generated sample eyes cannot be ordered. Replace them with your own eyes to order this artwork.'),
    replaceSampleEye: (i: number) => `Replace eye ${i} with your own`,
    // api/_lib/iris.py TICKET_TTL: an eye's draft is accepted only with its photo's 15-minute work ticket
    stale: (list: number[], total: number) => (total === 1
      ? 'Your photo was taken more than 15 minutes ago. A photo can be ordered within 15 minutes of taking it, so please take it again to order.'
      : `${list.length === 1 ? `Eye ${list[0]} was` : `Eyes ${andList(list, 'and')} were`} taken more than 15 minutes ago. A photo can be ordered within 15 minutes of taking it, so please take ${list.length === 1 ? 'it' : 'them'} again to order.${list.length < total ? ' Your other eyes stay as they are.' : ''}`),
    cancelled: 'Payment cancelled. Nothing was charged. Your artwork is still here: you can change it or order again.',
    cancelledLost: 'Payment cancelled. Nothing was charged. This page could not keep your preview, so please take your photo again.',
    close: 'Close',
    errors: {
      network: 'We could not reach SnapEyes. Please check your internet connection and try again.',
      busy: 'The payment service did not answer. Please try again in a moment.',
      payments: `We could not open the payment page. Please try again later, or write to ${CONTACT_EMAIL}.`,
      too_large: 'The photo of one of your eyes is too large to upload. Please take that eye again.',
      // api/order.py draft: 503 uploads_paused (the daily ceiling on unpaid uploads) and 429 too_many_uploads (30 per
      // order and day, retakes included). Both last until the next day (UTC).
      paused: `New orders are paused for today: the daily upload limit has been reached. Nothing was charged. Please try again tomorrow, or write to ${CONTACT_EMAIL}.`,
      too_many: `This order has reached its upload limit for today (30 uploads, retakes included). Nothing was charged. Please try again tomorrow, or write to ${CONTACT_EMAIL}.`,
      failed: `Something went wrong while preparing your order. Please try again, or write to ${CONTACT_EMAIL}.`,
      closed: 'Ordering is not open yet.',
    },
    footnote: 'One digital file (JPEG), 4096 px on its longest side, without watermark. This is the final price: we are not registered for VAT, so no VAT is added.',
  },

  study: {
    title: (shot: number, photos: number) => (photos > 1 ? `Family test · photos ${shot - photos + 1}-${shot}` : `Family test · shot ${shot}`),
    light: 'Light for this shot',
    lights: {
      window_daylight: 'Window daylight', room_lamp: 'Room lamp', phone_torch: 'Phone torch', someone_helped: 'Someone helped',
    } satisfies Record<LightAnswer, string>,
    comfort: 'How easy was it? 1 hard, 5 easy',
    skip: 'Skip',
    // the engine logs the answers only with an analyze request, so they wait for the next photo
    thanks: 'Thank you. These answers are sent with your next photo.',
    pending: (shots: number[]) => `Family test: your answers about ${shots.length === 1 ? `shot ${shots[0]}` : `shots ${shots.join(', ')}`} have not been sent yet. They go with your next photo, for example when you add another eye. If you close the page now, they are lost.`,
  },
};

export type TryCopy = typeof en;

// ---------------------------------------------------------------------------------------------------- German
// Formal "Sie" and the landing page's words (src/landing/copy.ts de): Rückkamera, Selfie-Kamera, 2-facher Zoom,
// Aufnahme (shot), Vorschau, Kunstwerk, restaurieren, Fasern, KI, Kunsthintergrund. Numbers with a decimal comma.

const augen = (n: number) => `${n} ${n === 1 ? 'Auge' : 'Augen'}`;

// the capture guide's steps in German: the same rule as above, word for word on the capture screen and in the
// retake cards
const LIGHT_DE = 'Tageslicht von einem Fenster, seitlich (nicht direkt von vorn). Keine Lampe, kein Blitz.';
const CAMERA_DE = 'Rückkamera mit 2-fachem Zoom, etwa 10 cm vor dem Auge.';
const FOCUS_DE = 'Tippen Sie auf dem Bildschirm auf die Iris, damit die Kamera darauf scharfstellt.';
const STEADY_DE = 'Halten Sie das Smartphone ruhig (stützen Sie die Ellbogen auf) und machen Sie 3-5 Aufnahmen.';
const DARK_LIGHT_DE = 'Mehr Licht bringt eine dunkle Iris zur Geltung: Stellen Sie sich bei Tageslicht nah an ein helles Fenster, das Fenster seitlich (keine direkte Sonne). Keine Lampe, kein Blitz.';
const DE_DECIMAL = new Intl.NumberFormat('de-DE', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

const de: TryCopy = {
  lang: 'de',
  meta: {
    title: 'SnapEyes Studio - Ihr Augenfoto als Iris-Kunst',
    description: 'Fotografieren Sie Ihr Auge mit dem Smartphone und sehen Sie Ihre eigene Iris in etwa einer Minute restauriert und als kosmisches Kunstwerk.',
  },
  switchLabel: 'Sprache',
  dec1: (v: number) => DE_DECIMAL.format(v),

  header: {
    tag: 'Private Atelier · Vorschau',
    study: 'Familientest',
  },

  errors: {
    tooLarge: 'Dieses Foto ist zu groß. Bitte versuchen Sie es mit einem normalen Kamerafoto.',
    timeout: 'Das hat bei uns zu lange gedauert. Bitte versuchen Sie es erneut.',
    notResponding: 'Das Studio antwortet gerade nicht. Bitte versuchen Sie es gleich noch einmal.',
    requestFailed: (status: number) => `Anfrage fehlgeschlagen (${status})`,
    unreadable: 'Dieses Bild konnte nicht gelesen werden',
    noEyeAny: 'Auf keinem dieser Fotos haben wir ein Auge gefunden.',
    noEyeShot: 'Auf dieser Aufnahme haben wir kein Auge gefunden.',
    noEye: 'Kein Auge gefunden',
    keepFailed: 'Beim Speichern Ihrer Aufnahmen ist etwas schiefgelaufen. Bitte machen Sie das Foto erneut.',
  },

  capture: {
    titleA: 'IHR AUGE, ',
    titleB: 'GANZ ECHT.',
    lead: 'Fotografieren Sie ein Auge. Wir finden die Iris, entfernen Spiegelungen, restaurieren die Fasern und setzen sie als Kunstwerk in Szene. Etwa eine Minute.',
    addTitle: (n: number) => `Auge ${n} hinzufügen`,
    addLead: 'Ihr Partner oder Ihre Partnerin, Ihr Kind oder Ihr anderes Auge. Dieselben Schritte wie zuvor: Machen Sie ein paar Aufnahmen, wir behalten die beste.',
    takeTurns: 'Sie fotografieren sich gegenseitig? Wechseln Sie sich ab: Eine Person hält das Smartphone, die andere schaut geradeaus. Dann tauschen Sie.',
    helper: 'Am einfachsten zu zweit: Eine Person hält das Smartphone, die andere schaut geradeaus.',
    retakeTitle: (n: number) => `Auge ${n} neu aufnehmen`,
    retakeLead: 'Dieselben Schritte wie zuvor. Ihre neue Aufnahme ersetzt dieses Auge im Kunstwerk, bis dahin bleibt es, wie es ist.',
    back: (n: number) => `Zurück zu Ihrem Kunstwerk (${augen(n)})`,
    sampleLink: 'oder mit einem KI-generierten Beispielauge ausprobieren',
    sampleButton: 'KI-generiertes Beispielauge',
    sampleLoadFailed: 'Das Beispielauge konnte nicht geladen werden.',
    thumbLabel: (i: number) => `Auge ${i}`,
    sampleThumb: 'KI-generiertes Beispiel',
    steps: [
      { title: '1. Rückkamera', text: '2- oder 3-facher Zoom, nicht die Selfie-Kamera.' },
      { title: '2. 10 cm Abstand', text: 'Die Iris sollte ein Drittel des Bildes füllen.' },
      { title: '3. Fensterlicht', text: LIGHT_DE },
      { title: '4. Scharfstellen', text: 'Tippen Sie auf die Iris, halten Sie still, lösen Sie aus.' },
    ],
    stepsOpen: 'Auge weit geöffnet. ',
    stepsOpenMore: 'Schauen Sie geradeaus und heben Sie das Oberlid sanft mit einer Fingerspitze an, damit weder Lid noch Wimpern über der Iris liegen.',
    stepsShots: 'Machen Sie 3-5 Aufnahmen und senden Sie alle.',
    stepsShotsMore: ' Drehen Sie sich zwischen den Aufnahmen ein wenig. Wir messen jede und verwenden die schärfste; in einem echten Test hatte die beste Aufnahme 3,7-mal so viele Details wie die schlechteste.',
    takePhoto: 'Foto aufnehmen',
    pickShots: '3-5 Fotos wählen',
    liveCamera: 'Live-Kamera + Zoom',
    consent: 'Mein Augenfoto und das Ergebnis im Trainingsspeicher von SnapEyes sichern, damit Restaurierungen mit der Zeit besser werden. Anonym, ohne Namen oder Gesicht. Sie können jederzeit die Löschung verlangen.',
  },

  working: {
    finding: 'Wir suchen Ihre Iris…',
    locating: 'Iris und Pupille werden gesucht',
    measuringSize: 'Größe und Schärfe werden gemessen',
    checking: (n: number, done: number) => `${n} Fotos werden geprüft: ${done} von ${n} fertig`,
    measuringShot: (k: number, max: number) => `Aufnahme ${k} von ${max} wird gemessen`,
    restoring: 'Ihre Iris wird restauriert…',
    restoringEye: (n: number) => `Auge ${n} wird restauriert…`,
    cut: 'Ihre Iris wird freigestellt',
    reflections: 'Spiegelungen werden entfernt',
    macro: 'Studio-Makro-Restaurierung (etwa 30 s)',
    composing: (n: number) => (n > 1 ? `Ihr Kunstwerk mit ${n} Augen wird gestaltet` : 'Ihr Kunstwerk wird gestaltet'),
    sampleCaption: 'KI-generiertes Beispiel',
    yourIris: 'Ihre Iris',
    elapsed: (s: number) => `${s} s`,
  },

  quality: {
    retake: 'Neu aufnehmen',
    continueAnyway: 'Trotzdem fortfahren',
    notCentred: 'Dieses Foto ist nicht auf eine Iris zentriert und kann daher nicht restauriert werden. Bitte nehmen Sie es neu auf, sodass ein Auge das Bild füllt.',
    blocks: {
      too_blurry: {
        badge: 'Zu unscharf',
        title: 'Zu unscharf, um Ihre eigene Iris zu restaurieren',
        reason: 'Auf diesem Foto ist zu wenig von Ihrem eigenen Irismuster zu sehen, um es zu restaurieren. Daher verwenden wir es nicht.',
        error: 'Dieses Foto ist zu unscharf, um Ihre eigene Iris zu restaurieren. Bitte nehmen Sie es mit den Schritten unten neu auf.',
        retakeLine: 'Diese Aufnahme ist zu unscharf, um Ihre eigene Iris zu restaurieren. Nehmen Sie sie bei Tageslicht von einem seitlichen Fenster neu auf, mit der Rückkamera und 2-fachem Zoom: Tippen Sie zum Scharfstellen auf die Iris und halten Sie das Smartphone ruhig.',
        thumb: 'unscharf',
        steps: [LIGHT_DE, CAMERA_DE, FOCUS_DE, STEADY_DE],
      },
      too_dark: {
        badge: 'Zu dunkel',
        title: 'Zu dunkel, um Ihr eigenes Irismuster zu erkennen',
        reason: 'Ihre Iris ist dunkel und es war zu wenig Licht, um ihr eigenes Muster zu erkennen. Daher verwenden wir dieses Foto nicht.',
        error: 'Dieses Foto ist zu dunkel, um Ihr eigenes Irismuster zu erkennen. Bitte nehmen Sie es mit den Schritten unten neu auf.',
        retakeLine: 'Diese Aufnahme ist zu dunkel, um Ihr eigenes Irismuster zu erkennen. Nehmen Sie sie bei Tageslicht nah an einem hellen Fenster neu auf, das Fenster seitlich. Keine Lampe, kein Blitz.',
        thumb: 'dunkel',
        steps: [DARK_LIGHT_DE, CAMERA_DE, FOCUS_DE, STEADY_DE],
      },
      pupil_too_large: {
        badge: 'Pupille zu weit',
        title: 'Ihre Pupille ist zu weit, um Ihre Iris zu restaurieren',
        reason: 'Ihre Pupille ist auf diesem Foto so weit geöffnet, dass zu wenig von Ihrer Iris zu sehen ist. Daher verwenden wir es nicht.',
        error: 'Ihre Pupille ist auf diesem Foto zu weit, um Ihre eigene Iris zu restaurieren. Bitte nehmen Sie es mit den Schritten unten neu auf.',
        retakeLine: 'Ihre Pupille ist auf dieser Aufnahme zu weit. Mehr Licht macht sie kleiner: Nehmen Sie sie bei Tageslicht nah an einem hellen Fenster neu auf, nicht mit Blitz.',
        thumb: 'Pupille',
        steps: [
          'Mehr Licht macht Ihre Pupille kleiner: Stellen Sie sich bei Tageslicht nah an ein helles Fenster, das Fenster seitlich (keine direkte Sonne). Kein Blitz.',
          'Geben Sie Ihrem Auge vor der Aufnahme eine Minute in diesem Licht, damit sich die Pupille verengen kann. Wenn es draußen dunkel ist, schalten Sie alle Deckenlampen ein.',
          CAMERA_DE,
          'Tippen Sie zum Scharfstellen auf die Iris, halten Sie das Smartphone ruhig und machen Sie 3-5 Aufnahmen.',
        ],
      },
      too_small: {
        badge: 'Zu klein',
        title: 'Ihre Iris ist auf diesem Foto zu klein',
        reason: 'Ihre Iris ist auf diesem Foto so klein, dass zu wenig von ihrem eigenen Muster zu sehen ist. Daher verwenden wir es nicht.',
        error: 'Ihre Iris ist auf diesem Foto zu klein, um sie zu restaurieren. Bitte nehmen Sie es näher mit den Schritten unten neu auf.',
        retakeLine: 'Ihre Iris ist auf dieser Aufnahme zu klein. Gehen Sie näher heran: Rückkamera mit 2-fachem Zoom, etwa 10 cm vor dem Auge, sodass die Iris etwa ein Drittel des Bildes füllt.',
        thumb: 'klein',
        steps: [
          'Gehen Sie näher heran: Rückkamera mit 2-fachem Zoom, etwa 10 cm vor dem Auge, sodass die Iris etwa ein Drittel des Bildes füllt.',
          LIGHT_DE,
          FOCUS_DE,
          STEADY_DE,
        ],
      },
    } satisfies Record<BlockReason, BlockCopy>,
    blockedOther: {
      badge: 'Zu wenig Details',
      title: 'Zu wenig Details, um Ihre eigene Iris zu restaurieren',
      reason: 'Auf diesem Foto ist zu wenig von Ihrem eigenen Irismuster zu sehen, um es zu restaurieren. Daher verwenden wir es nicht.',
      error: 'Dieses Foto zeigt zu wenig von Ihrer eigenen Iris, um sie zu restaurieren. Bitte nehmen Sie es mit den Schritten unten neu auf.',
      retakeLine: 'Diese Aufnahme zeigt zu wenig von Ihrer eigenen Iris, um sie zu restaurieren. Machen Sie eine weitere nach der Anleitung.',
      thumb: 'nochmal',
      steps: [LIGHT_DE, CAMERA_DE, FOCUS_DE, STEADY_DE],
    } satisfies BlockCopy,
    guideTitle: 'Für die neue Aufnahme',
    noneUsable: (n: number) => (n === 2 ? 'Wir haben beide Fotos geprüft, keines ist verwendbar.' : `Wir haben alle ${n} Fotos geprüft, keines davon ist verwendbar.`),
    shotUnusable: 'Diese Aufnahme ist nicht verwendbar. Machen Sie eine weitere mit den Hinweisen oben.',
    shotsUnusable: 'Noch keine dieser Aufnahmen ist verwendbar. Machen Sie eine weitere mit den Hinweisen oben.',
    fullUnusable: (max: number) => `Keine dieser ${max} Aufnahmen ist verwendbar. Machen Sie eine weitere, um neu zu beginnen.`,
    verdicts: { good: 'Sehr gutes Foto', ok: 'Brauchbares Foto', weak: 'Schwaches Foto' },
    detectedIris: 'Erkannte Iris',
    detail: 'Detail',
    aimFor: (d: number) => `Ziel: ${d}+`,
    fibresResolved: 'Fasern erkennbar',
    picked: (of: number, used: number) => `Wir haben ${of} Fotos verglichen und das beste verwendet (Foto ${used}).`,
    pickedRatio: (ratio: string) => ` Es zeigt ${ratio}-mal so viele Faserdetails wie das unschärfste.`,
    tryRetake: 'Neu aufnehmen',
    pupilNote: 'Eine Spiegelung auf der Pupille ist kein Problem: Wir bauen die Pupille als sauberes Schwarz neu auf.',
    lampFallback: 'Lampenlicht färbt das Weiße Ihres Auges, daher können die Farben wärmer wirken, als sie wirklich sind.',
    closer: 'Gehen Sie näher heran oder zoomen Sie, damit die Iris mehr vom Bild füllt.',
  },

  collector: {
    header: (n: number, max: number) => `Aufnahme ${n} von ${max}`,
    headerDetail: (d: number) => ` · Detail ${d}`,
    shotAlt: (n: number) => `Aufnahme ${n}`,
    bestLabel: (k: number, d?: number) => `Aufnahme ${k}${d !== undefined ? ` (Detail ${d})` : ''}`,
    full: (max: number, best: string) => `Das sind ${max} Aufnahmen. Wir verwenden Ihre beste, ${best}.`,
    more: (left: number) => `Machen Sie bis zu ${left} weitere. Wir messen jede Aufnahme und behalten die beste.`,
    sharpEnough: 'Diese ist scharf genug.',
    bestSoFar: 'Das ist bisher Ihre beste Aufnahme.',
    lampSkipped: (n: number, best: string) => `Lampenlicht hat Aufnahme ${n} gefärbt, daher verwenden wir ${best}, Ihre beste Aufnahme in echten Farben.`,
    bestIs: (best: string) => `Ihre bisher beste ist ${best}. Diese verwenden wir.`,
    lastFailed: (note: string) => `Die letzte Aufnahme war nicht verwendbar: ${note} Ihre bisher beste Aufnahme bleibt erhalten.`,
    takeAnother: 'Weitere Aufnahme',
    useBest: 'Beste verwenden',
    useThis: 'Diese verwenden',
    startOver: 'Neu beginnen',
  },

  live: {
    guide: 'Iris füllt diesen Kreis · 12-15 cm · 2x',
    sharp: 'Scharf ✓',
    holdStill: 'Ruhig halten / Iris antippen',
    close: 'Schließen',
    zoom: (v: string) => `Zoom ${v}x`,
    noZoom: 'Dieser Browser bietet keinen Kamerazoom. Nutzen Sie stattdessen „Foto aufnehmen“ und zoomen Sie in Ihrer Kamera-App auf 2x.',
    lowRes: 'Dieser Browser kann hier nur ein Bild mit geringer Auflösung aufnehmen. Für ein scharfes Ergebnis nutzen Sie stattdessen „Foto aufnehmen“, das öffnet die echte Kamera.',
    capture: 'Auslösen',
    unavailable: 'Kamera nicht verfügbar',
  },

  result: {
    beforeAfter: 'Vorher/Nachher',
    eyes: 'Augen auf diesem Kunstwerk',
    eyeLabel: (i: number) => `Auge ${i}`,
    sampleLabel: 'KI-generiertes Beispiel',
    yourPhoto: 'Ihr Foto',
    samplePhoto: 'KI-generiertes Beispiel',
    after: 'Studio-Makro',
    sliderBefore: 'Ihr Foto',
    sliderAfter: 'Restauriert',
    // src/landing/copy.ts TRANSPARENCY_DE, word for word
    transparency: 'Die Farbe stammt aus Ihrem eigenen Foto. Wo Ihr Smartphone die feinsten Fasern nicht erfassen konnte, stellt unsere KI sie wieder her.',
    sampleNote: 'Dieses Auge ist das KI-generierte Beispiel, kein echtes Foto. Mit Ihrem eigenen Foto stammt die Farbe aus Ihrem Foto.',
    colourOff: 'Unsere Farbprüfung zeigt, dass diese Restaurierung von Ihrem Foto abweicht: Sie kann heller oder dunkler wirken als Ihr Auge. Eine neue Aufnahme bei weichem Tageslicht behebt das meist.',
    retakeEye: (i: number) => `Auge ${i} neu aufnehmen`,
    retakeOnly: 'Dieses Auge neu aufnehmen',
    replaceSample: 'Stattdessen Ihr eigenes Auge verwenden',
    removed: (i: number) => `Auge ${i} entfernt.`,
    undo: 'Rückgängig',
    sampleArtwork: 'Beispiel-Kunstwerk',
    sampleBadge: 'KI-generiertes Beispiel',
    sampleTitle: 'KI-generiertes Beispiel',
    sampleArtworkNote: 'Nur aus dem KI-generierten Beispielauge erstellt, nicht aus einem echten Foto.',
    mixedArtworkNote: 'Dieses Kunstwerk enthält das KI-generierte Beispielauge, das kein echtes Foto ist.',
    drag: 'Ziehen Sie den Regler.',
    irisPx: (px: number) => `Iris in Ihrem Foto: ${px} px.`,
    reflection: 'Spiegelung entfernt.',
    upscaled: 'Kleines Foto: vor der Restaurierung hochskaliert.',
    badgeMacro: 'Studio-Makro',
    badgeFallback: 'Nur originalgetreu vergrößert',
    artwork: 'Ihr Kunstwerk',
    composing: 'Wird gestaltet…',
    composeFailed: 'Diese Vorschau konnte nicht erstellt werden.',
    retry: 'Erneut versuchen',
    layout: 'Anordnung',
    layouts: {
      single: 'Einzeln', duo: 'Nebeneinander', fusion: 'Fusion', triangle: 'Dreieck', row: 'In einer Reihe', grid: 'Raster', galaxy: 'Galaxie',
    } satisfies Record<Layout, string>,
    style: 'Stil',
    namesPlaceholder: 'Namen oder Widmung (optional)',
    save: 'Vorschau speichern',
    fileName: (style: string, n: number, sample: boolean) => `snapeyes-vorschau-${style}-${n}-${n === 1 ? 'auge' : 'augen'}${sample ? '-ki-generiertes-beispiel' : ''}.jpg`,
    addSecond: 'Zweites Auge hinzufügen',
    addAnother: 'Weiteres Auge hinzufügen',
    addHint: (left: number) => `Partner, Kind oder Ihr anderes Auge. Platz für ${left} ${left === 1 ? 'weiteres Auge' : 'weitere Augen'} auf diesem Kunstwerk.`,
    full: (max: number) => `Das sind ${max} Augen, mehr fasst ein Kunstwerk nicht.`,
    remove: (i: number) => `Auge ${i} entfernen`,
    startOver: 'Neu beginnen',
    confirmStartOver: (n: number) => `Alle ${n} Augen verwerfen und neu beginnen?`,
    stored: 'Im Trainingsspeicher gesichert',
  },

  price: {
    title: 'Preis für dieses Kunstwerk',
    oneEye: (style: string) => `1 Auge · ${style}`,
    duo: 'Couple Duo · 2 Augen',
    many: (n: number) => `${n} Augen · Couple Duo + ${n - 2} weitere`,
    oneEyeOther: (studioBlack: string, art: string) => `1 Auge: ${studioBlack} in Studio Black, ${art} mit Kunsthintergrund.`,
    duoOffer: (duo: string) => `Mit einem zweiten Auge wird es das Couple Duo: ${duo} für beide.`,
    extra: (duo: string, extra: string, max: number) => `Couple Duo ${duo}, dann +${extra} für jedes weitere Auge, bis zu ${max} Augen.`,
    // src/landing/copy.ts de.pricing.notice, word for word
    notice: 'Bestellungen sind bald möglich - Ihre Vorschau ist schon heute kostenlos.',
    footnote: 'Sie würden eine digitale Datei ohne Wasserzeichen erhalten, 4096 px an der längsten Seite. Preise in Euro.',
    demo: 'Dies ist eine Demo mit dem KI-generierten Beispielauge. Probieren Sie es mit Ihrem eigenen Auge, um Ihren Preis zu sehen.',
    sampleNotCounted: (k: number) => (k === 1
      ? 'Das KI-generierte Beispielauge ist nicht Teil einer Bestellung und wird daher nicht mitgezählt.'
      : `Die ${k} KI-generierten Beispielaugen sind nicht Teil einer Bestellung und werden daher nicht mitgezählt.`),
  },

  buy: {
    button: (price: string) => `${CHECKOUT_LEGAL.de.continueButton} · ${price}`,
    next: 'Als Nächstes öffnet sich die sichere Zahlungsseite von Stripe. Dort geben Sie Ihre E-Mail-Adresse ein und bestellen verbindlich, wenn Sie die Zahlung mit der Zahlungsschaltfläche bestätigen. Sobald Ihre Bestellbestätigung per E-Mail versandt ist, normalerweise innerhalb einer Minute nach Ihrer Zahlung, beginnen wir mit der Erstellung Ihrer Datei.',
    waitPreview: 'Die Vorschau für diese Auswahl wird noch erstellt. Sie können bestellen, sobald Sie sie sehen.',
    previewFailed: 'Bitte laden Sie zuerst die Vorschau für diese Auswahl (oben „Erneut versuchen“), damit Sie sehen, was Sie bestellen.',
    steps: {
      sync: 'Ihre Bestellung wird geprüft…',
      upload: (i: number, n: number) => (n > 1 ? `Auge ${i} von ${n} wird hochgeladen…` : 'Ihr Auge wird hochgeladen…'),
      arrange: 'Ihre Augen werden angeordnet…',
      checkout: 'Die sichere Zahlungsseite wird geöffnet…',
    },
    sample: (k: number): string => (k === 1
      ? 'Das KI-generierte Beispielauge kann nicht bestellt werden. Ersetzen Sie es durch Ihr eigenes Auge, um dieses Kunstwerk zu bestellen.'
      : 'Die KI-generierten Beispielaugen können nicht bestellt werden. Ersetzen Sie sie durch Ihre eigenen Augen, um dieses Kunstwerk zu bestellen.'),
    replaceSampleEye: (i: number) => `Auge ${i} durch Ihr eigenes ersetzen`,
    stale: (list: number[], total: number) => (total === 1
      ? 'Ihr Foto wurde vor mehr als 15 Minuten aufgenommen. Ein Foto kann innerhalb von 15 Minuten nach der Aufnahme bestellt werden. Bitte nehmen Sie es neu auf, um zu bestellen.'
      : `${list.length === 1 ? `Auge ${list[0]} wurde` : `Die Augen ${andList(list, 'und')} wurden`} vor mehr als 15 Minuten aufgenommen. Ein Foto kann innerhalb von 15 Minuten nach der Aufnahme bestellt werden. Bitte nehmen Sie ${list.length === 1 ? 'es' : 'sie'} neu auf, um zu bestellen.${list.length < total ? ' Ihre anderen Augen bleiben, wie sie sind.' : ''}`),
    cancelled: 'Zahlung abgebrochen. Es wurde nichts berechnet. Ihr Kunstwerk ist noch da: Sie können es ändern oder erneut bestellen.',
    cancelledLost: 'Zahlung abgebrochen. Es wurde nichts berechnet. Diese Seite konnte Ihre Vorschau nicht behalten. Bitte nehmen Sie Ihr Foto erneut auf.',
    close: 'Schließen',
    errors: {
      network: 'Wir konnten SnapEyes nicht erreichen. Bitte prüfen Sie Ihre Internetverbindung und versuchen Sie es erneut.',
      busy: 'Der Zahlungsdienst hat nicht geantwortet. Bitte versuchen Sie es gleich noch einmal.',
      payments: `Wir konnten die Zahlungsseite nicht öffnen. Bitte versuchen Sie es später erneut oder schreiben Sie an ${CONTACT_EMAIL}.`,
      too_large: 'Die Aufnahme eines Ihrer Augen ist zu groß zum Hochladen. Bitte nehmen Sie dieses Auge neu auf.',
      paused: `Neue Bestellungen sind für heute pausiert: Das tägliche Upload-Limit ist erreicht. Es wurde nichts berechnet. Bitte versuchen Sie es morgen erneut oder schreiben Sie an ${CONTACT_EMAIL}.`,
      too_many: `Diese Bestellung hat ihr Upload-Limit für heute erreicht (30 Uploads, Neuaufnahmen eingeschlossen). Es wurde nichts berechnet. Bitte versuchen Sie es morgen erneut oder schreiben Sie an ${CONTACT_EMAIL}.`,
      failed: `Beim Vorbereiten Ihrer Bestellung ist etwas schiefgelaufen. Bitte versuchen Sie es erneut oder schreiben Sie an ${CONTACT_EMAIL}.`,
      closed: 'Bestellungen sind noch nicht möglich.',
    },
    footnote: 'Eine digitale Datei (JPEG), 4096 px an der längsten Seite, ohne Wasserzeichen. Das ist der Endpreis: Wir sind nicht umsatzsteuerlich registriert, daher wird keine Umsatzsteuer berechnet.',
  },

  study: {
    title: (shot: number, photos: number) => (photos > 1 ? `Familientest · Fotos ${shot - photos + 1}-${shot}` : `Familientest · Aufnahme ${shot}`),
    light: 'Licht bei dieser Aufnahme',
    lights: {
      window_daylight: 'Tageslicht am Fenster', room_lamp: 'Zimmerlampe', phone_torch: 'Handy-Taschenlampe', someone_helped: 'Jemand hat geholfen',
    } satisfies Record<LightAnswer, string>,
    comfort: 'Wie einfach war es? 1 schwer, 5 leicht',
    skip: 'Überspringen',
    thanks: 'Danke. Diese Antworten werden mit Ihrem nächsten Foto gesendet.',
    pending: (shots: number[]) => `Familientest: Ihre Antworten zu ${shots.length === 1 ? `Aufnahme ${shots[0]}` : `den Aufnahmen ${shots.join(', ')}`} wurden noch nicht gesendet. Sie gehen mit Ihrem nächsten Foto mit, zum Beispiel wenn Sie ein weiteres Auge hinzufügen. Wenn Sie die Seite jetzt schließen, gehen sie verloren.`,
  },
};

export const COPY: Record<Lang, TryCopy> = { en, de };

/** The copy of the page's current language (a live binding: importers see every switch). */
export let T: TryCopy = en;

/** Switch T to another language. Only TryApp calls this, right before it re-renders in that language. */
export function setCopyLang(l: Lang): void {
  T = COPY[l];
}
