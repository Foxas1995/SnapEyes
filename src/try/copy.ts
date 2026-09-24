// Every string the multi-eye flow, the price card and the capture study show, in one place so /try can be
// translated later. English only for now (owner decision 2026-09-23: German starts on the landing page).
import type { Layout, LightAnswer } from './multi';

const eyes = (n: number) => `${n} ${n === 1 ? 'eye' : 'eyes'}`;

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

/** The reasons api/analyze.py gives for blocking a shot (quality.block_reason). A blocked shot gets no work
 *  ticket, so the page offers only a retake. */
export type BlockReason = 'too_blurry' | 'too_dark' | 'pupil_too_large';

/** What the page says about a blocked shot. badge: the verdict pill; title: the retake card's heading; reason:
 *  why, in one line, on the single-photo card (the steps follow in the retake card, so the server's own message,
 *  which lists them too, is not shown next to them); error: when the studio is asked for it anyway; retakeLine:
 *  one self-contained line for a shot collector whose best shot is still usable (no retake card there), used
 *  only when the server sends no message; thumb: under its thumbnail instead of a Detail number; steps: the
 *  retake card's list. */
export interface BlockCopy { badge: string; title: string; reason: string; error: string; retakeLine: string; thumb: string; steps: string[] }

export const T = {
  header: {
    tag: 'Private Atelier · preview',
    study: 'Family test',
  },

  capture: {
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
    stepsShots: 'Take 3-5 shots and send them all.',
    stepsShotsMore: ' Turn a little between shots. We measure every one and use the sharpest; on a real test the best shot had 3.7x the detail of the worst.',
  },

  working: {
    restoring: 'Restoring your iris…',
    restoringEye: (n: number) => `Restoring eye ${n}…`,
    cut: 'Cutting out your iris',
    reflections: 'Removing reflections',
    macro: 'Studio macro restoration (about 30 s)',
    composing: (n: number) => (n > 1 ? `Composing your artwork with ${n} eyes` : 'Composing your artwork'),
    sampleCaption: 'AI-generated sample',
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
  },

  result: {
    beforeAfter: 'Before / after',
    eyes: 'Eyes on this artwork',
    eyeLabel: (i: number) => `Eye ${i}`,
    sampleLabel: 'AI-generated sample',
    yourPhoto: 'Your photo',
    samplePhoto: 'AI-generated sample',
    after: 'Studio macro',
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
