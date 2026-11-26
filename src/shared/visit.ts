// The visit of the photo step: a random value made when the page loads, held in this page's memory only (no cookie, no storage, gone with the tab).
// /try sends it with each request of a free preview (analyze, deglare, enhance, compose) so that the server's kept copies of that tab's photos,
// restorations and previews lie in one folder for the owner's admin page (api/_lib/keep.py; the owner's decision of 2026-11-26). It names nothing
// about the visitor and is never sent anywhere else.
const make = (): string => {
  let r = '';
  try {
    const a = new Uint8Array(6);
    crypto.getRandomValues(a);
    r = Array.from(a, (b) => b.toString(36).padStart(2, '0')).join('').slice(0, 10);
  } catch {
    r = Math.random().toString(36).slice(2, 12);
  }
  return `${Date.now().toString(36)}-${r}`;
};

export const VISIT: string = make();
