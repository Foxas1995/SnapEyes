// Every string the multi-eye flow, the price card and the capture study show, in one place so /try can be
// translated later. English only for now (owner decision 2026-09-23: German starts on the landing page).
import type { Layout, LightAnswer } from './multi';

const eyes = (n: number) => `${n} ${n === 1 ? 'eye' : 'eyes'}`;

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
