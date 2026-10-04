// The terms of sale and the withdrawal information (with the model withdrawal form) as plain text, for the order
// confirmation email. A web page is not a durable medium (CJEU C-49/11), and Art. 8(7) Directive 2011/83/EU and
// § 312f Abs. 2 BGB want this information in the confirmation itself; the early end of the right of withdrawal
// (Art. 16(m), § 356 Abs. 5 BGB) depends on that confirmation too.
// The build writes legalMailPack() to /legal/order-mail.json (vite.config.ts), made from the very constants the legal
// pages print, so the email can never drift from them: the sender (api/_lib/pay.py) reads that file of its own
// deployment and puts the texts of the order's language into the email. Plain data only, no React, no DOM.
import type { Lang } from '../landing/copy';
import type { Block, LegalDoc } from './types';
import { LEGAL_PATH, LEGAL_UPDATED, SITE_HOST, formatLegalDate, legalHref, type LegalDocId } from '../shared/legal';
import { CONTACT_EMAIL, PHONE_OMITTED_BY_OWNER, SELLER, address, company, formLine } from './facts';
import { TERMS } from './docs/terms';
import { WITHDRAWAL } from './docs/withdrawal';

const ORIGIN = `https://${SITE_HOST}`;
const TOKEN = /\[([^\]]+)\]\(([^)\s]+)\)|\*\*([^*]+)\*\*/g;
const SHY = /\u00AD/g;

/** The inline markup of src/legal/types.ts as text: a link keeps its label and shows where it goes. */
function inline(text: string, lang: Lang, page: LegalDocId): string {
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
      if (doc in LEGAL_PATH) url = ORIGIN + legalHref(doc as LegalDocId, lang, section);
    } else if (h.startsWith('#')) {
      url = ORIGIN + legalHref(page, lang, h.slice(1));
    } else if (h.startsWith('/')) {
      url = ORIGIN + h;          // a page of the site, such as the online withdrawal function
    }
    // a label that is the address itself, with or without https:// (the online withdrawal function's address in
    // the statutory sentence), prints once, as the full address
    if (url === l || url === `https://${l}`) return url;
    return `${l} (${url})`;
  });
}

function block(b: Block, lang: Lang, page: LegalDocId): string {
  if (typeof b === 'string') return inline(b, lang, page);
  if ('ul' in b) return b.ul.map((li) => `- ${inline(li, lang, page)}`).join('\n');
  if ('dl' in b) return b.dl.map(([term, value]) => `${term}: ${inline(value, lang, page)}`).join('\n');
  const lines = b.box.map((line) => `    ${inline(line, lang, page)}`);
  return (b.label ? [`${b.label}:`, ...lines] : lines).join('\n');
}

/** One legal page as plain text: title, date, address of the page, lead, then the sections. Paragraphs are separated
 *  by an empty line and never wrapped (mail clients wrap them). */
export function legalPlainText(id: LegalDocId, doc: LegalDoc, lang: Lang): string {
  const updated = lang === 'de' ? `Stand: ${formatLegalDate(LEGAL_UPDATED, lang)}` : `Last updated: ${formatLegalDate(LEGAL_UPDATED, lang)}`;
  const out: string[] = [doc.title.replace(SHY, '').toUpperCase(), `${updated} · ${ORIGIN}${legalHref(id, lang)}`];
  if (doc.lead) out.push(inline(doc.lead, lang, id));
  doc.sections.forEach((s, i) => {
    out.push(`${doc.numbered ? `${i + 1}. ` : ''}${s.title.replace(SHY, '')}`);
    for (const b of s.blocks) out.push(block(b, lang, id));
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

const LANGS: Lang[] = ['en', 'de'];
const per = <T,>(f: (lang: Lang) => T) => Object.fromEntries(LANGS.map((l) => [l, f(l)])) as Record<Lang, T>;

function mailDoc(id: LegalDocId, doc: LegalDoc, lang: Lang): LegalMailDoc {
  return { title: doc.title.replace(SHY, ''), url: ORIGIN + legalHref(id, lang), text: legalPlainText(id, doc, lang) };
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
    docs: per((lang) => ({
      withdrawal: mailDoc('withdrawal', WITHDRAWAL[lang], lang),
      terms: mailDoc('terms', TERMS[lang], lang),
    })),
    missing: missingLegalFacts(),
    waived: waivedLegalFacts(),
  };
}
