// LAB: the few words of the centrepiece prototypes. The three provenance lines are the landing's own (src/landing/copy/<lang>.json styles.own,
// styles.licensed, styles.mixed); the button is new (the brief's "Try it with your eye"), the German and Hungarian ones not yet read by a native speaker.
// Nothing else is printed on the centrepiece: the style's name comes from the registry, the rest are labels for assistive technology.
import type { Prov } from './art';

export type Lang = 'en' | 'de' | 'lt' | 'hu';

export interface Words {
  cta: string;
  prov: Record<Prov, string>;
  /** the name of the whole centrepiece, for assistive technology */
  group: string;
  /** the label of the enlarged artwork, which closes it */
  close: string;
}

export const WORDS: Record<Lang, Words> = {
  en: {
    cta: 'Try it with your eye',
    prov: { own: 'Our own eye', licensed: 'Example photo, not a customer', mixed: 'Our own eye and example photos, not customers' },
    group: 'Style examples',
    close: 'Close',
  },
  de: {
    cta: 'Mit Ihrem Auge ausprobieren',
    prov: { own: 'Unser eigenes Auge', licensed: 'Beispielfoto, kein Kunde', mixed: 'Unser eigenes Auge und Beispielfotos, keine Kunden' },
    group: 'Stilbeispiele',
    close: 'Schließen',
  },
  lt: {
    cta: 'Išbandykite su savo akimi',
    prov: { own: 'Mūsų pačių akis', licensed: 'Pavyzdinė nuotrauka, ne kliento', mixed: 'Mūsų pačių akis ir pavyzdinės nuotraukos, ne klientų' },
    group: 'Stilių pavyzdžiai',
    close: 'Uždaryti',
  },
  hu: {
    cta: 'Próbáld ki a saját szemeddel',
    prov: { own: 'A saját szemünk', licensed: 'Példafotó, nem vásárló', mixed: 'A saját szemünk és példafotók, nem vásárlók' },
    group: 'Stíluspéldák',
    close: 'Bezárás',
  },
};
