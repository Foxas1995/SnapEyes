// Renders the two kinds of inline markup the legal texts use (see src/legal/types.ts): [label](href) and **bold**.
// The texts are our own constants, never user input, so no HTML is ever parsed.
import type { ReactNode } from 'react';
import type { Lang } from '../landing/copy';
import { LEGAL_PATH, legalHref, type LegalDocId } from '../shared/legal';

const TOKEN = /\[([^\]]+)\]\(([^)\s]+)\)|\*\*([^*]+)\*\*/g;
const LINK = 'text-zinc-100 underline decoration-[#f5c542]/50 underline-offset-4 hover:decoration-[#f5c542] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#f5c542] rounded-sm break-words';

function resolve(href: string, lang: Lang): { url: string; external: boolean } {
  if (href.startsWith('doc:')) {
    const [doc, section = ''] = href.slice(4).split('#');
    if (doc in LEGAL_PATH) return { url: legalHref(doc as LegalDocId, lang, section), external: false };
  }
  return { url: href, external: href.startsWith('http') };
}

export function Inline({ text, lang }: { text: string; lang: Lang }) {
  const out: ReactNode[] = [];
  let last = 0;
  for (const m of text.matchAll(TOKEN)) {
    const at = m.index ?? 0;
    if (at > last) out.push(text.slice(last, at));
    if (m[3] !== undefined) {
      out.push(<strong key={at} className="font-semibold text-white">{m[3]}</strong>);
    } else {
      const { url, external } = resolve(m[2], lang);
      out.push(
        <a key={at} href={url} className={LINK} {...(external ? { target: '_blank', rel: 'noopener noreferrer' } : {})}>
          {m[1]}
        </a>,
      );
    }
    last = at + m[0].length;
  }
  if (last < text.length) out.push(text.slice(last));
  return <>{out}</>;
}
