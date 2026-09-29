// An edition of a legal page made from another one: some sections replaced (by id) and new ones inserted after a given
// section, everything else shared word for word. The Australian edition (src/shared/legal.ts legalEdition "au") is made
// this way from the EU texts, so a change to a shared section reaches both. A section id that is not there stops the
// build (the page and the order-mail pack are made at build time), so an edition never silently loses its changes.
import type { LegalDoc, LegalSection } from './types';

export interface DocPatch {
  description?: string;
  lead?: string;
  /** Sections replaced by id: the new section, or a function of the old one. */
  replace?: Record<string, LegalSection | ((old: LegalSection) => LegalSection)>;
  /** New sections inserted after the section with this id. */
  after?: Record<string, LegalSection[]>;
}

export function patchDoc(base: LegalDoc, p: DocPatch): LegalDoc {
  const ids = new Set(base.sections.map((s) => s.id));
  for (const id of [...Object.keys(p.replace ?? {}), ...Object.keys(p.after ?? {})]) {
    if (!ids.has(id)) throw new Error(`legal edition of "${base.title}": no section "${id}" to change`);
  }
  const sections: LegalSection[] = [];
  for (const s of base.sections) {
    const r = p.replace?.[s.id];
    sections.push(r === undefined ? s : typeof r === 'function' ? r(s) : r);
    sections.push(...(p.after?.[s.id] ?? []));
  }
  const seen = new Set<string>();
  for (const s of sections) {
    if (seen.has(s.id)) throw new Error(`legal edition of "${base.title}": section "${s.id}" twice`);
    seen.add(s.id);
  }
  return {
    ...base,
    ...(p.description !== undefined ? { description: p.description } : {}),
    ...(p.lead !== undefined ? { lead: p.lead } : {}),
    sections,
  };
}
