// All landing page copy, English and German (formal "Sie"). Every sentence must stay true today:
// no reviews, customer counts, guarantees, awards, physical products or purchase buttons.
// Lines about ordering come in two forms: the plain one while ordering is not open, and an *Open one that the page
// swaps in once this deployment takes orders (src/landing/ordering.ts asks the API, as /try does). The meta
// description names neither, because it is read before that answer arrives.
import type { StyleId } from './config';
import { WITHDRAWAL_ONLINE, legalEdition } from '../shared/legal';
import type { Currency, Market } from '../shared/markets';
import type { Lang } from '../shared/lang';
import { lt } from './copy.lt';
import { hu } from './copy.hu';

export type { Lang };

export interface Copy {
  meta: { title: string; description: string; shareDescription: string; locale: string };
  langName: string;
  switchLabel: string;
  brandTag: string;
  nav: { beforeAfter: string; how: string; styles: string; pricing: string; faq: string; privacy: string };
  navLabels: { main: string; footer: string };
  cta: string;
  ctaShort: string;
  // A quiet line under the main calls to action; '' shows nothing (/try speaks both languages now).
  ctaNote: string;
  hero: {
    eyebrow: string;
    title: string;
    lead: string;
    points: string[];
    soon: string;
    // the same line once ordering is open, with the lowest price ("from ...")
    ready: (from: string) => string;
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
    steps: Array<{ title: string; body: string; bodyOpen?: string }>;
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
    noticeOpen: string;
    previewTitle: string;
    previewPrice: string;
    previewItems: string[];
    oneEyeTitle: string;
    oneEyeNote: string;
    // the row of the black price class is named by its one style (src/shared/styles.ts classStyle), the other by this text; the note under it and the
    // sentence of the group card take their list of styles and their number of eyes from the run-time catalogue (src/shared/catalogue.ts): {styles}, {max}
    artBackground: string;
    artBackgroundNote: string;
    severalTitle: string;
    severalNote: string;
    severalSoon: string;
    eyes: (n: number) => string;
    perEye: (price: string, max: number) => string;
    // the line under the prices, by the currency of the visitor's market (src/shared/markets.ts): footnote for
    // euros, the others for Australian dollars and forints; each names the currency and what is (not) added
    footnote: string;
    footnoteAud: string;
    footnoteHuf: string;
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
    // the link to the full privacy policy (src/legal, /privacy)
    policyLink: string;
  };
  faq: {
    eyebrow: string;
    title: string;
    items: Array<{ q: string; a: string; qOpen?: string; aOpen?: string }>;
  };
  final: { title: string; body: string };
  footer: {
    operatedBy: string;
    company: string;
    companyCode: string;
    country: string;
    contact: string;
    // printed only when SELLER.representative / SELLER.phone are set (src/landing/config.ts)
    representedBy: string;
    phone: string;
    rights: string;
    // the currency switch (the visitor's market, src/shared/markets.ts): shown when the site sells in more than one
    currency: string;
  };
  // the offer of the visitor's own currency (./MarketHint.tsx): shown only when the server's country hint names a
  // market in another currency, until the visitor takes it or closes it; one text per currency it can offer
  marketHint: { label: string; close: string } & Partial<Record<Currency, { text: string; show: string }>>;
}

const TRANSPARENCY_EN = 'Colour from your own photo. Where your phone could not capture the finest fibres, our AI restores them.';
const TRANSPARENCY_DE = 'Die Farbe stammt aus Ihrem eigenen Foto. Wo Ihr Smartphone die feinsten Fasern nicht erfassen konnte, stellt unsere KI sie wieder her.';

// Measured deliverable (api/master_compose.py, L.multi_canvas at 4096): one eye is 4096 x 4096 px; several
// eyes are 4096 px on the longest side (a pair is 4096 x 2731). Never promise a square file for all orders.
const PX = '4096\u00a0px';
const SQUARE = '4096\u00a0×\u00a04096\u00a0px';

// The withdrawal question of the FAQ: the Australian market answers it in its own words (copyFor below).
const WITHDRAW_Q: Record<'en' | 'de', string> = { en: 'Can I withdraw from an order?', de: 'Kann ich eine Bestellung widerrufen?' };

const en: Copy = {
  meta: {
    title: 'SnapEyes Private Atelier - Precision Iris Art from Your Smartphone',
    description:
      "Photograph one eye with your phone's back camera and see your own iris as fine art in a choice of styles. The watermarked preview is free.",
    shareDescription: 'Photograph one eye with your phone and see your own iris as fine art in a choice of styles. The watermarked preview is free.',
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
    points: ['Free watermarked preview of every style', 'About a minute, no sign-up'],
    soon: `Soon: your artwork as a ${PX} digital file`,
    ready: (from) => `Your artwork as a ${PX} digital file, from ${from}`,
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
      "This is the founder's own eye. On the left, the phone photo cropped to the iris at its original 315\u00a0px. On the right, the same eye in Clean Iris, rendered by the engine that makes your preview.",
    before: 'Before: phone photo',
    after: 'After: Clean Iris',
    beforeAlt: "Before: the founder's eye as the phone captured it",
    afterAlt: 'After: the same eye rendered in Clean Iris',
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
        body: 'Use the back camera at 2x or 3x zoom, not the selfie camera. Daylight from a window, off to one side, about 10\u00a0cm away. Take three to five shots; we measure every shot and use the best one.',
      },
      {
        title: 'See your free preview',
        body: 'In about a minute your iris appears in every style, with a watermark. No sign-up, nothing to pay.',
      },
      {
        title: `Order your ${PX} file`,
        body: `Choose a style and receive your artwork as a digital file, ${PX} on its longest side, rendered once in full resolution when you approve it. Ordering opens soon.`,
        bodyOpen: `Choose a style, pay through Stripe and receive your artwork as a digital file, ${PX} on its longest side, made once in full resolution as soon as your order is confirmed.`,
      },
    ],
  },
  styles: {
    eyebrow: 'Styles',
    title: 'The same eye, in different styles',
    intro:
      "Every image below is the founder's eye from the before and after above, rendered by our engine in each style. Your preview adds a watermark, which is left out here.",
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
    noticeOpen: 'Start with the free preview: you order only once you like the result.',
    previewTitle: 'Preview',
    previewPrice: 'Free',
    previewItems: ['Every style', 'With watermark', 'Available today'],
    oneEyeTitle: 'One eye',
    oneEyeNote: 'Your iris as one artwork, in the style you choose.',
    artBackground: 'Any other style',
    artBackgroundNote: '{styles}',
    severalTitle: 'Several eyes',
    severalNote: 'Two to {max} eyes on one artwork: yours and those of the people you love.',
    severalSoon: 'Free preview now. Ordering for this group opens soon.',
    eyes: (n) => `${n} eyes`,
    perEye: (price, max) => `+${price} for each further eye, up to ${max} eyes`,
    footnote: `Every order is one digital file without watermark, ${PX} on its longest side (${SQUARE} for one eye). Prices in euros. These are final prices: we are not registered for VAT, so no VAT is added.`,
    footnoteAud: `Every order is one digital file without watermark, ${PX} on its longest side (${SQUARE} for one eye). Prices in Australian dollars (A$). Each price is the total price: no GST is charged.`,
    footnoteHuf: `Every order is one digital file without watermark, ${PX} on its longest side (${SQUARE} for one eye). Prices in Hungarian forints (Ft). These are final prices: we are not registered for VAT, so no VAT is added.`,
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
      { title: 'Only for your artwork', body: 'Your photo is used only to make your artwork. From each shot we log a few measurements, never the image, to improve the capture guide.' },
      { title: 'Never for identification', body: 'It is never used to identify anyone, never sold and not used to train AI.' },
      {
        title: 'Free previews are not kept',
        body: "Your photo is processed and then discarded; we do not store it. If you order, we keep your order's files (not your phone photo) for 12 months, for downloads.",
      },
      {
        title: 'A few outside services',
        body: "Vercel runs the page and the preview, Google's Gemini API the restoration (Google keeps request logs for a limited time). Orders add Stripe for payment and a private Supabase store in the EU.",
      },
    ],
    controller: 'Responsible for your data: MB "Portretizuokis", Kaunas, Lithuania (full details at the foot of this page).',
    rights: 'You may ask what data we hold about you, have it corrected or deleted, and complain to a data protection authority.',
    policyLink: 'Read the full privacy policy',
  },
  faq: {
    eyebrow: 'Questions',
    title: 'Before you start',
    items: [
      {
        q: 'Which phone and camera should I use?',
        a: 'Any recent smartphone with a good back camera. Use the back camera at 2x or 3x zoom, not the selfie camera. Use daylight from a window, off to one side, not a lamp or the flash. Hold the phone about 10\u00a0cm from your eye, tap the iris to focus and take three to five shots.',
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
        aOpen: 'The free preview takes about a minute. After you pay, your file is rendered once in full resolution, usually in about half a minute per eye.',
      },
      {
        q: 'What happens to my photo?',
        a: 'For the free preview, your photo is processed and then discarded; we do not store it. When you order, we keep the files of your order (not your phone photo) for 12 months so you can download them again, and then delete them. Your iris is never used to identify anyone or to train AI. The details are in our privacy policy, linked at the foot of this page.',
      },
      {
        q: WITHDRAW_Q.en,
        a: `We start making your file as soon as your order confirmation email has gone out, normally within a minute of your payment. Before paying, you agree that we start straight away, so the 14-day right of withdrawal ends once we have started making your file. Until then you can withdraw by email or online with "${WITHDRAWAL_ONLINE.en.button}", at the foot of this page or through the withdrawal link in your order confirmation email. If your file is defective or clearly differs from the preview you approved, write to us: we render it again or refund you. The details are in our terms of sale and the withdrawal information, linked at the foot of this page.`,
      },
      {
        q: 'When can I order?',
        a: 'Ordering opens soon. Until then the preview is free.',
        qOpen: 'How do I order?',
        aOpen: "Right after your free preview, on the same page: choose your style, tick the box about the digital file and continue to Stripe's payment page, where you pay. Your order page opens straight away, and its link comes by email.",
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
    representedBy: 'Represented by',
    phone: 'Phone',
    rights: 'SnapEyes',
    currency: 'Prices in',
  },
  marketHint: {
    label: 'Prices in your currency',
    close: 'No thanks',
    aud: {
      text: 'Shopping from Australia? See our prices in Australian dollars (A$), with our terms for Australia.',
      show: 'Show prices in A$',
    },
    huf: {
      text: 'Shopping from Hungary? See our prices in Hungarian forints (Ft).',
      show: 'Show prices in Ft',
    },
  },
};

const de: Copy = {
  meta: {
    title: 'SnapEyes Private Atelier - Präzise Iris-Kunst vom Smartphone',
    description:
      'Fotografieren Sie ein Auge mit der Rückkamera Ihres Smartphones und sehen Sie Ihre eigene Iris als Kunstwerk in einer Auswahl von Stilen. Die Vorschau mit Wasserzeichen ist kostenlos.',
    shareDescription:
      'Fotografieren Sie ein Auge mit dem Smartphone und sehen Sie Ihre eigene Iris als Kunstwerk in einer Auswahl von Stilen. Die Vorschau mit Wasserzeichen ist kostenlos.',
    locale: 'de_DE',
  },
  langName: 'Deutsch',
  switchLabel: 'Sprache',
  brandTag: 'Private Atelier',
  nav: { beforeAfter: 'Vorher/Nachher', how: 'Ablauf', styles: 'Stile', pricing: 'Preise', faq: 'Fragen', privacy: 'Datenschutz' },
  navLabels: { main: 'Hauptnavigation', footer: 'Fußzeile' },
  cta: 'Kostenlose Vorschau erstellen',
  ctaShort: 'Gratis-Vorschau',
  // /try is German too now (src/try/copy.ts de): nothing to note under the calls to action
  ctaNote: '',
  hero: {
    eyebrow: 'SnapEyes Private Atelier',
    title: 'Präzise Iris-Kunst vom Smartphone',
    lead:
      'Fotografieren Sie ein Auge mit der Rückkamera Ihres Smartphones. Wir finden Ihre Iris, restaurieren sie und setzen sie im Stil Ihrer Wahl in Szene. Das Ergebnis sehen Sie zuerst, und zwar kostenlos.',
    points: ['Kostenlose Vorschau jedes Stils, mit Wasserzeichen', 'Etwa eine Minute, ohne Anmeldung'],
    soon: `Bald: Ihr Kunstwerk als digitale Datei mit ${PX}`,
    ready: (from) => `Ihr Kunstwerk als digitale Datei mit ${PX}, ab ${from}`,
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
      'Das ist das Auge des Gründers. Links das Smartphone-Foto, auf die Iris zugeschnitten, in der Originalgröße von 315\u00a0px. Rechts dasselbe Auge im Stil Clean Iris, gerendert von derselben Software, die auch Ihre Vorschau erstellt.',
    before: 'Vorher: Smartphone-Foto',
    after: 'Nachher: Clean Iris',
    beforeAlt: 'Vorher: das Auge des Gründers, so wie das Smartphone es aufgenommen hat',
    afterAlt: 'Nachher: dasselbe Auge im Stil Clean Iris',
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
        body: 'Nutzen Sie die Rückkamera mit 2- oder 3-fachem Zoom, nicht die Selfie-Kamera. Tageslicht von einem Fenster, seitlich, etwa 10\u00a0cm Abstand. Machen Sie drei bis fünf Aufnahmen, wir prüfen jede davon und verwenden die beste.',
      },
      {
        title: 'Kostenlose Vorschau ansehen',
        body: 'Nach etwa einer Minute sehen Sie Ihre Iris in jedem Stil, mit Wasserzeichen. Ohne Anmeldung und ohne Kosten.',
      },
      {
        title: `Datei mit ${PX} bestellen`,
        body: `Wählen Sie einen Stil und erhalten Sie Ihr Kunstwerk als digitale Datei mit ${PX} an der längsten Seite. Sie wird einmalig in voller Auflösung erstellt, sobald Sie das Motiv freigeben. Bestellungen sind in Kürze möglich.`,
        bodyOpen: `Wählen Sie einen Stil, bezahlen Sie über Stripe und erhalten Sie Ihr Kunstwerk als digitale Datei mit ${PX} an der längsten Seite, einmalig in voller Auflösung erstellt, sobald Ihre Bestellung bestätigt ist.`,
      },
    ],
  },
  styles: {
    eyebrow: 'Stile',
    title: 'Dasselbe Auge, in verschiedenen Stilen',
    intro:
      'Jedes Bild hier zeigt das Auge des Gründers aus dem Vorher/Nachher oben, von unserer Software in jedem Stil gerendert. Ihre Vorschau trägt ein Wasserzeichen; hier ist es weggelassen.',
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
    noticeOpen: 'Beginnen Sie mit der kostenlosen Vorschau: Sie bestellen erst, wenn Ihnen das Ergebnis gefällt.',
    previewTitle: 'Vorschau',
    previewPrice: 'Kostenlos',
    previewItems: ['Jeder Stil', 'Mit Wasserzeichen', 'Schon heute verfügbar'],
    oneEyeTitle: 'Ein Auge',
    oneEyeNote: 'Ihre Iris als einzelnes Kunstwerk, im Stil Ihrer Wahl.',
    artBackground: 'Jeder andere Stil',
    artBackgroundNote: '{styles}',
    severalTitle: 'Mehrere Augen',
    severalNote: 'Zwei bis {max} Augen auf einem Kunstwerk, etwa Ihr eigenes und die Ihrer Liebsten.',
    severalSoon: 'Die Vorschau ist schon jetzt kostenlos. Die Bestellung für diese Gruppe ist bald möglich.',
    eyes: (n) => `${n} Augen`,
    perEye: (price, max) => `+${price} für jedes weitere Auge, bis zu ${max} Augen`,
    footnote: `Jede Bestellung ist eine digitale Datei ohne Wasserzeichen, mit ${PX} an der längsten Seite (${SQUARE} bei einem Auge). Preise in Euro. Es sind Endpreise: Wir sind nicht umsatzsteuerlich registriert, daher wird keine Umsatzsteuer berechnet.`,
    footnoteAud: `Jede Bestellung ist eine digitale Datei ohne Wasserzeichen, mit ${PX} an der längsten Seite (${SQUARE} bei einem Auge). Preise in australischen Dollar (A$). Jeder Preis ist der Gesamtpreis: Es wird keine GST berechnet.`,
    footnoteHuf: `Jede Bestellung ist eine digitale Datei ohne Wasserzeichen, mit ${PX} an der längsten Seite (${SQUARE} bei einem Auge). Preise in ungarischen Forint (Ft). Es sind Endpreise: Wir sind nicht umsatzsteuerlich registriert, daher wird keine Umsatzsteuer berechnet.`,
  },
  curator: {
    eyebrow: 'Der Kurator',
    title: 'Hinter dem Atelier',
    role: 'Kurator des SnapEyes-Studios',
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
      { title: 'Nur für Ihr Kunstwerk', body: 'Ihr Foto dient nur dazu, Ihr Kunstwerk zu erstellen. Von jeder Aufnahme protokollieren wir einige Messwerte, nie das Bild, um die Aufnahmeanleitung zu verbessern.' },
      { title: 'Nie zur Identifizierung', body: 'Es wird nie genutzt, um jemanden zu identifizieren, nie verkauft und nicht zum Training von KI verwendet.' },
      {
        title: 'Vorschauen werden nicht gespeichert',
        body: 'Ihr Foto wird verarbeitet und danach verworfen; wir speichern es nicht. Wenn Sie bestellen, bewahren wir die Dateien Ihrer Bestellung (nicht Ihr Smartphone-Foto) 12 Monate für Ihre Downloads auf.',
      },
      {
        title: 'Wenige externe Dienste',
        body: 'Vercel betreibt die Seite und die Vorschau, die Gemini-API von Google die Restaurierung (Google speichert Anfrageprotokolle für begrenzte Zeit). Bei Bestellungen kommen Stripe für die Zahlung und ein privater Supabase-Speicher in der EU hinzu.',
      },
    ],
    controller: 'Verantwortlich für Ihre Daten: MB „Portretizuokis“, Kaunas, Litauen (vollständige Angaben am Ende dieser Seite).',
    rights: 'Sie können Auskunft über Ihre Daten verlangen, sie berichtigen oder löschen lassen und sich bei einer Datenschutzbehörde beschweren.',
    policyLink: 'Vollständige Datenschutzerklärung lesen',
  },
  faq: {
    eyebrow: 'Fragen',
    title: 'Bevor Sie beginnen',
    items: [
      {
        q: 'Welches Smartphone und welche Kamera brauche ich?',
        a: 'Jedes aktuelle Smartphone mit guter Rückkamera. Nutzen Sie die Rückkamera mit 2- oder 3-fachem Zoom, nicht die Selfie-Kamera. Nutzen Sie Tageslicht von einem Fenster, seitlich von Ihnen, keine Lampe und keinen Blitz. Halten Sie das Smartphone etwa 10\u00a0cm vor Ihr Auge, tippen Sie zum Scharfstellen auf die Iris und machen Sie drei bis fünf Aufnahmen.',
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
        a: 'Die kostenlose Vorschau dauert etwa eine Minute. Sobald Bestellungen möglich sind, wird Ihre Datei nach Ihrer Freigabe einmalig in voller Auflösung erstellt. Das dauert etwa eine halbe Minute pro Auge.',
        aOpen: 'Die kostenlose Vorschau dauert etwa eine Minute. Nach der Zahlung wird Ihre Datei einmalig in voller Auflösung erstellt, meist in etwa einer halben Minute pro Auge.',
      },
      {
        q: 'Was passiert mit meinem Foto?',
        a: 'Für die kostenlose Vorschau wird Ihr Foto verarbeitet und danach verworfen; wir speichern es nicht. Wenn Sie bestellen, bewahren wir die Dateien Ihrer Bestellung (nicht Ihr Smartphone-Foto) 12 Monate auf, damit Sie sie erneut herunterladen können, und löschen sie danach. Ihre Iris wird nie zur Identifizierung oder zum Training von KI verwendet. Einzelheiten finden Sie in unserer Datenschutzerklärung, verlinkt am Ende dieser Seite.',
      },
      {
        q: WITHDRAW_Q.de,
        a: `Wir beginnen mit der Erstellung Ihrer Datei, sobald Ihre Bestellbestätigung per E-Mail versandt ist, normalerweise innerhalb einer Minute nach Ihrer Zahlung. Vor der Zahlung stimmen Sie zu, dass wir sofort beginnen; das 14-tägige Widerrufsrecht erlischt daher, sobald wir mit der Erstellung Ihrer Datei begonnen haben. Bis dahin können Sie per E-Mail oder online mit „${WITHDRAWAL_ONLINE.de.button}“ widerrufen, am Ende dieser Seite oder über den Widerrufslink in Ihrer Bestellbestätigung per E-Mail. Ist Ihre Datei mangelhaft oder weicht sie deutlich von der freigegebenen Vorschau ab, schreiben Sie uns: Wir erstellen sie neu oder erstatten Ihnen den Preis. Einzelheiten stehen in unseren AGB und der Widerrufsbelehrung, verlinkt am Ende dieser Seite.`,
      },
      {
        q: 'Wann kann ich bestellen?',
        a: 'Bestellungen sind in Kürze möglich. Bis dahin ist die Vorschau kostenlos.',
        qOpen: 'Wie bestelle ich?',
        aOpen: 'Direkt nach Ihrer kostenlosen Vorschau, auf derselben Seite: Wählen Sie Ihren Stil, setzen Sie das Häkchen zur digitalen Datei und gehen Sie weiter zur Zahlungsseite von Stripe, auf der Sie bezahlen. Danach öffnet sich sofort Ihre Bestellseite, und ihren Link erhalten Sie per E-Mail.',
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
    representedBy: 'Vertreten durch',
    phone: 'Telefon',
    rights: 'SnapEyes',
    currency: 'Preise in',
  },
  marketHint: {
    label: 'Preise in Ihrer Währung',
    close: 'Nein, danke',
    aud: {
      text: 'Sie kaufen aus Australien? Sehen Sie unsere Preise in australischen Dollar (A$), mit unseren Bedingungen für Australien.',
      show: 'Preise in A$ anzeigen',
    },
    huf: {
      text: 'Sie kaufen aus Ungarn? Sehen Sie unsere Preise in ungarischen Forint (Ft).',
      show: 'Preise in Ft anzeigen',
    },
  },
};

export const COPY: Record<Lang, Copy> = { en, de, lt, hu };

// The Australian market's lines (src/shared/legal.ts legalEdition "au"), in place of the language's own: the FAQ answer
// about cancelling keeps the Australian Consumer Law (its guarantees cannot be excluded, so nothing may read as "no
// refunds", and no promise of our own to redo a faulty file: see src/legal/docs/terms.ts TERMS_AU) and frames the
// 14-day right as EU law. The rest of the copy is already written in Australian (British) spelling: colour,
// personalised, licence. Prices and their footnote follow the currency (pricing.footnoteAud).
const AU_FAQ: Record<'en' | 'de', { q: string; a: string }> = {
  en: {
    q: 'Can I cancel an order?',
    a: `We start making your file as soon as your order confirmation email has gone out, normally within a minute of your payment. Before paying, you agree that we start straight away, so the 14-day right of withdrawal under EU consumer law, which applies to your order, ends once we have started making your file. Until then you can cancel by email or online with "${WITHDRAWAL_ONLINE.en.button}", at the foot of this page or through the withdrawal link in your order confirmation email, and we refund you in full. That is only about changing your mind: our services come with guarantees that cannot be excluded under the Australian Consumer Law, so if your file is faulty or clearly differs from the preview you approved, write to us. The details are in our terms of sale (Your rights in Australia) and the withdrawal information, linked at the foot of this page.`,
  },
  de: {
    q: 'Kann ich eine Bestellung stornieren?',
    a: `Wir beginnen mit der Erstellung Ihrer Datei, sobald Ihre Bestellbestätigung per E-Mail versandt ist, normalerweise innerhalb einer Minute nach Ihrer Zahlung. Vor der Zahlung stimmen Sie zu, dass wir sofort beginnen; das 14-tägige Widerrufsrecht nach dem EU-Verbraucherrecht, das für Ihre Bestellung gilt, erlischt daher, sobald wir mit der Erstellung Ihrer Datei begonnen haben. Bis dahin können Sie per E-Mail oder online mit „${WITHDRAWAL_ONLINE.de.button}“ widerrufen, am Ende dieser Seite oder über den Widerrufslink in Ihrer Bestellbestätigung per E-Mail, und wir erstatten Ihnen den vollen Preis. Das betrifft nur eine Meinungsänderung: Unsere Leistungen sind mit Garantien verbunden, die nach dem Australian Consumer Law nicht ausgeschlossen werden können. Ist Ihre Datei mangelhaft oder weicht sie deutlich von der freigegebenen Vorschau ab, schreiben Sie uns. Einzelheiten stehen in unseren AGB (Ihre Rechte in Australien) und der Widerrufsbelehrung, verlinkt am Ende dieser Seite.`,
  },
};

// The Australian market has English and German pages only (src/shared/legal.ts EDITION_LANGS)
const COPY_AU: Partial<Record<Lang, Copy>> = {
  en: { ...en, faq: { ...en.faq, items: en.faq.items.map((it) => (it.q === WITHDRAW_Q.en ? { ...it, ...AU_FAQ.en } : it)) } },
  de: { ...de, faq: { ...de.faq, items: de.faq.items.map((it) => (it.q === WITHDRAW_Q.de ? { ...it, ...AU_FAQ.de } : it)) } },
};

/** The landing copy for a language and the visitor's market: the language's own, with the Australian lines for au. */
export function copyFor(lang: Lang, market: Market): Copy {
  return legalEdition(market) === 'au' ? COPY_AU[lang] ?? COPY[lang] : COPY[lang];
}

/** The price line under the price cards, in the words of the market's currency. */
export function priceFootnote(p: Copy['pricing'], currency: Currency): string {
  return currency === 'aud' ? p.footnoteAud : currency === 'huf' ? p.footnoteHuf : p.footnote;
}
