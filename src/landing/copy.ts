// All landing page copy, English and German (formal "Sie"). Every sentence must stay true today:
// no reviews, customer counts, guarantees, awards, physical products or purchase buttons.
import type { StyleId } from './config';

export type Lang = 'en' | 'de';

export interface Copy {
  meta: { title: string; description: string; shareDescription: string; locale: string };
  langName: string;
  switchLabel: string;
  brandTag: string;
  nav: { beforeAfter: string; how: string; styles: string; pricing: string; faq: string; privacy: string };
  navLabels: { main: string; footer: string };
  cta: string;
  ctaShort: string;
  // Shown under the main calls to action when /try is not in this language (it is English only for now).
  ctaNote: string;
  hero: {
    eyebrow: string;
    title: string;
    lead: string;
    points: string[];
    soon: string;
    secondary: string;
    imageAlt: string;
    insetAlt: string;
    insetLabel: string;
    caption: string;
    styleNote: string;
  };
  beforeAfter: {
    eyebrow: string;
    title: string;
    intro: string;
    before: string;
    after: string;
    beforeAlt: string;
    afterAlt: string;
    sliderLabel: string;
    caption: string;
    transparencyTitle: string;
    transparency: string;
  };
  how: {
    eyebrow: string;
    title: string;
    steps: Array<{ title: string; body: string }>;
  };
  styles: {
    eyebrow: string;
    title: string;
    intro: string;
    oneEye: string;
    desc: Record<StyleId, string>;
    alt: (name: string) => string;
  };
  pricing: {
    eyebrow: string;
    title: string;
    notice: string;
    previewTitle: string;
    previewPrice: string;
    previewItems: string[];
    oneEyeTitle: string;
    oneEyeNote: string;
    studioBlack: string;
    artBackground: string;
    artBackgroundNote: string;
    severalTitle: string;
    severalNote: string;
    duoLabel: string;
    eyes: (n: number) => string;
    perEye: (price: string, max: number) => string;
    footnote: string;
  };
  curator: {
    eyebrow: string;
    title: string;
    role: string;
    note: string;
    photoAlt: string;
    offer: string;
    offerCta: string;
  };
  privacy: {
    eyebrow: string;
    title: string;
    items: Array<{ title: string; body: string }>;
    controller: string;
    rights: string;
  };
  faq: {
    eyebrow: string;
    title: string;
    items: Array<{ q: string; a: string }>;
  };
  final: { title: string; body: string };
  footer: {
    operatedBy: string;
    company: string;
    companyCode: string;
    country: string;
    contact: string;
    rights: string;
  };
}

const TRANSPARENCY_EN = 'Colour from your own photo. Where your phone could not capture the finest fibres, our AI restores them.';
const TRANSPARENCY_DE = 'Die Farbe stammt aus Ihrem eigenen Foto. Wo Ihr Smartphone die feinsten Fasern nicht erfassen konnte, stellt unsere KI sie wieder her.';

// Measured deliverable (api/master_compose.py, L.multi_canvas at 4096): one eye is 4096 x 4096 px; several
// eyes are 4096 px on the longest side (a Couple Duo is 4096 x 2731). Never promise a square file for all orders.
const PX = '4096\u00a0px';
const SQUARE = '4096\u00a0x\u00a04096\u00a0px';

const en: Copy = {
  meta: {
    title: 'SnapEyes Private Atelier - Precision Iris Art from Your Smartphone',
    description:
      "Photograph one eye with your phone's back camera and see your own iris as fine art in six styles. The watermarked preview is free; ordering opens soon.",
    shareDescription: 'Photograph one eye with your phone and see your own iris as fine art in six styles. The watermarked preview is free.',
    locale: 'en_GB',
  },
  langName: 'English',
  switchLabel: 'Language',
  brandTag: 'Private Atelier',
  nav: { beforeAfter: 'Before & after', how: 'How it works', styles: 'Styles', pricing: 'Pricing', faq: 'FAQ', privacy: 'Privacy' },
  navLabels: { main: 'Main', footer: 'Footer' },
  cta: 'Create my free preview',
  ctaShort: 'Free preview',
  ctaNote: '',
  hero: {
    eyebrow: 'SnapEyes Private Atelier',
    title: 'Precision Iris Art from Your Smartphone',
    lead:
      'Photograph one eye with the back camera of your phone. We find your iris, restore it and set it in the style you choose. You see the result first, free of charge.',
    points: ['Free watermarked preview in 6 styles', 'About a minute, no sign-up'],
    soon: `Soon: your artwork as a ${PX} digital file`,
    secondary: 'See a real before and after',
    imageAlt: "The founder's own iris in the Celestial Gold style",
    insetAlt: "The founder's phone photo of the same eye",
    insetLabel: 'Phone photo, 315\u00a0px',
    caption: 'Mantas, founder - photographed at home with a phone',
    styleNote: 'Artwork in Celestial Gold',
  },
  beforeAfter: {
    eyebrow: 'A real before and after',
    title: 'One eye, one phone, one result',
    intro:
      "This is the founder's own eye. On the left, the phone photo cropped to the iris at its original 315\u00a0px. On the right, the same eye in Studio Black, rendered by the engine that makes your preview.",
    before: 'Before: phone photo',
    after: 'After: Studio Black',
    beforeAlt: "Before: the founder's eye as the phone captured it",
    afterAlt: 'After: the same eye rendered in Studio Black',
    sliderLabel: 'Compare before and after',
    caption: 'Mantas, founder - photographed at home with a phone',
    transparencyTitle: 'What comes from you, and what the AI adds',
    transparency: TRANSPARENCY_EN,
  },
  how: {
    eyebrow: 'How it works',
    title: 'Three steps, no studio',
    steps: [
      {
        title: 'Photograph one eye',
        body: 'Use the back camera at 2x or 3x zoom, not the selfie camera. Light from the side, about 10\u00a0cm away. Take three to five shots; we measure every shot and use the best one.',
      },
      {
        title: 'See your free preview',
        body: 'In about a minute your iris appears in all six styles, with a watermark. No sign-up, nothing to pay.',
      },
      {
        title: `Order your ${PX} file`,
        body: `Choose a style and receive your artwork as a digital file, ${PX} on its longest side, rendered once in full resolution when you approve it. Ordering opens soon.`,
      },
    ],
  },
  styles: {
    eyebrow: 'Six styles',
    title: 'The same eye, six ways',
    intro:
      "Every image below is the founder's eye from the before and after above, rendered by our engine in each style. Your preview adds a watermark, and the art styles a small signature line under the title; both are left out here.",
    oneEye: 'One eye',
    desc: {
      studio_black: 'Your iris alone, on pure black.',
      celestial_gold: 'A band of golden stardust.',
      deep_nebula: 'A star field in indigo and violet.',
      emerald_aurora: 'Green stardust with a touch of rose.',
      obsidian_smoke: 'Silver stars on deep black.',
      supernova: 'Stardust in red and orange.',
    },
    alt: (name) => `The founder's iris in the ${name} style`,
  },
  pricing: {
    eyebrow: 'Pricing',
    title: 'Clear prices for one digital file',
    notice: 'Ordering opens soon - your preview is free today.',
    previewTitle: 'Preview',
    previewPrice: 'Free',
    previewItems: ['All 6 styles', 'With watermark', 'Available today'],
    oneEyeTitle: 'One eye',
    oneEyeNote: 'Your iris as one artwork, in the style you choose.',
    studioBlack: 'Studio Black',
    artBackground: 'Art background',
    artBackgroundNote: 'Celestial Gold, Deep Nebula, Emerald Aurora, Obsidian Smoke or Supernova',
    severalTitle: 'Several eyes',
    severalNote: 'Two to eight eyes on one artwork: yours and those of the people you love.',
    duoLabel: '2 eyes · Couple Duo',
    eyes: (n) => `${n} eyes`,
    perEye: (price, max) => `+${price} for each further eye, up to ${max} eyes`,
    footnote: `Every order is one digital file without watermark, ${PX} on its longest side (${SQUARE} for one eye). Prices in euros.`,
  },
  curator: {
    eyebrow: 'The curator',
    title: 'Behind the atelier',
    role: 'SnapEyes Studio Curator',
    note:
      'The eye on this page is mine, photographed at home with my phone. The preview is free so that you can judge the result with your own eyes before you pay anything.',
    photoAlt: "Mantas's own iris",
    offer: "Can't get a sharp shot? Send me your best photos and I will personally check them within 24 hours.",
    offerCta: 'Email Mantas',
  },
  privacy: {
    eyebrow: 'Your photo',
    title: 'A promise about your eye',
    items: [
      { title: 'Only for your artwork', body: 'Your photo is used to make your artwork and for nothing else.' },
      { title: 'Never for identification', body: 'It is never used to identify anyone, never sold and not used to train AI.' },
      { title: 'Not kept on our server', body: 'Your photo is processed and then discarded. We do not store it.' },
      {
        title: 'Two outside services',
        body: "The page and the preview run on Vercel's servers; the restoration runs on Google AI. Google keeps request logs for a limited time.",
      },
    ],
    controller: 'Responsible for your data: MB "Portretizuokis", Kaunas, Lithuania (full details at the foot of this page).',
    rights: 'You may ask what data we hold about you, have it corrected or deleted, and complain to a data protection authority.',
  },
  faq: {
    eyebrow: 'Questions',
    title: 'Before you start',
    items: [
      {
        q: 'Which phone and camera should I use?',
        a: 'Any recent smartphone with a good back camera. Use the back camera at 2x or 3x zoom, not the selfie camera. Have light coming from one side, from a window or a lamp. Hold the phone about 10\u00a0cm from your eye, tap the iris to focus and take three to five shots.',
      },
      {
        q: 'Is it really my eye?',
        a: `Yes. ${TRANSPARENCY_EN} So the very finest detail is a restoration, not a microscope photograph. The free preview lets you judge the result before you pay anything.`,
      },
      {
        q: 'What do I receive?',
        a: `Your artwork as one digital file without the watermark, in the style you choose: ${SQUARE} for one eye, ${PX} on the longest side for several eyes.`,
      },
      {
        q: 'How long does it take?',
        a: 'The free preview takes about a minute. Once ordering opens, your file is rendered once in full resolution after you approve it, which takes about half a minute per eye.',
      },
      {
        q: 'When can I order?',
        a: 'Ordering opens soon. Until then the preview is free.',
      },
    ],
  },
  final: {
    title: 'See your own iris',
    body: 'All it takes is your phone, good light and about a minute.',
  },
  footer: {
    operatedBy: 'SnapEyes is operated by',
    company: 'MB "Portretizuokis"',
    companyCode: 'Company code',
    country: 'Lithuania',
    contact: 'Contact',
    rights: 'SnapEyes',
  },
};

const de: Copy = {
  meta: {
    title: 'SnapEyes Private Atelier - Präzise Iris-Kunst vom Smartphone',
    description:
      'Fotografieren Sie ein Auge mit der Rückkamera Ihres Smartphones und sehen Sie Ihre eigene Iris als Kunstwerk in sechs Stilen. Die Vorschau mit Wasserzeichen ist kostenlos, Bestellungen sind bald möglich.',
    shareDescription:
      'Fotografieren Sie ein Auge mit dem Smartphone und sehen Sie Ihre eigene Iris als Kunstwerk in sechs Stilen. Die Vorschau mit Wasserzeichen ist kostenlos.',
    locale: 'de_DE',
  },
  langName: 'Deutsch',
  switchLabel: 'Sprache',
  brandTag: 'Private Atelier',
  nav: { beforeAfter: 'Vorher/Nachher', how: 'Ablauf', styles: 'Stile', pricing: 'Preise', faq: 'Fragen', privacy: 'Datenschutz' },
  navLabels: { main: 'Hauptnavigation', footer: 'Fußzeile' },
  cta: 'Kostenlose Vorschau erstellen',
  ctaShort: 'Gratis-Vorschau',
  // src/try/copy.ts: /try is English only for now (owner decision 2026-09-23). Remove this once it is translated.
  ctaNote: 'Die Vorschau-App ist derzeit nur auf Englisch verfügbar.',
  hero: {
    eyebrow: 'SnapEyes Private Atelier',
    title: 'Präzise Iris-Kunst vom Smartphone',
    lead:
      'Fotografieren Sie ein Auge mit der Rückkamera Ihres Smartphones. Wir finden Ihre Iris, restaurieren sie und setzen sie im Stil Ihrer Wahl in Szene. Das Ergebnis sehen Sie zuerst, und zwar kostenlos.',
    points: ['Kostenlose Vorschau in 6 Stilen, mit Wasserzeichen', 'Etwa eine Minute, ohne Anmeldung'],
    soon: `Bald: Ihr Kunstwerk als digitale Datei mit ${PX}`,
    secondary: 'Echtes Vorher/Nachher ansehen',
    imageAlt: 'Die Iris des Gründers im Stil Celestial Gold',
    insetAlt: 'Das Smartphone-Foto desselben Auges',
    insetLabel: 'Smartphone-Foto, 315\u00a0px',
    caption: 'Mantas, Gründer - zu Hause mit dem Smartphone fotografiert',
    styleNote: 'Kunstwerk im Stil Celestial Gold',
  },
  beforeAfter: {
    eyebrow: 'Echtes Vorher/Nachher',
    title: 'Ein Auge, ein Smartphone, ein Ergebnis',
    intro:
      'Das ist das Auge des Gründers. Links das Smartphone-Foto, auf die Iris zugeschnitten, in der Originalgröße von 315\u00a0px. Rechts dasselbe Auge im Stil Studio Black, berechnet von derselben Software, die auch Ihre Vorschau erstellt.',
    before: 'Vorher: Smartphone-Foto',
    after: 'Nachher: Studio Black',
    beforeAlt: 'Vorher: das Auge des Gründers, so wie das Smartphone es aufgenommen hat',
    afterAlt: 'Nachher: dasselbe Auge im Stil Studio Black',
    sliderLabel: 'Vorher und Nachher vergleichen',
    caption: 'Mantas, Gründer - zu Hause mit dem Smartphone fotografiert',
    transparencyTitle: 'Was von Ihnen stammt und was die KI ergänzt',
    transparency: TRANSPARENCY_DE,
  },
  how: {
    eyebrow: 'Ablauf',
    title: 'Drei Schritte, kein Fotostudio',
    steps: [
      {
        title: 'Ein Auge fotografieren',
        body: 'Nutzen Sie die Rückkamera mit 2- oder 3-fachem Zoom, nicht die Selfie-Kamera. Licht von der Seite, etwa 10\u00a0cm Abstand. Machen Sie drei bis fünf Aufnahmen, wir prüfen jede davon und verwenden die beste.',
      },
      {
        title: 'Kostenlose Vorschau ansehen',
        body: 'Nach etwa einer Minute sehen Sie Ihre Iris in allen sechs Stilen, mit Wasserzeichen. Ohne Anmeldung und ohne Kosten.',
      },
      {
        title: `Datei mit ${PX} bestellen`,
        body: `Wählen Sie einen Stil und erhalten Sie Ihr Kunstwerk als digitale Datei mit ${PX} an der längsten Seite. Sie wird einmalig in voller Auflösung berechnet, sobald Sie das Motiv freigeben. Bestellungen sind in Kürze möglich.`,
      },
    ],
  },
  styles: {
    eyebrow: 'Sechs Stile',
    title: 'Dasselbe Auge, sechs Stile',
    intro:
      'Jedes Bild hier zeigt das Auge des Gründers aus dem Vorher/Nachher oben, von unserer Software in jedem Stil berechnet. Ihre Vorschau trägt ein Wasserzeichen, die Kunststile zusätzlich eine kleine Signaturzeile unter dem Titel; beides ist hier weggelassen.',
    oneEye: 'Ein Auge',
    desc: {
      studio_black: 'Nur Ihre Iris, auf reinem Schwarz.',
      celestial_gold: 'Ein Band aus goldenem Sternenstaub.',
      deep_nebula: 'Ein Sternenfeld in Indigo und Violett.',
      emerald_aurora: 'Grüner Sternenstaub mit einem Hauch Rosé.',
      obsidian_smoke: 'Silberne Sterne auf tiefem Schwarz.',
      supernova: 'Sternenstaub in Rot und Orange.',
    },
    alt: (name) => `Die Iris des Gründers im Stil ${name}`,
  },
  pricing: {
    eyebrow: 'Preise',
    title: 'Klare Preise für eine digitale Datei',
    notice: 'Bestellungen sind bald möglich - Ihre Vorschau ist schon heute kostenlos.',
    previewTitle: 'Vorschau',
    previewPrice: 'Kostenlos',
    previewItems: ['Alle 6 Stile', 'Mit Wasserzeichen', 'Schon heute verfügbar'],
    oneEyeTitle: 'Ein Auge',
    oneEyeNote: 'Ihre Iris als einzelnes Kunstwerk, im Stil Ihrer Wahl.',
    studioBlack: 'Studio Black',
    artBackground: 'Kunsthintergrund',
    artBackgroundNote: 'Celestial Gold, Deep Nebula, Emerald Aurora, Obsidian Smoke oder Supernova',
    severalTitle: 'Mehrere Augen',
    severalNote: 'Zwei bis acht Augen auf einem Kunstwerk, etwa Ihr eigenes und die Ihrer Liebsten.',
    duoLabel: '2 Augen · Couple Duo',
    eyes: (n) => `${n} Augen`,
    perEye: (price, max) => `+${price} für jedes weitere Auge, bis zu ${max} Augen`,
    footnote: `Jede Bestellung ist eine digitale Datei ohne Wasserzeichen, mit ${PX} an der längsten Seite (${SQUARE} bei einem Auge). Preise in Euro.`,
  },
  curator: {
    eyebrow: 'Der Kurator',
    title: 'Hinter dem Atelier',
    role: 'SnapEyes Studio Curator',
    note:
      'Das Auge auf dieser Seite ist mein eigenes, zu Hause mit meinem Smartphone fotografiert. Die Vorschau ist kostenlos, damit Sie das Ergebnis mit eigenen Augen beurteilen können, bevor Sie etwas bezahlen.',
    photoAlt: 'Die Iris von Mantas',
    offer: 'Gelingt Ihnen kein scharfes Foto? Schicken Sie mir Ihre besten Aufnahmen, ich sehe sie mir innerhalb von 24 Stunden persönlich an.',
    offerCta: 'E-Mail an Mantas',
  },
  privacy: {
    eyebrow: 'Ihr Foto',
    title: 'Unser Versprechen für Ihr Auge',
    items: [
      { title: 'Nur für Ihr Kunstwerk', body: 'Ihr Foto dient dazu, Ihr Kunstwerk zu erstellen, und zu nichts anderem.' },
      { title: 'Nie zur Identifizierung', body: 'Es wird nie genutzt, um jemanden zu identifizieren, nie verkauft und nicht zum Training von KI verwendet.' },
      { title: 'Nicht auf unserem Server gespeichert', body: 'Ihr Foto wird verarbeitet und danach verworfen. Wir speichern es nicht.' },
      {
        title: 'Zwei externe Dienste',
        body: 'Die Seite und die Vorschau laufen auf Servern von Vercel, die Restaurierung über Google AI. Google speichert Anfrageprotokolle für begrenzte Zeit.',
      },
    ],
    controller: 'Verantwortlich für Ihre Daten: MB „Portretizuokis“, Kaunas, Litauen (vollständige Angaben am Ende dieser Seite).',
    rights: 'Sie können Auskunft über Ihre Daten verlangen, sie berichtigen oder löschen lassen und sich bei einer Datenschutzbehörde beschweren.',
  },
  faq: {
    eyebrow: 'Fragen',
    title: 'Bevor Sie beginnen',
    items: [
      {
        q: 'Welches Smartphone und welche Kamera brauche ich?',
        a: 'Jedes aktuelle Smartphone mit guter Rückkamera. Nutzen Sie die Rückkamera mit 2- oder 3-fachem Zoom, nicht die Selfie-Kamera. Sorgen Sie für seitliches Licht, etwa von einem Fenster oder einer Lampe. Halten Sie das Smartphone etwa 10\u00a0cm vor Ihr Auge, tippen Sie zum Scharfstellen auf die Iris und machen Sie drei bis fünf Aufnahmen.',
      },
      {
        q: 'Ist das wirklich mein Auge?',
        a: `Ja. ${TRANSPARENCY_DE} Die allerfeinsten Details sind also eine Restaurierung, keine Mikroskopaufnahme. Mit der kostenlosen Vorschau beurteilen Sie das Ergebnis, bevor Sie etwas bezahlen.`,
      },
      {
        q: 'Was erhalte ich?',
        a: `Ihr Kunstwerk als digitale Datei ohne Wasserzeichen, im Stil Ihrer Wahl: ${SQUARE} bei einem Auge, bei mehreren Augen ${PX} an der längsten Seite.`,
      },
      {
        q: 'Wie lange dauert es?',
        a: 'Die kostenlose Vorschau dauert etwa eine Minute. Sobald Bestellungen möglich sind, wird Ihre Datei nach Ihrer Freigabe einmalig in voller Auflösung berechnet. Das dauert etwa eine halbe Minute pro Auge.',
      },
      {
        q: 'Wann kann ich bestellen?',
        a: 'Bestellungen sind in Kürze möglich. Bis dahin ist die Vorschau kostenlos.',
      },
    ],
  },
  final: {
    title: 'Sehen Sie Ihre eigene Iris',
    body: 'Sie brauchen nur Ihr Smartphone, gutes Licht und etwa eine Minute.',
  },
  footer: {
    operatedBy: 'SnapEyes wird betrieben von',
    company: 'MB „Portretizuokis“',
    companyCode: 'Unternehmenscode',
    country: 'Litauen',
    contact: 'Kontakt',
    rights: 'SnapEyes',
  },
};

export const COPY: Record<Lang, Copy> = { en, de };

export function formatEuro(cents: number, lang: Lang): string {
  return new Intl.NumberFormat(lang === 'de' ? 'de-DE' : 'en-IE', { style: 'currency', currency: 'EUR' }).format(cents / 100);
}
