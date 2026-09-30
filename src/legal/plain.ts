// The terms of sale and the withdrawal information (with the model withdrawal form) as plain text, for the order
// confirmation email. A web page is not a durable medium (CJEU C-49/11), and Art. 8(7) Directive 2011/83/EU and
// § 312f Abs. 2 BGB want this information in the confirmation itself; the early end of the right of withdrawal
// (Art. 16(m), § 356 Abs. 5 BGB) depends on that confirmation too.
// The build writes legalMailPack() to /legal/order-mail.json (vite.config.ts), made from the very constants the legal
// pages print, so the email can never drift from them: the sender (api/_lib/pay.py) reads that file of its own
// deployment and puts the texts of the order's language into the email. Plain data only, no React, no DOM.
// The other editions (src/shared/legal.ts legalEdition: "au", the Australian market's, and "hu", the Hungarian market's
// with the prices in forints) travel apart, under "editions": {"au": ..., "hu": ...}, with every link to a legal page
// carrying m=au / m=hu, so an order's email quotes (and links) the texts its customer accepted; "docs" stays the EU
// edition, as before, with plain links. Languages: English, German, Lithuanian and Hungarian for the EU and Hungarian
// editions, English and German for the Australian one (src/shared/legal.ts EDITION_LANGS).
import type { Lang } from '../shared/lang';
import type { Block, LegalDoc } from './types';
import {
  EDITION_LANGS, EDITION_MARKETS, LEGAL_PATH, LEGAL_UPDATED, SITE_HOST, formatLegalDate, legalHref, type LegalDocId, type LegalEdition,
} from '../shared/legal';
import { DEFAULT_MARKET } from '../shared/markets';
import { CONTACT_EMAIL, PHONE_OMITTED_BY_OWNER, SELLER, address, company, formLine } from './facts';
import { EDITIONS } from './editions';

const ORIGIN = `https://${SITE_HOST}`;
const TOKEN = /\[([^\]]+)\]\(([^)\s]+)\)|\*\*([^*]+)\*\*/g;
const SHY = /\u00AD/g;

/** The inline markup of src/legal/types.ts as text: a link keeps its label and shows where it goes (a link to a legal
 *  page carries the edition's market: m=au for the Australian edition, nothing for the EU one). */
function inline(text: string, lang: Lang, page: LegalDocId, market: string = DEFAULT_MARKET): string {
  return text.replace(TOKEN, (_m: string, label: string | undefined, href: string | undefined, bold: string | undefined) => {
    if (bold !== undefined) return bold;
    const l = label ?? '';
    const h = href ?? '';
    if (h.startsWith('mailto:')) {
      const addr = h.slice(7).split('?')[0];
      return l === addr ? l : `${l} (${addr})`;
    }
    let url = h;
    if (h.startsWith('doc:')) {
      const [doc, section = ''] = h.slice(4).split('#');
      if (doc in LEGAL_PATH) url = ORIGIN + legalHref(doc as LegalDocId, lang, section, market);
    } else if (h.startsWith('#')) {
      url = ORIGIN + legalHref(page, lang, h.slice(1), market);
    } else if (h.startsWith('/')) {
      url = ORIGIN + h;          // a page of the site, such as the online withdrawal function
    }
    // a label that is the address itself, with or without https:// (the online withdrawal function's address in
    // the statutory sentence), prints once, as the full address
    if (url === l || url === `https://${l}`) return url;
    return `${l} (${url})`;
  });
}

function block(b: Block, lang: Lang, page: LegalDocId, market: string): string {
  if (typeof b === 'string') return inline(b, lang, page, market);
  if ('ul' in b) return b.ul.map((li) => `- ${inline(li, lang, page, market)}`).join('\n');
  if ('dl' in b) return b.dl.map(([term, value]) => `${term}: ${inline(value, lang, page, market)}`).join('\n');
  const lines = b.box.map((line) => `    ${inline(line, lang, page, market)}`);
  return (b.label ? [`${b.label}:`, ...lines] : lines).join('\n');
}

/** The words before the date under a legal text's title in the email ("Last updated: 2026-09-30"). */
const UPDATED: Record<Lang, string> = { en: 'Last updated:', de: 'Stand:', lt: 'Atnaujinta:', hu: 'Utolsó frissítés:' };

/** One legal page as plain text: title, date, address of the page, lead, then the sections. Paragraphs are separated
 *  by an empty line and never wrapped (mail clients wrap them). */
export function legalPlainText(id: LegalDocId, doc: LegalDoc, lang: Lang, market: string = DEFAULT_MARKET): string {
  const updated = `${UPDATED[lang]} ${formatLegalDate(LEGAL_UPDATED, lang)}`;
  const out: string[] = [doc.title.replace(SHY, '').toUpperCase(), `${updated} · ${ORIGIN}${legalHref(id, lang, '', market)}`];
  if (doc.lead) out.push(inline(doc.lead, lang, id, market));
  doc.sections.forEach((s, i) => {
    out.push(`${doc.numbered ? `${i + 1}. ` : ''}${s.title.replace(SHY, '')}`);
    for (const b of s.blocks) out.push(block(b, lang, id, market));
  });
  return out.join('\n\n');
}

export interface LegalMailDoc { title: string; url: string; text: string }

/** Everything the order confirmation email needs, per language, from the constants the legal pages print. */
export interface LegalMailPack {
  updated: string;
  seller: {
    name: string;
    code: string;
    email: string;
    phone: string;          // '' while no phone is shown (owner decision: PHONE_OMITTED_BY_OWNER)
    representative: string; // '' until the owner sets SELLER.representative
    company: Record<Lang, string>;
    address: Record<Lang, string>;
    contact: Record<Lang, string>; // company, address, email: the model form's "To:" line (formLine, never a phone)
  };
  docs: Record<Lang, { withdrawal: LegalMailDoc; terms: LegalMailDoc }>;
  /** The other editions ("au", the Australian market's, in English and German; "hu", the Hungarian market's, in every
   *  language), the same shape as docs: api/_lib/pay.py quotes them for an order of that market and keeps live
   *  ordering closed while one of a selectable market is missing. */
  editions: { au: Partial<Record<Lang, { withdrawal: LegalMailDoc; terms: LegalMailDoc }>>; hu: Record<Lang, { withdrawal: LegalMailDoc; terms: LegalMailDoc }> };
  /** Facts the law requires in these texts that are still empty and that nobody decided to leave out, as
   *  "seller.email": [] when complete. api/_lib/pay.py may keep live ordering closed while this list is not empty.
   *  The representative is never in it: no rule that applies to a Lithuanian seller requires the name. */
  missing: string[];
  /** Facts the law asks for that the OWNER decided to leave out, with the risk accepted: today ["seller.phone"]
   *  (Art. 6(1)(c) Directive 2011/83/EU; Art. 246a § 1 Abs. 1 Nr. 2 EGBGB; Anlage 1 EGBGB Gestaltungshinweis 2; see
   *  PHONE_OMITTED_BY_OWNER in src/landing/config.ts). Not a reason to keep ordering closed; listed so that the owner's
   *  tools can still show the gap. */
  waived: string[];
}

const LANGS: Lang[] = ['en', 'de', 'lt', 'hu'];
const per = <T,>(f: (lang: Lang) => T, langs: readonly Lang[] = LANGS) => Object.fromEntries(langs.map((l) => [l, f(l)])) as Record<Lang, T>;

function mailDoc(id: LegalDocId, doc: LegalDoc, lang: Lang, market: string = DEFAULT_MARKET): LegalMailDoc {
  return {
    title: doc.title.replace(SHY, ''), url: ORIGIN + legalHref(id, lang, '', market), text: legalPlainText(id, doc, lang, market),
  };
}

/** The withdrawal information and the terms of an edition in a language, as the email quotes them (an edition with
 *  its own market: links carrying m=). A text an edition lacks stops the build. */
function editionDocs(edition: LegalEdition, lang: Lang): { withdrawal: LegalMailDoc; terms: LegalMailDoc } {
  const market = edition === 'eu' ? DEFAULT_MARKET : EDITION_MARKETS[edition];
  const w = EDITIONS[edition].withdrawal[lang];
  const t = EDITIONS[edition].terms[lang];
  if (!w || !t) throw new Error(`legal pack: the ${edition} edition has no ${lang} texts`);
  return { withdrawal: mailDoc('withdrawal', w, lang, market), terms: mailDoc('terms', t, lang, market) };
}

/** The legally required seller facts that are still empty and not left out by the owner's decision (see
 *  LegalMailPack.missing). */
export function missingLegalFacts(): string[] {
  const out: string[] = [];
  if (!SELLER.phone.trim() && !PHONE_OMITTED_BY_OWNER) out.push('seller.phone');
  if (!CONTACT_EMAIL.trim()) out.push('seller.email');
  if (!SELLER.name.trim() || !SELLER.code.trim() || !SELLER.street.trim() || !SELLER.postcode.trim() || !SELLER.city.trim()) {
    out.push('seller.address');
  }
  return out;
}

/** The legally asked-for seller facts the owner decided to leave out (see LegalMailPack.waived). */
export function waivedLegalFacts(): string[] {
  return !SELLER.phone.trim() && PHONE_OMITTED_BY_OWNER ? ['seller.phone'] : [];
}

export function legalMailPack(): LegalMailPack {
  return {
    updated: LEGAL_UPDATED,
    seller: {
      name: SELLER.name,
      code: SELLER.code,
      email: CONTACT_EMAIL,
      phone: SELLER.phone,
      representative: SELLER.representative,
      company: per(company),
      address: per(address),
      contact: per(formLine),
    },
    docs: per((lang) => editionDocs('eu', lang)),
    editions: {
      au: per((lang) => editionDocs('au', lang), EDITION_LANGS.au),
      hu: per((lang) => editionDocs('hu', lang), EDITION_LANGS.hu),
    },
    missing: missingLegalFacts(),
    waived: waivedLegalFacts(),
  };
}
